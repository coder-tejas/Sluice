# Sluice — Architecture & Implementation Decisions

Living record of decisions made while building Sluice (formerly scaffolded as
ModelForge). Status values: **Implemented** (in the repo), **Accepted** (agreed,
not built yet), **Deferred** (explicitly out of current scope), **Open**
(unresolved, needs a call before dependent work).

Last updated: 2026-11-09.

---

## 1. Product and scope

- **D1. Sluice is an OpenAI-compatible model hosting platform.** Core value is
  a drop-in `base_url` swap for the official OpenAI clients, backed by real
  local inference. Status: Accepted.
- **D2. Build vertical slices, data plane first.** The demo-critical path is
  `client → router → llama-server → response`. Registry UI/API, auth, billing,
  and dashboards come after the data plane works. Status: Accepted.
- **D3. Scope is deliberately staged P0 → P1 → P2.**
  - P0: chat completions (stream + non-stream), `GET /v1/models`, OpenAI
    errors, registry CRUD, deployments (start/stop/delete/status), routing,
    llama.cpp worker, API keys, token accounting, core Prometheus metrics.
  - P1: embeddings, legacy completions, sampling params, tool calling, JSON
    mode, load balancing, queues/backpressure, MinIO artifacts, usage API,
    Grafana dashboards, benchmark, dashboard.
  - P2: `n`, logprobs, cancellation, vision, canary, caching, OTel, CLI, k8s,
    Terraform, eval harness.
  Status: Accepted; P0 is the resume-project target.
- **D4. Honest scope rule.** No feature is claimed as done unless it is
  implemented and verified. Docs mark unimplemented areas as such instead of
  aspirational language. Status: Implemented as a working rule.

## 2. Repository and service layout

- **D5. Monorepo with independent services.** `apps/api` is the control plane;
  `apps/router` is a separate data-plane service; `apps/inference-worker` stays
  a scaffold for now; shared Python packages go in `packages/python/*`.
  Status: `apps/api` implemented, `apps/router` accepted, worker scaffold-only.
- **D6. Control plane and data plane are separate processes.** The API owns
  PostgreSQL and management operations; the router owns model traffic and has
  no database dependency. This keeps the hot path free of DB coupling and lets
  them scale/fail independently. Status: Accepted.
- **D7. Ports:** API `:8000`, router `:8001`, llama-server `:8080` (raw worker,
  used for debugging), PostgreSQL `:5432`. Status: Implemented/Agreed.
- **D8. `apps/inference-worker` is intentionally not used in P0.** A wrapper
  earns its place only when ONNX, artifact download, registry-driven config, or
  heartbeats arrive. `llama-server` itself is the P0 worker. Status: Deferred.
- **D9. One workspace, one lockfile.** `uv` workspace members are
  `apps/api`, `apps/router`, and `packages/python/*`; each app has its own
  `pyproject.toml` (hatchling build backend). The API package is `app`; the
  router package is `sluice_router` to avoid a duplicate top-level `app`
  package in the shared workspace venv. Status: Implemented.

## 3. Language and stack

- **D10. Python 3.12+.** Code must run on the repo's `requires-python`.
  Status: Implemented.
- **D11. FastAPI + Pydantic v2 + uvicorn** for both HTTP services. Status:
  Implemented (API), accepted (router).
- **D12. SQLAlchemy 2.x async with `asyncpg`** for the application path, and a
  separate synchronous engine using `psycopg` for Alembic. Async in the app,
  sync where migrations need it. Status: Implemented.
- **D13. PostgreSQL 16** is the metadata store. Model weights do not live in
  PostgreSQL; they live in object storage and are referenced by URI.
  Status: Implemented for schema.
- **D14. `structlog` for structured logging**, JSON-style key/event pairs, with
  request ID bound into context. Status: Implemented.
- **D15. No new dependency without justification.** Standard library or an
  already-installed dependency is preferred. Status: Working rule.
- **D16. `httpx` is the upstream HTTP client** for the router because it
  supports both regular and streaming requests with one client.
  Status: Accepted.

## 4. Configuration

- **D17. All Python service config uses `pydantic-settings` with env prefix
  `SLUICE_`.** Missing required values fail at startup; unknown env vars are
  ignored (`extra="ignore"`). Status: Implemented.
- **D18. Settings are cached per process** (`lru_cache`) and read once at app
  creation. Status: Implemented.
- **D19. Router config is environment-only** — `SLUICE_WORKER_URL`,
  `SLUICE_MODEL_ID`, `SLUICE_UPSTREAM_TIMEOUT`. No DB, no config file.
  Status: Accepted.
