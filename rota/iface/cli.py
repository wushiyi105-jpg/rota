"""CLI：Typer + rich。退出码 0 成功 / 1 运行错误 / 2 参数或输入错误。"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from ..adapters.llm import build_llm
from ..adapters.store import SqliteStore
from ..app import jobs as job_app
from ..app.plan import build_for
from ..app.report import markdown as schedule_markdown
from ..app.run import explain_plan, export_ics, plan_month, replan_with_leave
from ..config import settings as base_settings
from ..domain.engine import explain
from ..domain.export import csv_rows, group_message, per_staff_totals
from ..domain.models import KIND_LABELS
from ..domain.solver import parse_month

app = typer.Typer(add_completion=False, help="Rota —— 小团队排班")
console = Console()


def _settings(db: Path | None, port: int | None = None):
    update: dict = {}
    if db:
        update["db_path"] = db
    if port:
        update["port"] = port
    return base_settings.model_copy(update=update) if update else base_settings


def _load_seed() -> dict:
    path = Path("data/seed.json")
    if not path.exists():
        path = Path(__file__).resolve().parents[2] / "data" / "seed.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def _holidays() -> set[date]:
    return {date.fromisoformat(x) for x in _load_seed().get("holidays", [])}


@app.command()
def seed(db: Path = typer.Option(None, help="数据库路径")) -> None:
    """写入示例团队、技能与请假。"""
    s = _settings(db)
    store = SqliteStore(s.db_path)
    data = _load_seed()
    for row in data.get("staff", []):
        store.add_staff(row["name"], row.get("skills", []))
    staff = store.list_staff()
    by_name = {x.name: x.id for x in staff}
    for row in data.get("leaves", []):
        sid = by_name.get(row["staff"])
        if sid:
            store.add_leave(sid, date.fromisoformat(row["start"]), date.fromisoformat(row["end"]), row.get("reason", ""))
    console.print(f"[green]已写入[/] {len(staff)} 名员工、{len(data.get('leaves', []))} 条请假")


def _print_plan(plan, month: str, staff_names: dict[int, str]) -> None:
    table = Table(title=f"{month} 班表 · 总分 {plan.result.score}")
    table.add_column("日期")
    for kind in ("morning", "evening", "night"):
        table.add_column(KIND_LABELS[kind])
    by_day = plan.result.by_day(staff_names)
    for d in plan.days:
        row = by_day.get(d.isoformat(), {})
        table.add_row(d.isoformat(), row.get("morning", "-"), row.get("evening", "-"), row.get("night", "-"))
    console.print(table)
    console.print("\n" + explain(plan.result))
    if plan.result.changes:
        console.print("\n[yellow]本次改动：[/]")
        for c in plan.result.changes:
            console.print(
                f"  {c.label}：{staff_names.get(c.from_staff or -1, '-')} → {staff_names.get(c.to_staff or -1, '-')}"
            )


@app.command()
def plan(
    month: str = typer.Option(..., help="YYYY-MM"),
    db: Path = typer.Option(None, help="数据库路径"),
    as_json: bool = typer.Option(False, "--json"),
) -> None:
    """生成某个月的班表。"""
    s = _settings(db)
    store = SqliteStore(s.db_path)
    if not store.list_staff():
        console.print("[red]没有员工，先跑 seed[/]")
        raise typer.Exit(code=1)
    try:
        parse_month(month)
    except ValueError as exc:
        console.print(f"[red]❌ {exc}[/]")
        raise typer.Exit(code=2) from exc
    plan = plan_month(store, s, month, _holidays())
    names = {x.id: x.name for x in store.list_staff()}
    if as_json:
        console.print_json(
            json.dumps(
                {
                    "month": month,
                    "score": plan.result.score,
                    "counts": plan.result.counts,
                    "findings": [
                        {"rule": f.rule_id, "score": f.score, "message": f.message, "evidence": f.evidence}
                        for f in plan.result.findings
                    ],
                },
                ensure_ascii=False,
            )
        )
        return
    _print_plan(plan, month, names)


@app.command()
def report(
    month: str = typer.Option(..., help="YYYY-MM"),
    out: Path = typer.Option(None, help="输出 Markdown 班表；给出后同时写同名 .ics"),
    ics_out: Path = typer.Option(None, help="ICS 单独输出路径"),
    no_llm: bool = typer.Option(False, "--no-llm", help="只出本地解释"),
    db: Path = typer.Option(None),
) -> None:
    """一条命令出整月班表 + 公平账 + 可发群文本。"""
    s = _settings(db)
    store = SqliteStore(s.db_path)
    if not store.list_staff():
        console.print("[red]没有员工，先跑 seed[/]")
        raise typer.Exit(code=1)
    try:
        parse_month(month)
    except ValueError as exc:
        console.print(f"[red]❌ {exc}[/]")
        raise typer.Exit(code=2) from exc
    holidays = _holidays()
    plan = plan_month(store, s, month, holidays)
    names = {x.id: x.name for x in store.list_staff()}
    llm = build_llm(s.llm_base_url, s.llm_api_key, s.llm_model) if s.llm_enabled and not no_llm else None
    comment, source, dropped = explain_plan(plan, names, s, llm)
    text = schedule_markdown(
        month=month,
        assignments=plan.result.assignments,
        names=names,
        staff=store.list_staff(),
        holidays=holidays,
        findings=plan.result.findings,
        score=plan.result.score,
        comment=comment,
        comment_source=source,
        changes=plan.result.changes,
        team=str(_load_seed().get("team", "")),
    )
    body = text
    if source == "offline" and llm is None:
        body += "\n本次为本地求解：模型未参与，上面是本地规则写的解释。\n"
    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(body, encoding="utf-8")
        target = ics_out or out.with_suffix(".ics")
        target.write_text(export_ics(plan.result.assignments, names, month), encoding="utf-8")
        console.print(f"[green]已写出[/] {out} + {target}（{len(plan.result.assignments)} 条班次）")
    else:
        console.print(body)
    if dropped:
        console.print(f"[yellow]（{dropped}，模型解释已退回本地）[/]")


@app.command()
def show(month: str = typer.Option(..., help="YYYY-MM"), db: Path = typer.Option(None)) -> None:
    """查看已保存的班表。"""
    store = SqliteStore(_settings(db).db_path)
    rows = store.list_assignments(month)
    if not rows:
        console.print("[yellow]没有这个月的班表[/]")
        return
    names = {x.id: x.name for x in store.list_staff()}
    for a in rows:
        console.print(f"{a.day}  {KIND_LABELS.get(a.kind, a.kind):4}  {names.get(a.staff_id, a.staff_id)}")


@app.command()
def replan(
    month: str = typer.Option(..., help="YYYY-MM"),
    staff_id: int = typer.Option(..., help="请假员工编号"),
    start: str = typer.Option(..., help="YYYY-MM-DD"),
    end: str = typer.Option(..., help="YYYY-MM-DD"),
    reason: str = typer.Option("", help="请假事由"),
    db: Path = typer.Option(None),
) -> None:
    """插一条请假并重排，只动必要的人。"""
    s = _settings(db)
    store = SqliteStore(s.db_path)
    try:
        parse_month(month)
        d1, d2 = date.fromisoformat(start), date.fromisoformat(end)
    except ValueError as exc:
        console.print(f"[red]❌ 日期格式应为 YYYY-MM-DD：{exc}[/]")
        raise typer.Exit(code=2) from exc
    if d2 < d1:
        console.print("[red]❌ 请假的结束日期早于开始日期[/]")
        raise typer.Exit(code=2)
    plan = replan_with_leave(store, s, month, staff_id, d1, d2, reason, _holidays())
    names = {x.id: x.name for x in store.list_staff()}
    _print_plan(plan, month, names)


@app.command()
def comment(month: str = typer.Option(..., help="YYYY-MM"), db: Path = typer.Option(None)) -> None:
    """模型把扣分解释成店长能读的一段（无 key 或守卫丢弃时给离线文本）。"""
    s = _settings(db)
    store = SqliteStore(s.db_path)
    try:
        year, mon = parse_month(month)
    except ValueError as exc:
        console.print(f"[red]❌ {exc}[/]")
        raise typer.Exit(code=2) from exc
    staff = store.list_staff()
    leaves = store.list_leaves()
    plan = build_for(month, staff, leaves, s, holidays=_holidays())
    names = {x.id: x.name for x in staff}
    llm = build_llm(s.llm_base_url, s.llm_api_key, s.llm_model) if s.llm_enabled else None
    text, source, dropped = explain_plan(plan, names, s, llm)
    console.print(text)
    if dropped:
        console.print(f"[yellow]（{dropped}，已退回离线解释）[/]")
    elif source == "offline":
        console.print("[dim]（离线模式：未配置模型 key）[/]")


@app.command()
def export(
    month: str = typer.Option(..., help="YYYY-MM"),
    fmt: str = typer.Option("ics", "--format", help="ics / csv / totals / message"),
    out: Path = typer.Option(None, help="输出文件；不填打印到终端"),
    db: Path = typer.Option(None),
) -> None:
    """导出 ICS / CSV / 人均统计 / 群消息。"""
    store = SqliteStore(_settings(db).db_path)
    if fmt not in ("ics", "csv", "totals", "message"):
        console.print(f"[red]❌ 不认识的格式：{fmt}[/]")
        raise typer.Exit(code=2)
    assignments = store.list_assignments(month)
    if not assignments:
        console.print("[red]这个月还没有班表，先跑 plan[/]")
        raise typer.Exit(code=1)
    names = {x.id: x.name for x in store.list_staff()}
    if fmt == "ics":
        body = export_ics(assignments, names, month)
    elif fmt == "csv":
        body = csv_rows(assignments, names)
    elif fmt == "totals":
        body = per_staff_totals(assignments, names)
    elif fmt == "message":
        body = group_message(month, assignments, names)
    else:  # 上面已校验过，这里只是给类型检查一个兜底
        body = ""
    if out:
        out.write_text(body, encoding="utf-8")
        console.print(f"[green]已写出[/] {out}")
    else:
        console.print(body)


@app.command("jobs")
def jobs_cmd(
    now: str = typer.Option("", help="当前时间，默认今天 08:00"),
    enqueue: bool = typer.Option(False, "--enqueue", help="给这个月排一条每日提醒"),
    month: str = typer.Option("", help="YYYY-MM"),
    db: Path = typer.Option(None),
) -> None:
    """跑到期任务，或给某个月入队。"""
    s = _settings(db)
    store = SqliteStore(s.db_path)
    now = now or f"{date.today().isoformat()}T08:00:00"
    if enqueue:
        if not month:
            console.print("[red]❌ --enqueue 需要同时给 --month[/]")
            raise typer.Exit(code=2)
        created = job_app.enqueue_daily_digest(store, month, date.fromisoformat(now[:10]))
        console.print("[green]已入队[/]" if created else "[dim]这个键已存在，跳过[/]")
        return
    from ..adapters.notify import WebhookNotifier

    results = job_app.run_due(store, s, WebhookNotifier(s.webhook_url), now)
    if not results:
        console.print("没有到期任务。")
        return
    for r in results:
        console.print(f"任务 {r['id']}（{r['kind']}）：{'已推送' if r['sent'] else '未发送（webhook 未配置或失败）'}")


@app.command()
def doctor(db: Path = typer.Option(None)) -> None:
    """体检：配置 / 数据库 / 模型 / webhook。"""
    from ..doctor import main as run

    raise typer.Exit(code=run(_settings(db)))


@app.command()
def serve(
    port: int = typer.Option(None, help="默认 8001"),
    db: Path = typer.Option(None),
    host: str = typer.Option("127.0.0.1"),
) -> None:
    """Web 界面。"""
    import uvicorn

    from .web import create_app

    s = _settings(db, port)
    uvicorn.run(create_app(s), host=host, port=s.port)


@app.command()
def web(
    port: int = typer.Option(None, help="默认 8001"),
    db: Path = typer.Option(None),
) -> None:
    """`python -m rota web` 的别名。"""
    serve(port=port, db=db)


if __name__ == "__main__":  # pragma: no cover
    app()
