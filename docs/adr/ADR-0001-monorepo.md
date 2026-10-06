# ADR-0001: Why Sluice uses a monorepo

Status: accepted.

## Context

Sluice spans Python services, a Next.js dashboard, shared TS/Python
packages, Terraform modules, Helm charts, and K8s manifests that evolve
together (e.g. an API change ripples into SDKs, dashboard, and charts).

## Decision

Keep everything in one repository with `pnpm` workspaces (JS/TS) and a
`uv` workspace (Python) under one root `Makefile`.

## Consequences

- Atomic cross-service changes; single CI entry point.
- Must keep services independently deployable (separate images/charts).
- Must keep shared packages small to avoid coupling everything together.
