"""公平：周末与节假日算两次权重，差距超过 1 就说明。"""

from __future__ import annotations

from collections import Counter
from datetime import date

from ..models import Assignment, Finding, Staff

WEEKEND_WEIGHT = 2


def weight_of(day: date, holidays: set[date] | None = None) -> int:
    if holidays and day in holidays:
        return WEEKEND_WEIGHT
    return WEEKEND_WEIGHT if day.weekday() >= 5 else 1


def fairness_counts(
    assignments: list[Assignment], staff: list[Staff], holidays: set[date] | None = None
) -> dict[int, int]:
    counter: Counter[int] = Counter()
    for a in assignments:
        counter[a.staff_id] += weight_of(a.day, holidays)
    for s in staff:
        counter.setdefault(s.id, 0)
    return dict(counter)


def fairness_finding(
    counts: dict[int, int], names: dict[int, str], weight: int
) -> Finding | None:
    if len(counts) < 2:
        return None
    hi_staff, hi = max(counts.items(), key=lambda kv: (kv[1], -kv[0]))
    lo_staff, lo = min(counts.items(), key=lambda kv: (kv[1], kv[0]))
    spread = hi - lo
    if spread <= 1:
        return None
    severity = "high" if spread > 3 else "warn"
    return Finding(
        rule_id="fairness.spread",
        severity=severity,
        message=f"加权班次差 {spread}（{names[hi_staff]} {hi} / {names[lo_staff]} {lo}）",
        evidence=f"周末与节假日按 2 计：最高 {names[hi_staff]}={hi}，最低 {names[lo_staff]}={lo}",
        suggestion="把下一个周末班给次数最少的人",
        score=-spread * weight,
    )
