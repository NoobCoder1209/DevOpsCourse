from __future__ import annotations


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
