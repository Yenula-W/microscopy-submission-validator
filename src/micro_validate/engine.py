"""Rules engine: load YAML rule sets, dispatch rules to registered checks, collect results.

Kept independent of how a dataset is discovered or how images are read, so other tools
(e.g. microscopy-metadata-repair) can reuse it with their own context object and checks.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path
from typing import Any, Callable

import yaml

STATUS_RANK = {"pass": 0, "skip": 1, "warn": 2, "fail": 3}
SEVERITIES = ("fail", "warn")


@dataclass
class Issue:
    """One problem found by a check. level 'problem' takes the rule's severity, 'warning' is always warn."""

    level: str
    message: str


class SkipCheck(Exception):
    """Raised by a check when it does not apply (e.g. no image files to compare)."""


@dataclass
class Rule:
    id: str
    title: str
    check: str
    severity: str = "fail"
    params: dict[str, Any] = field(default_factory=dict)
    fix: str = ""
    sources: list[str] = field(default_factory=list)


@dataclass
class RuleSet:
    target: str
    name: str
    description: str
    retrieved: str
    sources: dict[str, dict[str, str]]
    rules: list[Rule]

    def source_urls(self, rule: Rule) -> list[str]:
        return [self.sources[s]["url"] for s in rule.sources]


@dataclass
class Result:
    rule_id: str
    title: str
    status: str
    severity: str
    messages: list[str]
    fix: str
    sources: list[str]

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


CheckFn = Callable[[Any, dict[str, Any]], list[Issue]]
CHECKS: dict[str, CheckFn] = {}


def check(name: str) -> Callable[[CheckFn], CheckFn]:
    """Register a check function under a name usable from rule YAML."""

    def deco(fn: CheckFn) -> CheckFn:
        CHECKS[name] = fn
        return fn

    return deco


def list_targets() -> list[str]:
    return sorted(p.name[:-5] for p in resources.files("micro_validate").joinpath("rules").iterdir() if p.name.endswith(".yaml"))


def load_ruleset(target_or_path: str | Path) -> RuleSet:
    p = Path(target_or_path)
    if p.suffix in (".yaml", ".yml") and p.exists():
        text = p.read_text()
    else:
        f = resources.files("micro_validate").joinpath("rules").joinpath(f"{target_or_path}.yaml")
        if not f.is_file():
            raise ValueError(f"unknown target {target_or_path!r}; known: {', '.join(list_targets())}")
        text = f.read_text()
    data = yaml.safe_load(text)
    sources = data.get("sources", {})
    rules = []
    seen = set()
    for r in data["rules"]:
        rule = Rule(
            id=r["id"],
            title=r["title"],
            check=r["check"],
            severity=r.get("severity", "fail"),
            params=r.get("params", {}) or {},
            fix=r.get("fix", ""),
            sources=r.get("sources", []),
        )
        if rule.id in seen:
            raise ValueError(f"duplicate rule id {rule.id}")
        seen.add(rule.id)
        if rule.severity not in SEVERITIES:
            raise ValueError(f"{rule.id}: severity must be one of {SEVERITIES}")
        for s in rule.sources:
            if s not in sources:
                raise ValueError(f"{rule.id}: unknown source {s!r}")
        rules.append(rule)
    return RuleSet(
        target=data["target"],
        name=data["name"],
        description=data.get("description", ""),
        retrieved=str(data.get("retrieved", "")),
        sources=sources,
        rules=rules,
    )


def run_rules(ruleset: RuleSet, ctx: Any, max_messages: int = 20) -> list[Result]:
    results = []
    for rule in ruleset.rules:
        fn = CHECKS.get(rule.check)
        if fn is None:
            raise ValueError(f"{rule.id}: no check registered named {rule.check!r}")
        try:
            issues = fn(ctx, rule.params)
            if not issues:
                status = "pass"
            elif any(i.level == "problem" for i in issues):
                status = rule.severity
            else:
                status = "warn"
            messages = [i.message for i in issues]
        except SkipCheck as e:
            status, messages = "skip", [str(e)]
        except Exception as e:  # a crashing check must not hide the other results
            status, messages = "fail", [f"check crashed: {type(e).__name__}: {e}"]
        if len(messages) > max_messages:
            messages = messages[:max_messages] + [f"... and {len(messages) - max_messages} more"]
        results.append(
            Result(rule.id, rule.title, status, rule.severity, messages, rule.fix, ruleset.source_urls(rule))
        )
    return results


def overall_status(results: list[Result]) -> str:
    """Worst status; skipped rules do not count against the dataset."""
    return max((r.status for r in results if r.status != "skip"), key=STATUS_RANK.__getitem__, default="pass")
