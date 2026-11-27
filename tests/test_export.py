from __future__ import annotations

from datetime import date

from rota.domain.export import csv_rows, ics, per_staff_totals
from rota.domain.models import Assignment

NAMES = {1: "阿泽", 2: "小林"}


def _rows() -> list[Assignment]:
    return [
        Assignment(date(2026, 12, 1), "morning", 1),
        Assignment(date(2026, 12, 2), "night", 2),
    ]


def test_ics_has_one_event_per_assignment():
    body = ics(_rows(), NAMES, calendar="排班 2026-12")
    assert body.startswith("BEGIN:VCALENDAR")
    assert body.rstrip().endswith("END:VCALENDAR")
    assert body.count("BEGIN:VEVENT") == len(_rows())
    assert "SUMMARY:早班 · 阿泽" in body
    assert "DTSTART;TZID=Asia/Shanghai:20261201T080000" in body


def test_ics_night_ends_next_day():
    body = ics([Assignment(date(2026, 12, 2), "night", 2)], NAMES)
    assert "DTEND;TZID=Asia/Shanghai:20261203T080000" in body


def test_csv_has_header_and_all_rows():
    body = csv_rows(_rows(), NAMES)
    lines = body.strip().splitlines()
    assert lines[0] == "日期,班次,员工,编号"
    assert len(lines) == 3
    assert "夜班,小林,2" in body


def test_totals_sum_matches_assignment_count():
    body = per_staff_totals(_rows(), NAMES)
    lines = body.strip().splitlines()[1:]
    assert sum(int(line.split(",")[1]) for line in lines) == len(_rows())
