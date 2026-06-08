# Post-Phase-20 Cutover Audit

## Current Verdict

The active product runtime has been cut over to the ontology-native path:

- Fuseki/TDB2 is the only Compose-managed data runtime.
- The Kotlin/JVM semantic-service owns the private semantic query endpoint.
- The React dashboard reads `POST /semantic/query/{queryId}` through
  `VITE_SEMANTIC_API_BASE_URL`.
- The old tracked FastAPI/Postgres/SQLAlchemy backend package has been removed.

The frontend still contains a compatibility adapter that maps graph-backed
semantic envelopes into the current dashboard component contracts. Remaining
defaults are defensive handling for absent optional semantic facts, not a
dependency on the removed relational runtime.

## Removed Old Runtime Scope

Removed from the active source tree:

- `backend/`
- FastAPI route handlers and health endpoint
- SQLAlchemy models/session setup
- Alembic migrations
- Python pipeline/sample-data generator
- Python RDF projection helpers
- Python backend tests
- Postgres service and volume from `docker-compose.yml`
- Postgres-only environment variables from `.env.example`

## Current Active Runtime Surface

| Surface | Classification | Notes |
| --- | --- | --- |
| `docker-compose.yml` Fuseki service | Active runtime | Persistent RDF graph store for ontology-native execution. |
| `semantic-service/` | Active runtime | Kotlin/JVM service for approved query execution, result shaping, serialization, and private endpoint serving. |
| `queries/manifest.ttl` and `queries/read-model/` | Active runtime contracts | Approved read-only SPARQL query catalog and product read-model queries. |
| `ontology/`, `shapes/`, `fixtures/`, `rdf-mapping/`, `reasoning/` | Active semantic contracts | Ontology modules, SHACL contracts, fixtures, mapping contracts, and reasoning scaffolds. |
| `frontend/` | Active user interface | Follow-up workflow UI; data access goes through semantic-service. |
| `docs/ontology-native/` | Active/reference documentation | Mix of current runtime docs and historical phase records. Older phase docs may still mention previous no-delete constraints as historical context. |

## Compatibility Adapter Gaps

The adapter now reads graph-backed queue rank/title/status/time, priority
level, business impact, priority score inputs, impact exposure, redundancy,
mitigation, vendor, thermal, stage thresholds, stage history, aggregate
downtime/wait-hour summaries, evidence timestamp, work-order, validation,
telemetry readings, telemetry alerts, repeat-failure counters,
engineer-assignment counters, and semantic trust-finding detail fields when
present.

Parameterized approved semantic queries now cover incident evidence, incident
timeline, follow-up detail, trust-finding detail, dependency impact, and blast
radius lookups. The remaining adapter fallbacks are narrow null guards for
optional facts that may be missing from a fixture or future source extract.

## Safe Next Migration Work

1. Continue replacing optional null guards only when new graph facts and tests
   make the field mandatory.
2. Add SHACL constraints for any operational fields promoted from optional to
   required.
3. Keep old Python/Postgres code out of the runtime unless a historical
   reference is intentionally restored from Git history.

## Verification Commands

```bash
docker compose config

docker run --rm \
  -v "$PWD":/workspace \
  -w /workspace/semantic-service \
  gradle:8.10.2-jdk17 \
  gradle --no-daemon test

cd frontend && npm run build

rg -n "VITE_API_BASE_URL|localhost:8000|from fastapi|sqlalchemy|create_engine|psycopg|uvicorn" \
  README.md .env.example docker-compose.yml frontend semantic-service

git diff --check
```
