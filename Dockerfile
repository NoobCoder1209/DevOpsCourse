# syntax=docker/dockerfile:1.7
ARG PYTHON_VERSION=3.12-slim

# ---- deps stage --------------------------------------------------------------
FROM python:${PYTHON_VERSION} AS deps

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build
COPY requirements.txt .
RUN pip install --user --no-warn-script-location -r requirements.txt

# ---- runtime stage -----------------------------------------------------------
FROM python:${PYTHON_VERSION} AS runtime

LABEL org.opencontainers.image.source="https://github.com/NoobCoder1209/DevOpsCourse" \
      org.opencontainers.image.title="podinfo-app" \
      org.opencontainers.image.description="Demo Flask app exposing pod identity via the Kubernetes Downward API" \
      org.opencontainers.image.licenses="MIT"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH=/home/app/.local/bin:$PATH \
    PORT=8000

# Non-root user (UID matches Helm chart's securityContext.runAsUser).
RUN useradd --uid 10001 --create-home --shell /usr/sbin/nologin app

WORKDIR /app
COPY --from=deps --chown=app:app /root/.local /home/app/.local
COPY --chown=app:app app ./app

USER 10001
EXPOSE 8000

# Healthcheck uses urllib so we don't need curl in the runtime image.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2).status == 200 else 1)"

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--access-logfile", "-", "--error-logfile", "-", "app.main:create_app()"]
