from __future__ import annotations

from datetime import date

from rota.domain.models import Assignment, Staff
from rota.domain.rules.fairness import fairness_counts, fairness_finding, weight_of


def test_weekend_weighs_double():
    # 2026-12-05 是周六
    assert weight_of(date(2026, 12, 5)) == 2
    assert weight_of(date(2026, 12, 3)) == 1


def test_holiday_weighs_double():
    assert weight_of(date(2026, 12, 3), {date(2026, 12, 3)}) == 2


def test_counts_include_people_with_zero():
    counts = fairness_counts(
        [Assignment(date(2026, 12, 5), "morning", 1)], [Staff(1, "A"), Staff(2, "B")]
    )
    assert counts == {1: 2, 2: 0}


def test_spread_is_flagged_with_rule_id():
    counts = {1: 6, 2: 1, 3: 1}
    f = fairness_finding(counts, {1: "阿泽", 2: "小林", 3: "文文"}, 10)
    assert f is not None
    assert f.rule_id == "fairness.spread"
    assert f.score == -50
    assert "6" in f.evidence and "1" in f.evidence


def test_small_spread_is_silent():
    assert fairness_finding({1: 3, 2: 2}, {1: "A", 2: "B"}, 10) is None
