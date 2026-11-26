from __future__ import annotations

from datetime import date

from rota.adapters.store import SqliteStore
from rota.app import jobs as job_app
from rota.app.run import plan_month


class FakeNotifier:
    def __init__(self, ok: bool = True) -> None:
        self.ok = ok
        self.sent: list[str] = []

    def send(self, text: str) -> bool:
        self.sent.append(text)
        return self.ok


def test_enqueue_is_idempotent(settings):
    store = SqliteStore(settings.db_path)
    assert store.enqueue("daily_digest", "k1", {"month": "2026-12"}, "2026-12-01T08:00:00") is True
    assert store.enqueue("daily_digest", "k1", {"month": "2026-12"}, "2026-12-01T08:00:00") is False


def test_due_jobs_only_returns_due(settings):
    store = SqliteStore(settings.db_path)
    store.enqueue("daily_digest", "now", {}, "2026-12-01T08:00:00")
    store.enqueue("daily_digest", "later", {}, "2026-12-09T08:00:00")
    due = store.due_jobs("2026-12-02T08:00:00")
    assert [j["idem_key"] for j in due] == ["now"]


def test_run_due_sends_and_marks_done(settings, staff):
    store = SqliteStore(settings.db_path)
    for s in staff:
        store.add_staff(s.name, sorted(s.skills))
    plan_month(store, settings, "2026-12")
    job_app.enqueue_daily_digest(store, "2026-12", date(2026, 12, 1))
    notifier = FakeNotifier()
    results = job_app.run_due(store, settings, notifier, "2026-12-01T09:00:00")
    assert results and results[0]["sent"] is True
    assert notifier.sent and "2026-12" in notifier.sent[0]
    assert store.due_jobs("2026-12-02T00:00:00") == []


def test_failed_push_stays_pending(settings, staff):
    store = SqliteStore(settings.db_path)
    for s in staff:
        store.add_staff(s.name, sorted(s.skills))
    job_app.enqueue_daily_digest(store, "2026-12", date(2026, 12, 1))
    job_app.run_due(store, settings, FakeNotifier(ok=False), "2026-12-01T09:00:00")
    due = store.due_jobs("2026-12-02T00:00:00")
    assert due, "推送失败的任务必须留着重试"


def test_digest_says_no_shift_when_empty(settings):
    store = SqliteStore(settings.db_path)
    assert "没有排班" in job_app.digest_text(store, "2026-12", date(2026, 12, 1))
