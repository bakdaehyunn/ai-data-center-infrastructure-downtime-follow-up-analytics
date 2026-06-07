# Production Rollout

## Runtime Components

```text
source extracts or controlled fixtures
  -> RDF mapping and graph promotion gates
  -> Fuseki/TDB2 dataset
  -> Kotlin/JVM semantic-service
  -> React/Vite dashboard
```

## Local Runtime

Run Fuseki:

```bash
docker compose up fuseki
```

Run the private semantic endpoint:

```bash
docker run --rm \
  -v "$PWD":/workspace \
  -w /workspace/semantic-service \
  -e DCAI_FUSEKI_DATASET_URL=http://host.docker.internal:3030/infrastructure \
  gradle:8.10.2-jdk17 \
  gradle --no-daemon run --args="--repo-root=/workspace --serve-private-query-endpoint"
```

Run the frontend:

```bash
cd frontend
npm run dev
```

Set `VITE_SEMANTIC_API_BASE_URL` when the semantic-service endpoint is not
available at `http://127.0.0.1:18080`.

## Deployment Gates

- Fuseki dataset URL is configured.
- RDF fixtures/source extracts parse.
- SHACL validation gates pass.
- Approved SPARQL query files parse and remain read-only.
- semantic-service tests pass.
- frontend build passes.
- `docker compose config` shows Fuseki as the only Compose-managed data
  runtime.
- scans show no active FastAPI/Postgres runtime references.

## Observability Direction

The first production signal should be semantic runtime health:

- graph store reachable
- approved query catalog loaded
- response serializer contract version
- SHACL conformance state
- latest graph promotion activity
- query execution failure counts

Tracing, scheduled orchestration, Kubernetes, Airflow, Kafka, and OpenTelemetry
can be added later if they solve a concrete deployment or integration problem.
