from __future__ import annotations

from rota.adapters.store import SqliteStore
from rota.doctor import check_config, check_db, check_model, run_doctor


def test_db_check_passes_after_init(settings):
    SqliteStore(settings.db_path)
    check = check_db(settings)
    assert check.ok, check.detail


def test_model_check_is_ok_when_offline(settings):
    check = check_model(settings)
    assert check.ok and "离线" in check.detail


def test_config_check_passes(settings):
    assert check_config(settings).ok


def test_run_doctor_returns_true(settings):
    SqliteStore(settings.db_path)
    checks, ok = run_doctor(settings)
    assert ok
    assert {c.name for c in checks} == {"配置", "数据库", "模型", "webhook"}
