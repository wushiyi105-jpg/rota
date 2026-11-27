"""用例编排：排班、请假重排、解释（带守卫）、导出。"""

from __future__ import annotations

import json
from datetime import date

from ..config import Settings
from ..domain.diff import diff
from ..domain.engine import explain
from ..domain.errors import LLMError
from ..domain.export import csv_rows, group_message, ics, per_staff_totals
from ..domain.guard import guard_text
from ..domain.models import Assignment, Finding
from ..ports import LLMPort, StorePort
from .plan import Plan, build_for


def plan_month(store: StorePort, settings: Settings, month: str, holidays: set[date] | None = None) -> Plan:
    staff = store.list_staff()
    leaves = store.list_leaves()
    plan = build_for(month, staff, leaves, settings, holidays=holidays)
    store.save_plan(month, plan.result.assignments, plan.result.score)
    return plan


def replan_with_leave(
    store: StorePort,
    settings: Settings,
    month: str,
    staff_id: int,
    start: date,
    end: date,
    reason: str = "",
    holidays: set[date] | None = None,
) -> Plan:
    """插一条请假并重排：旧班表能留的都留下，只动受影响的那几条。"""
    old = store.list_assignments(month)
    store.add_leave(staff_id, start, end, reason)
    staff = store.list_staff()
    leaves = store.list_leaves()
    plan = build_for(month, staff, leaves, settings, holidays=holidays, keep=old)
    plan.result.changes = diff(old, plan.result.assignments)
    store.save_plan(month, plan.result.assignments, plan.result.score)
    return plan


def facts_of(plan: Plan, names: dict[int, str]) -> str:
    """给模型的事实：只写扣分与人数，不写建议。"""
    lines = [f"月份 {plan.result.month}，员工 {len(names)} 人，总分 {plan.result.score}。"]
    for f in plan.result.findings:
        lines.append(f"{f.rule_id} {f.message}（{f.score}）")
    if not plan.result.findings:
        lines.append("没有任何扣分。")
    return "\n".join(lines)


def explain_plan(
    plan: Plan, names: dict[int, str], settings: Settings, llm: LLMPort | None = None
) -> tuple[str, str, str | None]:
    """返回 (说明文本, 来源, 丢弃原因)。来源是 model 或 offline。"""
    offline = explain(plan.result)
    if llm is None:
        return offline, "offline", None
    facts = facts_of(plan, names)
    try:
        raw = llm.explain(facts)
    except LLMError as exc:
        return offline, "offline", f"模型调用失败：{exc}"

    # 新提示词要求 JSON；解析成功就只让模型填“摘要 + 动作”，
    # 问题本身用本地 finding 原文，避免整段因一个多余数字被丢掉。
    try:
        data = json.loads(raw)
    except (TypeError, ValueError):
        data = None
    if isinstance(data, dict) and "summary" in data:
        summary, reason = guard_text(str(data.get("summary", "")), facts, list(names.values()))
        if reason:
            return offline, "offline", reason
        by_rule = {f.rule_id: f for f in plan.result.findings}
        kept: list[str] = []
        for issue in list(data.get("issues", []))[:5]:
            if not isinstance(issue, dict):
                continue
            rule_id = str(issue.get("rule_id", ""))
            action = str(issue.get("action", "")).strip()
            finding = by_rule.get(rule_id)
            if finding is None or not action:
                continue
            safe_action, because = guard_text(action, facts, list(names.values()))
            if because:
                continue
            kept.append(f"- {finding.message} → {safe_action}")
        body = summary.strip()
        if kept:
            body += "\n" + "\n".join(kept)
        return body, "model", None

    raw_kept, reason = guard_text(raw, facts, list(names.values()))
    if reason:
        return offline, "offline", reason
    return raw_kept, "model", None


def export_ics(assignments: list[Assignment], names: dict[int, str], month: str) -> str:
    return ics(assignments, names, calendar=f"排班 {month}")


def export_csv(assignments: list[Assignment], names: dict[int, str]) -> str:
    return csv_rows(assignments, names)


def export_totals(assignments: list[Assignment], names: dict[int, str]) -> str:
    return per_staff_totals(assignments, names)


def export_message(month: str, assignments: list[Assignment], names: dict[int, str]) -> str:
    return group_message(month, assignments, names)


def top_findings(plan: Plan, limit: int = 5) -> list[Finding]:
    return plan.result.findings[:limit]
