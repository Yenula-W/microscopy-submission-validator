"""Names-only mirror of a BioImage Archive study from the BioStudies JSON API alone (no FTP crawl).

Writes the study page-tab JSON, one TSV rebuilt from the files API (all file lists merged, columns unioned)
and a zero-byte placeholder per listed file. Disk and list agree by construction, and merged columns leave
cells empty, so file_list_matches / file_list_format / file_list_header are not judged on these inputs.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from fetch import get  # noqa: E402

API = "https://www.ebi.ac.uk/biostudies/api/v1"


def fetch_api_names(acc: str, d: Path, max_rows: int = 6000) -> dict:
    study = get(f"{API}/studies/{acc}")
    rows: list[dict] = []
    start = 0
    while start < max_rows:
        page = json.loads(get(f"{API}/files/{acc}?start={start}&length=1000&metadata=true"))
        rows += page["data"]
        start += 1000
        if start >= page.get("recordsTotal", 0):
            break
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{acc}.json").write_bytes(study)
    skip = {"path", "Size", "type", "isDirectory", "md5"}
    cols = list(dict.fromkeys(k for r in rows for k in r if k not in skip))
    lines = ["\t".join(["Files"] + cols)] + ["\t".join([r["path"]] + [str(r.get(c, "") or "") for c in cols]) for r in rows]
    (d / "api_file_list.tsv").write_text("\n".join(lines) + "\n")
    for r in rows:
        p = d / r["path"]
        if r.get("isDirectory") != "true" and not p.exists():
            p.parent.mkdir(parents=True, exist_ok=True)
            p.touch()
    return {"n_files": len(rows)}


if __name__ == "__main__":
    for a in sys.argv[2:]:
        print(a, fetch_api_names(a, Path(sys.argv[1]) / a))
