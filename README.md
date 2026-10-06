# Sluice

### Production ML/LLM Inference Platform

ModelForge is a production-oriented platform for **registering, deploying, serving, monitoring, evaluating, and operating ML and LLM models at scale**.

It provides a unified inference layer over traditional ML models, deep-learning models, embedding models, and LLMs, with Kubernetes-based deployment, AWS infrastructure, asynchronous inference, model versioning, canary releases, observability, autoscaling, and automated rollback.

The project is designed around a simple principle:

> **Model inference should be treated as production infrastructure, not as a Python script behind an HTTP endpoint.**

---

## Architecture

```text
                              ┌───────────────────┐
                              │      Clients      │
                              │ Web / SDK / CLI   │
                              └─────────┬─────────┘
                                        │
                                        ▼
                              ┌───────────────────┐
                              │    API Gateway    │
                              │ Auth / RBAC /     │
                              │ Rate Limiting     │
                              └─────────┬─────────┘
                                        │
                         ┌──────────────┼──────────────┐
                         │              │              │
                         ▼              ▼              ▼
                  ┌────────────┐ ┌────────────┐ ┌────────────┐
                  │   Model    │ │   Model    │ │    Jobs    │
                  │  Registry  │ │   Router   │ │    API     │
                  └─────┬──────┘ └─────┬──────┘ └─────┬──────┘
                        │              │              │
                        ▼              ▼              ▼
                       S3       Inference Services    SQS
                                       │              │
                          ┌────────────┼────────────┐  │
                          │            │            │  │
                          ▼            ▼            ▼  ▼
                       PyTorch       LLM        Embedding
                       Server       Server        Server
                          │            │            │
                          └────────────┼────────────┘
                                       │
                       ┌───────────────┼────────────────┐
                       │               │                │
                       ▼               ▼                ▼
                    Redis         PostgreSQL          S3
                       │               │
                       └───────┬───────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   Observability     │
                    │ OpenTelemetry       │
                    │ Prometheus          │
                    │ Grafana             │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │ Incident / Quality  │
                    │ Analysis Engine     │
                    └─────────────────────┘
```

---

# Features

## Model Registry

- Model registration
- Model versioning
- Model metadata
- Model ownership
- Model tags
- Model artifact storage
- S3-backed artifact management
- Artifact checksums
- Model lifecycle management
- Model deprecation and archival

Example:

```text
sentiment-classifier
├── v1.0.0
├── v1.1.0
└── v2.0.0
```

---

## Multi-Framework Model Support

ModelForge is designed to provide a common deployment and inference layer for different model types.

### Traditional ML

- Scikit-learn
- XGBoost
- LightGBM

### Deep Learning

- PyTorch
- Hugging Face Transformers

### LLM

- Hugging Face LLMs
- vLLM
- Quantized models
- AWS Bedrock adapters

### Embeddings

- Sentence Transformers
- Embedding APIs

---

# Inference

## Synchronous Inference

```http
POST /v1/models/{model}/predict
```

Example:

```json
{
  "input": "This product is excellent."
}
```

Response:

```json
{
  "prediction": "positive",
  "confidence": 0.982,
  "model": "sentiment-classifier",
  "version": "2.1.0",
  "latency_ms": 18
}
```

---

## Asynchronous Inference

Large or expensive workloads can be submitted as jobs.

```http
POST /v1/jobs
```

```json
{
  "model": "llama-8b",
  "version": "2.1.0",
  "input": "Generate a detailed report..."
}
```

Response:

```json
{
  "job_id": "job_81af2",
  "status": "QUEUED"
}
```

Job lifecycle:

```text
QUEUED
   ↓
RUNNING
   ↓
COMPLETED

or

QUEUED → RUNNING → FAILED
```

SQS is used as the asynchronous work queue.

---

# Model Routing

The inference layer separates the public API from individual model deployments.

```text
                    Model Router
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
            v1.0       v2.0       v3.0
             70%        20%        10%
```

Supported routing strategies:

- Weighted routing
- Load-aware routing
- Latency-aware routing
- Model-version routing
- Fallback routing
- Tenant-specific routing

---

# Canary Deployments

New model versions can be progressively exposed to production traffic.

Example:

```text
v1 → 90%
v2 → 10%
```

