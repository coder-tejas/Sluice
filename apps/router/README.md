# sluice-router

OpenAI-compatible gateway for Sluice. Proxies `/v1/models` and
`/v1/chat/completions` (including SSE streaming) to a `llama-server` worker.

Configuration:

| Variable | Default | Purpose |
|---|---|---|
| `SLUICE_WORKER_URL` | `http://llama-server:8080` | llama.cpp server base URL |
| `SLUICE_MODEL_ID` | `qwen2.5-0.5b-instruct` | public model id |
| `SLUICE_UPSTREAM_TIMEOUT` | `300` | upstream read timeout (seconds) |

Run locally (from the repo root, so the workspace venv is synced fully):

```bash
uv sync --all-packages --all-extras
cd apps/router
uv run uvicorn sluice_router.main:app --port 8001
uv run pytest -q
```
