from __future__ import annotations

from typer.testing import CliRunner

from rota.adapters.store import SqliteStore
from rota.iface.cli import app

runner = CliRunner()


def _db(settings) -> str:
    SqliteStore(settings.db_path).add_staff("阿泽", ["收银"])
    return str(settings.db_path)


def test_plan_json_has_rule_ids(settings):
    db = _db(settings)
    result = runner.invoke(app, ["plan", "--month", "2026-12", "--db", db, "--json"])
    assert result.exit_code == 0, result.output
    assert "coverage.gap" in result.output or "findings" in result.output


def test_bad_month_is_exit_2(settings):
    db = _db(settings)
    result = runner.invoke(app, ["plan", "--month", "2026-13", "--db", db])
    assert result.exit_code == 2
    assert "❌" in result.output


def test_plan_on_empty_db_is_exit_1(settings):
    db = str(settings.db_path)
    result = runner.invoke(app, ["plan", "--month", "2026-12", "--db", db])
    assert result.exit_code == 1


def test_unknown_export_format_is_exit_2(settings):
    db = str(settings.db_path)
    result = runner.invoke(app, ["export", "--month", "2026-12", "--format", "pdf", "--db", db])
    assert result.exit_code == 2


def test_replan_rejects_reversed_dates(settings):
    db = _db(settings)
    result = runner.invoke(
        app,
        ["replan", "--month", "2026-12", "--staff-id", "1", "--start", "2026-12-10", "--end", "2026-12-08", "--db", db],
    )
    assert result.exit_code == 2
