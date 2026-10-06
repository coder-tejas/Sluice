# Local deployment

Run infrastructure dependencies only (PostgreSQL, Redis, MinIO,
Prometheus, Grafana) for local development:

```bash
make docker-up
```

Production parity comes from Terraform + Helm, not Compose.
