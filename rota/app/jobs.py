"""后台任务：每天扫一次下周班表，把要上班的人推给群。

幂等键 = 任务类型 + 月份 + 日期，重复入队只留一条。
"""

from __future__ import annotations

from datetime import date, datetime, timedelta

from ..config import Settings
from ..domain.models import KIND_LABELS
from ..ports import NotifierPort, StorePort


def enqueue_daily_digest(store: StorePort, month: str, run_date: date) -> bool:
    return store.enqueue(
        kind="daily_digest",
        idem_key=f"daily_digest:{month}:{run_date.isoformat()}",
        payload={"month": month},
        next_run_at=f"{run_date.isoformat()}T08:00:00",
    )


def digest_text(store: StorePort, month: str, run_date: date) -> str:
    staff = {s.id: s.name for s in store.list_staff()}
    rows = [
        a
        for a in store.list_assignments(month)
        if run_date <= a.day <= run_date + timedelta(days=6)
    ]
    if not rows:
        return f"{month} 未来 7 天没有排班。"
    lines = [f"{month} 未来 7 天："]
    for a in sorted(rows, key=lambda x: (x.day, x.kind)):
        lines.append(f"{a.day.isoformat()} {KIND_LABELS.get(a.kind, a.kind)} {staff.get(a.staff_id, a.staff_id)}")
    return "\n".join(lines)


def run_due(
    store: StorePort, settings: Settings, notifier: NotifierPort, now: str
) -> list[dict]:
    """跑所有到期任务，返回每条的处理结果。"""
    results: list[dict] = []
    for job in store.due_jobs(now):
        text = digest_text(store, job["payload"].get("month", now[:7]), date.fromisoformat(now[:10]))
        ok = notifier.send(text)
        store.finish_job(job["id"], ok)
        results.append({"id": job["id"], "kind": job["kind"], "sent": ok})
    return results


def next_run(now: datetime) -> str:
    return (now + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0).isoformat()
