from __future__ import annotations

from fastapi.testclient import TestClient

from rota.adapters.store import SqliteStore
from rota.iface.web import create_app


def _client(settings) -> TestClient:
    store = SqliteStore(settings.db_path)
    store.add_staff("阿泽", ["收银", "夜班"])
    store.add_staff("小林", ["收银"])
    return TestClient(create_app(settings, store))


def test_index_serves_page(settings):
    resp = _client(settings).get("/")
    assert resp.status_code == 200
    assert "Rota" in resp.text


def test_plan_then_export_ics(settings):
    client = _client(settings)
    resp = client.post("/plan", data={"month": "2026-12"}, follow_redirects=False)
    assert resp.status_code == 303
    calendar = client.get("/export.ics", params={"month": "2026-12"})
    assert calendar.status_code == 200
    assert "BEGIN:VEVENT" in calendar.text


def test_bad_month_does_not_500(settings):
    resp = _client(settings).post("/plan", data={"month": "2026-13"}, follow_redirects=False)
    assert resp.status_code == 303
    assert "error=month" in resp.headers["location"]


def test_health_reports_staff(settings):
    body = _client(settings).get("/health").json()
    assert body["status"] == "ok" and body["staff"] == 2


def test_replan_with_bad_date_does_not_500(settings):
    resp = _client(settings).post(
        "/replan",
        data={"month": "2026-12", "staff_id": 1, "start": "2026-12-10", "end": "2026-12-08"},
        follow_redirects=False,
    )
    assert resp.status_code == 303
    assert "error=date" in resp.headers["location"]
