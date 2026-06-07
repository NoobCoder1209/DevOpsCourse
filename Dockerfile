# syntax=docker/dockerfile:1.7
ARG PYTHON_VERSION=3.12-slim

# ---- deps stage --------------------------------------------------------------
FROM python:${PYTHON_VERSION} AS deps

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --user --no-warn-script-location -r requirements.txt

# ---- runtime stage -----------------------------------------------------------
FROM python:${PYTHON_VERSION} AS runtime

LABEL org.opencontainers.image.source="https://github.com/NoobCoder1209/DevOpsCourse" \
      org.opencontainers.image.title="podinfo-app" \
      org.opencontainers.image.description="Demo Flask app exposing pod identity via the Kubernetes Downward API" \
      org.opencontainers.image.licenses="MIT"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/home/app/.local/bin:$PATH \
    PORT=8000 \
    GUNICORN_WORKERS=2

# Non-root user (UID matches Helm chart's securityContext.runAsUser).
RUN useradd --uid 10001 --create-home --shell /sbin/nologin app

WORKDIR /app
COPY --from=deps --chown=app:app /root/.local /home/app/.local
COPY --chown=app:app app ./app

USER app
EXPOSE 8000

# Healthcheck uses urllib so we don't need curl in the runtime image.
# Wrapped in try/except so HTTPError / URLError / timeouts produce a clean
# `exit 1` instead of a noisy traceback in container logs.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD ["python", "-c", "import sys, urllib.request\ntry:\n    r = urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2)\n    sys.exit(0 if r.status == 200 else 1)\nexcept Exception:\n    sys.exit(1)"]

# Gunicorn worker count is overridable via the GUNICORN_WORKERS env var
# (defaults to 2). The Helm chart can tune it without rebuilding the image.
# Using sh -c so shell parameter expansion works; `exec` keeps gunicorn as
# PID 1 for correct signal handling. The WSGI target is `app.main:app`
# (a module-level Flask instance) so the CMD string contains no shell-
# interpreted parentheses.
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:${PORT:-8000} --workers ${GUNICORN_WORKERS:-2} --access-logfile - --error-logfile - app.main:app"]
