from __future__ import annotations

import re

from app.podinfo import podinfo


def test_podinfo_uses_downward_api_env(monkeypatch):
    monkeypatch.setenv("POD_NAME", "demo-pod-abc")
    monkeypatch.setenv("POD_IP", "10.244.1.7")
    monkeypatch.setenv("NODE_NAME", "kind-worker-1")
    info = podinfo()
    assert info["podName"] == "demo-pod-abc"
    assert info["podIP"] == "10.244.1.7"
    assert info["nodeName"] == "kind-worker-1"


def test_podinfo_falls_back_when_env_missing(monkeypatch):
    for k in ("POD_NAME", "POD_IP", "NODE_NAME"):
        monkeypatch.delenv(k, raising=False)
    info = podinfo()
    assert info["podName"]  # falls back to socket.gethostname()
    assert info["podIP"] == "127.0.0.1"
    assert info["nodeName"] == "local-node"


def test_podinfo_timestamp_is_iso8601_utc():
    info = podinfo()
    assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", info["timestamp"])
    assert info["timestamp"].endswith("+00:00")
