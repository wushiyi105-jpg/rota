"""两份班表的差异：谁被换掉、换给谁。重排只需要打印这几行。"""

from __future__ import annotations

from .models import Assignment, Change


def diff(old: list[Assignment], new: list[Assignment]) -> list[Change]:
    old_by = {a.key(): a.staff_id for a in old}
    new_by = {a.key(): a.staff_id for a in new}
    out: list[Change] = []
    for key in sorted(set(old_by) | set(new_by)):
        before = old_by.get(key)
        after = new_by.get(key)
        if before == after:
            continue
        out.append(Change(day=key[0], kind=key[1], from_staff=before, to_staff=after))
    return out


def affected_days(changes: list[Change]) -> set[str]:
    return {c.day.isoformat() for c in changes}
