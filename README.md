# Sluice

> **Early Development / Architecture Scaffold** — structure and templates only;
> no services are implemented yet.

Sluice is a production-oriented platform for registering, deploying,
serving, monitoring, evaluating, and operating ML and LLM models at scale,
built to demonstrate ML/LLM inference infrastructure, backend engineering,
distributed systems, Kubernetes, AWS, DevOps, MLOps, observability, and
reliability engineering.

## Architecture overview

A control plane (API, registry, router, jobs, deployment controller) over a
data plane of model servers (PyTorch, LLM, embeddings), backed by PostgreSQL,
Redis, S3, and SQS on AWS EKS, with Prometheus/Grafana/OpenTelemetry
observability. Details: `docs/architecture/`.

## Technology stack

Python (FastAPI), TypeScript (Next.js), PostgreSQL/RDS, Redis/ElastiCache,
S3, SQS, Docker, Kubernetes, Helm, Terraform, Prometheus, Grafana,
OpenTelemetry, GitHub Actions.

## Repository structure

Monorepo (`pnpm` + `uv` workspaces; see `docs/adr/ADR-0001-monorepo.md`):

```text
apps/            # deployable services (api, router, workers, controller, dashboard)
packages/        # shared Python + TypeScript libraries
models/          # model dirs with template configs (no weights)
infrastructure/  # Terraform modules/envs, Kubernetes manifests, Helm chart
observability/   # Prometheus, Grafana, OpenTelemetry, alerts
tests/           # integration, e2e, load, failure (planned)
docs/            # architecture, api, deployment, operations, development, adr
scripts/         # dev / deployment / testing helpers
```

## Current status

Scaffolding only. Nothing is implemented: no APIs, no inference logic, no
routing, no controllers, no infrastructure provisioning.

## Development roadmap

1. Inference core (API, registry, one model, prediction API)
2. Model infrastructure (versions, artifacts, router, async jobs)
3. Kubernetes (manifests, Helm, autoscaling)
4. AWS (Terraform modules, EKS, managed services)
5. Production operations (metrics, tracing, cost tracking)
6. Deployment intelligence (canary, rollback, quality gates, evaluation)
7. LLM infrastructure (gateway, streaming, token accounting)

## Local development prerequisites

```text
Python 3.12+, uv, Node.js 20+, pnpm, Docker, Docker Compose
Optional: kubectl, helm, terraform
```

```bash
make setup
make docker-up
```

## License

MIT — see `LICENSE`.
