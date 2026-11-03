"""Names-only mirrors of BioImage Archive studies, for judging file-list checks.

Usage: python -I scripts/holdout/fetch_names.py <out-dir> S-BIADnnn [...]
For each accession, creates <out-dir>/names/<acc>/ holding:
  - the study page-tab JSON,
  - every file-list TSV the submitter uploaded (or a TSV rebuilt from the JSON list),
  - a zero-byte placeholder for every file actually present in the study's FTP Files/ tree.
Only names and paths are real, so only name-based checks (file_list_*, filename_chars) are meaningful.
"""
from __future__ import annotations

import json
import re
import sys
import urllib.parse
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from fetch import _iter_attrs, _json_list_to_tsv, get  # noqa: E402

MAX_ENTRIES = 3000


class _Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href", "")
            if href and not href.startswith(("?", "/", "http", "../")):
                self.links.append(urllib.parse.unquote(href))


def crawl(url: str, rel: str = "", out: list[str] | None = None) -> list[str]:
    out = [] if out is None else out
    p = _Links()
    p.feed(get(url + "/").decode("utf-8", "replace"))
    for link in p.links:
        if len(out) > MAX_ENTRIES:
            raise RuntimeError("too many files")
        if link.endswith("/"):
            crawl(f"{url}/{urllib.parse.quote(link[:-1])}", f"{rel}{link}", out)
        else:
            out.append(f"{rel}{link}")
    return out


def main() -> None:
    root = Path(sys.argv[1]) / "names"
    for acc in sys.argv[2:]:
        d = root / acc
        if d.exists():
            print("have", acc)
            continue
        info = json.loads(get(f"https://www.ebi.ac.uk/biostudies/api/v1/studies/{acc}/info"))
        http = info["httpLink"]
        study = get(f"https://www.ebi.ac.uk/biostudies/api/v1/studies/{acc}")
        files = crawl(f"{http}/Files")
        lists = sorted({a["value"] for a in _iter_attrs(json.loads(study)) if a.get("name") == "File List"})
        d.mkdir(parents=True)
        (d / f"{acc}.json").write_bytes(study)
        for fl in lists:
            stem = re.sub(r"\.(json|tsv|xlsx?)$", "", fl, flags=re.I)
            uploaded = [f for f in files if re.sub(r"\.(json|tsv|xlsx?)$", "", f, flags=re.I) == stem]
            tsv = next((f for f in uploaded if f.lower().endswith(".tsv")), None)
            data = get(f"{http}/Files/{urllib.parse.quote(tsv)}") if tsv else _json_list_to_tsv(get(f"{http}/Files/{urllib.parse.quote(fl)}"))
            (d / f"{stem}.tsv").parent.mkdir(parents=True, exist_ok=True)
            (d / f"{stem}.tsv").write_bytes(data)
            for f in uploaded:  # the list itself (any format) is not a data file
                files.remove(f)
        for f in files:
            p = d / f
            p.parent.mkdir(parents=True, exist_ok=True)
            p.touch()
        print(acc, len(files), "files,", len(lists), "lists")


if __name__ == "__main__":
    main()
