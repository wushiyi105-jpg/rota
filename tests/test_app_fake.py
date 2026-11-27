"""真实内存 Store 跑 plan_month：不建 SQLite，mypy 校验 StorePort。"""

from __future__ import annotations

from datetime import date

from rota.app.run import plan_month
from rota.config import Settings
from rota.domain.models import Assignment, Leave, Staff
from rota.ports import StorePort


class InMemoryStore:
    def list_staff(self) -> list[Staff]:
        return []

    def add_staff(self, name: str, skills: list[str] | None = None) -> int:
        return 1

    def list_leaves(self) -> list[Leave]:
        return []

    def add_leave(self, staff_id: int, start: date, end: date, reason: str = "") -> None:
        return None

    def save_plan(self, month: str, assignments: list[Assignment], score: int) -> None:
        return None

    def list_assignments(self, month: str) -> list[Assignment]:
        return []

    def plan_score(self, month: str) -> int | None:
        return None

    def enqueue(self, kind: str, idem_key: str, payload: dict | str, next_run_at: str) -> bool:
        return True

    def due_jobs(self, now: str) -> list[dict]:
        return []

    def finish_job(self, job_id: int, ok: bool) -> None:
        return None


def test_plan_month_with_memory_store(tmp_path) -> None:
    store: StorePort = InMemoryStore()
    out = plan_month(store, Settings(db_path=tmp_path / "x.db"), "2026-12")
    assert out.days
    assert not (tmp_path / "x.db").exists()
