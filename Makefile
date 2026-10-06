.PHONY: setup dev test lint format build docker-up docker-down terraform-plan helm-lint

setup:
	uv sync
	pnpm install

dev:
	@echo "PENDING: dev orchestration lands with the first implemented service."

test:
	@echo "PENDING: test suites land with the first implemented service."
	@exit 1

lint:
	python -m compileall apps packages -q && echo "python syntax OK"
	pnpm -r --if-present lint

format:
	@echo "PENDING: formatters (ruff/tsc) land with the first implemented service."
	@exit 1

build:
	pnpm -r --if-present build

docker-up:
	docker compose up -d

docker-down:
	docker compose down

terraform-plan:
	@echo "PENDING: terraform modules are scaffolding with no resources."

helm-lint:
	@if command -v helm >/dev/null; then helm lint infrastructure/helm/Sluice; else echo "PENDING: helm not installed."; exit 1; fi
