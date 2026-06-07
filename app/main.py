"""Flask app factory + WSGI entry point for gunicorn.

Gunicorn loads `app.main:create_app()` from the Dockerfile CMD.
"""

from __future__ import annotations

import logging
import os

from flask import Flask

from app.errors import register_error_handlers
from app.routes import bp


def create_app() -> Flask:
    app = Flask(__name__)
    logging.basicConfig(
        level=os.environ.get("LOG_LEVEL", "INFO").upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    app.register_blueprint(bp)
    register_error_handlers(app)
    return app


# Allow `python -m app.main` for quick local sanity checks.
if __name__ == "__main__":  # pragma: no cover
    create_app().run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