After successful evaluation:

```text
v1 → 50%
v2 → 50%
```

Eventually:

```text
v2 → 100%
```

If the deployment violates configured SLOs, traffic can automatically return to the previous version.

---

# Automatic Rollback

Deployments are monitored against configurable thresholds.

Example:

```text
Error rate       < 1%
P95 latency      < 500ms
Model quality    > 92%
```

If:

```text
P95 latency = 840ms
Error rate  = 7.8%
```

the deployment controller can trigger:

```text
Detection
    ↓
Traffic reduction
    ↓
Rollback
    ↓
Previous model restored
```

---

# LLM Gateway

ModelForge provides a unified interface for LLM inference.

```text
                 LLM Gateway
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
      Local LLM   Bedrock     External API
```

Capabilities:

- Provider abstraction
- Model routing
- Provider fallback
- Streaming responses
- Token accounting
- Context-window validation
- Structured output
- JSON output
- Tool calling
- Prompt versioning
- Response caching
- Model fallback

---

# Reliability

ModelForge treats inference as a distributed system.

Implemented reliability mechanisms include:

- Request timeouts
- Retries
- Exponential backoff
- Circuit breakers
- Idempotency
- Dead-letter queues
- Backpressure
- Graceful shutdown
- Health checks
- Liveness probes
- Readiness probes
- Startup probes

Example:

```text
Request
   ↓
Model A
   ↓
timeout
   ↓
Retry
   ↓
Model A
   ↓
failure
   ↓
Fallback Model B
```

---

# Autoscaling

Inference workloads can scale based on workload characteristics.

Supported scaling signals:

- CPU utilization
- Memory utilization
- Request rate
- Queue depth
- GPU utilization
- Inference latency

Example:

```text
Queue depth > 100
        ↓
3 replicas
        ↓
8 replicas
```

GPU-backed models can use dedicated Kubernetes node pools.

---

# Model Warmup

Model startup is handled separately from application startup.

```text
Pod starts
   ↓
Download model
   ↓
Load weights
   ↓
Initialize runtime
   ↓
Warmup inference
   ↓
Readiness = TRUE
   ↓
Receive production traffic
```

This prevents requests from being sent to a model that has not finished loading.

---

# Batch Inference

Large workloads can be submitted as batch jobs.

```text
10,000 inputs
      ↓
     S3
      ↓
     SQS
      ↓
Worker Pool
      ↓
Parallel Inference
      ↓
Results → S3
```

Features:

- Parallel processing
- Job progress
- Partial failure handling
- Retries
- Result storage
- Result expiration

---

# Caching

Redis is used for low-latency operations.

Potential cache layers:

```text
Request
   ↓
Redis
   ↓ cache miss
Inference
   ↓
Redis
```

Cacheable data includes:

- Model metadata
- Predictions
- Embeddings
- LLM responses
- Routing configuration

Cache keys incorporate model version and relevant inference parameters to prevent stale predictions.

---

# Rate Limiting

Rate limits can be applied at multiple levels:

```text
Global
  ↓
Organization
  ↓
User
  ↓
API Key
  ↓
Model
```

Supported controls include:

- Requests/minute
- Tokens/minute
- Concurrent requests
- Per-model limits

Redis provides distributed rate-limit state.

---

# Usage & Cost Tracking

Every inference request can generate a usage record.

```text
request_id
tenant_id
user_id
model
version
input_tokens
output_tokens
latency
status
timestamp
```

The platform can calculate:

```text
Cost / request
Cost / model
Cost / tenant
Cost / day
Cost / month
GPU hours
```

For LLM workloads:

```text
Input tokens × input price
+
Output tokens × output price
```

---

# Model Evaluation

Models are evaluated before production promotion.

Traditional ML metrics:

- Accuracy
- Precision
- Recall
- F1
- ROC-AUC
- Confusion matrix

LLM evaluation:

- Relevance
- Faithfulness
- Hallucination rate
- Toxicity
- Structured-output correctness
- Latency
- Token consumption

---

# Quality Gates

A model can be blocked from deployment if it does not satisfy configured requirements.

Example:

```text
Accuracy       >= 92%
P95 latency    <= 500ms
Error rate     <= 1%
```

Failed evaluation:

