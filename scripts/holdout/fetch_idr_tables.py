"""Download the published study + assay/library/annotation tables of IDR studies (no images).

Usage: python -I scripts/holdout/fetch_idr_tables.py <out-dir> <repos.txt> [skip-prefixes...]
Writes <out-dir>/idrmeta/<repo>/ with the study file and every table found in the repo,
flattened to their file names (tables over MAX_BYTES are skipped). Used to judge idr_assay_present against real accepted studies.
Needs `gh` (GitHub CLI) for the tree listing.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from fetch import GH_RAW, get  # noqa: E402

MAX_BYTES = 30_000_000  # larger tables (e.g. idr0016, 95 MB) are skipped
TABLE = re.compile(r"(assay|library|annotation)[^/]*\.(txt|tsv|csv)$", re.I)


def main() -> None:
    out = Path(sys.argv[1]) / "idrmeta"
    repos = Path(sys.argv[2]).read_text().split()
    skip = tuple(sys.argv[3:])
    for repo in repos:
        if repo.startswith(skip) or (out / repo).exists():
            continue
        n = fetch_repo(repo, out / repo)
        if n is not None:
            print(repo, n, "tables")


def fetch_repo(repo: str, d: Path) -> int | None:
    """Study file + every assay/library/annotation table of one IDR repo, flattened into d."""
    tree = json.loads(subprocess.run(["gh", "api", f"repos/IDR/{repo}/git/trees/HEAD?recursive=1"],
                                     capture_output=True, text=True).stdout or "{}").get("tree", [])
    blobs = [(t["path"], t.get("size", 0)) for t in tree if t.get("type") == "blob"]
    study = [p for p, _ in blobs if "/" not in p and re.search(r"study.*\.txt$", p, re.I)]
    tables = [p for p, s in blobs if TABLE.search(p) and s < MAX_BYTES]
    if not study:
        return None
    d.mkdir(parents=True, exist_ok=True)
    for p in study + tables:
        try:
            (d / Path(p).name).write_bytes(get(f"{GH_RAW}/{repo}/HEAD/{p}"))
        except Exception as e:
            print("  skip", repo, p, e)
    return len(tables)


if __name__ == "__main__":
    main()
