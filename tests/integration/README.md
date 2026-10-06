# Integration tests

Will cover service-to-service contracts against local dependencies
(PostgreSQL, Redis, MinIO via `docker compose`):

- API ↔ database (registry CRUD)
- API ↔ queue ↔ worker (async inference path)
- Router ↔ model versions (traffic splitting)

Not implemented yet.
