"""Verify, patch and deterministically package upstream PHP releases."""

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import posixpath
import re
import shutil
import subprocess
import tarfile
import tempfile
import time
from urllib.request import urlopen

from .manifest import load_manifest, patch_series, read_json, version_entry


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def download(root, entry):
    cache = Path(root) / ".cache"
    cache.mkdir(exist_ok=True)
    target = cache / f"php-{entry['version']}-{entry['sha256']}.tar.xz"
    if not target.exists():
        temporary = target.with_suffix(".part")
        try:
            for attempt in range(3):
                try:
                    with urlopen(entry["url"], timeout=90) as response, temporary.open("wb") as stream:
                        shutil.copyfileobj(response, stream)
                    break
                except OSError:
                    if attempt == 2:
                        raise
                    time.sleep(attempt + 1)
            if digest(temporary) != entry["sha256"]:
                raise ValueError(f"source checksum mismatch: {entry['version']}")
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
    if digest(target) != entry["sha256"]:
        raise ValueError(f"cached source checksum mismatch: {entry['version']}")
    return target


def extract(archive_path, destination, version):
    expected = f"php-{version}"
    try:
        with tarfile.open(archive_path) as archive:
            members = archive.getmembers()
            if not members:
                raise ValueError("empty upstream archive")
            for member in members:
                path = PurePosixPath(member.name)
                if path.is_absolute() or ".." in path.parts or not path.parts or path.parts[0] != expected:
                    raise ValueError(f"unsafe archive path: {member.name}")
                if not (member.isfile() or member.isdir() or member.issym() or member.islnk()):
                    raise ValueError(f"unsupported archive entry: {member.name}")
                if member.issym() or member.islnk():
                    target = member.linkname
                    resolved = posixpath.normpath(
                        posixpath.join(str(path.parent), target) if member.issym() else target
                    )
                    if PurePosixPath(target).is_absolute() or not resolved.startswith(expected + "/"):
                        raise ValueError(f"unsafe archive link: {member.name}")
            archive.extractall(destination, members=members, filter="data")
    except (tarfile.TarError, OSError) as error:
        raise ValueError(f"invalid upstream archive: {error}") from error
    return Path(destination) / expected


def apply_patch(tree, patch):
    # Validate destination headers before giving patch permission to modify files.
    headers = 0
    for line in patch.read_text().splitlines():
        if line.startswith(("--- ", "+++ ")):
            name = line[4:].split("\t", 1)[0].split(" ", 1)[0]
            if name == "/dev/null":
                continue
            path = PurePosixPath(name)
            if not name.startswith(("a/", "b/")) or ".." in path.parts or len(path.parts) < 2:
                raise ValueError(f"unsafe patch destination: {name}")
            destination = tree.joinpath(*path.parts[1:]).resolve()
            if not destination.is_relative_to(tree.resolve()):
                raise ValueError(f"escaping patch destination: {name}")
            headers += 1
    if not headers:
        raise ValueError(f"patch contains no file headers: {patch.name}")
    result = subprocess.run(
        ["patch", "-p1", "--batch", "--forward", "--fuzz=0", "-i", str(patch)],
        cwd=tree, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        env={**os.environ, "LC_ALL": "C"},
    )
    if result.returncode or re.search(r"\b(offset|fuzz|FAILED|Reversed)\b", result.stdout, re.I):
        raise ValueError(f"patch failed ({patch.name}):\n{result.stdout}")


def prepare(root, branch, output=None):
    root = Path(root).resolve()
    config = load_manifest(root)
    entry = version_entry(config, branch)
    patches = patch_series(root, branch)
    upstream = download(root, entry)
    output = Path(output or root / "dist") / branch
    output.mkdir(parents=True, exist_ok=True)
    name = f"php-{entry['version']}-up.{entry['revision']}"
    security = read_json(root / "security.json")
    manifest = {
        "branch": branch, "version": entry["version"], "revision": entry["revision"],
        "upstream_url": entry["url"], "upstream_sha256": entry["sha256"],
        "source_date_epoch": config["source_date_epoch"],
        "configure": entry["configure"], "build": config["build"],
        "patches": [{"path": str(p.relative_to(root)), "sha256": digest(p)} for p in patches],
        "fixed_cves": [record for record in security["fixes"] if record["branch"] == branch],
    }
    # Session-only patches do not change the SDK's core/toolchain identity.
    core_patches = []
    for patch in patches:
        destinations = [line[4:].split()[0] for line in patch.read_text().splitlines() if line.startswith("+++ ")]
        if any(name != "/dev/null" and not name.startswith("b/ext/session/") for name in destinations):
            core_patches.append(digest(patch))
    recipe_names = ("docker/Dockerfile", "docker/build-php.sh")
    recipes = {name: digest(root / name) for name in recipe_names if (root / name).exists()}
    manifest["abi_id"] = hashlib.sha256(json_bytes({
        "upstream": entry["sha256"], "configure": entry["configure"],
        "build": config["build"], "core_patches": core_patches, "recipes": recipes,
    })).hexdigest()
    with tempfile.TemporaryDirectory(prefix=".prepare-", dir=output) as temporary:
        stage = Path(temporary)
        tree = extract(upstream, stage, entry["version"])
        for patch in patches:
            apply_patch(tree, patch)
        provenance = tree / "phpup"
        if provenance.exists():
            raise ValueError("upstream tree already contains the reserved phpup directory")
        (provenance / "patches").mkdir(parents=True)
        (provenance / "manifest.json").write_bytes(json_bytes(manifest))
        for index, patch in enumerate(patches, 1):
            shutil.copyfile(patch, provenance / "patches" / f"{index:04d}-{patch.name}")
        archive_path = stage / (name + ".tar.xz")
        with tarfile.open(archive_path, "w:xz", format=tarfile.PAX_FORMAT, preset=6) as archive:
            for path in [tree, *sorted(tree.rglob("*"))]:
                relative = path.relative_to(tree)
                info = archive.gettarinfo(str(path), arcname=str(Path(name) / relative))
                info.uid = info.gid = 0
                info.uname = info.gname = ""
                info.mtime = config["source_date_epoch"]
                info.pax_headers = {}
                info.mode = 0o755 if info.isdir() or info.mode & 0o111 else 0o644
                if info.isfile():
                    with path.open("rb") as stream:
                        archive.addfile(info, stream)
                else:
                    archive.addfile(info)
        metadata = stage / (name + ".json")
        metadata.write_bytes(json_bytes({**manifest, "archive_sha256": digest(archive_path)}))
        checksum = stage / (name + ".sha256")
        checksum.write_text(f"{digest(archive_path)}  {archive_path.name}\n{digest(metadata)}  {metadata.name}\n")
        for path in (metadata, checksum, archive_path):
            path.replace(output / path.name)
    return output / archive_path.name
