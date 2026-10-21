#!/usr/bin/env python3
"""Run real CLI/FastCGI checks for prepared branches and their session modules."""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from phpup.manifest import load_manifest, version_entry
from phpup.source import prepare


def image_names(root, config, branch):
    archive = prepare(root, branch)
    metadata = json.loads(archive.with_suffix("").with_suffix(".json").read_text())
    entry = version_entry(config, branch)
    platform = os.environ.get("PLATFORM", config["build"]["platform"])
    architecture = platform.split("/")[1]
    prefix = os.environ.get("IMAGE_PREFIX", "phpup")
    suffix = "" if platform == config["build"]["platform"] else "-" + architecture
    base = f"{prefix}:{entry['version']}-up.{entry['revision']}{suffix}"
    return {
        "branch": branch,
        "version": entry["version"],
        "revision": entry["revision"],
        "platform": platform,
        "architecture": architecture,
        "cli": base + "-cli",
        "fpm": base + "-fpm",
        "sdk": f"phpup:{entry['version']}-{metadata['abi_id'][:12]}-{architecture}-sdk",
        "metadata": metadata,
        "archive": str(archive),
    }


def verify(root, config, branch, module, build):
    names = image_names(root, config, branch)
    if build:
        subprocess.run([str(root / "scripts/build-images.sh"), branch], cwd=root, check=True,
                       env=os.environ.copy())
    patch_names = [Path(item["path"]).name for item in names["metadata"]["patches"]]
    require_final = "session-upload-progress-counters.patch" in patch_names
    command = [sys.executable, str(root / "tests/smoke.py"),
               "--cli", names["cli"], "--fpm", names["fpm"], "--version", names["version"]]
    if require_final:
        command.append("--require-final-counter")
    if module:
        module_dir = root / "dist" / branch / "session" / names["architecture"]
        module_path = module_dir / "session.so"
        module_metadata_path = module_dir / "session.json"
        if not module_path.is_file() or not module_metadata_path.is_file():
            raise ValueError(f"missing session module; run scripts/build-session.sh {branch}")
        module_metadata = json.loads(module_metadata_path.read_text())
        if module_metadata["source"]["abi_id"] != names["metadata"]["abi_id"]:
            raise ValueError("session module was built for a different SDK/source identity")
        command += ["--module", str(module_path)]
    subprocess.run(command, cwd=root, check=True)
    names["module"] = str(module_path) if module else None
    return names


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--branch")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--module", action="store_true")
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--print-tags", action="store_true")
    args = parser.parse_args()
    if bool(args.branch) == bool(args.all):
        parser.error("choose exactly one of --branch or --all")
    config = load_manifest(ROOT)
    branches = [entry["branch"] for entry in config["versions"]] if args.all else [args.branch]
    results = []
    for branch in branches:
        if args.print_tags:
            names = image_names(ROOT, config, branch)
            results.append({key: names[key] for key in ("branch", "version", "revision", "platform", "cli", "fpm", "sdk")})
        else:
            results.append(verify(ROOT, config, branch, args.module, args.build))
    print(json.dumps(results if args.all else results[0], indent=2))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError) as error:
        sys.exit(f"error: {error}")
