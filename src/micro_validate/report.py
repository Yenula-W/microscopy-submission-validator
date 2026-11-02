"""Render validation results as JSON and Markdown."""
from __future__ import annotations

import datetime as _dt
from collections import Counter
from typing import Any

from . import __version__
from .dataset import Dataset
from .engine import STATUS_RANK, Result, RuleSet, overall_status

LABEL = {"pass": "PASS", "warn": "WARN", "fail": "FAIL", "skip": "SKIP"}


def build_report(ruleset: RuleSet, ds: Dataset, results: list[Result]) -> dict[str, Any]:
    counts = Counter(r.status for r in results)
    fixes = [
        {"rule_id": r.rule_id, "status": r.status, "title": r.title, "fix": r.fix, "examples": r.messages[:5]}
        for r in sorted(results, key=lambda r: -STATUS_RANK[r.status])
        if r.status in ("fail", "warn")
    ]
    return {
        "tool": "micro-validate",
        "version": __version__,
        "generated": _dt.datetime.now(_dt.timezone.utc).isoformat(timespec="seconds"),
        "target": {"id": ruleset.target, "name": ruleset.name, "rules_retrieved": ruleset.retrieved},
        "dataset": {
            "root": str(ds.root),
            "metadata_file": ds.metadata_path or None,
            "file_lists": [t.path for t in ds.file_lists],
            "idr_study_file": ds.idr_study_path or None,
            "idr_assay_files": [t.path for t in ds.idr_assays],
            "n_data_files": len(ds.data_files),
            "n_images": len(ds.image_files),
        },
        "overall": overall_status(results),
        "summary": {k: counts.get(k, 0) for k in ("pass", "warn", "fail", "skip")},
        "results": [r.to_dict() for r in results],
        "fixes": fixes,
        "images": [i.to_dict() for i in ds._images.values()],
        "sources": ruleset.sources,
    }


def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def to_markdown(report: dict[str, Any]) -> str:
    t, d, s = report["target"], report["dataset"], report["summary"]
    out = [
        f"# Submission check: {t['name']}",
        "",
        f"**Overall: {LABEL[report['overall']]}** — {s['pass']} pass, {s['warn']} warn, {s['fail']} fail, {s['skip']} skipped",
        "",
        f"- Dataset: `{d['root']}` ({d['n_images']} images, {d['n_data_files']} data files)",
        f"- Metadata: `{d['metadata_file'] or 'none'}`",
    ]
    if d["file_lists"]:
        out.append(f"- File lists: {', '.join(f'`{x}`' for x in d['file_lists'])}")
    if d["idr_study_file"] or d["idr_assay_files"]:
        out.append(f"- IDR study: `{d['idr_study_file'] or 'none'}`; assays: {', '.join(f'`{x}`' for x in d['idr_assay_files']) or 'none'}")
    out += [f"- Rules retrieved: {t['rules_retrieved']} · micro-validate {report['version']}", ""]

    if report["fixes"]:
        out += ["## Fix list", ""]
        for n, f in enumerate(report["fixes"], 1):
            out.append(f"{n}. **[{LABEL[f['status']]}] {f['rule_id']} {f['title']}** — {f['fix']}")
            for ex in f["examples"]:
                out.append(f"   - {ex}")
        out.append("")

    out += ["## All rules", "", "| Status | Rule | Check | Details | Source |", "|---|---|---|---|---|"]
    for r in report["results"]:
        details = "; ".join(r["messages"][:3]) + (" …" if len(r["messages"]) > 3 else "")
        src = " ".join(f"[{i + 1}]({u})" for i, u in enumerate(r["sources"]))
        out.append(f"| {LABEL[r['status']]} | {r['rule_id']} | {_cell(r['title'])} | {_cell(details)} | {src} |")
    out.append("")

    if report["images"]:
        out += ["## Images read", "", "| File | Format | Readable | XYZCT | dtype | Pixel size x/y/z (µm) |", "|---|---|---|---|---|---|"]
        for i in report["images"][:200]:
            sz = "×".join(str(i["sizes"].get(k, "?")) for k in "XYZCT") if i["sizes"] else ""
            ps = "/".join("-" if i["pixel_size_um"].get(a) is None else f"{i['pixel_size_um'][a]:.4g}" for a in "xyz") if i["pixel_size_um"] else ""
            rd = {True: "yes", False: "NO", None: "unverified"}[i["readable"]]
            out.append(f"| `{_cell(i['path'])}` | {i['format']} | {rd} | {sz} | {i['dtype']} | {ps} |")
        if len(report["images"]) > 200:
            out.append(f"\n… {len(report['images']) - 200} more images in the JSON report.")
        out.append("")

    out += ["## Sources", ""]
    for sid, src in report["sources"].items():
        out.append(f"- **{sid}**: [{src['title']}]({src['url']})")
    out.append("")
    return "\n".join(out)
