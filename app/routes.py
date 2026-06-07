"""HTTP routes for the demo app.

`/`        — pod identity payload (Downward API or localhost fallback)
`/healthz` — liveness/readiness probe target. Returns no internal info.
"""

from __future__ import annotations

from flask import Blueprint, jsonify

from app.podinfo import podinfo

bp = Blueprint("main", __name__)


@bp.get("/")
def index():
    return jsonify(podinfo())


@bp.get("/healthz")
def healthz():
    return jsonify({"status": "ok"}), 200
