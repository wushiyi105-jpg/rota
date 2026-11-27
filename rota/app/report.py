"""排班产品视图：整月班表、公平账、可发群文本。"""

from __future__ import annotations

from collections import Counter
from datetime import date, timedelta

from ..domain.catalog import match_template, rules, templates
from ..domain.models import KIND_LABELS, Assignment, Staff
from ..domain.solver import month_days


def weekend_counts(
    assignments: list[Assignment], staff: list[Staff], holidays: set[date] | None = None
) -> dict[int, int]:
    """周末/节假日班次数；只数“周末班”，不数加权总分。"""
    holiday = holidays or set()
    counter: Counter[int] = Counter()
    for a in assignments:
        if a.day.weekday() >= 5 or a.day in holiday:
            counter[a.staff_id] += 1
    for s in staff:
        counter.setdefault(s.id, 0)
    return dict(counter)


def fairness_lines(assignments: list[Assignment], staff: list[Staff], holidays: set[date] | None) -> list[str]:
    counts = weekend_counts(assignments, staff, holidays)
    if not counts:
        return ["没有可统计的周末班。"]
    total = sum(counts.values())
    target = total / len(counts)
    lines = [f"周末班共 {total} 个，人均 {target:.1f} 个。"]
    for s in staff:
        n = counts.get(s.id, 0)
        if n < target - 0.5:
            lines.append(f"- {s.name}：{n} 个，**还欠 {target - n:.1f} 个周末班**")
        elif n > target + 0.5:
            lines.append(f"- {s.name}：{n} 个，多背 {n - target:.1f} 个")
        else:
            lines.append(f"- {s.name}：{n} 个，基本持平")
    return lines


def month_message(month: str, assignments: list[Assignment], names: dict[int, str]) -> str:
    """整月可发群版：每天一行，不截断、不写“近几天”。"""
    if not assignments:
        return f"{month} 班表：暂无排班。"
    by_day: dict[date, list[Assignment]] = {}
    for a in assignments:
        by_day.setdefault(a.day, []).append(a)
    lines = [f"{month} 班表"]
    for day in sorted(by_day):
        cells = "；".join(
            f"{KIND_LABELS.get(a.kind, a.kind)} {names.get(a.staff_id, a.staff_id)}"
            for a in sorted(by_day[day], key=lambda x: x.kind)
        )
        week = "一二三四五六日"[day.weekday()]
        lines.append(f"{day.month}/{day.day} 周{week}：{cells}")
    return "\n".join(lines)


def markdown(
    *,
    month: str,
    assignments: list[Assignment],
    names: dict[int, str],
    staff: list[Staff],
    holidays: set[date] | None,
    findings: list,
    score: int,
    comment: str,
    comment_source: str,
    changes: list | None = None,
    team: str = "",
) -> str:
    days = month_days(int(month[:4]), int(month[5:7]))
    template = match_template(team)
    enforced = [r for r in rules() if r["enforced"]]
    by_day: dict[date, dict[str, str]] = {}
    for a in assignments:
        by_day.setdefault(a.day, {})[a.kind] = names.get(a.staff_id, str(a.staff_id))
    lines = [
        f"# {month} 门店班表",
        "",
        f"> 总分 **{score}**；{'AI 只改写解释，班表与数字由本地求解器生成。' if comment_source == 'model' else '本次为本地求解，未使用模型解释。'}",
        f"> 门店模板：**{template['name']}**（模板库 {len(templates())} 类）；"
        f"规则库 {len(rules())} 条，其中 {len(enforced)} 条由引擎强制。",
        "",
        "## 一、整月班表",
        "",
        "| 日期 | 星期 | 早班 | 晚班 | 夜班 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for day in days:
        row = by_day.get(day, {})
        week = "一二三四五六日"[day.weekday()]
        lines.append(
            f"| {day.month}/{day.day} | 周{week} | {row.get('morning', '-')} | "
            f"{row.get('evening', '-')} | {row.get('night', '-')} |"
        )
    lines += ["", "## 二、公平账（周末班）", ""]
    lines += fairness_lines(assignments, staff, holidays)
    lines += ["", "## 三、约束扣分", ""]
    if findings:
        for f in findings[:8]:
            lines.append(f"- **{f.rule_id}**（{f.score}）：{f.message}；建议：{f.suggestion}")
    else:
        lines.append("- 没有命中约束扣分。")
    lines += ["", "## 四、店长可读版", "", comment, ""]
    if changes:
        lines += ["## 五、本次重排只动了这些", ""]
        for c in changes:
            lines.append(
                f"- {c.label}：{names.get(c.from_staff or -1, '-')} → {names.get(c.to_staff or -1, '-')}"
            )
        lines.append("")
    lines += [
        "## 六、直接发群",
        "",
        "```text",
        month_message(month, assignments, names),
        "```",
        "",
        "---",
        "",
        "口径：周末与法定节假日按 2 倍权重计公平；夜班后接早班休息不足 11 小时；连续上班上限 5 天。",
        "",
    ]
    return "\n".join(lines)


def next_month(month: str) -> str:
    year, mon = int(month[:4]), int(month[5:7])
    first = date(year, mon, 1)
    nxt = first + timedelta(days=32)
    return f"{nxt.year:04d}-{nxt.month:02d}"
