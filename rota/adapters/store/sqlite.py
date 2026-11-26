"""SQLite 存储：SQLAlchemy 2.0，每请求一个 session。"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from sqlalchemy import Date, Integer, String, UniqueConstraint, create_engine, delete, select, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from ...domain.models import Assignment, Leave, Staff


class Base(DeclarativeBase):
    pass


class StaffRow(Base):
    __tablename__ = "staff"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    skills: Mapped[str] = mapped_column(String(200), default="")
    active: Mapped[int] = mapped_column(Integer, default=1)


class LeaveRow(Base):
    __tablename__ = "leaves"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    staff_id: Mapped[int] = mapped_column(Integer, index=True)
    start: Mapped[date] = mapped_column(Date)
    end: Mapped[date] = mapped_column(Date)
    reason: Mapped[str] = mapped_column(String(120), default="")


class PlanRow(Base):
    __tablename__ = "plans"
    __table_args__ = (UniqueConstraint("month", name="uq_plans_month"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    month: Mapped[str] = mapped_column(String(7), index=True)
    score: Mapped[int] = mapped_column(Integer, default=0)


class AssignmentRow(Base):
    __tablename__ = "assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    month: Mapped[str] = mapped_column(String(7), index=True)
    day: Mapped[date] = mapped_column(Date)
    kind: Mapped[str] = mapped_column(String(16))
    staff_id: Mapped[int] = mapped_column(Integer, index=True)


class JobRow(Base):
    __tablename__ = "jobs"
    __table_args__ = (UniqueConstraint("idem_key", name="uq_jobs_idem"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    kind: Mapped[str] = mapped_column(String(32))
    idem_key: Mapped[str] = mapped_column(String(120))
    payload: Mapped[str] = mapped_column(String(2000), default="{}")
    state: Mapped[str] = mapped_column(String(16), default="pending")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    next_run_at: Mapped[str] = mapped_column(String(32), index=True)
    created_at: Mapped[str] = mapped_column(String(32), default="")


class SqliteStore:
    def __init__(self, db_path: Path) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_engine(f"sqlite:///{db_path}", future=True)
        self.session_factory = sessionmaker(self.engine, expire_on_commit=False)
        Base.metadata.create_all(self.engine)

    # ---- staff / leave ---------------------------------------------------
    def add_staff(self, name: str, skills: list[str] | None = None) -> int:
        with self.session_factory() as s:
            row = StaffRow(name=name, skills=",".join(skills or []))
            s.add(row)
            s.commit()
            return row.id

    def list_staff(self) -> list[Staff]:
        with self.session_factory() as s:
            rows = s.scalars(select(StaffRow).order_by(StaffRow.id)).all()
            return [
                Staff(
                    id=r.id,
                    name=r.name,
                    skills=frozenset(x for x in r.skills.split(",") if x),
                    active=bool(r.active),
                )
                for r in rows
            ]

    def add_leave(self, staff_id: int, start: date, end: date, reason: str = "") -> None:
        with self.session_factory() as s:
            s.add(LeaveRow(staff_id=staff_id, start=start, end=end, reason=reason))
            s.commit()

    def list_leaves(self) -> list[Leave]:
        with self.session_factory() as s:
            rows = s.scalars(select(LeaveRow).order_by(LeaveRow.id)).all()
            return [Leave(r.staff_id, r.start, r.end, r.reason) for r in rows]

    # ---- plan ------------------------------------------------------------
    def save_plan(self, month: str, assignments: list[Assignment], score: int) -> None:
        with self.session_factory() as s:
            s.execute(delete(AssignmentRow).where(AssignmentRow.month == month))
            s.execute(delete(PlanRow).where(PlanRow.month == month))
            s.add(PlanRow(month=month, score=score))
            for a in assignments:
                s.add(AssignmentRow(month=month, day=a.day, kind=a.kind, staff_id=a.staff_id))
            s.commit()

    def list_assignments(self, month: str) -> list[Assignment]:
        with self.session_factory() as s:
            rows = s.scalars(
                select(AssignmentRow)
                .where(AssignmentRow.month == month)
                .order_by(AssignmentRow.day, AssignmentRow.kind)
            ).all()
            return [Assignment(day=r.day, kind=r.kind, staff_id=r.staff_id) for r in rows]

    def plan_score(self, month: str) -> int | None:
        with self.session_factory() as s:
            row = s.scalar(select(PlanRow).where(PlanRow.month == month))
            return row.score if row else None

    # ---- jobs ------------------------------------------------------------
    def enqueue(self, kind: str, idem_key: str, payload: dict | str, next_run_at: str) -> bool:
        """幂等入队：同一个 idem_key 只留一条。返回是否真的新插入。"""
        body = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
        with self.session_factory() as s:
            exists = s.scalar(select(JobRow).where(JobRow.idem_key == idem_key))
            if exists:
                return False
            s.add(
                JobRow(
                    kind=kind,
                    idem_key=idem_key,
                    payload=body,
                    next_run_at=next_run_at,
                    created_at=next_run_at,
                )
            )
            s.commit()
            return True

    def due_jobs(self, now: str) -> list[dict]:
        with self.session_factory() as s:
            rows = s.scalars(
                select(JobRow)
                .where(JobRow.state == "pending", JobRow.next_run_at <= now)
                .order_by(JobRow.next_run_at, JobRow.id)
            ).all()
            return [
                {
                    "id": r.id,
                    "kind": r.kind,
                    "idem_key": r.idem_key,
                    "payload": json.loads(r.payload or "{}"),
                    "attempts": r.attempts,
                }
                for r in rows
            ]

    def finish_job(self, job_id: int, ok: bool) -> None:
        with self.session_factory() as s:
            row = s.get(JobRow, job_id)
            if row is None:
                return
            row.attempts += 1
            row.state = "done" if ok else "pending"
            s.commit()

    def schema_ok(self) -> bool:
        """doctor 用：确认建表完成，且 alembic 版本表可读。"""
        with self.engine.connect() as conn:
            names = set(
                conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).scalars()
            )
        needed = {"staff", "leaves", "plans", "assignments", "jobs"}
        return needed <= names
