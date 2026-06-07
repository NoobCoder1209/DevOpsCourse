# `DevOpsCourse` — Execution Plan (Full Rebuild)

## How to use this plan

You are the build session for this repo. Read this file end-to-end, then start executing immediately.

**Working agreement:**

1. **Start without waiting.** Begin Phase 1 in the *Subagent playbook* below.
2. **Always ask the user about business decisions and business logic.** What this repo *should be* (see "Business decisions" below), demo app theme, README copy, screenshot framing.
3. **Ask the user when you are genuinely blocked.**
4. **Do not ask the user about engineering details.** Internal tool versions, file layout, manifest field names — your call.
5. **Use subagents aggressively.** Default to the playbook below.
6. **TaskCreate / TaskUpdate everything.**
7. **Pattern 3 only.** No deployed cluster demo. README ships GIF/screenshots of CI passing + `kind` smoke test.
8. **Follow shared standards** (MIT, README, CI, topics, **flip public when verification passes — repo is currently public, so it should NEVER be visibly broken on `main`. Use a `rebuild/*` branch and merge only when ready.**).
9. **All `Agent` tool calls must pass `model: "opus"`.**
10. **Off-limits forever:** SAP-internal references, `~/.claude/`, RCA content.

## Branch + PR workflow (mandatory)

Every PLAN.md inherits this. Sessions never commit straight to `main`.

1. **One branch per phase.** Name branches `phase/<N>-<slug>` matching the build phases below. Examples: `phase/1-bootstrap`, `phase/2-core`, `phase/3-tests`, `phase/4-readme`, `phase/5-polish`. ~3–5 phases per repo, ~3–5 PRs per repo.
2. **Aggressive commits within a branch.** Push every meaningful commit to the working branch. WIP is fine on a feature branch.
3. **Open a PR when the phase is complete.** Use `gh pr create`. Clear title (`phase 2: core agent loop` style) and a short body summarising what changed.
4. **Run `/pr-reviewer` on every PR.** No exceptions. The reviewer reads the diff and produces findings.
5. **Decision rule:**
   - **Clean review (zero findings) → auto-merge** with `gh pr merge --squash --auto`. Move on to the next phase.
   - **Any findings (even nits) → surface them to the user.** Do NOT auto-merge. Wait for user direction (fix on the same branch, defer, or override).
6. **`main` stays green.** Phase branches can be WIP; `main` only ever gets reviewed-clean code.
7. **Branch naming + commit messages must follow `git-safety-standards`** (`feature/`, `fix/`, `docs/` prefixes acceptable as alternatives to `phase/N-` when a change spans phases).
8. **Never `--force` push to `main`.** Force-push to your own phase branches is fine before the PR is opened.

## Subagent playbook (this repo)

Full rebuild = lots of moving parts. 4 in research, 2 in review.

**Phase 1 — Research (parallel):**
- `Explore` (Opus): "Find current best-practice end-to-end DevOps demo app: what's the simplest stack a 2026 Upwork client would respect? Compare options: Flask + Helm + GitHub Actions + Argo CD vs FastAPI + Helm + Tekton vs Node + Helm + GH Actions. Return ≤300 words."
- `Explore` (Opus): "Find the canonical kind-based GitHub Actions smoke test for a Helm-deployed app — install chart, wait for pods ready, curl service, helm test. Return a complete workflow."
- `Explore` (Opus): "Find a clean reference for a Flask app + Dockerfile + docker-compose.yml that's production-shaped (non-root user, multi-stage, healthcheck). Return ≤120 lines."
- `Explore` (Opus): "Find the canonical Argo CD ApplicationSet + GitHub Actions integration where merging to main triggers redeploy via GitOps. Return architecture summary."

**Phase 2 — Design (single):**
- `Plan` (Opus): "Given research, the user's business decisions, and this PLAN.md, propose the rebuild file tree, the demo app's purpose, the build order, and a CI matrix. Return as a checklist."

**Phase 3 — Build:** main session writes the rebuild on a `rebuild/v1` branch. Dispatch `Explore` for specific tooling questions.

**Phase 4 — Review (parallel):**
- `code-reviewer` (Opus): "Review for: clean rewrite (no leftover from old repo), Dockerfile production-shape (no Docker-in-Docker), Helm chart correctness (probes/resources/securityContext), CI test coverage. High effort."
- `tester` (Opus): "Run the full local flow: `docker compose up`, kind cluster install, `helm install`, smoke curl. Confirm green. Add unit + integration tests for the app."

**Phase 5 — Polish:** PR `rebuild/v1` → `main`, capture GIF, update README, ask user before merging.

---

## Goal

Rebuild this repo from a messy university coursework dump into a **clean, end-to-end DevOps reference project** that can sit on the public profile next to the new portfolio repos.

