# ADR-0002: Generic Model Registry

## Decision

- A model represents a logical model, e.g. "Fraud Classifier".
- A model version represents an immutable artifact and its runtime configuration.
- A deployment represents a running instance of a specific model version.

## Supported model types

- traditional_ml
- llm

## Initial runtimes

- sklearn
- vllm

## Database tables

- models
- model_versions
- deployments

## Artifact storage

Store model metadata in PostgreSQL.
Store model files in object storage, using an artifact URI.