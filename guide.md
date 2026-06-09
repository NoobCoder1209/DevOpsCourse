# DevOpsCourse — Hands-On Guide

> **Last verified:** 2026-06-09 against commit `1f5a87b` (main HEAD at time of verification).
> Ran the full local flow on macOS 14 (Apple Silicon) with Docker Desktop 29.5.2, kind v0.23.0, helm v3.16, kubectl 1.30, Python 3.12.8.
> Observed: `pytest -q` 10/10 green at 100% coverage, `docker compose up` returned 200 on `/healthz`, kind+helm install + port-forward + curl returned the live K8s Downward API payload (`podName: demo-podinfo-app-59c4d666b8-qf62t`, `nodeName: guide-demo-control-plane`, `podIP: 10.244.0.5`), `helm test demo --logs` reported `Phase: Succeeded`. Captured terminal output is in [`docs/screenshots/local-demo.txt`](docs/screenshots/local-demo.txt) and a browser screenshot of `/` is in [`docs/screenshots/local-demo-browser.png`](docs/screenshots/local-demo-browser.png).

This guide is for someone who has never touched the repo. It covers:

1. [What this repo *is*](#1-what-this-repo-is)
2. [Prerequisites](#2-prerequisites)
3. [Run the demo end-to-end](#3-run-the-demo-end-to-end)
4. [Repo layout — what every file/dir does](#4-repo-layout--what-every-filedir-does)
5. [Environment variables and secrets](#5-environment-variables-and-secrets)
6. [How to verify the demo actually worked](#6-how-to-verify-the-demo-actually-worked)
7. [Common failure modes and fixes](#7-common-failure-modes-and-fixes)

---

## 1. What this repo *is*

A reference DevOps project: a tiny Flask app whose only job is to return its own pod identity, wired through a multi-stage Docker image, a Helm chart, five GitHub Actions workflows, and an Argo CD ApplicationSet. The app is intentionally trivial — the *pipeline* is the artifact. If you can install it on `kind` with `helm` and watch Argo CD reconcile a new image tag back into the cluster, you understand the demo.

Stack: Python 3.12 + Flask 3.1 + gunicorn 23 / Docker / Helm v3+ / kind / GitHub Actions / Argo CD.

---

## 2. Prerequisites

You need these on `PATH` before running anything below. Versions are what `Last verified` was tested against; older versions may work but are untested.

| Tool | Tested version | Install on macOS |
| --- | --- | --- |
| Python 3.12 | 3.12.8 | `brew install python@3.12` |
| Docker Desktop | 29.5.2 | https://docs.docker.com/desktop/install/mac-install/ — must be *running* before any `docker` / `kind` command |
| `kind` | v0.23.0 | `brew install kind` |
| `kubectl` | 1.30 | `brew install kubectl` |
| `helm` | v3.15+ | `brew install helm` |
| `gh` (GitHub CLI) | latest | `brew install gh` (only needed if you want to merge PRs / inspect Actions runs from the terminal) |

Linux / Windows-WSL users: every command below is plain bash and will work; just install the tools through your distro's package manager.

No language runtime other than Python is needed locally — the container image is built by Docker.

---

## 3. Run the demo end-to-end

Three flavours, in increasing order of "completeness":

- **3A** — local Python tests (~30 seconds)
- **3B** — local Docker container (~1 minute)
- **3C** — kind + Helm round trip (~3 minutes, this is the real demo)

Pick one or run all three in order — they're independent.

### 3A. Run the test suite (no Docker, no cluster)

```bash
git clone https://github.com/NoobCoder1209/DevOpsCourse.git
cd DevOpsCourse

python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

ruff check .
pytest -q
```

Expected output:

```
All checks passed!
..........                                                               [100%]

---------- coverage: platform darwin, python 3.12.8-final-0 ----------
TOTAL                46      0   100%
```

10 tests, 100% line coverage on the `app/` package. `ruff` returns silently when clean.

### 3B. Run the app in Docker locally

Docker Desktop must be running first.

```bash
docker compose up -d --build
```

This builds the multi-stage image and starts the container in the background. After ~5 seconds:

```bash
curl http://localhost:8000/healthz
# → {"status":"ok"}

curl http://localhost:8000/ | python3 -m json.tool
# → {
#     "hostname": "...",
#     "nodeName": "local-node",
#     "podIP": "127.0.0.1",
#     "podName": "local-pod",
#     "timestamp": "2026-06-09T..."
#   }

docker compose ps
# Wait ~15s for the first healthcheck probe — the container starts up
# in a few seconds but stays in `(health: starting)` until the first
# /healthz probe succeeds. After that it flips to:
# Container should show:  Up X seconds (healthy)

docker compose exec app id
# → uid=10001(app) gid=10001(app)  ← non-root, as designed
```

When you're done:

```bash
docker compose down
```

### 3C. Run the full kind + Helm demo (the real demo)

This is the canonical "DevOps story": build the image, side-load it into a kind cluster, install the chart, prove the pod gets identity from the K8s Downward API, run the in-cluster `helm test`.

```bash
# 1. Build the image (uses the same Dockerfile as production)
docker build -t podinfo-app:demo .

# 2. Spin up a single-node kind cluster
kind create cluster --name guide-demo --image kindest/node:v1.30.0

# 3. Side-load the local image so the cluster can pull it without GHCR
kind load docker-image podinfo-app:demo --name guide-demo

# 4. Install the chart, overriding image + pullPolicy
kubectl --context kind-guide-demo create namespace demo
helm --kube-context kind-guide-demo install demo chart/ -n demo \
  --set image.repository=podinfo-app \
  --set image.tag=demo \
  --set image.pullPolicy=Never \
  --wait --timeout 3m

# 5. Confirm the pod is Running 1/1
kubectl --context kind-guide-demo -n demo get pods,svc

# 6. Port-forward the service. Run this in one terminal and leave it running:
kubectl --context kind-guide-demo -n demo port-forward svc/demo-podinfo-app 18091:80

# 7. In a second terminal:
curl http://localhost:18091/healthz
# → {"status":"ok"}

curl http://localhost:18091/ | python3 -m json.tool
# → all 5 fields with REAL pod identity, e.g.
# {
#   "hostname": "demo-podinfo-app-59c4d666b8-qf62t",
#   "nodeName": "guide-demo-control-plane",
#   "podIP": "10.244.0.5",
#   "podName": "demo-podinfo-app-59c4d666b8-qf62t",
#   "timestamp": "..."
# }

# 8. Run the chart's built-in test pod (curls /healthz + / from inside the cluster):
helm --kube-context kind-guide-demo test demo -n demo --logs
# → Phase: Succeeded
# → POD LOGS: probing http://demo-podinfo-app:80/healthz
#             probing http://demo-podinfo-app:80/

# 9. Tear down (skip if you want to keep poking around):
kind delete cluster --name guide-demo
```

Verbatim captured output from a successful run: [`docs/screenshots/local-demo.txt`](docs/screenshots/local-demo.txt).

### Optional: Argo CD GitOps flow

The repo ships full Argo CD manifests under `argocd/` and a `gitops-e2e.yml` workflow that proves the round-trip on every PR (kind cluster → install Argo CD via Helm → apply the ApplicationSet → wait Synced+Healthy → curl the deployed service). See [`argocd/README.md`](argocd/README.md) for the local recipe — it's stricter than the smoke test and exercises the full GitOps story, but isn't necessary to "see the demo work".

---

## 4. Repo layout — what every file/dir does

### Root

| Path | Purpose |
| --- | --- |
| `README.md` | Public-facing pitch: badges, architecture diagram, three demo screenshots, quick start |
| `PLAN.md` | The original execution plan that drove the rebuild — kept for posterity |
| `guide.md` | This file. Hands-on walkthrough |
| `LICENSE` | MIT |
| `Dockerfile` | Multi-stage image. Stage 1 builds Python deps as `pip --user`; stage 2 (`python:3.12-slim`) copies them in, runs as UID 10001, healthchecks via `urllib`, `CMD` is `sh -c 'exec gunicorn ... app.main:app'` |
| `docker-compose.yml` | Local dev shape. Maps port 8000, loads `.env.example`, mirrors the Dockerfile healthcheck, `init: true` for clean Ctrl-C |
| `requirements.txt` | Pinned runtime deps: Flask 3.1.3, gunicorn 23.0.0, pydantic 2.13.4 |
| `requirements-dev.txt` | Adds ruff, pytest, pytest-cov |
| `pyproject.toml` | Single source of truth for ruff + pytest config |
| `.env.example` | Documents the K8s Downward API env vars (`POD_NAME`, `POD_IP`, `NODE_NAME`) and their localhost fallbacks |
| `.gitignore` / `.dockerignore` | Standard. `.env*` blocked except `.env.example`; Helm `Chart.lock` and packaged `.tgz` files ignored |

### `app/` — the Flask application

| File | What it does |
| --- | --- |
| `app/main.py` | Flask app factory. `create_app()` registers the blueprint + global error handlers. **Module-level `app = create_app()`** is what gunicorn loads as `app.main:app` |
| `app/routes.py` | Blueprint with `GET /` (returns the pod identity payload) and `GET /healthz` (returns `{"status":"ok"}` and **nothing else** — opaque by design). The non-opaque `/` is documented in `podinfo.py`'s module docstring as the demo endpoint where pod identity is the point |
| `app/podinfo.py` | Reads `POD_NAME` / `POD_IP` / `NODE_NAME` from env (Downward API in cluster) with localhost fallbacks. Adds `hostname` (always `socket.gethostname()`) and an ISO-8601 UTC `timestamp` |
| `app/errors.py` | Global error handler: every unhandled exception becomes `{"error": "...", "request_id": "..."}` JSON. **Tracebacks never leave the server.** Per-request UUID set in `before_request` for correlating client error to server log |
| `app/__init__.py` | Empty marker file |

### `tests/`

| File | What it tests |
| --- | --- |
| `tests/__init__.py` | Empty marker file |
| `tests/conftest.py` | Single `client` fixture wrapping `create_app()` (sets `app.testing = True` then yields the test client) |
| `tests/test_routes.py` | `/healthz` opacity (only `status` key), `/` payload shape, JSON 404, forced exception → JSON 500 with `request_id` and **no traceback substring**, request_id uniqueness across two requests, server-side log capture (caplog) on the 500 path |
| `tests/test_podinfo.py` | Env-var override + localhost fallback + ISO-8601 UTC timestamp |

### `chart/` — the Helm chart

| File | Purpose |
| --- | --- |
| `chart/Chart.yaml` | apiVersion v2, name `podinfo-app`, version 0.1.0, appVersion "0.1.0". **Comment explains chart-vs-app version coupling** |
| `chart/values.yaml` | Defaults. `image.tag: ""` defaults to `Chart.AppVersion` via the deployment template — env overlays pin a real tag. PSS-restricted securityContext (UID 10001, drop ALL caps, readOnlyRootFilesystem with `/tmp` emptyDir for gunicorn scratch). Probes hit `/healthz`. `automountServiceAccountToken: false` |
| `chart/values.schema.json` | JSON-Schema enforcing `image.repository`, `service.{port,targetPort}` ranges, gunicornWorkers 1-32, etc. Fails `helm install` early instead of producing a broken Pod |
| `chart/templates/deployment.yaml` | Wires the Downward API env vars `POD_NAME` / `POD_IP` / `NODE_NAME`. `automountServiceAccountToken: false` on the pod spec too (defense in depth) |
| `chart/templates/service.yaml` | ClusterIP, port 80 → named-port `http` (8000) |
| `chart/templates/serviceaccount.yaml` | `automountServiceAccountToken: false` (the app makes no API calls) |
| `chart/templates/ingress.yaml` | Gated on `.Values.ingress.enabled` |
| `chart/templates/_helpers.tpl` | Standard fullname / labels / selectorLabels / serviceAccountName templates |
| `chart/templates/NOTES.txt` | Post-install instructions printed by `helm install`. Includes a watch loop that proves pod identity rotates on rollout |
| `chart/templates/tests/test-connection.yaml` | `helm test` pod (curlimages/curl 8.10.1). Curls `/healthz` and `/` against the in-cluster Service. **`hook-delete-policy: before-hook-creation`** keeps the pod alive after success so `--logs` works |
| `chart/.helmignore` | Standard, **does NOT** exclude `templates/tests/` so `helm test` survives `helm package` |

### `environments/`

| File | Purpose |
| --- | --- |
| `environments/dev/values.yaml` | Dev image tag overlay. **Rewritten by `build-and-push.yml` on every merge to `main`** — a `yq -i` edit + commit-back. Don't hand-edit; the next CI run will overwrite |
| `environments/prod/values.yaml` | Human-pinned tag, 2 replicas, larger gunicorn worker count + resources budget. **Only `release.yml` (on `v*` tags) bumps prod.** Deliberately gated, not auto-promoted |

### `argocd/`

| File | Purpose |
| --- | --- |
| `argocd/applicationset.yaml` | `goTemplate: true` ApplicationSet with a list generator over `[dev, prod]`. Uses `templatePatch` to set typed booleans (prune/selfHeal) per env — dev is auto-sync, prod is manual |
| `argocd/application-dev.yaml` | Standalone Application for dev (alternative to the ApplicationSet) |
| `argocd/application-prod.yaml` | Same for prod, with manual sync policy |
| `argocd/README.md` | How to install Argo CD into any cluster + apply these manifests. **Documents the GHCR-private-by-default caveat** |

### `.github/`

| File | Triggers | What it does |
| --- | --- | --- |
| `workflows/ci.yml` | PR + push (any branch) | Three jobs in parallel: python (ruff + pytest), helm (lint + template + Downward API contract grep), actionlint |
| `workflows/build-and-push.yml` | push to `main`, paths-filtered | buildx → GHCR (sha-7 + latest tags, OCI labels), then `bump-dev` rewrites `environments/dev/values.yaml` and commits back as `github-actions[bot]` with `[skip ci]`. Now uses the published reusable workflow `_docker-buildx@v0.1.0` |
| `workflows/smoke.yml` | PR + push to main, paths-filtered | kind cluster + build + side-load image + `helm install --wait` + port-forward + curl `/healthz` and `/` (asserts `podName` actually came from the Downward API) + `helm test --logs`. Diagnostics on failure |
| `workflows/gitops-e2e.yml` | PR + push to main, paths-filtered | The GitOps proof: kind + install Argo CD via Helm + patch ApplicationSet to PR's ref + apply → wait Synced+Healthy → curl |
| `workflows/release.yml` | `v*` tag | Tagged image push (with leading `v` stripped from the docker tag) + GitHub Release with auto notes |
| `dependabot.yml` | Schedule | Weekly: github-actions, pip, docker. Limits: 5 / 5 / 3 |

### `docs/`

| File | Purpose |
| --- | --- |
| `docs/screenshots/ci-passing.png` | All 4 workflows green on main (Actions overview) |
| `docs/screenshots/kind-smoke.png` | `smoke.yml` run detail page |
| `docs/screenshots/argo-sync.png` | `gitops-e2e.yml` run detail page |
| `docs/screenshots/local-demo.txt` | **Verbatim terminal output** from the local kind+helm flow above (added with this guide) |
| `docs/screenshots/local-demo-browser.png` | **Browser screenshot** of `/` rendering the live Downward API JSON (added with this guide) |

---

## 5. Environment variables and secrets

### App-level (read by the Flask app at runtime)

| Variable | Default | Where set | Notes |
| --- | --- | --- | --- |
| `POD_NAME` | `socket.gethostname()` | Downward API (`metadata.name`) in cluster; `.env.example` for local | Shown in `/` payload |
| `POD_IP` | `127.0.0.1` | Downward API (`status.podIP`) in cluster; `.env.example` for local | Shown in `/` payload |
| `NODE_NAME` | `local-node` | Downward API (`spec.nodeName`) in cluster; `.env.example` for local | Shown in `/` payload |
| `PORT` | `8000` | Helm chart (= `targetPort`) or env | Bound by gunicorn |
| `GUNICORN_WORKERS` | `2` | Helm chart (`.Values.gunicornWorkers`) | Tunable per env without rebuilding the image |
| `LOG_LEVEL` | `INFO` | Optional; only sets Python `logging.basicConfig` level | |

For **local development**, copy `.env.example` to `.env` and tweak as you like. `.env` is gitignored. `docker-compose.yml` loads `.env.example` directly (it's all defaults; nothing secret).

### CI / Pipeline secrets

The pipeline uses **only** `secrets.GITHUB_TOKEN`, which GitHub Actions injects automatically. There are no additional secrets to configure.

- `build-and-push.yml` and `release.yml` use `${{ secrets.GITHUB_TOKEN }}` to push images to GHCR (requires `permissions: packages: write` at the job level — already set).
- `bump-dev` job uses the same token to commit back to `main`.
- No external registry auth, no external service tokens, no Slack webhooks, no PagerDuty.

If you fork this repo, the only thing you need to do is **make the GHCR package public** after the first push (it defaults to private). Either:

1. Open https://github.com/users/&lt;your-user&gt;/packages/container/devopscourse/settings, scroll to "Danger Zone", change visibility to public; OR
2. Add `imagePullSecrets` referencing a GHCR PAT to your env overlay (`environments/dev/values.yaml`).

---

## 6. How to verify the demo actually worked

Three independent gates, in increasing order of strength:

### Local
- `pytest -q` → 10 passed, 100% coverage
- `docker compose up -d` → `docker compose ps` shows `Up X seconds (healthy)`
- `curl http://localhost:8000/healthz` → `{"status":"ok"}`
- `curl http://localhost:8000/` → JSON with all 5 fields (`hostname`, `nodeName`, `podIP`, `podName`, `timestamp`)
- `docker compose exec app id` → `uid=10001(app)`

### Cluster (kind)
- `kubectl -n demo get pods` → `demo-podinfo-app-...   1/1   Running`
- `helm test demo -n demo --logs` → `Phase: Succeeded` plus `probing http://demo-podinfo-app:80/healthz` and `.../` lines
- The `/` payload's `podName` equals the actual pod name (proves the Downward API fired, not just localhost fallback)
- The `/` payload's `nodeName` equals the kind cluster's node name (e.g. `guide-demo-control-plane`)

### CI on `main`
- https://github.com/NoobCoder1209/DevOpsCourse/actions — all 4 workflows show green for the latest commit
- After the merge, a new commit appears on `main` from `github-actions[bot]`: `chore(dev): bump image to sha-XXXXXXX [skip ci]`. That commit modified only `environments/dev/values.yaml`. **This is the GitOps loop closing.**
- `gh release view v0.1.0` shows the published release + linked image

If all three pass, the demo "actually worked" in every meaningful sense.

---

## 7. Common failure modes and fixes

### "Cannot connect to the Docker daemon"

Docker Desktop isn't running. Open the Docker app from `/Applications` and wait 10-15 seconds for the whale icon in the menu bar to stop animating. Re-run.

### `kind create cluster` hangs at "Ensuring node image"

First-time pull of `kindest/node` is ~700MB and slow. Wait. If it eventually times out, re-run — kind resumes from the partial pull.

### `helm install` returns `Error: INSTALLATION FAILED: context deadline exceeded`

The pod isn't reaching `Ready` within `--timeout 3m`. Almost always one of:

1. **Image not loaded into kind.** `kind load docker-image podinfo-app:demo --name <cluster>` — and the tag in `--set image.tag=` must match.
2. **Wrong `pullPolicy`.** Without `--set image.pullPolicy=Never`, Kubernetes tries to pull from the public registry, fails (because `podinfo-app:demo` only exists in your local kind), and the pod sits in `ErrImageNeverPull`.
3. **You started a fresh `kind create` but reused an old `helm install`** in the same namespace from a prior run. `kubectl get all -n demo` and clean up.

Diagnostics:
```bash
kubectl -n demo describe pods
kubectl -n demo logs -l app.kubernetes.io/instance=demo --tail=200
kubectl -n demo get events --sort-by=.lastTimestamp
```

### `helm test` exits 1 with `unable to get pod logs ... pods "..." not found`

This was a real bug, fixed in the chart. If you're seeing it on a fresh clone, your chart cache is stale — `rm -rf chart/charts chart/Chart.lock` and try again. The fix: `chart/templates/tests/test-connection.yaml` uses `helm.sh/hook-delete-policy: before-hook-creation` (NOT `hook-succeeded`), so the test pod stays around for `--logs` to fetch.

### Pod logs say `sh: 1: Syntax error: "(" unexpected`

You're on an old commit. The Dockerfile's `CMD` used to call `app.main:create_app()`. Fixed in `5d407a4`: switched the WSGI target from `app.main:create_app()` to module-level `app.main:app` so the CMD argv contains no parentheses. Pull `main` and rebuild.

### `helm install` rejects values with a schema error

`values.schema.json` is doing its job. The error message names the offending path (e.g. `at '/service/port': maximum: got 99,999, want 65,535`). Fix the value or remove the override.

### `docker build` on Apple Silicon fails the buildx multi-arch build

The Dockerfile is single-arch (`linux/amd64`) by default. If you've configured a custom buildx builder targeting other platforms and it fails, run with `docker build --platform linux/arm64 -t podinfo-app:demo .` instead. The chart and CI don't care about arch; they pin `linux/amd64` in CI.

### `kubectl port-forward` returns "connection refused" immediately

Background-launching port-forward is timing-dependent. Run it in the foreground in its own terminal and leave it running — that's the canonical pattern.

### Argo CD's `templatePatch` is silently ignored

You're on Argo CD < v2.11. `templatePatch` GA'd in v2.11; any earlier version silently drops it. If you're applying these manifests against a self-managed Argo install, check its version: `kubectl -n argocd get deploy argocd-server -o jsonpath='{.spec.template.spec.containers[0].image}'`. The `gitops-e2e.yml` workflow uses `helm install argocd argo/argo-cd --version 7.6.12`, which provisions an Argo CD release new enough to support `templatePatch`.

### Image push to GHCR returns 403 / 401

First-push behaviour. Two causes:

1. The workflow is missing `permissions: packages: write` at the job level (it isn't — but if you're forking and stripped it, that's the cause).
2. **Repo Settings → Actions → General → Workflow permissions** is set to "Read repository contents and packages permissions". Change to "Read and write permissions" (one-time per fork).

After the first successful push, the package is created **private**. To make it pullable from outside Actions, see [Section 5](#5-environment-variables-and-secrets).

### CI `build-and-push` runs cancel each other on rapid merges

By design — `concurrency: build-${{ github.ref }}`. The latest push wins, earlier in-flight runs are cancelled. The latest run still produces the canonical image and the GitOps tag bump. Not a bug.

### Dependabot PR has merge conflicts

Two dependabot PRs touched the same line in `requirements*.txt` — typical when two test-deps land near each other. Either:
- Merge them in conflict-free order (the first one merges fine, dependabot rebases the second automatically); or
- Close the conflicting one and let dependabot regenerate it on the next weekly run.
