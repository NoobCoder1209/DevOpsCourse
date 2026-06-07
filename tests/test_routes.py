from __future__ import annotations

import logging


def test_healthz_returns_ok(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_healthz_does_not_leak_internals(client):
    response = client.get("/healthz")
    body = response.get_json()
    # Healthcheck must be opaque — no version, build, env keys.
    assert set(body.keys()) == {"status"}


def test_index_returns_pod_payload(client):
    response = client.get("/")
    assert response.status_code == 200
    body = response.get_json()
    assert set(body.keys()) >= {"podName", "podIP", "nodeName", "hostname", "timestamp"}
    assert all(isinstance(v, str) and v for v in body.values())


def test_404_returns_json_not_html(client):
    response = client.get("/this-route-does-not-exist")
    assert response.status_code == 404
    assert response.is_json
    body = response.get_json()
    assert "error" in body
    assert "request_id" in body
    assert body["request_id"]


def test_unexpected_exception_returns_json_500(client, monkeypatch):
    # Force an exception inside a route to prove the global handler shapes the response.
    from app import routes

    def boom():
        raise RuntimeError("boom")

    monkeypatch.setattr(routes, "podinfo", boom)
    response = client.get("/")
    assert response.status_code == 500
    body = response.get_json()
    assert body["error"] == "internal server error"
    assert body["request_id"]
    # Stack traces never go over the wire.
    assert "Traceback" not in response.get_data(as_text=True)


def test_request_ids_are_unique_across_requests(client):
    # Two 404s give us two error responses with request_ids; they must differ.
    r1 = client.get("/missing-1")
    r2 = client.get("/missing-2")
    id1 = r1.get_json()["request_id"]
    id2 = r2.get_json()["request_id"]
    assert id1 and id2
    assert id1 != id2


def test_unhandled_exception_logged_server_side(client, monkeypatch, caplog):
    # The contract has two halves: clean JSON to the client AND full detail
    # in server logs. This covers the log half.
    from app import routes

    def boom():
        raise RuntimeError("boom-for-logs")

    monkeypatch.setattr(routes, "podinfo", boom)
    with caplog.at_level(logging.ERROR, logger="app.errors"):
        response = client.get("/")
    assert response.status_code == 500
    assert any("unhandled exception" in rec.message for rec in caplog.records)
    # The original exception message should appear in the server-side log
    # (typically inside the traceback) — never in the response body.
    assert any("boom-for-logs" in rec.getMessage() + (rec.exc_text or "") for rec in caplog.records)
    assert "boom-for-logs" not in response.get_data(as_text=True)
