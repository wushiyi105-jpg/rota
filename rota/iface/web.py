"""FastAPI + Jinja2 服务端渲染。"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from ..adapters.export import csv_rows, per_staff_totals
from ..adapters.store import SqliteStore
from ..app.run import export_ics, plan_month, replan_with_leave
from ..config import Settings
from ..domain.engine import explain
from ..domain.models import KIND_LABELS
from ..domain.solver import parse_month

TEMPLATES = Jinja2Templates(directory=str(Path(__file__).resolve().parents[2] / "templates"))


def create_app(settings: Settings, store: SqliteStore | None = None) -> FastAPI:
    app = FastAPI(title="Rota", version="1.0.0")
    store = store or SqliteStore(settings.db_path)

    def render(request: Request, month: str) -> HTMLResponse:
        staff = store.list_staff()
        names = {s.id: s.name for s in staff}
        assignments = store.list_assignments(month)
        result_rows = []
        by_day: dict[str, dict[str, str]] = {}
        for a in assignments:
            by_day.setdefault(a.day.isoformat(), {})[a.kind] = names.get(a.staff_id, str(a.staff_id))
        for d, row in sorted(by_day.items()):
            result_rows.append({"day": d, "morning": row.get("morning", "-"),
                                "evening": row.get("evening", "-"), "night": row.get("night", "-")})
        return TEMPLATES.TemplateResponse(
            request,
            "index.html",
            {
                "month": month,
                "rows": result_rows,
                "score": store.plan_score(month),
                "staff": staff,
                "kinds": KIND_LABELS,
                "today": date.today().isoformat(),
            },
        )

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request, month: str = "") -> HTMLResponse:
        return render(request, month or date.today().strftime("%Y-%m"))

    @app.post("/plan")
    def do_plan(month: str = Form(...)) -> RedirectResponse:
        month = month.strip()
        try:
            parse_month(month)
        except ValueError:
            return RedirectResponse(url=f"/?month={date.today().strftime('%Y-%m')}&error=month", status_code=303)
        staff = store.list_staff()
        if not staff:
            return RedirectResponse(url="/?error=noseed", status_code=303)
        plan_month(store, settings, month)
        return RedirectResponse(url=f"/?month={month}", status_code=303)

    @app.post("/replan")
    def do_replan(
        month: str = Form(...),
        staff_id: int = Form(...),
        start: str = Form(...),
        end: str = Form(...),
        reason: str = Form(""),
    ) -> RedirectResponse:
        try:
            d1, d2 = date.fromisoformat(start), date.fromisoformat(end)
            parse_month(month)
        except ValueError:
            return RedirectResponse(url=f"/?month={month}&error=date", status_code=303)
        if d2 < d1:
            return RedirectResponse(url=f"/?month={month}&error=date", status_code=303)
        replan_with_leave(store, settings, month, staff_id, d1, d2, reason)
        return RedirectResponse(url=f"/?month={month}", status_code=303)

    @app.get("/export.ics", response_class=PlainTextResponse)
    def export_calendar(month: str) -> PlainTextResponse:
        names = {s.id: s.name for s in store.list_staff()}
        body = export_ics(store.list_assignments(month), names, month)
        return PlainTextResponse(body, media_type="text/calendar; charset=utf-8")

    @app.get("/export.csv", response_class=PlainTextResponse)
    def export_table(month: str) -> PlainTextResponse:
        names = {s.id: s.name for s in store.list_staff()}
        return PlainTextResponse(csv_rows(store.list_assignments(month), names), media_type="text/csv; charset=utf-8")

    @app.get("/export.totals", response_class=PlainTextResponse)
    def export_totals(month: str) -> PlainTextResponse:
        names = {s.id: s.name for s in store.list_staff()}
        return PlainTextResponse(per_staff_totals(store.list_assignments(month), names))

    @app.get("/explain", response_class=PlainTextResponse)
    def explain_month(month: str) -> PlainTextResponse:
        from ..app.plan import build_for

        staff = store.list_staff()
        plan = build_for(month, staff, store.list_leaves(), settings)
        return PlainTextResponse(explain(plan.result))

    @app.get("/health")
    def health() -> dict[str, object]:
        return {"status": "ok", "staff": len(store.list_staff())}

    return app


def app_factory(settings: Settings | None = None) -> FastAPI:
    if settings is None:
        from ..config import settings as default_settings

        settings = default_settings
    return create_app(settings)
