"""技能匹配与一人多班：排班表里最容易漏掉的两条。"""

from __future__ import annotations

from collections import Counter
from datetime import date

from ..models import KIND_LABELS, Assignment, Finding, Slot, Staff


def skill_mismatches(
    assignments: list[Assignment],
    staff: list[Staff],
    slots: dict[str, Slot],
    weight: int,
) -> list[Finding]:
    """某个班要求技能，被排的人没有这项技能。"""
    people = {s.id: s for s in staff}
    out: list[Finding] = []
    for a in assignments:
        slot = slots.get(a.kind)
        person = people.get(a.staff_id)
        if slot is None or person is None or not slot.required_skill:
            continue
        if not person.has(slot.required_skill):
            out.append(
                Finding(
                    rule_id="skill.mismatch",
                    severity="high",
                    message=(
                        f"{KIND_LABELS.get(a.kind, a.kind)}要求「{slot.required_skill}」，"
                        f"{person.name} 没有这项技能"
                    ),
                    evidence=(
                        f"{a.day.isoformat()} {a.kind} → {person.name}（技能："
                        f"{'、'.join(sorted(person.skills)) or '无'}）"
                    ),
                    suggestion=f"换成有「{slot.required_skill}」的人，或改这一天的班次需求",
                    score=-weight,
                )
            )
    return out


def double_bookings(assignments: list[Assignment], weight: int) -> list[Finding]:
    """同一个人同一天被排了两个班。"""
    seen: Counter[tuple[date, int]] = Counter((a.day, a.staff_id) for a in assignments)
    out: list[Finding] = []
    for (day, staff_id), n in sorted(seen.items()):
        if n > 1:
            out.append(
                Finding(
                    rule_id="load.double_booked",
                    severity="high",
                    message=f"员工 {staff_id} 在 {day.isoformat()} 被排了 {n} 个班",
                    evidence=f"{day.isoformat()} 出现 {n} 条同一人的排班记录",
                    suggestion="同一天只留一个班，另一个换人",
                    score=-weight * 2,
                )
            )
    return out
