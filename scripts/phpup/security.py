"""Keep claimed CVE coverage tied to real branch patches and regression files."""

from pathlib import Path
import re
from urllib.parse import urlparse

from .manifest import confined, patch_series, read_json, version_entry

START = "<!-- phpup:fixed-cves:start -->"
END = "<!-- phpup:fixed-cves:end -->"
CVE = re.compile(r"CVE-\d{4}-\d{4,}")


def validate_security(root, config):
    root = Path(root).resolve()
    security = read_json(root / "security.json")
    if set(security) != {"reported", "fixes"}:
        raise ValueError("unexpected security registry fields")
    seen = set()
    for report in security["reported"]:
        if not report.get("ids") or not all(CVE.fullmatch(item) for item in report["ids"]):
            raise ValueError("invalid reported CVE identifiers")
        if urlparse(report.get("url", "")).scheme != "https" or report.get("status") not in {"unverified", "under-review", "fixed-upstream"}:
            raise ValueError("invalid reported advisory")
    for record in security["fixes"]:
        required = {"cve", "branch", "first_revision", "advisory", "summary", "patches", "tests", "origin"}
        if set(record) != required or not CVE.fullmatch(record["cve"]):
            raise ValueError("invalid fixed CVE record")
        identity = (record["cve"], record["branch"])
        if identity in seen:
            raise ValueError(f"duplicate CVE branch coverage: {identity}")
        seen.add(identity)
        entry = version_entry(config, record["branch"])
        revision = record["first_revision"]
        if type(revision) is not int or not 0 < revision <= entry["revision"]:
            raise ValueError("fixed CVE revision is not included in this build")
        if urlparse(record["advisory"]).scheme != "https" or record["origin"] not in {"upstream", "independent"}:
            raise ValueError("invalid fixed CVE origin")
        applied = set(patch_series(root, record["branch"]))
        if not record["patches"] or not record["tests"]:
            raise ValueError("fixed CVE requires patches and regression evidence")
        for name in record["patches"]:
            if confined(root, name) not in applied:
                raise ValueError(f"fixed CVE patch is not applied: {name}")
        for name in record["tests"]:
            if not confined(root, name).is_file():
                raise ValueError(f"missing CVE regression test: {name}")
    return security


def readme_text(root, config, source):
    security = validate_security(root, config)
    if source.count(START) != 1 or source.count(END) != 1 or source.index(START) >= source.index(END):
        raise ValueError("README must contain one ordered pair of fixed-CVE markers")
    if not security["fixes"]:
        table = "No independently verified CVE fixes are claimed yet. See the reported issues below.\n"
    else:
        rows = ["| CVE | Branch | First fixed build | Patches | Regression | Origin |", "| --- | --- | --- | --- | --- | --- |"]
        for record in sorted(security["fixes"], key=lambda item: (item["cve"], tuple(map(int, item["branch"].split("."))))):
            entry = version_entry(config, record["branch"])
            patches = ", ".join(f"[{Path(path).name}]({path})" for path in record["patches"])
            tests = ", ".join(f"[{Path(path).name}]({path})" for path in record["tests"])
            rows.append(f"| [{record['cve']}]({record['advisory']}) | {record['branch']} | {entry['version']}-up.{record['first_revision']} | {patches} | {tests} | {record['origin']} |")
        table = "\n".join(rows) + "\n"
    before = source.split(START)[0]
    after = source.split(END)[1]
    return before + START + "\n\n" + table + "\n" + END + after