```text
Model v2
    ↓
Evaluation
    ↓
Accuracy = 88%
    ↓
DEPLOYMENT BLOCKED
```

---

# Experiment Tracking

MLflow is used for experiment tracking and model lifecycle management.

Tracked information includes:

```text
Experiment
Run
Dataset
Hyperparameters
Metrics
Artifacts
Model
Git commit
```

This enables:

- Experiment comparison
- Reproducibility
- Artifact tracking
- Model registration
- Best-model selection

---

# Dataset & Model Lineage

ModelForge tracks the relationship between:

```text
Dataset
   ↓
Training Run
   ↓
Model
   ↓
Model Version
   ↓
Deployment
   ↓
Inference
```

This makes it possible to answer:

> Which dataset and code produced the model serving this request?

---

# Observability

## Metrics

The platform exposes metrics including:

```text
Requests/sec
P50 latency
P95 latency
P99 latency
Error rate
Queue depth
CPU utilization
Memory utilization
GPU utilization
Tokens/sec
Cache hit rate
```

---

## Distributed Tracing

OpenTelemetry traces the complete request lifecycle:

```text
API
 ↓
Authentication
 ↓
Model Router
 ↓
Redis
 ↓
SQS
 ↓
Inference Worker
 ↓
Model
```

Each request receives a trace ID.

---

## Structured Logging

Example:

```json
{
  "request_id": "req_81231",
  "tenant_id": "tenant_42",
  "model": "sentiment",
  "version": "2.1.0",
  "latency_ms": 183,
  "status": 200
}
```

---

# Monitoring Dashboard

The frontend dashboard provides:

### Overview

- Requests/sec
- Active models
- Error rate
- P95 latency
- GPU utilization
- Queue depth
- Estimated cost

### Model View

- Model versions
- Deployment status
- Traffic distribution
- Latency
- Errors
- Resource utilization
- Cost

### Deployment View

```text
v1 → 80%
v2 → 20%
```

with:

- Latency comparison
- Error comparison
- Quality comparison
- Promote
- Rollback

---

# Incident Management

ModelForge can detect production incidents based on configured SLOs.

```text
Metric anomaly
      ↓
Alert
      ↓
Incident
      ↓
Diagnosis
      ↓
Remediation
      ↓
Resolution
```

Incident records contain:

- Affected model
- Deployment
- Timeline
- Metrics
- Logs
- Trace IDs
- Resolution

---

# AI Operations

The platform can use AI to analyze operational signals.

Example:

```text
Error rate ↑
Latency ↑
Database connections ↑
Recent deployment detected
        ↓
       LLM
        ↓
Likely cause:
database connection exhaustion
introduced after deployment v2.
```

Potential capabilities:

- Anomaly detection
- Root-cause analysis
- Incident summarization
- Deployment risk scoring
- Remediation recommendations

---

# Security

## Application

- JWT/OAuth
- API keys
- RBAC
- Multi-tenancy
- Request validation
- Rate limiting
- Payload limits

## AWS

- IAM
- IAM Roles for Service Accounts
- KMS
- Secrets Manager
- Private subnets
- Security groups
- VPC endpoints

## Containers

- Non-root containers
- Minimal base images
- Image vulnerability scanning
- Dependency scanning
- Resource limits

---

# CI/CD

```text
Git Push
   ↓
Lint
   ↓
Unit Tests
   ↓
Integration Tests
   ↓
Build
   ↓
Security Scan
   ↓
Docker Image
   ↓
ECR
   ↓
Kubernetes Deployment
   ↓
Smoke Tests
   ↓
Canary
   ↓
Promote / Rollback
```

Tools:

- GitHub Actions
- Docker
- Trivy
- Helm
- Terraform
- Amazon ECR

---

# Infrastructure

Infrastructure is provisioned using Terraform.

AWS resources include:

```text
VPC
├── Public Subnets
├── Private Subnets
├── NAT
└── Security Groups

EKS
├── CPU Node Pool
└── GPU Node Pool

RDS PostgreSQL

ElastiCache Redis

S3

SQS

ECR

CloudWatch

Load Balancer
```

The goal is to make the entire environment reproducible from code.

---

# API

Example endpoints:

