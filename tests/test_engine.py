from __future__ import annotations

from datetime import date

from rota.domain.engine import evaluate, explain
from rota.domain.models import Assignment, Slot, Staff


def _staff() -> list[Staff]:
    return [Staff(1, "阿泽", frozenset({"收银"})), Staff(2, "小林", frozenset({"收银"}))]


def test_engine_orders_findings_by_score():
    staff = _staff()
    a = [Assignment(date(2026, 12, 1), "morning", 1)]
    result = evaluate("2026-12", a, staff, [], {date(2026, 12, 1): ["morning", "night"]})
    assert result.findings
    assert result.findings[0].score <= result.findings[-1].score
    assert result.score < 0


def test_engine_flags_skill_mismatch_when_slot_declared():
    staff = _staff()
    a = [Assignment(date(2026, 12, 1), "night", 2)]
    result = evaluate(
        "2026-12",
        a,
        staff,
        [],
        {date(2026, 12, 1): ["night"]},
        slots=[Slot("night", "夜班")],
    )
    assert any(f.rule_id == "skill.mismatch" for f in result.findings)


def test_explain_mentions_score():
    staff = _staff()
    result = evaluate("2026-12", [], staff, [], {date(2026, 12, 1): ["morning"]})
    assert "总分" in explain(result)
