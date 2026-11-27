"""新功能：整月班表 + 公平账 + 可发群文本。"""

from __future__ import annotations

from datetime import date

from typer.testing import CliRunner

from rota.app.report import fairness_lines, month_message
from rota.domain.catalog import match_template, rules, templates
from rota.domain.models import Assignment, Staff
from rota.iface.cli import app


def test_catalog_has_six_templates_and_twelve_rules() -> None:
    assert len(templates()) == 6
    assert len(rules()) == 12
    assert match_template("城南咖啡")["name"] == "餐饮"


def test_month_message_is_not_truncated() -> None:
    rows = [Assignment(date(2026, 12, d), "morning", 1) for d in range(1, 6)]
    body = month_message("2026-12", rows, {1: "阿泽"})
    assert body.count("阿泽") == 5
    assert "近几天" not in body


def test_fairness_points_out_who_owes() -> None:
    rows = [
        Assignment(date(2026, 12, 5), "morning", 1),
        Assignment(date(2026, 12, 6), "morning", 1),
    ]
    text = "\n".join(fairness_lines(rows, [Staff(1, "阿泽"), Staff(2, "小林")], None))
    assert "小林" in text
    assert "还欠" in text


def test_report_cli_writes_md_and_ics(tmp_path) -> None:
    runner = CliRunner()
    db = str(tmp_path / "rota.db")
    assert runner.invoke(app, ["seed", "--db", db]).exit_code == 0
    out = tmp_path / "班表.md"
    result = runner.invoke(
        app, ["report", "--month", "2026-12", "--db", db, "--no-llm", "--out", str(out)]
    )
    assert result.exit_code == 0
    body = out.read_text(encoding="utf-8")
    assert "# 2026-12 门店班表" in body
    assert "规则库 12 条" in body
    assert "直接发群" in body
    assert out.with_suffix(".ics").exists()
