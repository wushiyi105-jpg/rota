from __future__ import annotations

from datetime import date

from rota.adapters.store import SqliteStore
from rota.app.run import plan_month, replan_with_leave
from rota.domain.models import Staff

TEAM = [
    Staff(1, "阿泽", frozenset({"收银", "夜班"})),
    Staff(2, "小林", frozenset({"收银"})),
    Staff(3, "文文", frozenset({"夜班"})),
    Staff(4, "大刘"),
    Staff(5, "小周", frozenset({"收银"})),
    Staff(6, "阿满", frozenset({"夜班"})),
]


def _store(settings) -> SqliteStore:
    store = SqliteStore(settings.db_path)
    for s in TEAM:
        store.add_staff(s.name, sorted(s.skills))
    return store


def test_replan_only_touches_leave_days(settings):
    store = _store(settings)
    plan_month(store, settings, "2026-12")
    before = store.list_assignments("2026-12")

    replan = replan_with_leave(store, settings, "2026-12", 2, date(2026, 12, 10), date(2026, 12, 11))

    days = {c.day for c in replan.result.changes}
    assert days <= {date(2026, 12, 10), date(2026, 12, 11)}
    assert replan.result.changes, "插了请假还不改班，说明重排没生效"

    after = store.list_assignments("2026-12")
    assert len(after) == len(before), "重排不该凭空多出或少掉班次"
    assert not any(a.staff_id == 2 and a.day in days for a in after), "请假期间不能再排这个人"


def test_replan_does_not_duplicate_leave_rows(settings):
    store = _store(settings)
    plan_month(store, settings, "2026-12")
    replan_with_leave(store, settings, "2026-12", 3, date(2026, 12, 5), date(2026, 12, 5))
    replan_with_leave(store, settings, "2026-12", 3, date(2026, 12, 5), date(2026, 12, 5))
    assert sum(1 for lv in store.list_leaves() if lv.staff_id == 3) == 2


def test_plan_score_is_persisted(settings):
    store = _store(settings)
    plan = plan_month(store, settings, "2026-12")
    assert store.plan_score("2026-12") == plan.result.score
