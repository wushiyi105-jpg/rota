from __future__ import annotations

from datetime import date

import pytest

from rota.domain.models import Assignment, Leave, Slot
from rota.domain.solver import month_days, parse_month, solve


def test_month_days_handles_lengths():
    assert len(month_days(2026, 12)) == 31
    assert len(month_days(2026, 2)) == 28
    assert len(month_days(2028, 2)) == 29


def test_parse_month_rejects_bad_input():
    with pytest.raises(ValueError):
        parse_month("2026-13")
    with pytest.raises(ValueError):
        parse_month("2026/12")
    with pytest.raises(ValueError):
        parse_month("1999-01")


def test_solver_never_double_books(staff):
    days = month_days(2026, 12)
    slots = [Slot("morning", "收银"), Slot("evening"), Slot("night", "夜班")]
    a = solve(staff, days, slots, [])
    keys = [(x.day, x.kind) for x in a]
    assert len(keys) == len(set(keys))
    per_day: dict[date, set[int]] = {}
    for x in a:
        per_day.setdefault(x.day, set()).add(x.staff_id)
    assert all(len(v) == len(per_day[k]) for k, v in per_day.items())


def test_solver_respects_leave(staff):
    days = month_days(2026, 12)
    leave = Leave(2, date(2026, 12, 10), date(2026, 12, 12))
    a = solve(staff, days, [Slot("morning", "收银")], [leave])
    assert not any(
        x.staff_id == 2 and date(2026, 12, 10) <= x.day <= date(2026, 12, 12) for x in a
    )


def test_solver_respects_skill(staff):
    days = [date(2026, 12, 1)]
    a = solve(staff, days, [Slot("night", "夜班")], [])
    assert a and all(x.staff_id in (1, 3) for x in a)


def test_solver_keeps_valid_assignments(staff):
    days = month_days(2026, 12)
    slots = [Slot("morning", "收银"), Slot("evening")]
    first = solve(staff, days, slots, [])
    keep = [x for x in first if x.day == date(2026, 12, 3)]
    second = solve(staff, days, slots, [], keep=keep)
    for x in keep:
        assert x in second, "旧班表里没受影响的班必须原样保留"


def test_solver_fills_gap_when_keeper_is_on_leave(staff):
    days = [date(2026, 12, 10), date(2026, 12, 11)]
    slots = [Slot("morning", "收银")]
    first = solve(staff, days, slots, [])
    leave = Leave(first[0].staff_id, date(2026, 12, 10), date(2026, 12, 10))
    second = solve(staff, days, slots, [leave], keep=first)
    assert all(not (x.staff_id == leave.staff_id and x.day == leave.start) for x in second)
    assert len(second) == len(first)


def test_assignment_is_hashable_for_diff():
    a = Assignment(date(2026, 12, 1), "morning", 1)
    assert a in {a}
