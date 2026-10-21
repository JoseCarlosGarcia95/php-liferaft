#!/usr/bin/env python3
"""Build exact prepared source inputs, or rebuild only the shared session module."""

import argparse
import json
import os
from pathlib import Path
import shlex
import subprocess

from phpup.manifest import load_manifest, version_entry
from phpup.source import digest, prepare


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("images", "session"))
    parser.add_argument("branch")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    config = load_manifest(root)
    entry = version_entry(config, args.branch)
    archive = prepare(root, args.branch)
    metadata = json.loads(archive.with_suffix("").with_suffix(".json").read_text())
    platform = os.environ.get("PLATFORM", config["build"]["platform"])
    architecture = platform.split("/")[1]
    prefix = os.environ.get("IMAGE_PREFIX", "phpup")
    sdk = f"phpup:{entry['version']}-{metadata['abi_id'][:12]}-{architecture}-sdk"
    suffix = "" if platform == config["build"]["platform"] else "-" + architecture
    base = f"{prefix}:{entry['version']}-up.{entry['revision']}{suffix}"
    source_url = os.environ.get("SOURCE_URL", "https://github.com/JoseCarlosGarcia95/php-liferaft")
    extra = shlex.split(os.environ.get("DOCKER_BUILD_EXTRA_ARGS", ""))
    common = ["docker", "build", "--platform", platform, "--progress=plain", *extra]
    arguments = [
        "--build-arg", f"SOURCE_ARCHIVE={archive.relative_to(root)}",
        "--build-arg", f"SOURCE_SHA256={digest(archive)}",
        "--build-arg", f"SOURCE_URL={source_url}",
        "--build-arg", f"SOURCE_VERSION={entry['version']}",
        "--build-arg", f"PROJECT_REVISION={entry['revision']}",
    ]
    if args.mode == "images":
        image_common = common + ["--load"]
        try:
            revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True, stderr=subprocess.DEVNULL).strip()
        except subprocess.CalledProcessError:
            revision = "uncommitted"
        for target, tag in (("sdk", sdk), ("cli", base + "-cli"), ("fpm", base + "-fpm")):
            command = image_common + ["-f", "docker/Dockerfile", "--target", target, "-t", tag, *arguments,
                "--build-arg", f"BASE_IMAGE={config['build']['base_image']}",
                "--build-arg", f"DEBIAN_SNAPSHOT={config['build']['debian_snapshot']}",
                "--build-arg", f"MAKE_JOBS={os.environ.get('MAKE_JOBS', '4')}",
                "--build-arg", f"REPOSITORY_REVISION={revision}", "."]
            subprocess.run(command, cwd=root, check=True)
        print(json.dumps({"cli": base + "-cli", "fpm": base + "-fpm", "sdk": sdk}))
    else:
        output = root / "dist" / args.branch / "session" / architecture
        output.mkdir(parents=True, exist_ok=True)
        subprocess.run(common + ["-f", "docker/Dockerfile", "--target", "session-export", *arguments,
            "--build-arg", f"BASE_IMAGE={config['build']['base_image']}",
            "--build-arg", f"DEBIAN_SNAPSHOT={config['build']['debian_snapshot']}",
            "--build-arg", f"MAKE_JOBS={os.environ.get('MAKE_JOBS', '4')}",
            "--output", f"type=local,dest={output}", "."], cwd=root, check=True)
        print(output)


if __name__ == "__main__":
    main()
