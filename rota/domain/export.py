"""导出：ICS 日历与 CSV 班表。都用标准库拼，不引新依赖。"""

from __future__ import annotations

from datetime import datetime, timedelta

from .models import KIND_LABELS, Assignment

ALARMS = {"morning": ("08:00", "12:00"), "evening": ("14:00", "22:00"), "night": ("22:00", "08:00")}


def _fold(line: str) -> str:
    """ICS 规定每行不超过 75 字节，超了要折行。"""
    out, buf = [], line
    while len(buf.encode("utf-8")) > 75:
        cut = 74
        while len(buf[:cut].encode("utf-8")) > 74:
            cut -= 1
        out.append(buf[:cut])
        buf = " " + buf[cut:]
    out.append(buf)
    return "\r\n".join(out)


def ics(assignments: list[Assignment], names: dict[int, str], calendar: str = "Rota") -> str:
    stamp = datetime(2026, 1, 1, 0, 0, 0).strftime("%Y%m%dT%H%M%S")
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//rota//排班表//CN",
        f"X-WR-CALNAME:{calendar}",
    ]
    for a in sorted(assignments, key=lambda x: (x.day, x.kind)):
        start_s, end_s = ALARMS.get(a.kind, ("09:00", "18:00"))
        start = datetime.combine(a.day, datetime.strptime(start_s, "%H:%M").time())
        end_day = a.day + timedelta(days=1) if a.kind == "night" else a.day
        end = datetime.combine(end_day, datetime.strptime(end_s, "%H:%M").time())
        lines += [
            "BEGIN:VEVENT",
            f"UID:{a.day.isoformat()}-{a.kind}-{a.staff_id}@rota",
            f"DTSTAMP:{stamp}Z",
            f"DTSTART;TZID=Asia/Shanghai:{start.strftime('%Y%m%dT%H%M%S')}",
            f"DTEND;TZID=Asia/Shanghai:{end.strftime('%Y%m%dT%H%M%S')}",
            _fold(f"SUMMARY:{KIND_LABELS.get(a.kind, a.kind)} · {names.get(a.staff_id, a.staff_id)}"),
            f"DESCRIPTION:员工编号 {a.staff_id}",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


def csv_rows(assignments: list[Assignment], names: dict[int, str]) -> str:
    lines = ["日期,班次,员工,编号"]
    for a in sorted(assignments, key=lambda x: (x.day, x.kind)):
        lines.append(
            f"{a.day.isoformat()},{KIND_LABELS.get(a.kind, a.kind)},{names.get(a.staff_id, a.staff_id)},{a.staff_id}"
        )
    return "\n".join(lines) + "\n"


def per_staff_totals(assignments: list[Assignment], names: dict[int, str]) -> str:
    counts: dict[int, int] = {}
    for a in assignments:
        counts[a.staff_id] = counts.get(a.staff_id, 0) + 1
    lines = ["员工,班次数"]
    for staff_id, n in sorted(counts.items()):
        lines.append(f"{names.get(staff_id, staff_id)},{n}")
    return "\n".join(lines) + "\n"


def group_message(month: str, assignments: list[Assignment], names: dict[int, str], limit: int = 0) -> str:
    """群里能直接发的一段：整月每天一行；limit>0 时才截断。"""
    rows = sorted(assignments, key=lambda x: (x.day, x.kind))
    if limit:
        rows = rows[:limit]
    lines = [f"{month} 班表："]
    for a in rows:
        lines.append(
            f"{a.day.month}/{a.day.day} {KIND_LABELS.get(a.kind, a.kind)} {names.get(a.staff_id, a.staff_id)}"
        )
    return "\n".join(lines)
