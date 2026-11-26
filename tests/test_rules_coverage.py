from __future__ import annotations

from datetime import date

from rota.domain.models import Assignment, Slot, Staff
from rota.domain.rules.coverage import coverage_findings
from rota.domain.rules.skill import double_bookings, skill_mismatches

D = date(2026, 12, 1)
STAFF = [
    Staff(1, "阿泽", frozenset({"收银", "夜班"})),
    Staff(2, "小林", frozenset({"收银"})),
    Staff(3, "文文", frozenset({"夜班"})),
]


def test_coverage_gap_has_high_severity_and_score():
    found = coverage_findings({D: ["morning", "night"]}, [Assignment(D, "morning", 1)])
    assert len(found) == 1
    assert found[0].rule_id == "coverage.gap"
    assert found[0].severity == "high"
    assert found[0].score == -100


def test_full_coverage_is_silent():
    a = [Assignment(D, "morning", 1), Assignment(D, "night", 3)]
    assert coverage_findings({D: ["morning", "night"]}, a) == []


def test_skill_mismatch_is_reported():
    slots = {"morning": Slot("morning", "收银")}
    found = skill_mismatches([Assignment(D, "morning", 3)], STAFF, slots, 15)
    assert found and found[0].rule_id == "skill.mismatch"
    assert "收银" in found[0].message


def test_skill_match_is_silent():
    slots = {"morning": Slot("morning", "收银")}
    assert skill_mismatches([Assignment(D, "morning", 2)], STAFF, slots, 15) == []


def test_double_booking_is_reported():
    a = [Assignment(D, "morning", 1), Assignment(D, "evening", 1)]
    found = double_bookings(a, 15)
    assert found and found[0].rule_id == "load.double_booked"
    assert found[0].score == -30


def test_two_people_different_shifts_is_fine():
    a = [Assignment(D, "morning", 1), Assignment(D, "evening", 2)]
    assert double_bookings(a, 15) == []