- **D20. Upstream timeout is long (300 s)** because CPU generation is slow;
  connect timeout stays short (10 s). Status: Accepted.
- **D21. `.env` is supported locally but real config comes from the
  environment** (Compose or deployment platform). Status: Implemented.

## 5. Database schema and modeling conventions

- **D22. Integer primary keys, not UUIDs.** The repository had no UUID
  convention; matching the existing `system_metadata` table was preferred over
  introducing one. Trade-off: distributed ID generation and public-ID opacity
  are lost. Status: Implemented. **Open:** if external IDs are needed, do it
  before registry data exists or add a separate public identifier column.
- **D23. Timestamps are `DateTime(timezone=True)` with
  `server_default=func.now()`.** The database is authoritative for creation
  time. Status: Implemented.
- **D24. String lengths are explicit** (`String(128)`, `String(32)`,
  `String(64)`); long free text uses `Text`. Status: Implemented.
- **D25. Structured config is `JSONB` with a server default of `'{}'`** and a
  Python-level `dict` default. Status: Implemented (`model_versions.runtime_config`).
- **D26. Foreign keys use `ON DELETE CASCADE` where the child cannot exist
  without the parent**, paired with ORM `cascade="all, delete-orphan"`.
  Status: Implemented (`model_versions.model_id`).
- **D27. Constraint naming is explicit** for composite constraints
  (`uq_model_versions_model_id_version`). Status: Implemented.
- **D28. Registry is two tables.** `models` is the stable logical identity;
  `model_versions` holds immutable artifacts. A new artifact means a new
  version, never an update to an existing version. Status: Implemented.
- **D29. `models.slug` is unique and is the public identifier**; `name` is
  display text and may change. Status: Implemented.
- **D30. `(model_id, version)` is unique**, so version strings are scoped per
  model. Status: Implemented.
- **D31. `model_type` and `runtime` are plain strings, not DB enums or CHECK
  constraints.** ADR-0002 lists `traditional_ml`/`llm` and `sklearn`/`vllm`,
  but validation is deferred to the service/API layer to avoid a migration per
  new runtime. Status: Implemented; validation still **Open**.
- **D32. `artifact_uri` is NOT NULL.** Registering a version requires a
  location. Consequence: upload-before-register is assumed. Status:
  Implemented; revisit if "registered but not uploaded" becomes a real state.
- **D33. Deployments are a separate future table**, not part of the registry
  slice. ADR-0002 names it, but it was explicitly out of M3 scope.
  Status: Deferred.
- **D34. MySQL/SQLite are not supported.** JSONB, `psycopg`, and the test setup
  assume PostgreSQL. Status: Accepted.
- **D35. Schema evolution is additive.** Applied migrations are never edited or
  rewritten; corrections are new migrations. Status: Implemented as policy.

## 6. Migrations

- **D36. Alembic owns the schema; `create_all` is not run at application
  startup.** Status: Implemented.
- **D37. `alembic/env.py` imports every model module explicitly** so
  autogenerate sees complete metadata. Status: Implemented.
- **D38. The Alembic URL always comes from `SLUICE_DATABASE_URL`**, not from
  `alembic.ini`. Status: Implemented.
- **D39. Migrations are generated with autogenerate, then reviewed by hand**
  before applying. Status: Implemented.
- **D40. `alembic check` is part of verification**: a clean result proves the
  models and migrations agree. Status: Implemented.
- **D41. Migrations are applied only to local/dev databases in this project.**
  No production database is touched. Status: Implemented as policy.
- **D42. Migration cycle (upgrade → downgrade → upgrade) is tested on a blank
  Testcontainers database.** Status: Implemented.

## 7. HTTP API conventions

- **D43. Versioned routes live under `/v1`.** Health/readiness also live under
  `/v1` for consistency (`/v1/health`, `/v1/health/ready`, `/v1/db/ping`).
  Status: Implemented.
- **D44. Control-plane errors use one envelope:**
  `{"error": {"code", "message", "request_id"}}`, including validation errors;
  the request ID is echoed in the response header `X-Request-ID`.
  Status: Implemented.
- **D45. Data-plane errors use the OpenAI envelope:**
  `{"error": {"message", "type", "param", "code"}}`. The two envelopes are
  deliberately different because OpenAI SDKs parse the latter.
  Status: Accepted for router.
- **D46. OpenAI-compatible status codes:** 400 invalid request, 401
  unauthenticated, 404 `model_not_found`, 429 rate limit, 500 server error,
  502 upstream unavailable. Status: Accepted.
