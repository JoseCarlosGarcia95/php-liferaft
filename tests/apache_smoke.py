#!/usr/bin/env python3
"""Verify an Apache + mod_php image over real HTTP."""

import argparse
import json
from pathlib import Path
import subprocess
import time
import urllib.request


def docker(*args):
    return subprocess.check_output(["docker", *args], text=True).strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True)
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    fixtures = Path(__file__).resolve().parent / "fixtures"
    container = docker("run", "-d", "--rm", "-p", "127.0.0.1::80",
                       "-v", f"{fixtures}:/var/www/html:ro", args.image)
    try:
        port = int(docker("port", container, "80/tcp").rsplit(":", 1)[1])
        data = None
        for _ in range(100):
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/upload.php", timeout=2) as response:
                    data = json.load(response)
                break
            except OSError:
                time.sleep(0.1)
        if data is None:
            raise RuntimeError("Apache did not serve a PHP response")
        if data.get("version") != args.version:
            raise RuntimeError(f"unexpected PHP version: {data.get('version')}")
        if "session" not in data.get("extensions", []):
            raise RuntimeError("session extension is not loaded")
        print(json.dumps({"version": args.version, "image": args.image,
                          "extensions_ok": True, "pid": data.get("pid")}))
    finally:
        logs = docker("logs", container)
        docker("stop", container)
        if logs:
            print(logs, file=__import__("sys").stderr)


if __name__ == "__main__":
    main()
