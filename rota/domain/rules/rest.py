"""休息间隔：夜班后接次日早班，实际休息不足。"""

from __future__ import annotations

from datetime import date, timedelta

from ..models import Assignment, Finding

NIGHT_TO_MORNING_HOURS = 8


def rest_findings(
    assignments: list[Assignment], min_rest_hours: int, weight: int
) -> list[Finding]:
    by_staff: dict[int, dict[date, set[str]]] = {}
    for a in assignments:
        by_staff.setdefault(a.staff_id, {}).setdefault(a.day, set()).add(a.kind)

    out: list[Finding] = []
    for staff_id, days in sorted(by_staff.items()):
        for day, kinds in sorted(days.items()):
            next_kinds = days.get(day + timedelta(days=1), set())
            if "night" in kinds and "morning" in next_kinds:
                out.append(
                    Finding(
                        rule_id="rest.night_to_morning",
                        severity="high",
                        message=f"员工 {staff_id} 夜班后接早班，休息不足 {min_rest_hours} 小时",
                        evidence=(
                            f"{day.isoformat()} 夜班 → {(day + timedelta(days=1)).isoformat()} 早班，"
                            f"间隔约 {NIGHT_TO_MORNING_HOURS} 小时"
                        ),
                        suggestion="同组换人，或次日只排晚班",
                        score=-weight,
                    )
                )
    return out
