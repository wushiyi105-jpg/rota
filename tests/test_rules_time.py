from __future__ import annotations

from datetime import date

from rota.domain.models import Assignment, Leave
from rota.domain.rules.consecutive import consecutive_findings
from rota.domain.rules.leave import leave_conflicts
from rota.domain.rules.rest import rest_findings

D = date(2026, 12, 1)


def day(n: int) -> date:
    return D.replace(day=n)


def test_night_then_morning_is_flagged():
    a = [Assignment(day(1), "night", 1), Assignment(day(2), "morning", 1)]
    found = rest_findings(a, 11, 8)
    assert len(found) == 1
    assert found[0].rule_id == "rest.night_to_morning"
    assert found[0].score == -8


def test_night_then_evening_is_fine():
    a = [Assignment(day(1), "night", 1), Assignment(day(2), "evening", 1)]
    assert rest_findings(a, 11, 8) == []


def test_consecutive_over_limit_names_the_start():
    a = [Assignment(day(i), "morning", 1) for i in range(1, 8)]
    found = consecutive_findings(a, max_days=5, weight=6)
    assert found and found[0].rule_id == "consecutive.over_limit"
    assert "2026-12-01" in found[0].message


def test_consecutive_within_limit_is_silent():
    a = [Assignment(day(i), "morning", 1) for i in range(1, 5)]
    assert consecutive_findings(a, max_days=5, weight=6) == []


def test_leave_conflict_carries_reason():
    a = [Assignment(day(3), "morning", 2)]
    found = leave_conflicts(a, [Leave(2, day(2), day(4), "事假")])
    assert found and found[0].rule_id == "leave.conflict"
    assert "事假" in found[0].message


def test_leave_outside_window_is_silent():
    a = [Assignment(day(5), "morning", 2)]
    assert leave_conflicts(a, [Leave(2, day(2), day(4))]) == []
