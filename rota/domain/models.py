"""领域模型：纯 dataclass，不碰 IO、不依赖框架。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

KINDS = ("morning", "evening", "night")
KIND_LABELS = {"morning": "早班", "evening": "晚班", "night": "夜班"}


@dataclass(frozen=True)
class Staff:
    id: int
    name: str
    skills: frozenset[str] = frozenset()
    active: bool = True

    def has(self, skill: str) -> bool:
        return not skill or skill in self.skills


@dataclass(frozen=True)
class Leave:
    staff_id: int
    start: date
    end: date
    reason: str = ""

    def covers(self, day: date) -> bool:
        return self.start <= day <= self.end


@dataclass(frozen=True)
class Slot:
    """一天里的一个班次需求。"""

    kind: str
    required_skill: str = ""
    headcount: int = 1


@dataclass(frozen=True)
class Assignment:
    day: date
    kind: str
    staff_id: int

    def key(self) -> tuple[date, str]:
        return (self.day, self.kind)


@dataclass(frozen=True)
class Change:
    """重排前后的一条差异。to_staff 为 None 表示这个班被撤掉。"""

    day: date
    kind: str
    from_staff: int | None
    to_staff: int | None

    @property
    def label(self) -> str:
        return f"{self.day.isoformat()} {KIND_LABELS.get(self.kind, self.kind)}"


@dataclass(frozen=True)
class Finding:
    """一条可解释的约束判定。score 为负数是扣分。"""

    rule_id: str
    severity: str
    message: str
    evidence: str
    suggestion: str = ""
    score: int = 0


@dataclass
class PlanResult:
    month: str
    assignments: list[Assignment] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    counts: dict[int, int] = field(default_factory=dict)
    changes: list[Change] = field(default_factory=list)

    @property
    def score(self) -> int:
        return sum(f.score for f in self.findings)

    @property
    def gaps(self) -> list[Finding]:
        return [f for f in self.findings if f.rule_id == "coverage.gap"]

    def by_day(self, names: dict[int, str]) -> dict[str, dict[str, str]]:
        out: dict[str, dict[str, str]] = {}
        for a in self.assignments:
            out.setdefault(a.day.isoformat(), {})[a.kind] = names.get(a.staff_id, str(a.staff_id))
        return out