- **D47. Request IDs are generated per request if absent, logged, bound to
  structured logs, and returned in `X-Request-ID`.** Status: Implemented.
- **D48. Metadata CRUD is a small real feature used to prove the
  schema/service/repository/API layers**, not a permanent product surface.
  Status: Implemented.
- **D49. Layering is schema → repository → service → route.** Only
  `system_metadata` has the full stack today. Status: Implemented for metadata;
  registry stack not built.

## 8. Data plane (M4a)

- **D50. M4a slice is exactly:** `GET /v1/models`, non-streaming
  `POST /v1/chat/completions`, SSE streaming for the same endpoint, and
  OpenAI-shaped errors. Status: Accepted, not implemented.
- **D51. No auth, registry lookup, deployments, metrics, or worker wrapper in
  M4a.** One static model selected by `SLUICE_MODEL_ID`. Status: Accepted.
- **D52. The router forwards the request body verbatim.** This preserves
  `temperature`, `top_p`, `max_tokens`, `stop`, `seed`, penalties, and tool
  definitions without per-parameter code. Status: Accepted.
- **D53. `GET /v1/models` returns the OpenAI list shape** with one entry:
  `id = SLUICE_MODEL_ID`, `object = "model"`, `owned_by = "sluice"`.
  Status: Accepted.
- **D54. The worker is launched with `--alias $SLUICE_MODEL_ID`** so its
  responses carry the public model id. This avoids rewriting SSE chunks on the
  router. Status: Accepted.
- **D55. Streaming is a raw byte relay**, not a re-framing of SSE. The router
  yields upstream chunks unchanged and lets llama.cpp terminate with
  `data: [DONE]`. Status: Accepted.
- **D56. Streaming responses set `Cache-Control: no-cache` and
  `X-Accel-Buffering: no`.** Status: Accepted.
- **D57. The streaming response owns the upstream connection.** Open the
  stream with `client.send(..., stream=True)`, check the status, then hand the
  still-open response to a generator that closes it in `finally`. You cannot
  return a `StreamingResponse` from inside `async with client.stream(...)`.
  Status: Accepted.
- **D58. Upstream error bodies are read before hand-off and passed through**
  if they are already OpenAI-shaped; otherwise they are wrapped in the OpenAI
  envelope. Status: Accepted.
- **D59. Transport errors become 502 `upstream_unavailable`.** Status: Accepted.
- **D60. The router has no database and no dependency on `apps/api`.**
  Status: Accepted.
- **D61. The router is injectable for tests:** `create_app(transport=...)`
  accepts an `httpx.AsyncBaseTransport`, so contract tests run without a
  model server. Status: Accepted.
- **D62. Router tests use the official `openai` client (test-only dependency)
  against a stub FastAPI upstream via `httpx.ASGITransport`.** Use
  `AsyncOpenAI` because `ASGITransport` is async-only. Status: Accepted.
- **D63. No pytest-asyncio dependency is introduced;** router tests wrap async
  tests in `asyncio.run`, matching the existing API test style. Status: Accepted.

## 9. Inference runtime and local stack

- **D64. Real llama.cpp `llama-server`, no fake inference.** Status: Accepted.
- **D65. Development model is Qwen2.5-0.5B-Instruct GGUF, Q4_K_M**, chosen for
  CPU speed and size (a few hundred MB). Status: Accepted; throughput not yet
  verified.
- **D66. The model is baked into a small `docker/llama` image at build time**
  so `docker compose up` has no runtime download step. Trade-off: larger image,
  needs network during build. Status: Accepted.
- **D67. llama-server runs with `--ctx-size 4096`, `--threads 4`,
  `--alias <model id>`.** Status: Accepted.
- **D68. llama-server's `/health` is the readiness signal** (503 while loading,
  200 when ready); the router waits on `service_healthy`. Status: Accepted.
- **D69. Docker Compose is the local orchestration** (PostgreSQL, API, Redis,
  MinIO, Prometheus, Grafana; plus llama-server and router in M4a). Compose is
  explicitly not production architecture; its services map to AWS managed
  services in production. Status: Implemented for existing services.
- **D70. CPU-only dev box.** GPU/CUDA support is optional and later. Status:
  Accepted.
- **D71. Demo guidance: always pass `max_tokens`** so CPU generation stays
  bounded; streaming is the preferred demo. Status: Accepted.

## 10. Auth, metering, observability

