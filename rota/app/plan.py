"""用例：生成一个月的班表（可带上一次班表做最小改动重排）。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from ..config import Settings
from ..domain import engine
from ..domain.models import Assignment, Leave, PlanResult, Slot, Staff
from ..domain.solver import month_days, parse_month, solve


@dataclass
class Plan:
    result: PlanResult
    days: list[date]


def default_slots(settings: Settings) -> list[Slot]:
    return [Slot(kind=kind, required_skill=skill) for kind, skill in settings.slot_specs]


def build_month(
    year: int,
    month: int,
    staff: list[Staff],
    leaves: list[Leave],
    settings: Settings,
    *,
    slots: list[Slot] | None = None,
    holidays: set[date] | None = None,
    keep: list[Assignment] | None = None,
) -> Plan:
    days = month_days(year, month)
    use_slots = slots if slots is not None else default_slots(settings)
    assignments = solve(
        staff,
        days,
        use_slots,
        leaves,
        max_consecutive=settings.max_consecutive_days,
        holidays=holidays,
        keep=keep,
    )
    needed = {d: [s.kind for s in use_slots for _ in range(max(1, s.headcount))] for d in days}
    result = engine.evaluate(
        f"{year:04d}-{month:02d}",
        assignments,
        staff,
        leaves,
        needed,
        slots=use_slots,
        weight_fairness=settings.weight_fairness,
        weight_rest=settings.weight_rest,
        weight_consecutive=settings.weight_consecutive,
        weight_skill=settings.weight_skill,
        max_consecutive=settings.max_consecutive_days,
        min_rest_hours=settings.min_rest_hours,
        holidays=holidays,
    )
    return Plan(result=result, days=days)


def build_for(month: str, staff: list[Staff], leaves: list[Leave], settings: Settings, **kw) -> Plan:
    year, mon = parse_month(month)
    return build_month(year, mon, staff, leaves, settings, **kw)
