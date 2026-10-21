import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from phpup.security import readme_text, validate_security


class SecurityTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "patches/8.2").mkdir(parents=True)
        (self.root / "patches/8.2/one.patch").write_text("patch")
        (self.root / "patches/8.2/series").write_text("one.patch\n")
        (self.root / "tests").mkdir()
        (self.root / "tests/regression.phpt").write_text("synthetic test reference")
        self.config = {"versions": [{"branch": "8.2", "version": "8.2.34", "revision": 1}]}
        self.record = {
            "cve": "CVE-2026-12345", "branch": "8.2", "first_revision": 1,
            "advisory": "https://example.org/advisory", "summary": "Synthetic fixture",
            "patches": ["patches/8.2/one.patch"], "tests": ["tests/regression.phpt"],
            "origin": "independent",
        }

    def save(self, fixes):
        (self.root / "security.json").write_text(json.dumps({"reported": [], "fixes": fixes}))

    def test_fix_requires_applied_patches_and_existing_regression(self):
        self.save([self.record])
        self.assertEqual(len(validate_security(self.root, self.config)["fixes"]), 1)
        for field, value in (("patches", ["patches/8.2/missing.patch"]), ("tests", []), ("tests", ["../escape"]), ("first_revision", 2), ("cve", "CVE-pending")):
            with self.subTest(field=field, value=value):
                self.save([{**self.record, field: value}])
                with self.assertRaises(ValueError):
                    validate_security(self.root, self.config)

    def test_duplicate_branch_fix_records_are_rejected(self):
        self.save([self.record, self.record])
        with self.assertRaises(ValueError):
            validate_security(self.root, self.config)

    def test_empty_registry_makes_no_fixed_cve_claim(self):
        self.save([])
        source = "Before\n<!-- phpup:fixed-cves:start -->\nstale\n<!-- phpup:fixed-cves:end -->\nAfter\n"
        rendered = readme_text(self.root, self.config, source)
        self.assertIn("No independently verified CVE fixes", rendered)
        self.assertNotIn("stale", rendered)
        self.assertTrue(rendered.startswith("Before\n"))
        self.assertTrue(rendered.endswith("After\n"))

    def test_fixed_table_identifies_exact_branch_patch_and_test(self):
        self.save([self.record])
        source = "<!-- phpup:fixed-cves:start -->\n<!-- phpup:fixed-cves:end -->"
        rendered = readme_text(self.root, self.config, source)
        for expected in ("CVE-2026-12345", "8.2.34-up.1", "patches/8.2/one.patch", "tests/regression.phpt", "independent"):
            self.assertIn(expected, rendered)

    def test_missing_or_ambiguous_readme_markers_are_rejected(self):
        self.save([])
        for source in ("no markers", "<!-- phpup:fixed-cves:start -->" * 2):
            with self.assertRaises(ValueError):
                readme_text(self.root, self.config, source)


if __name__ == "__main__":
    unittest.main()
