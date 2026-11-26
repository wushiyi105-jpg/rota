"""求解：贪心 + 保留既有排班，插入请假后只动必要的人。"""

from __future__ import annotations

from datetime import date, timedelta

from .models import Assignment, Leave, Slot, Staff
from .rules import fairness_counts, weight_of


def month_days(year: int, month: int) -> list[date]:
    d = date(year, month, 1)
    out: list[date] = []
    while d.month == month:
        out.append(d)
        d += timedelta(days=1)
    return out


def parse_month(month: str) -> tuple[int, int]:
    """YYYY-MM → (year, month)。格式不对抛 ValueError，由入口层翻成退出码 2。"""
    parts = month.split("-")
    if len(parts) != 2:
        raise ValueError(f"月份格式应为 YYYY-MM：{month}")
    year, mon = int(parts[0]), int(parts[1])
    if not 1 <= mon <= 12:
        raise ValueError(f"月份超出范围：{month}")
    if year < 2000 or year > 2100:
        raise ValueError(f"年份超出范围：{month}")
    return year, mon


def is_available(staff: Staff, day: date, leaves: list[Leave]) -> bool:
    return staff.active and not any(lv.staff_id == staff.id and lv.covers(day) for lv in leaves)


def _can_take(
    staff: Staff,
    kind: str,
    day: date,
    current: list[Assignment],
    max_consecutive: int,
) -> bool:
    yesterday = day - timedelta(days=1)
    mine = {a.kind for a in current if a.staff_id == staff.id and a.day == yesterday}
    if "night" in mine and kind == "morning":
        return False
    days = sorted({a.day for a in current if a.staff_id == staff.id} | {day})
    run = 1
    for prev, cur in zip(days, days[1:]):
        run = run + 1 if (cur - prev).days == 1 else 1
        if run > max_consecutive:
            return False
    return True


def solve(
    staff: list[Staff],
    days: list[date],
    slots: list[Slot],
    leaves: list[Leave],
    *,
    max_consecutive: int = 5,
    holidays: set[date] | None = None,
    keep: list[Assignment] | None = None,
) -> list[Assignment]:
    """逐日填空：留下的旧排班先占位，其余按加权次数最少者优先。

    `keep` 是上一次的班表。只要它还合法（人可用、有技能、不冲突），就原样保留，
    于是「插一条请假」只会改动与这条请假相关的班，diff 才是最小的。
    """
    slots_by_kind = {s.kind: s for s in slots}
    assignments: list[Assignment] = []
    counts: dict[int, int] = {}

    if keep:
        for a in keep:
            slot = slots_by_kind.get(a.kind)
            person = next((s for s in staff if s.id == a.staff_id), None)
            if slot is None or person is None or not is_available(person, a.day, leaves):
                continue
            if a.day not in days or not person.has(slot.required_skill):
                continue
            if any(b.day == a.day and b.kind == a.kind for b in assignments):
                continue
            if any(b.day == a.day and b.staff_id == a.staff_id for b in assignments):
                continue
            assignments.append(a)

    counts = fairness_counts(assignments, staff, holidays)

    for day in days:
        for slot in slots:
            occupied = [a for a in assignments if a.day == day and a.kind == slot.kind]
            if len(occupied) >= max(1, slot.headcount):
                continue
            candidates = [
                s
                for s in staff
                if is_available(s, day, leaves) and s.has(slot.required_skill)
            ]
            candidates = [
                s for s in candidates if _can_take(s, slot.kind, day, assignments, max_consecutive)
            ]
            if not candidates:
                continue
            busy = {a.staff_id for a in assignments if a.day == day}
            pool = [s for s in candidates if s.id not in busy] or candidates
            pick = min(pool, key=lambda s: (counts.get(s.id, 0), s.id))
            assignments.append(Assignment(day=day, kind=slot.kind, staff_id=pick.id))
            counts[pick.id] = counts.get(pick.id, 0) + weight_of(day, holidays)

    assignments.sort(key=lambda a: (a.day, a.kind))
    return assignments
