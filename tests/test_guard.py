from __future__ import annotations

from rota.domain.guard import guard_text

FACTS = (
    "月份 2026-12，员工 4 人，总分 -320。\n"
    "fairness.spread 加权班次差 5（阿泽 9 / 小林 4）（-50）\n"
    "2026-12-05 晚班给阿泽"
)
NAMES = ["阿泽", "小林", "文文", "大刘"]


def test_clean_text_passes():
    text = "建议微调。阿泽的加权班次偏高，把 2026-12-05 的晚班换给小林。"
    kept, reason = guard_text(text, FACTS, NAMES)
    assert reason is None
    assert kept == text


def test_foreign_number_is_rejected():
    text = "建议微调。阿泽这个月上了 15 个班，明显偏多。"
    kept, reason = guard_text(text, FACTS, NAMES)
    assert kept == ""
    assert reason and "15" in reason


def test_foreign_person_is_rejected():
    text = "建议把班换给阿强，他更合适。"
    kept, reason = guard_text(text, FACTS, NAMES)
    assert kept == ""
    assert reason and "阿强" in reason


def test_foreign_date_is_rejected():
    text = "把 2026-12-19 的夜班换个人。"
    kept, reason = guard_text(text, FACTS, NAMES)
    assert kept == ""
    assert reason and "2026-12-19" in reason


def test_empty_output_is_rejected():
    kept, reason = guard_text("   ", FACTS, NAMES)
    assert kept == ""
    assert reason == "模型返回为空"
