"""引擎：把一次排班的所有规则跑一遍，出可解释结果。"""

from __future__ import annotations

from datetime import date

from .models import Assignment, Finding, Leave, PlanResult, Slot, Staff
from .rules import (
    consecutive_findings,
    coverage_findings,
    double_bookings,
    fairness_counts,
    fairness_finding,
    leave_conflicts,
    rest_findings,
    skill_mismatches,
)


def evaluate(
    month: str,
    assignments: list[Assignment],
    staff: list[Staff],
    leaves: list[Leave],
    needed: dict[date, list[str]],
    *,
    slots: list[Slot] | None = None,
    weight_fairness: int = 10,
    weight_rest: int = 8,
    weight_consecutive: int = 6,
    weight_skill: int = 15,
    max_consecutive: int = 5,
    min_rest_hours: int = 11,
    holidays: set[date] | None = None,
) -> PlanResult:
    slot_map = {s.kind: s for s in (slots or [])}
    findings: list[Finding] = []
    findings += coverage_findings(needed, assignments)
    findings += leave_conflicts(assignments, leaves)
    findings += double_bookings(assignments, weight_skill)
    if slot_map:
        findings += skill_mismatches(assignments, staff, slot_map, weight_skill)
    findings += rest_findings(assignments, min_rest_hours, weight_rest)
    findings += consecutive_findings(assignments, max_consecutive, weight_consecutive)

    counts = fairness_counts(assignments, staff, holidays)
    fair = fairness_finding(counts, {s.id: s.name for s in staff}, weight_fairness)
    if fair:
        findings.append(fair)

    findings.sort(key=lambda f: (f.score, f.rule_id))
    return PlanResult(month=month, assignments=assignments, findings=findings, counts=counts)


def explain(result: PlanResult) -> str:
    """离线解释：只用已有扣分事实，不补充任何新数字。"""
    if not result.findings:
        return "本月排班没有命中任何约束扣分。"
    lines = [f"总分 {result.score}，主要问题："]
    for f in result.findings[:5]:
        lines.append(f"- {f.message}（{f.score}）：{f.suggestion}")
    return "\n".join(lines)


__all__ = ["evaluate", "explain"]
