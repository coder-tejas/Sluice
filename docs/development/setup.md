# Development setup

Prerequisites: Python 3.12+, `uv`, Node.js 20+, `pnpm`, Docker,
Docker Compose. Optional: `kubectl`, `helm`, `terraform`.

```bash
make setup   # install Python + JS workspaces
docker compose up -d postgres api   # API on :8000, PostgreSQL on :5432
cd apps/api && alembic upgrade head # schema owned by migrations
```

API health: `curl localhost:8000/v1/health/ready` → `{"status":"ready"}`.

Tests (from `apps/api`, with the dev DB up):

```bash
uv sync --extra test   # plain `uv sync` prunes the pytest extra
SLUICE_DATABASE_URL=postgresql://Sluice:Sluice@localhost:5432/Sluice \
  uv run pytest tests/ -q
```

Unit tests mock the repository (no DB); container-backed integration
tests spin their own PostgreSQL via Testcontainers.

Conventions (lint, format, commits) live in `docs/development/conventions.md`.
