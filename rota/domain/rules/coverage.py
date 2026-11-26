"""覆盖：该有的班没人上。"""

from __future__ import annotations

from collections import Counter
from datetime import date

from ..models import KIND_LABELS, Assignment, Finding


def coverage_findings(
    needed: dict[date, list[str]], assignments: list[Assignment]
) -> list[Finding]:
    filled: Counter[tuple[date, str]] = Counter((a.day, a.kind) for a in assignments)
    out: list[Finding] = []
    for day, kinds in sorted(needed.items()):
        for kind in kinds:
            if filled.get((day, kind), 0) == 0:
                out.append(
                    Finding(
                        rule_id="coverage.gap",
                        severity="high",
                        message=f"{day.isoformat()} 的{KIND_LABELS.get(kind, kind)}没人",
                        evidence="当天该班次需求 ≥1，实际排班 0",
                        suggestion="指定补班人，或调整当天的请假",
                        score=-100,
                    )
                )
    return out
