import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from phpup.manifest import load_manifest, patch_series
from phpup.source import prepare


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "patches/8.2").mkdir(parents=True)
        (self.root / "patches/8.2/series").write_text("# empty baseline\n")
        self.archive = self.root / "upstream.tar.xz"
        self.write_archive([("php-8.2.34/file.txt", b"original\n")])
        self.config = {
            "source_date_epoch": 1792540800,
            "build": {
                "base_image": "debian:bookworm-slim@sha256:" + "a" * 64,
                "debian_snapshot": "20261020T000000Z",
                "platform": "linux/amd64",
            },
            "versions": [{
                "branch": "8.2", "version": "8.2.34", "revision": 0,
                "url": self.archive.as_uri(),
                "sha256": hashlib.sha256(self.archive.read_bytes()).hexdigest(),
                "configure": [],
            }],
        }
        (self.root / "security.json").write_text('{"reported": [], "fixes": []}\n')
        self.save_config()

    def save_config(self):
        (self.root / "versions.json").write_text(json.dumps(self.config))

    def write_archive(self, entries):
        with tarfile.open(self.archive, "w:xz") as archive:
            for name, data in entries:
                info = tarfile.TarInfo(name)
                info.size = len(data)
                archive.addfile(info, io.BytesIO(data))

    def patch(self, name, text):
        (self.root / "patches/8.2" / name).write_text(text)

    def test_empty_series_and_manifest_are_valid(self):
        self.assertEqual(load_manifest(self.root)["versions"][0]["version"], "8.2.34")
        self.assertEqual(patch_series(self.root, "8.2"), [])

    def test_bad_checksum_and_duplicate_branch_are_rejected(self):
        for value in ("", "0" * 64, "not-a-digest"):
            with self.subTest(value=value):
                self.config["versions"][0]["sha256"] = value
                self.save_config()
                with self.assertRaises(ValueError):
                    load_manifest(self.root)
        self.config["versions"][0]["sha256"] = "b" * 64
        self.config["versions"].append(self.config["versions"][0].copy())
        self.save_config()
        with self.assertRaises(ValueError):
            load_manifest(self.root)

    def test_escaping_duplicate_and_unlisted_patches_are_rejected(self):
        self.patch("one.patch", "contents")
        for series in ("../one.patch\n", "one.patch\none.patch\n", "", "missing.patch\n"):
            with self.subTest(series=series):
                (self.root / "patches/8.2/series").write_text(series)
                with self.assertRaises(ValueError):
                    patch_series(self.root, "8.2")

    def test_preparation_is_deterministic_and_carries_provenance(self):
        first = prepare(self.root, "8.2", self.root / "out1")
        second = prepare(self.root, "8.2", self.root / "out2")
        self.assertEqual(first.read_bytes(), second.read_bytes())
        with tarfile.open(first) as archive:
            self.assertEqual(archive.extractfile("php-8.2.34-up.0/file.txt").read(), b"original\n")
            manifest = json.load(archive.extractfile("php-8.2.34-up.0/phpup/manifest.json"))
        self.assertEqual(manifest["upstream_sha256"], self.config["versions"][0]["sha256"])
        self.assertEqual(manifest["patches"], [])

    def test_checksum_is_checked_even_for_cached_downloads(self):
        prepare(self.root, "8.2", self.root / "out")
        cache = next((self.root / ".cache").glob("*.tar.xz"))
        cache.write_bytes(b"corrupted")
        with self.assertRaisesRegex(ValueError, "checksum"):
            prepare(self.root, "8.2", self.root / "out")

    def test_archive_traversal_and_unsafe_links_are_rejected(self):
        for name in ("../escaped", "/absolute", "php-8.2.34/../../escaped"):
            with self.subTest(name=name):
                self.write_archive([(name, b"bad")])
                self.config["versions"][0]["sha256"] = hashlib.sha256(self.archive.read_bytes()).hexdigest()
                self.save_config()
                with self.assertRaises(ValueError):
                    prepare(self.root, "8.2", self.root / "out")
        with tarfile.open(self.archive, "w:xz") as archive:
            link = tarfile.TarInfo("php-8.2.34/link")
            link.type = tarfile.SYMTYPE
            link.linkname = "/etc/passwd"
            archive.addfile(link)
        self.config["versions"][0]["sha256"] = hashlib.sha256(self.archive.read_bytes()).hexdigest()
        self.save_config()
        with self.assertRaises(ValueError):
            prepare(self.root, "8.2", self.root / "out")

    def test_patch_order_is_enforced_and_conflicts_fail(self):
        self.patch("one.patch", "--- a/file.txt\n+++ b/file.txt\n@@ -1 +1 @@\n-original\n+second\n")
        self.patch("two.patch", "--- a/file.txt\n+++ b/file.txt\n@@ -1 +1 @@\n-second\n+third\n")
        series = self.root / "patches/8.2/series"
        series.write_text("one.patch\ntwo.patch\n")
        self.config["versions"][0]["revision"] = 1
        self.save_config()
        result = prepare(self.root, "8.2", self.root / "out")
        with tarfile.open(result) as archive:
            self.assertEqual(archive.extractfile("php-8.2.34-up.1/file.txt").read(), b"third\n")
        series.write_text("two.patch\none.patch\n")
        with self.assertRaisesRegex(ValueError, "patch"):
            prepare(self.root, "8.2", self.root / "out")


if __name__ == "__main__":
    unittest.main()