- **D72. API keys are stored hashed, never plaintext**, shown once at creation.
  Status: Deferred (P0 next).
- **D73. Bearer auth will be enforced in the router**, not the control plane
  only, because that is the public data path. Status: Deferred.
- **D74. Token accounting is per request: prompt, completion, total**; usage
  rows are attributed to key, model, project, and time bucket. Status: Deferred.
- **D75. Prometheus `/metrics` on router and workers; Grafana dashboards are
  provisioned as code.** Status: Deferred; compose placeholders exist.
- **D76. Metrics to expose first:** request count, error count, latency
  histograms, time to first token, tokens/sec, in-flight requests, queue depth.
  Status: Deferred.
- **D77. OpenTelemetry and request-log capture are P1/P2**, with prompt
  capture opt-in and redacted. Status: Deferred.
- **D78. Redis is for rate limits, queues, and exact-match cache** — none
  implemented yet. Status: Deferred.

## 11. Testing strategy

- **D79. Unit tests mock repositories (no DB); integration tests use real
  PostgreSQL.** Status: Implemented.
- **D80. Integration tests use Testcontainers PostgreSQL** for schema,
  constraint, repository, service, and migration-cycle checks.
  Status: Implemented.
- **D81. A dedicated dev-PostgreSQL test path exists** for faster local runs;
  the same tests are run against `SLUICE_DATABASE_URL` when containers are
  undesired. Status: Implemented.
- **D82. Contract tests target the OpenAI wire contract, not model quality.**
  A stub upstream keeps them fast and deterministic. Status: Accepted.
- **D83. A real-model compose smoke test is optional and marked slow.**
  Status: Accepted.
- **D84. Test dependencies live in a `test` extra; `dev` includes both test
  and ruff.** Plain `uv sync` prunes extras, so test runs use
  `uv sync --extra test`. Status: Implemented.
- **D85. `ruff` is the linter/formatter** (line length 88, target Python 3.12).
  Status: Implemented.
- **D86. CI should run lint and pytest (unit + Testcontainers) once the
  pipeline is wired.** Currently CI only compiles Python. Status: **Open /
  pending cleanup.**

## 12. Naming, docs, and repo hygiene

- **D87. Public product name in code/packages is Sluice** (`sluice-api`,
  `sluice-router`), while some scaffold paths still say `modelforge`
  (legacy). Renaming those is cosmetic and not blocking. Status: Open.
- **D88. Architecture decisions that are broad enough get an ADR** in
  `docs/adr/`; implementation-level calls are recorded here.
  Status: Implemented (ADR-0001 monorepo, ADR-0002 registry).
- **D89. `decisions.md` is the single running log**; it is updated when a
  decision is made or reversed, not rewritten to look consistent.
  Status: Implemented.
- **D90. Root `README.md`, `apps/api/README.md`, and the root `Makefile` are
  stale** ("scaffold only", `make test` PENDING, `helm-lint` points at a
  nonexistent chart). Fixing them is a known cleanup item, not a design
  question. Status: Open.

## 13. Deferred and open decisions

| # | Question | Current stance | Needed before |
|---|---|---|---|
| O1 | UUID vs integer public IDs | Integer PKs; no public UUID | Any external API that exposes IDs |
| O2 | DB CHECK constraints vs service validation for `model_type` / `runtime` | Service-level validation planned | Registry CRUD |
| O3 | Can a version be registered before its artifact exists? | No — `artifact_uri` is required | Upload workflows |
| O4 | Does deleting a model with deployments cascade or get blocked? | Blocked is the intent; no deployment table yet | Deployments |
| O5 | One model per router vs registry-driven routing | Static env config | Registry API + router integration |
| O6 | `llama.cpp` image tag pinning | `:server` moves; pin during spike | Committing the llama image |
| O7 | CPU throughput / demo model final choice | Qwen2.5-0.5B Q4_K_M proposed | M4a spike |
| O8 | Retry/backpressure policy | Not in M4a | P1 router work |
| O9 | Streaming cancellation semantics | Generator `finally` closes upstream; no explicit cancel endpoint | P2 cancellation work |
| O10 | Cost rates per model | Not modeled | Usage/billing |

## 14. Commit trail (context for the log)

- `49d8657` monorepo scaffold.
- `8aa5d1b`–`7963017` API foundation: config, sync/async DB, sessions,
  `system_metadata` model.
- `d5c51de` metadata CRUD, Alembic, model registry schema, 42 tests passing.
- M4a (router + llama-server + contract tests) is designed and accepted but
  **not implemented** as of this log.
