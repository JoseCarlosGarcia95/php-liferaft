#!/usr/bin/env python3
"""Prepare auditable PHP builds without third-party Python dependencies."""

import argparse
import json
from pathlib import Path
import sys

from phpup.manifest import load_manifest, version_entry
from phpup.source import prepare
from phpup.security import readme_text


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("validate")
    matrix = commands.add_parser("matrix")
    matrix.add_argument("--branch")
    info = commands.add_parser("info")
    info.add_argument("--branch", required=True)
    sources = commands.add_parser("prepare")
    selection = sources.add_mutually_exclusive_group(required=True)
    selection.add_argument("--branch")
    selection.add_argument("--all", action="store_true")
    sources.add_argument("--output", type=Path)
    readme = commands.add_parser("readme")
    mode = readme.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args()
    config = load_manifest(args.root)
    if args.command == "validate":
        print(f"Validated {len(config['versions'])} PHP branches")
    elif args.command == "matrix":
        versions = config["versions"]
        if args.branch:
            version_entry(config, args.branch)
            versions = [entry for entry in versions if entry["branch"] == args.branch]
        print(json.dumps({"branch": [entry["branch"] for entry in versions]}))
    elif args.command == "info":
        entry = version_entry(config, args.branch)
        print(json.dumps({**entry, "build": config["build"], "name": f"php-{entry['version']}-up.{entry['revision']}"}))
    elif args.command == "prepare":
        branches = [entry["branch"] for entry in config["versions"]] if args.all else [args.branch]
        for branch in branches:
            print(prepare(args.root, branch, args.output), flush=True)
    elif args.command == "readme":
        path = args.root / "README.md"
        original = path.read_text()
        expected = readme_text(args.root, config, original)
        if args.write:
            path.write_text(expected)
        elif original != expected:
            raise ValueError("README CVE table is stale; run readme --write")
        print("README CVE table is consistent")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError) as error:
        sys.exit(f"error: {error}")