**What's there now (do not keep):** a half-finished Flask app, a Docker-in-Docker Dockerfile that doesn't make sense for the app, a Jenkinsfile that pushes to Docker Hub with credentials that probably don't work, and a `kubernetes-jenkins/` directory that deploys Jenkins into a cluster (not the app). Empty README. No CI. No screenshots.

**What this should become (target):** A small "demo app + IaC + GitOps" reference repo. Concretely:
- A small **demo web app** (Python Flask or Node, user picks)
- A **production-shaped Dockerfile** (multi-stage, non-root)
- A **Helm chart** for it (referenced from `helm-chart-template` if appropriate)
- A **GitHub Actions CI/CD pipeline** (build → test → push to GHCR → kind smoke test)
- A small `argocd/` directory with ApplicationSet manifests showing how a GitOps deploy would wire up
- A clean README explaining the journey from "code change → image → deploy"

**Sells:** DevOps, CI/CD, Kubernetes, Helm, Docker, GitHub Actions, GitOps, Argo CD.

## Business decisions to ask the user about

These are the load-bearing questions — surface them **before any code is written**:

- **Keep "DevOpsCourse" as the repo name?** It's a uni-course holdover. Alternatives: `gitops-demo`, `devops-reference`, `flask-cicd-demo`. Renaming is cheap; pick the right one for the public profile.
- **Demo app stack** — recommend Python Flask (matches user's CV "Python" line, simple). Alternatives: Node Express, Go net/http.
- **What the demo app *does*** — recommend a single-page "what time is it in N timezones" or "what's the public IP of this pod" — the actual functionality has to be 5 minutes of code so the focus stays on the pipeline. User may have a topic in mind.
- **Whether to delete the old `kubernetes-jenkins/` Jenkins-on-K8s manifests** — recommend yes (clutter). Alternative: extract into a separate scratch branch.
- **Whether to keep the old Jenkinsfile** — recommend no (the new pipeline is GitHub Actions). Move to scratch branch if user is sentimental.
- **Argo CD section depth** — manifest-only (recommended) vs include a `kind` + Argo install script for full local demo (more impressive, more upkeep).

## Scope (must-haves)

1. **Clean rebuild** on a `rebuild/v1` branch; merge to `main` only at the end.
2. **Demo app** — small Flask app with one endpoint + healthcheck + a unit test.
3. **Dockerfile** — multi-stage, non-root user, healthcheck instruction, sensible labels.
4. **`docker-compose.yml`** — local dev with hot reload (or close to it).
5. **Helm chart** under `chart/` — either copy `helm-chart-template` if that repo has shipped, or write a slim version inline.
6. **GitHub Actions CI/CD**:
   - Lint + test
   - Build image, push to GHCR on push to `main`, semver release on tag
   - Kind cluster + `helm install` smoke test on PR
7. **Argo CD manifests** under `argocd/` — `Application` or `ApplicationSet`, points at the chart in this repo, sample values for `dev` + `prod`.
8. **README** with: hero, architecture diagram (the journey), quick start, "Skills demonstrated," license.

## Production hygiene (must apply, not optional)

Inherits the master plan's "Production hygiene checklist." Repo-specific application:

- **Env vars at runtime.** `.env.example` shipped; `.env*` gitignored; no secrets ever in image layers.
- **Pydantic input validation on every Flask route accepting payloads.** Use Pydantic v2 models for request bodies. Bad input → 400 with a clean JSON error, never a stack trace.
- **Global Flask error handler.** `@app.errorhandler(Exception)` returns a generic JSON `{ "error": "...", "request_id": "..." }`. **No tracebacks in HTTP responses, ever.** Log full details server-side at `ERROR` level for debugging.
- **Healthcheck endpoint that doesn't leak.** `/healthz` returns 200 with `{ "status": "ok" }` — no version strings, no internals.
- **Index on the high-traffic field.** If the demo app reads from any persistent store (likely not for this scope), document the index choice.

## Out of scope

- No Jenkins (replaced)
- No SonarQube (different repo, different scope)
- No real cloud deployment (Pattern 3)
- No multi-app monorepo
- No databases / external dependencies in the demo app

## Tech stack

Default (subject to user decision):
- **App:** Python 3.12 + Flask
- **Image registry:** GHCR
- **Helm:** v3.13+
- **CI:** GitHub Actions
- **Smoke test:** kind v1.28
- **GitOps:** Argo CD (manifests only)
- **Linting:** `ruff` (Python), `helm lint`, `actionlint`
- **Testing:** `pytest`

## File tree (after rebuild)

```
DevOpsCourse/                    ← rename pending user decision
  README.md
  PLAN.md
  LICENSE                        ← MIT (already exists; keep)
  .gitignore
  .dockerignore
  app/
    __init__.py
    main.py                      ← Flask app
    routes.py
    healthcheck.py
  tests/
    test_main.py
  Dockerfile                     ← multi-stage, non-root
  docker-compose.yml
  requirements.txt
  pyproject.toml
  ruff.toml
  chart/                         ← Helm chart for the app
    Chart.yaml
    values.yaml
    values.schema.json
    templates/
      _helpers.tpl
      deployment.yaml
      service.yaml
      ingress.yaml
      configmap.yaml
      NOTES.txt
    tests/test-connection.yaml
  argocd/
    application-dev.yaml
    application-prod.yaml
    applicationset.yaml
  .github/workflows/
    ci.yml                       ← lint + test
    build-and-push.yml           ← image build + push on main
    smoke.yml                    ← kind + helm install
    release.yml                  ← semver on tag
  docs/
    architecture.png
    screenshots/
      ci-passing.png
      kind-smoke.png
```

## Step-by-step build

### 1. Branch + clean

```bash
git checkout -b rebuild/v1
git rm -rf app.py main.py Dockerfile docker-compose.debug.yml \
  get_helm.sh kubernetes-jenkins Virtual app
```

(Keep `LICENSE`, `README.md`, `requirements.txt` to overwrite; remove everything else.)

### 2. App skeleton

`app/main.py`:
```python
from flask import Flask
def create_app():
    app = Flask(__name__)
    from .routes import bp
    app.register_blueprint(bp)
    return app
```

`app/routes.py`: `/` returns the demo content (decided with user), `/healthz` returns 200.

`tests/test_main.py`: pytest covering both endpoints.

### 3. Dockerfile (multi-stage, non-root)

```dockerfile
FROM python:3.12-slim AS deps
WORKDIR /build
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.12-slim AS runtime
RUN useradd -u 10001 -m app
WORKDIR /app
COPY --from=deps /root/.local /home/app/.local
COPY --chown=app:app app/ ./app/
ENV PATH=/home/app/.local/bin:$PATH PYTHONUNBUFFERED=1
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD curl -f http://localhost:8000/healthz || exit 1
CMD ["gunicorn", "-b", "0.0.0.0:8000", "app.main:create_app()"]
```

Add `gunicorn` to `requirements.txt`.

### 4. `docker-compose.yml`

```yaml
services:
  app:
    build: .
    ports: ["8000:8000"]
    environment: { FLASK_ENV: development }
```

### 5. Helm chart

If `helm-chart-template` has shipped, fork it; otherwise write a slim version. Probes hit `/healthz`. `values.yaml` exposes image repo + tag.

### 6. GitHub Actions

- `ci.yml` — `ruff check`; `pytest`.
- `build-and-push.yml` — Docker Buildx multi-arch, push to `ghcr.io/noobcoder1209/devopscourse:${{ github.sha }}` on push to `main`.
- `smoke.yml` — kind v1.28; `helm install` chart with image-tag override; `kubectl wait`; curl.
- `release.yml` — on `v*` tag, push image with that tag, create GitHub Release.

### 7. Argo CD manifests

`argocd/application-dev.yaml` pointing at `chart/`, `values-dev.yaml`. Same for prod. `applicationset.yaml` showing the multi-env shape. README explains how to apply against an existing Argo CD install.

### 8. README

1. Title — depends on rename
2. Demo — `docs/screenshots/ci-passing.png` + `kind-smoke.png`
3. Architecture — `docs/architecture.png` (commit → Actions → image → kind → optional Argo CD)
4. What it shows
5. Skills demonstrated — DevOps, CI/CD, Kubernetes, Helm, Docker, GitHub Actions, GitOps, Argo CD, Python, Flask
6. Quick start — local docker-compose + kind smoke
7. License — MIT

### 9. Polish + merge

PR `rebuild/v1` → `main`. Capture screenshots before merge. Topics: `devops`, `cicd`, `kubernetes`, `helm`, `docker`, `github-actions`, `gitops`, `argocd`, `flask`. Ask user before merging.

## Verification

- [ ] Old files removed (`kubernetes-jenkins/`, `Virtual/`, `get_helm.sh`, ad-hoc Python files)
- [ ] Fresh clone → `docker compose up` works
- [ ] `pytest` green
- [ ] Image builds + pushes to GHCR on `main`
- [ ] `helm install` smoke test green in CI on a kind cluster
- [ ] Argo CD manifests valid (`kubectl apply --dry-run=server`)
- [ ] README has architecture diagram + screenshots
- [ ] No SAP-internal references; no `~/.claude/` references
- [ ] Topics + description set
- [ ] Repo renamed if user agreed
- [ ] All Flask error responses are JSON-shaped, no HTML stack-trace pages
- [ ] Bad payload returns 400 with Pydantic-shaped error, not 500
- [ ] `/healthz` returns no internal version / build info

## Stretch (defer)

- Real Argo CD instance in kind in CI for true e2e GitOps proof
- Cosign signing pushed images
- Renovate config
- Multi-arch image
