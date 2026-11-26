"""请假冲突：请假期间被排班一律报红。"""

from __future__ import annotations

from ..models import Assignment, Finding, Leave


def leave_conflicts(assignments: list[Assignment], leaves: list[Leave]) -> list[Finding]:
    out: list[Finding] = []
    for a in assignments:
        for lv in leaves:
            if lv.staff_id != a.staff_id or not lv.covers(a.day):
                continue
            reason = f"（{lv.reason}）" if lv.reason else ""
            out.append(
                Finding(
                    rule_id="leave.conflict",
                    severity="high",
                    message=f"员工 {a.staff_id} 在请假期间被排班{reason}",
                    evidence=f"{a.day.isoformat()} {a.kind} 落在 {lv.start.isoformat()}~{lv.end.isoformat()}",
                    suggestion="重新分配给当天可用的人",
                    score=-20,
                )
            )
    return out
