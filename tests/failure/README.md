# Failure tests

Will verify reliability mechanisms via deliberate fault injection:

- Kill inference pods (rescheduling / fallback)
- Inject latency and HTTP 500s (timeouts / retries / circuit breakers)
- Fill queues, break Redis connections (backpressure / degradation)
- Simulate bad deployments (detection → rollback)

Not implemented yet.
