# AI Code Reviewer

A centralized, AI-powered pull request review service built with **FastAPI**. It fetches the changed files of a GitHub pull request, sends each supported file's diff (with optional surrounding file context) to a chat-completions-compatible LLM endpoint, parses the model's structured JSON response, and posts inline review comments back onto the PR.

It is designed to run **organization-wide from a single service** so individual repositories do not need their own review pipelines. A Jenkins webhook pipeline triggers the service on PR events (or on a `/ai-review` comment), and the service does the rest.

---

## Table of Contents

- [How it works](#how-it-works)
- [Features](#features)
- [Project structure](#project-structure)
- [API reference](#api-reference)
- [Configuration](#configuration)
- [Quick start (local)](#quick-start-local)
- [Run with Docker](#run-with-docker)
- [Deploy to Kubernetes (Helm)](#deploy-to-kubernetes-helm)
- [CI/CD and webhook triggers (Jenkins)](#cicd-and-webhook-triggers-jenkins)
- [Security notes](#security-notes)
- [Development notes and limitations](#development-notes-and-limitations)
- [License](#license)

---

## How it works

```
GitHub PR event / "/ai-review" comment
        │
        ▼
Jenkins webhook pipeline (ai-reviewer.Jenkinsfile)
        │  POST { owner, repo, pull_number }
        ▼
FastAPI service  ──►  POST /review/pr
        │
        ├─ 1. Fetch PR metadata + changed files   (GitHub REST API)
        ├─ 2. Skip unsupported / empty-diff files
        ├─ 3. Classify each file (node / python / k8s / default)
        ├─ 4. Build a language-specific prompt
        ├─ 5. Run inference                        (LLM chat-completions endpoint)
        ├─ 6. Parse + validate + dedupe JSON comments
        └─ 7. Post inline comments back to the PR  (GitHub REST API)
```

The request flow in code:

1. `POST /review/pr` is handled by `app/api/review.py`, which calls `review_pr()` in `app/services/review_service.py`.
2. `pr_service.fetch_pr_context()` calls the GitHub API (via `app/clients/github_client.py`) to get the PR's `head_sha` and changed files.
3. For each file, `prompt_service` decides whether the file type is supported, classifies it, and builds a prompt from the templates in `app/core/constants.py`.
4. `inference_client.run_inference()` (`app/clients/inference_client.py`) POSTs the prompt to the configured inference endpoint.
5. The model must return JSON of the form `{"comments": [{"line", "side", "body"}]}`. Comments are validated and deduplicated.
6. If `post_comments` is `true`, each comment is posted inline on the PR.

---

## Features

- Organization-wide PR review without modifying individual repositories.
- Language-aware review for **Node.js / React / TypeScript**, **Python**, and **Kubernetes YAML**, with a generic fallback for other supported types.
- Structured JSON comment generation with per-file comment caps and deduplication.
- Inline GitHub PR comments using the official GitHub REST API.
- Provider-agnostic inference: works with any OpenAI-chat-completions-compatible endpoint via configuration.
- Dry-run mode (`post_comments=false`) for safe testing.
- Container image, Helm chart, and Jenkins pipelines included for production deployment.

---

## Project structure

```
app/
├── api/
│   └── review.py          # POST /review/pr route
├── services/
│   ├── pr_service.py      # Fetch PR context, extract files, normalize comments
│   ├── prompt_service.py  # File-type detection + prompt building
│   └── review_service.py  # Orchestrates the full review flow
├── clients/
│   ├── github_client.py   # GitHub REST API calls
│   └── inference_client.py# LLM inference call
├── core/
│   ├── config.py          # Environment-driven configuration
│   └── constants.py       # Prompt templates, limits, file-type rules
├── models/
│   ├── request_models.py  # PRReviewRequest (+ future org/webhook models)
│   └── response_models.py # ReviewResponse, ReviewComment
├── utils/
│   └── logger.py          # Stdout logger
└── main.py                # FastAPI app + /health

helm_chart/                # Kubernetes Helm chart (Deployment, Service, HPA, Ingress, ServiceMonitor)
Dockerfile                 # Container image (python:3.11-slim)
Jenkinsfile                # Build/push image + Helm deploy pipeline
ai-reviewer.Jenkinsfile    # Webhook-triggered pipeline that calls POST /review/pr
repo-sync.groovy           # Jenkins helper to sync repos on a GitHub App installation
repo-sync.yml              # Declarative repo -> add/remove map for repo-sync
tests/                     # Unit tests
```

---

## API reference

### `GET /health`

Health/readiness probe.

```json
{ "status": "ok" }
```

### `POST /review/pr`

Review a single pull request.

**Request body**

| Field           | Type    | Required | Default | Description                                        |
| --------------- | ------- | -------- | ------- | -------------------------------------------------- |
| `owner`         | string  | yes      | —       | Repository owner / org.                            |
| `repo`          | string  | yes      | —       | Repository name.                                   |
| `pull_number`   | integer | yes      | —       | PR number (must be >= 1).                          |
| `post_comments` | boolean | no       | `true`  | `false` runs a dry run and posts nothing to GitHub. |

```json
{
  "owner": "example-org",
  "repo": "example-service",
  "pull_number": 123,
  "post_comments": true
}
```

**Response body** (`ReviewResponse`)

```json
{
  "owner": "example-org",
  "repo": "example-service",
  "pull_number": 123,
  "head_sha": "abc123...",
  "reviewed_files": ["src/app.py"],
  "skipped_files": ["README.md"],
  "comment_count": 2,
  "comments": [
    { "path": "src/app.py", "line": 42, "side": "RIGHT", "body": "..." }
  ]
}
```

Errors are returned as HTTP `500` with `{ "detail": "<message>" }`.

**Supported file types:** `.js`, `.jsx`, `.ts`, `.tsx`, `.py`, `.yaml`, `.yml`. Other file types and files with no diff are skipped.

---

## Configuration

Configuration is environment-driven (loaded from the process environment and, if present, a local `.env` file via `python-dotenv`). See [`.env.example`](.env.example).

| Variable          | Required | Default                                              | Description                                                                 |
| ----------------- | -------- | ---------------------------------------------------- | --------------------------------------------------------------------------- |
| `GITHUB_TOKEN`    | **Yes**  | —                                                    | Token used as `Bearer` for all GitHub API calls. Missing value fails startup. |
| `INFERENCE_TOKEN` | **Yes**  | —                                                    | Bearer token for the inference endpoint. Missing value fails startup.        |
| `GITHUB_API_URL`  | No       | `https://github.example.com/api/v3`                  | GitHub REST API base URL (public GitHub or GitHub Enterprise).               |
| `INFERENCE_URL`   | No       | `https://inference.example.com/v1/chat/completions`  | Chat-completions-compatible inference endpoint.                             |
| `INFERENCE_MODEL` | No       | `example-code-review-model`                          | Model name sent in the inference payload.                                    |

> The defaults are placeholders (`*.example.com`). Set real values for your environment.

**GitHub token permissions:** the token needs `pull_requests: read/write` (to read PRs and post review comments) and `contents: read`.

Non-env tunables (in `app/core/constants.py`): max comments per file (`MAX_COMMENTS = 5`), patch truncation (`MAX_PATCH_CHARS = 12000`), file-context truncation (`MAX_FILE_CONTEXT_CHARS = 20000`), and the prompt templates.

---

## Quick start (local)

**Prerequisites:** Python 3.11+.

```bash
# 1. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# then edit .env and set GITHUB_TOKEN, INFERENCE_TOKEN, and the URLs/model

# 4. Run the service
uvicorn app.main:app --reload
```

The service is available at `http://127.0.0.1:8000` (interactive docs at `http://127.0.0.1:8000/docs`).

**Smoke test:**

```bash
# Health check
curl http://127.0.0.1:8000/health

# Dry-run review (nothing is posted to GitHub)
curl -X POST http://127.0.0.1:8000/review/pr \
  -H "Content-Type: application/json" \
  -d '{
    "owner": "example-org",
    "repo": "example-service",
    "pull_number": 123,
    "post_comments": false
  }'
```

---

## Run with Docker

```bash
# Build
docker build -t ai-code-reviewer .

# Run (the container listens on port 8000)
docker run -p 8000:8000 \
  -e GITHUB_TOKEN=your_github_token \
  -e INFERENCE_TOKEN=your_inference_token \
  -e GITHUB_API_URL=https://github.example.com/api/v3 \
  -e INFERENCE_URL=https://inference.example.com/v1/chat/completions \
  -e INFERENCE_MODEL=example-code-review-model \
  ai-code-reviewer
```

> Note: the Dockerfile exposes and runs on port `8000`. The Helm chart overrides the runtime command to listen on port `5002` with multiple workers, so container and cluster ports differ by design.

---

## Deploy to Kubernetes (Helm)

The chart lives in [`helm_chart/`](helm_chart) and provisions a Deployment, Service, HPA, optional Ingress, and a Prometheus ServiceMonitor.

Review and override [`helm_chart/values.yaml`](helm_chart/values.yaml) for your environment, in particular:

- `api.containerPath` / `api.containerLabel` — image repository and tag.
- `api.port` (default `5002`), replica counts, and resources.
- `ingress.enabled`, `ingress.host`, and `ingress.tlsSecretName`.

```bash
helm lint ./helm_chart
helm template ai-code-reviewer ./helm_chart
helm upgrade --install ai-code-reviewer ./helm_chart \
  --namespace ai-code-reviewer --create-namespace \
  -f ./helm_chart/values.yaml
```

Provide `GITHUB_TOKEN` and `INFERENCE_TOKEN` to the pod via a Kubernetes Secret / your secret manager rather than plain values.

> The bundled `serviceMonitor.yaml` scrapes `/metrics`, but the app currently only exposes `/health`. Add a metrics endpoint (or disable the ServiceMonitor) before relying on scraping.

---

## CI/CD and webhook triggers (Jenkins)

Two pipelines are included:

- **`Jenkinsfile`** — the build/deploy pipeline. It reads the version from the Helm chart, materializes the app `.env` from a Jenkins file credential, builds and pushes the Docker image, and runs `helm lint/template/upgrade`. On the `main` branch it auto-enables build and deploy. It can also run repo-sync (see below).
- **`ai-reviewer.Jenkinsfile`** — the webhook pipeline. It consumes GitHub `pull_request` and `issue_comment` webhooks via `GenericTrigger` and only proceeds when:
  - a PR is `opened` and still `open` (and not merged), or
  - an `open` PR receives a comment containing `/ai-review`.

  It then extracts `owner`, `repo`, and `pull_number` and calls the service:

  ```
  POST ${REVIEW_API_URL}   # e.g. https://reviewer.example.com/review/pr
  ```

**Repo sync (optional).** `repo-sync.groovy` reconciles which repositories are attached to a GitHub App installation, driven by the declarative [`repo-sync.yml`](repo-sync.yml):

```yaml
example-api: add
example-web: add
```

`add` attaches the repo to the installation; repos not listed as `add` are removed. Run it with `DRY_RUN` first to preview changes.

All pipeline secrets (registry credentials, GitHub tokens, GitHub App credentials, webhook token) are supplied through **Jenkins credential bindings**, not stored in the repo.

---

## Security notes

A review of the repository found **no hardcoded secrets, API keys, tokens, passwords, or private keys**. Secret handling follows good hygiene:

- `app/core/config.py` reads `GITHUB_TOKEN` and `INFERENCE_TOKEN` only from the environment.
- `.env.example` contains placeholders only; no real `.env` is committed, and `.gitignore` excludes `.env`, `.env.*`, `*.pem`, `*.key`, and `secrets/`.
- `helm_chart/values.yaml` contains no credentials; TLS is referenced by secret name only.
- Both Jenkinsfiles and `repo-sync.groovy` pull all secrets via Jenkins credential bindings (`credentials(...)`, `withCredentials([...])`).

Minor hardening opportunities (not leaked secrets):

- `Jenkinsfile` runs `chmod 777 .env` on the generated env file in the build workspace; tighten to `600`.
- `inference_client.run_inference()` does not call `raise_for_status()`, so a non-2xx inference response surfaces as a `KeyError` on `result["choices"]` rather than a clear error. GitHub calls likewise have no retry/backoff.
- Keep `GITHUB_TOKEN` scoped to the minimum permissions listed in [Configuration](#configuration).

---

## Development notes and limitations

- Use `post_comments=false` while testing to avoid posting to real PRs.
- Logs go to stdout at `INFO` level.
- Invalid model JSON is logged and that file is skipped rather than failing the whole run.
- `OrgReviewRequest`, `WebhookReviewRequest`, and `OrgReviewResponse` models exist but are not yet wired to routes (placeholders for future org-wide / direct-webhook features).
- Dependencies in `requirements.txt` are unpinned; pin versions for reproducible builds.

### Running tests

```bash
python -m unittest discover -s tests
```

---

## License

No license file is currently included. Add a license appropriate for your organization before distributing this project.
