"""连续上班：超过上限要指出来，并给出起点。"""

from __future__ import annotations

from datetime import date

from ..models import Assignment, Finding


def consecutive_findings(
    assignments: list[Assignment], max_days: int, weight: int
) -> list[Finding]:
    by_staff: dict[int, set[date]] = {}
    for a in assignments:
        by_staff.setdefault(a.staff_id, set()).add(a.day)

    out: list[Finding] = []
    for staff_id, days in sorted(by_staff.items()):
        ordered = sorted(days)
        run_start = ordered[0]
        run = 1
        for prev, cur in zip(ordered, ordered[1:]):
            if (cur - prev).days == 1:
                run += 1
            else:
                run_start, run = cur, 1
            if run > max_days:
                out.append(
                    Finding(
                        rule_id="consecutive.over_limit",
                        severity="warn",
                        message=f"员工 {staff_id} 从 {run_start.isoformat()} 起连上 {run} 天，超过 {max_days} 天",
                        evidence=f"{run_start.isoformat()}~{cur.isoformat()} 每天都排了班",
                        suggestion="插一天休息，或把其中一天换给空闲成员",
                        score=-weight,
                    )
                )
                break
    return out
