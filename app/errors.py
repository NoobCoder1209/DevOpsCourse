"""Global JSON error handling.

Every unhandled exception becomes a generic JSON response with a
request_id so it can be cross-referenced with server-side logs.
No tracebacks ever cross the wire.
"""

from __future__ import annotations

import logging
import uuid

from flask import Flask, g, jsonify, request
from werkzeug.exceptions import HTTPException

log = logging.getLogger(__name__)


def register_error_handlers(app: Flask) -> None:
    @app.before_request
    def _assign_request_id() -> None:
        g.request_id = uuid.uuid4().hex

    @app.errorhandler(HTTPException)
    def _handle_http_exception(exc: HTTPException):
        return (
            jsonify(
                {
                    "error": exc.name,
                    "request_id": getattr(g, "request_id", None),
                }
            ),
            exc.code or 500,
        )

    @app.errorhandler(Exception)
    def _handle_unexpected(exc: Exception):
        log.exception(
            "unhandled exception",
            extra={"request_id": getattr(g, "request_id", None), "path": request.path},
        )
        return (
            jsonify(
                {
                    "error": "internal server error",
                    "request_id": getattr(g, "request_id", None),
                }
            ),
            500,
        )