```text
Authentication
POST   /auth/login
POST   /auth/refresh

Models
GET    /v1/models
POST   /v1/models
GET    /v1/models/:name
DELETE /v1/models/:name

Versions
POST   /v1/models/:name/versions
GET    /v1/models/:name/versions

Deployments
POST   /v1/deployments
GET    /v1/deployments
POST   /v1/deployments/:id/promote
POST   /v1/deployments/:id/rollback

Inference
POST   /v1/models/:name/predict
POST   /v1/jobs
GET    /v1/jobs/:id

Metrics
GET    /v1/models/:name/metrics

Usage
GET    /v1/usage

Health
GET    /health
GET    /ready
```

---

# CLI

Example:

```bash
# Authentication
modelforge login

# Models
modelforge models list
modelforge models register model.yaml
modelforge models inspect sentiment:v2

# Deploy
modelforge deploy sentiment:v2

# Deploy with canary
modelforge deploy sentiment:v2 --traffic 10%

# Monitor
modelforge deployments list
modelforge metrics sentiment:v2
modelforge logs sentiment:v2

# Rollback
modelforge rollback sentiment:v2
```

---

# SDK

Python:

```python
from modelforge import Client

client = Client(
    api_key="mf_live_xxxxx"
)

result = client.predict(
    model="sentiment",
    version="2.1.0",
    input="This product is fantastic."
)

print(result)
```

TypeScript:

```typescript
const result = await modelForge.predict({
  model: "sentiment",
  version: "2.1.0",
  input: "This product is fantastic."
});
```

---

# Technology Stack

## Backend

- Python
- FastAPI
- Pydantic
- SQLAlchemy

## Machine Learning

- PyTorch
- Hugging Face
- XGBoost
- scikit-learn
- vLLM
- MLflow

## Data

- PostgreSQL
- Redis
- S3

## Messaging

- Amazon SQS

## Infrastructure

- Docker
- Kubernetes
- Helm
- Terraform

## AWS

- EKS
- ECR
- S3
- RDS
- ElastiCache
- SQS
- IAM
- KMS
- Secrets Manager
- CloudWatch
- Application Load Balancer

## Observability

- OpenTelemetry
- Prometheus
- Grafana

## CI/CD

- GitHub Actions
- Trivy

---

# Repository Structure

```text
modelforge/
│
├── services/
│   ├── api/
│   ├── model-registry/
│   ├── model-router/
│   ├── inference-worker/
│   ├── job-service/
│   └── evaluation-service/
│
├── models/
│   ├── sentiment/
│   ├── fraud/
│   └── embeddings/
│
├── sdk/
│   ├── python/
│   └── typescript/
│
├── cli/
│
├── frontend/
│
├── infrastructure/
│   ├── terraform/
│   ├── helm/
│   └── kubernetes/
│
├── monitoring/
│   ├── prometheus/
│   ├── grafana/
│   └── alerts/
│
├── experiments/
│
├── datasets/
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── docker/
│
├── .github/
│   └── workflows/
│
└── README.md
```

---

# Local Development

## Requirements

```text
Python 3.12+
Docker
Docker Compose
kubectl
Helm
Terraform
Node.js 20+
```

Optional for local Kubernetes:

```text
kind
minikube
```

---

## Start Dependencies

```bash
docker compose up -d
```

This starts:

```text
PostgreSQL
Redis
MinIO
Prometheus
Grafana
```

MinIO provides an S3-compatible object-storage environment for local development.

---

## Start API

```bash
cd services/api

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

uvicorn app.main:app --reload
```

API:

```text
http://localhost:8000
```

Swagger:

```text
http://localhost:8000/docs
```

---

# Kubernetes Development

Create a local cluster:

```bash
kind create cluster --name modelforge
```

Build images:

```bash
docker build -t modelforge-api .
```

Load images:

```bash
kind load docker-image modelforge-api
```

Deploy:

```bash
helm install modelforge ./infrastructure/helm/modelforge
```

Check:

```bash
kubectl get pods
kubectl get services
kubectl get deployments
```

---

# AWS Deployment

Provision infrastructure:

```bash
cd infrastructure/terraform

terraform init
terraform plan
terraform apply
```

Build and push images:

```bash
docker build -t modelforge-api .

docker tag modelforge-api:latest \
  <account>.dkr.ecr.<region>.amazonaws.com/modelforge-api:latest

docker push \
  <account>.dkr.ecr.<region>.amazonaws.com/modelforge-api:latest
```

