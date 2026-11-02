"""Command line entry point: micro-validate <dataset> --target bia|idr|rembi."""
from __future__ import annotations

import argparse
import json
import sys
from importlib import resources
from pathlib import Path

from . import __version__, checks  # noqa: F401  (registers checks)
from .dataset import load_dataset
from .engine import list_targets, load_ruleset, run_rules
from .report import build_report, to_markdown


def _template(target: str) -> str:
    if target == "idr":
        return (
            "# IDR uses its own tab-separated study and assay templates.\n"
            "# Download them from https://github.com/IDR/idr0000-lastname-example\n"
            "# (idr0000-study_nonHCS.txt, experimentB/idr0000-experimentB-assays.txt) and place them\n"
            "# in the dataset root as <name>-study.txt and <name>-assays.txt.\n"
        )
    return resources.files("micro_validate").joinpath("templates", "submission.yaml").read_text()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        prog="micro-validate",
        description="Validate a microscopy dataset against repository submission requirements.",
    )
    p.add_argument("dataset", nargs="?", help="dataset folder (images + submission.yaml / file list / IDR tables)")
    p.add_argument("-t", "--target", default="bia", help=f"rule set: {', '.join(list_targets())} or a path to a rules YAML")
    p.add_argument("-m", "--metadata", help="submission metadata file (default: <dataset>/submission.yaml)")
    p.add_argument("-o", "--out", help="write <out>.md and <out>.json report files")
    p.add_argument("--json", action="store_true", help="print JSON instead of Markdown to stdout")
    p.add_argument("--no-pixels", action="store_true", help="read headers only, do not decode a pixel block per image")
    p.add_argument("--strict", action="store_true", help="exit non-zero on warnings too")
    p.add_argument("--list-targets", action="store_true", help="list built-in targets and exit")
    p.add_argument("--template", metavar="TARGET", help="print a metadata template for TARGET and exit")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    a = p.parse_args(argv)

    if a.list_targets:
        for t in list_targets():
            rs = load_ruleset(t)
            print(f"{t:8s} {rs.name} ({len(rs.rules)} rules, retrieved {rs.retrieved})")
        return 0
    if a.template:
        sys.stdout.write(_template(a.template))
        return 0
    if not a.dataset:
        p.error("dataset folder is required")

    try:
        ruleset = load_ruleset(a.target)
        ds = load_dataset(a.dataset, metadata=a.metadata, read_pixels=not a.no_pixels)
    except (ValueError, NotADirectoryError, FileNotFoundError) as e:
        print(f"micro-validate: error: {e}", file=sys.stderr)
        return 2
    results = run_rules(ruleset, ds)
    report = build_report(ruleset, ds, results)
    md = to_markdown(report)
    if a.out:
        out = Path(a.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.with_suffix(".md").write_text(md)
        out.with_suffix(".json").write_text(json.dumps(report, indent=2, default=str))
        print(f"wrote {out.with_suffix('.md')} and {out.with_suffix('.json')}", file=sys.stderr)
    print(json.dumps(report, indent=2, default=str) if a.json else md)
    if report["overall"] == "fail" or (a.strict and report["overall"] == "warn"):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
