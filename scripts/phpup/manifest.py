"""Validate build inputs before touching upstream sources."""

import json
from pathlib import Path, PurePosixPath
import re
from urllib.parse import urlparse


def read_json(path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result
    return json.loads(Path(path).read_text(), object_pairs_hook=unique)


def confined(directory, name):
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError(f"unsafe relative path: {name}")
    candidate = (directory / name).resolve()
    if not candidate.is_relative_to(directory.resolve()):
        raise ValueError(f"escaping path: {name}")
    return candidate


def patch_series(root, branch):
    directory = Path(root) / "patches" / branch
    series = directory / "series"
    if not series.is_file():
        raise ValueError(f"missing patch series: {branch}")
    patches = []
    for line in series.read_text().splitlines():
        name = line.split("#", 1)[0].strip()
        if not name:
            continue
        path = confined(directory, name)
        if path.suffix != ".patch" or not path.is_file() or path in patches:
            raise ValueError(f"invalid or duplicate patch: {branch}/{name}")
        patches.append(path)
    if set(directory.rglob("*.patch")) != set(patches):
        raise ValueError(f"unlisted patch in {branch}")
    return patches


def load_manifest(root):
    root = Path(root)
    config = read_json(root / "versions.json")
    if set(config) != {"source_date_epoch", "build", "versions"}:
        raise ValueError("unexpected manifest fields")
    if type(config["source_date_epoch"]) is not int or config["source_date_epoch"] < 0:
        raise ValueError("invalid source_date_epoch")
    build = config["build"]
    if set(build) != {"base_image", "debian_snapshot", "platform"}:
        raise ValueError("unexpected build fields")
    if not re.fullmatch(r"debian:bookworm-slim@sha256:[0-9a-f]{64}", build["base_image"]):
        raise ValueError("Docker base must be digest-pinned")
    if not re.fullmatch(r"\d{8}T\d{6}Z", build["debian_snapshot"]):
        raise ValueError("invalid Debian snapshot timestamp")
    if build["platform"] != "linux/amd64":
        raise ValueError("published platform must be linux/amd64")
    seen = set()
    if not config["versions"]:
        raise ValueError("no PHP versions configured")
    for entry in config["versions"]:
        if set(entry) != {"branch", "version", "revision", "url", "sha256", "configure"}:
            raise ValueError("unexpected version fields")
        branch = entry["branch"]
        if not re.fullmatch(r"\d+\.\d+", branch) or branch in seen:
            raise ValueError(f"invalid or duplicate branch: {branch}")
        seen.add(branch)
        if not re.fullmatch(re.escape(branch) + r"\.\d+", entry["version"]):
            raise ValueError(f"version does not match branch: {branch}")
        if type(entry["revision"]) is not int or entry["revision"] < 0:
            raise ValueError(f"invalid revision: {branch}")
        if not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"]) or entry["sha256"] == "0" * 64:
            raise ValueError(f"invalid checksum: {branch}")
        url = urlparse(entry["url"])
        if url.scheme not in {"https", "file"}:
            raise ValueError(f"unsupported source URL: {branch}")
        if url.scheme == "https" and url.hostname not in {"www.php.net", "museum.php.net"}:
            raise ValueError(f"source must use an official PHP host: {branch}")
        if not isinstance(entry["configure"], list) or not all(
            isinstance(arg, str) and re.fullmatch(r"--[a-zA-Z0-9_=.,/+:-]+", arg)
            for arg in entry["configure"]
        ):
            raise ValueError(f"invalid configure arguments: {branch}")
        patches = patch_series(root, branch)
        if patches and entry["revision"] == 0:
            raise ValueError(f"patched branch cannot have baseline revision 0: {branch}")
    from .security import validate_security
    validate_security(root, config)
    return config


def version_entry(config, branch):
    for entry in config["versions"]:
        if entry["branch"] == branch:
            return entry
    raise ValueError(f"unsupported PHP branch: {branch}")