Deploy to EKS:

```bash
helm upgrade --install modelforge \
  ./infrastructure/helm/modelforge
```

Verify:

```bash
kubectl get pods
kubectl get services
kubectl get ingress
```

---

# Testing

Run unit tests:

```bash
pytest tests/unit
```

Integration tests:

```bash
pytest tests/integration
```

End-to-end tests:

```bash
pytest tests/e2e
```

The E2E pipeline should validate:

```text
Register model
      ↓
Create version
      ↓
Deploy
      ↓
Send inference
      ↓
Receive prediction
      ↓
Collect metrics
      ↓
Deploy v2
      ↓
Canary
      ↓
Trigger failure
      ↓
Automatic rollback
```

---

# Failure Testing

ModelForge intentionally supports failure injection for reliability testing.

Examples:

```text
Kill inference pod
Inject latency
Return HTTP 500
Exhaust CPU
Exhaust GPU
Fill SQS queue
Disable model
Break Redis connection
Simulate deployment failure
```

The objective is to verify that:

```text
failure
  ↓
detection
  ↓
recovery
```

actually works.

---

# Development Roadmap

## Phase 1 — Inference Core

- [ ] FastAPI
- [ ] One ML model
- [ ] Prediction API
- [ ] Docker
- [ ] PostgreSQL
- [ ] Model registry

## Phase 2 — Model Infrastructure

- [ ] Model versions
- [ ] S3 artifacts
- [ ] Redis
- [ ] Model router
- [ ] Async inference
- [ ] SQS
- [ ] Worker service

## Phase 3 — Kubernetes

- [ ] Kubernetes deployment
- [ ] Helm
- [ ] Health checks
- [ ] HPA
- [ ] Resource limits
- [ ] CPU/GPU node pools

## Phase 4 — AWS

- [ ] Terraform
- [ ] VPC
- [ ] EKS
- [ ] ECR
- [ ] RDS
- [ ] ElastiCache
- [ ] S3
- [ ] SQS
- [ ] IAM

## Phase 5 — Production Operations

- [ ] Prometheus
- [ ] Grafana
- [ ] OpenTelemetry
- [ ] Distributed tracing
- [ ] Structured logging
- [ ] Alerting
- [ ] Cost tracking

## Phase 6 — Deployment Intelligence

- [ ] Canary releases
- [ ] Traffic splitting
- [ ] Automatic rollback
- [ ] Quality gates
- [ ] Model evaluation
- [ ] MLflow

## Phase 7 — LLM Infrastructure

- [ ] vLLM
- [ ] LLM gateway
- [ ] Streaming
- [ ] Token accounting
- [ ] Provider abstraction
- [ ] Fallback routing
- [ ] Prompt versioning
- [ ] LLM evaluation

## Phase 8 — Advanced

- [ ] GPU autoscaling
- [ ] Dynamic batching
- [ ] Scale-to-zero
- [ ] AI incident analysis
- [ ] Deployment risk scoring
- [ ] Automated anomaly detection
- [ ] Intelligent model routing

---

# Engineering Goals

ModelForge is intended to demonstrate practical knowledge of:

```text
Distributed Systems
        +
Machine Learning
        +
LLM Infrastructure
        +
Kubernetes
        +
AWS
        +
DevOps
        +
Observability
        +
Reliability Engineering
```

The project intentionally focuses on operational problems that appear when ML models move from notebooks into production:

- How are models versioned?
- How are models deployed?
- How is traffic shifted between versions?
- What happens when inference fails?
- How do expensive models scale?
- How do you monitor GPU workloads?
- How do you roll back a bad model?
- How do you track inference cost?
- How do you evaluate model quality before deployment?
- How do you trace a request across distributed services?
- How do you operate LLMs alongside conventional ML models?

---

# Project Philosophy

ModelForge is not intended to be another ML demo.

The objective is to build a **small-scale production inference platform** and use it to explore the engineering problems behind real ML infrastructure.

The project prioritizes:

```text
Correctness
   ↓
Reliability
   ↓
Observability
   ↓
Scalability
   ↓
Automation
```

rather than simply adding more technologies.

---

# License

MIT License
