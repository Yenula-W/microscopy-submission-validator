"""Run micro-validate on every held-out input and every target; collect stats and findings.

Usage: python scripts/holdout/run_eval.py <out-dir> [micro-validate executable]
Writes <out-dir>/runs.csv, <out-dir>/findings.csv and <out-dir>/sample.csv (stratified sample for hand checking).
"""
from __future__ import annotations

import csv
import json
import random
import subprocess
import sys
import time
from collections import defaultdict
from pathlib import Path

import yaml

TARGETS = ["bia", "idr", "rembi"]
PARTIAL_KINDS = {"bia", "idr", "names", "idrmeta"}  # subsets of accepted submissions


def check_types() -> dict[str, str]:
    import micro_validate

    rules = Path(micro_validate.__file__).parent / "rules"
    out = {}
    for f in rules.glob("*.yaml"):
        for r in yaml.safe_load(f.read_text())["rules"]:
            out[r["id"]] = r["check"]
    return out


def main() -> None:
    out = Path(sys.argv[1])
    exe = sys.argv[2] if len(sys.argv) > 2 else "micro-validate"
    manifest = json.loads((out / "manifest.json").read_text())
    rep_dir = out / "reports"
    rep_dir.mkdir(exist_ok=True)
    types = check_types()
    runs, findings = [], []
    for hid in sorted(manifest):
        d = out / "inputs" / hid
        partial = manifest[hid]["kind"] in PARTIAL_KINDS
        for t in TARGETS:
            base = rep_dir / f"{hid}-{t}"
            cmd = [exe, str(d), "-t", t, "-o", str(base)] + (["--partial"] if partial else [])
            t0 = time.perf_counter()
            p = subprocess.run(cmd, capture_output=True, text=True)
            dt = time.perf_counter() - t0
            crashed = p.returncode not in (0, 1)
            crash_msgs = []
            summary = {}
            if not crashed:
                rep = json.loads(base.with_suffix(".json").read_text())
                summary = rep["summary"]
                for r in rep["results"]:
                    crash_msgs += [m for m in r["messages"] if "check crashed" in m]
                    if r["status"] in ("warn", "fail"):
                        for m in r["messages"]:
                            findings.append({"input": hid, "kind": manifest[hid]["kind"], "target": t, "rule": r["rule_id"],
                                             "check": types.get(r["rule_id"], "?"), "status": r["status"],
                                             "message": m})
            size = sum(base.with_suffix(s).stat().st_size for s in (".md", ".json") if base.with_suffix(s).exists())
            runs.append({"input": hid, "target": t, "exit": p.returncode, "crashed": crashed or bool(crash_msgs),
                         "seconds": round(dt, 2), "report_bytes": size, "partial": partial,
                         **{k: summary.get(k, "") for k in ("pass", "warn", "fail", "skip")},
                         "stderr": (p.stderr.strip().splitlines() or [""])[-1][:200] if crashed else "",
                         "crash_msgs": "; ".join(crash_msgs)[:300]})
            print(f"{hid:28s} {t:5s} exit={p.returncode} {dt:6.2f}s {summary}")
    with open(out / "runs.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(runs[0]))
        w.writeheader()
        w.writerows(runs)
    with open(out / "findings.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["input", "kind", "target", "rule", "check", "status", "message"])
        w.writeheader()
        w.writerows(findings)
    # stratified sample: >=3 per check type (all if fewer), then fill to >=60 at random
    rng = random.Random(20261102)
    by_check = defaultdict(list)
    for f_ in findings:
        by_check[f_["check"]].append(f_)
    sample = []
    for c, items in sorted(by_check.items()):
        rng.shuffle(items)
        sample += items[:4]
    rest = [f_ for f_ in findings if f_ not in sample]
    rng.shuffle(rest)
    sample += rest[: max(0, 64 - len(sample))]
    with open(out / "sample.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["n", "input", "kind", "target", "rule", "check", "status", "message", "verdict", "note"])
        w.writeheader()
        for i, s in enumerate(sample, 1):
            w.writerow({"n": i, **s, "verdict": "", "note": ""})
    print(f"\n{len(runs)} runs, {sum(r['crashed'] for r in runs)} crashed, {len(findings)} findings, sample {len(sample)}")


if __name__ == "__main__":
    main()
