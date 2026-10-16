from app.db import get_db
from app.main import app

BUG = {"title": "Login fails", "component": "backend", "status": "open", "reported_on": "2026-09-01", "notes": "reproducible"}


def make(client, **overrides):
    return client.post("/api/bugs", json={**BUG, **overrides})


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_ready(client):
    assert client.get("/ready").status_code == 200


def test_ready_returns_503_when_db_down(client):
    class Broken:
        def execute(self, *_):
            raise RuntimeError("db down")

    app.dependency_overrides[get_db] = lambda: Broken()
    assert client.get("/ready").status_code == 503


def test_create_bug(client):
    r = make(client)
    assert r.status_code == 201
    assert r.json()["id"] == 1 and r.json()["title"] == "Login fails"


def test_create_rejects_invalid_status(client):
    assert make(client, status="ghosted").status_code == 422


def test_create_rejects_blank_title(client):
    assert make(client, title="   ").status_code == 422


def test_list_and_filter(client):
    make(client)
    make(client, title="Slow search", status="resolved")
    assert len(client.get("/api/bugs").json()) == 2
    resolved_bugs = client.get("/api/bugs", params={"status": "resolved"}).json()
    assert [j["title"] for j in resolved_bugs] == ["Slow search"]


def test_get_bug(client):
    make(client)
    assert client.get("/api/bugs/1").json()["component"] == "backend"


def test_get_missing_returns_404(client):
    assert client.get("/api/bugs/99").status_code == 404


def test_update_bug(client):
    make(client)
    r = client.put("/api/bugs/1", json={**BUG, "status": "investigating"})
    assert r.status_code == 200 and r.json()["status"] == "investigating"


def test_update_missing_returns_404(client):
    assert client.put("/api/bugs/99", json=BUG).status_code == 404


def test_delete_bug(client):
    make(client)
    assert client.delete("/api/bugs/1").status_code == 204
    assert client.get("/api/bugs/1").status_code == 404


def test_delete_missing_returns_404(client):
    assert client.delete("/api/bugs/99").status_code == 404


def test_stats_empty(client):
    assert client.get("/api/bugs/stats").json() == {
        "total": 0, "open": 0, "investigating": 0, "resolved": 0, "closed": 0,
    }


def test_stats_counts(client):
    make(client)
    make(client, status="resolved")
    s = client.get("/api/bugs/stats").json()
    assert s["total"] == 2 and s["open"] == 1 and s["resolved"] == 1


def test_metrics_exposed(client):
    client.get("/health")
    body = client.get("/metrics").text
    assert "http_requests_total" in body
