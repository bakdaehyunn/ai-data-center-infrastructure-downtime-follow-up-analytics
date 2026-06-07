# Post-Phase-20 Cutover Audit

## Purpose

This audit identifies which pre-rewrite FastAPI/Postgres/SQLAlchemy/React
surfaces are still active, stale, dead, or reference-only after Phase 20. It is
intentionally a planning artifact only. No runtime code is removed by this
audit.

## Current Verdict

The project is not fully cut over to the ontology-native runtime yet.

The Kotlin/JVM semantic service now has a runnable internal baseline, Fuseki
graph access boundaries, controlled fixture loading, approved read-only query
execution, shaped query envelopes, response serialization, and endpoint
readiness decisions. It does not yet expose public or private HTTP endpoints for
the dashboard.

The current user-facing dashboard still depends on the old runtime:

- `frontend/src/api.ts` defaults to `http://localhost:8000`.
- `frontend/src/api.ts` calls existing `/api/*` FastAPI routes.
- `backend/app/main.py` still creates the FastAPI application.
- `backend/app/api/routes.py` still owns the active dashboard API surface.
- `backend/app/db.py`, `backend/app/settings.py`, `backend/app/models/`, and
  `backend/alembic/` still support the SQLAlchemy/Postgres runtime.
- `docker-compose.yml` still defines Postgres because the old runtime remains
  executable.

No tracked old runtime source file is safe to delete immediately without first
adding semantic-service endpoint parity and switching the UI away from the old
API.

## Classification Legend

- **Active runtime**: Still required to run the current product.
- **Migrate-first**: Must be replaced by ontology-native behavior before
  removal.
- **Reference-only**: Useful as domain reference, but should not remain a
  runtime authority after cutover.
- **Remove-later**: Safe to remove only after explicit gates pass.
- **Generated/local cleanup**: Build, cache, dependency, or generated output;
  not a source migration decision.
- **No-delete-now**: Keep until a later deletion goal explicitly approves
  removal.

## Runtime Surface Audit

| Surface | Current classification | Why it matters | Safe next action |
| --- | --- | --- | --- |
| `backend/app/main.py` | Active runtime, migrate-first, no-delete-now | Creates the FastAPI app, CORS policy, `/api/health`, and includes the active API router. | Keep until semantic-service endpoints replace the dashboard API. |
| `backend/app/api/routes.py` | Active runtime, migrate-first, no-delete-now | Owns the current `/api/*` dashboard, semantic projection, topology, connector, pipeline, and data-quality routes. | Build a route parity matrix, then implement semantic-service equivalents before retirement. |
| `backend/app/schemas/` | Active runtime, migrate-first | Defines response models currently consumed by the React frontend. | Use as reference for semantic response DTO parity, then retire after UI migration. |
| `backend/app/db.py` | Active runtime, migrate-first | Creates SQLAlchemy engine/session for current API and pipeline reads. | Remove only after no runtime code imports `get_db`, `SessionLocal`, or `engine`. |
| `backend/app/settings.py` | Active runtime, migrate-first | Still sets the default Postgres URL and optional triple-store sync URL. | Split future semantic-service config from old backend config before removing. |
| `backend/app/models/` | Active runtime, migrate-first | SQLAlchemy entities are still the current source for the old API and analytics materializations. | Replace with RDF named-graph source-of-truth and SPARQL view models before deleting. |
| `backend/alembic/` and `backend/alembic.ini` | Active runtime, remove-later | Maintains the Postgres schema used by the current backend. | Remove only after Postgres is no longer started, migrated, or tested. |
| `backend/app/pipeline/` | Active runtime/reference, migrate-first | Loads raw data, transforms to relational core, runs quality/reconciliation, and builds analytics rows. | Migrate concepts to RDF ingestion, SHACL gates, promotion rules, and reasoning jobs. |
| `backend/app/sample_data/` | Active runtime/reference, migrate-first | Generates the old sample dataset used by backend tests and demo workflows. | Convert scenarios into RDF fixtures/source mappings before deletion. |
| `backend/generated/sample_data/` | Generated/local cleanup | Ignored generated output from sample generation. | Can be regenerated; do not treat as authoritative source. |
| `backend/app/domain/infrastructure_ontology.py` | Reference-only after cutover, migrate-first | Contains Python vocabulary and validation logic that informed ontology hardening. | Migrate durable rules into OWL/RDFS/SHACL/SPARQL, then retire. |
| `backend/app/domain/semantic_export.py` | Bridge/projection, migrate-first | Projects relational data to RDF; not an ontology-native source of truth. | Remove after RDF ingestion/promotion replaces SQL-to-RDF projection. |
| `backend/app/domain/semantic_graph.py` | Bridge/projection, migrate-first | Provides Python semantic validation/query helpers for old API endpoints. | Replace with semantic-service query execution and validation. |
| `backend/app/connectors/contracts.py` | Reference-only, migrate-first | Describes expected source extract contracts. | Recast as source-to-canonical RDF mapping and ingestion contract. |
| `backend/tests/` | Active verification, no-delete-now | Tests protect current old runtime behavior while parity is being built. | Keep until equivalent semantic-service and UI parity tests exist. |
| `backend/requirements.txt` | Active runtime, remove-later | Keeps FastAPI, SQLAlchemy, Alembic, rdflib, pyshacl, pytest, and old runtime dependencies. | Shrink only after backend runtime is archived or removed. |
| `backend/Dockerfile` | Active runtime, remove-later | Builds the old FastAPI backend container. | Remove only after Compose and deployment paths no longer need the old backend. |
| `frontend/src/App.tsx` | Active runtime, migrate-first | Implements the current follow-up workflow UX and detail routes. | Preserve UX intent but move data access to semantic-service view models. |
| `frontend/src/api.ts` | Active runtime, migrate-first | Hard-wires the UI to old `/api/*` endpoints. | Introduce a semantic API adapter only after semantic-service endpoints exist. |
| `frontend/src/App.css`, `frontend/src/index.css` | Active runtime, migrate-first | Current UX styling for the follow-up workflow. | Keep until UI is intentionally redesigned or migrated. |
| `frontend/package.json` and lockfile | Active runtime, remove-later | Current React/Vite app is still the user-facing dashboard. | Remove only if the UI framework is replaced in a later approved phase. |
| `frontend/Dockerfile` | Active runtime, remove-later | Builds the current dashboard with `VITE_API_BASE_URL`. | Update or remove after dashboard points to semantic-service endpoints. |
| `docker-compose.yml` Postgres service | Active runtime, remove-later | Required by the old backend path. | Remove only after backend/Postgres route parity is no longer needed. |
| `docker-compose.yml` Fuseki service | Target runtime | Supports ontology-native graph storage. | Keep and promote from scaffold to required runtime. |
| `semantic-service/` | Target runtime | The ontology-native transition stack from Phases 10-20. | Continue implementation toward private endpoints and graph execution. |
| Root `README.md` old API/stack sections | Documentation drift, migrate-first | Still describes FastAPI and SQL-backed API as active. That is currently true, but it conflicts with the target cutover direction. | Add cutover status language before deleting old architecture docs. |
| `docs/01_architecture.md`, `docs/04_api.md`, `docs/09_production_rollout.md`, `docs/11_topology_semantic_connectors.md` | Documentation drift/reference | Describe old or hybrid runtime behavior. | Mark as legacy/reference or revise after semantic-service endpoint parity. |
| `backend/.venv`, `frontend/node_modules`, `frontend/dist`, `__pycache__`, `.pytest_cache` | Generated/local cleanup | Local dependency/build/cache artifacts, ignored by Git. | Can be locally cleaned anytime; not part of source cutover. |

## Active API Surface To Replace

The old FastAPI router still exposes the current product surface:

- `GET /api/overview`
- `GET /api/follow-ups`
- `GET /api/follow-ups/{incident_id}`
- `GET /api/follow-ups/{incident_id}/timeline`
- `GET /api/downtime/stages`
- `GET /api/equipment/delays`
- `GET /api/assets/delays`
- `GET /api/lines/delays`
- `GET /api/zones/delays`
- `GET /api/parts/waiting`
- `GET /api/spares/waiting`
- `GET /api/impact/summary`
- `GET /api/topology/dependencies`
- `GET /api/metadata/filters`
- `GET /api/pipeline-runs`
- `GET /api/data-quality/checks`
- `GET /api/data-quality/checks/{check_result_id}`
- `GET /api/semantic/infrastructure.ttl`
- `GET /api/semantic/validation`
- `GET /api/semantic/query/dependency-impact/{asset_id}`
- `GET /api/semantic/query/incident-evidence/{incident_id}`
- `GET /api/semantic/query/blast-radius/{asset_id}`
- `POST /api/semantic/graph/sync`
- `GET /api/connectors/contracts`

The frontend currently uses only a subset of those routes, but deletion should
be based on router-level parity, not only visible UI calls.

## Safe Removal And Migration Plan

### Phase A: Route Parity Matrix

Create a matrix from every old `/api/*` route to one of:

- semantic-service endpoint replacement
- semantic-service internal query/command replacement
- archived reference-only behavior
- deliberate removal with product rationale

Gate: every old route has an owner, replacement decision, response contract, and
test strategy.

### Phase B: Private Semantic Endpoint Scaffold

Implement private semantic-service HTTP endpoints only after Phase 20's endpoint
readiness decision is accepted. Endpoints must use the Phase 19 serializer and
Phase 18 response contract rules.

Gate: endpoint tests prove no raw query results or graph internals leak outside
the serializer boundary.

### Phase C: Semantic View Models For Current UX

Build semantic-service view models for:

- queue summary
- queue list
- selected follow-up preview
- follow-up detail summary
- impact
- trust
- dependencies
- filter metadata
- provenance lookup

Gate: sample fixture responses match the current UX needs without requiring SQL
or FastAPI.

### Phase D: UI Adapter Switch

Change `frontend/src/api.ts` to call the semantic-service endpoint set behind a
clear environment switch. Keep the follow-up workflow UX unless a separate UI
redesign is approved.

Gate: the frontend can run against semantic-service responses with no old
FastAPI backend process.

### Phase E: Parity And Regression Verification

Run old-vs-new parity checks for the sample scenarios:

- ranked queue order
- KPI/exposure counts
- selected follow-up preview
- detail Summary/Impact/Trust/Dependencies content
- dependency path evidence
- trust findings
- error envelopes
- provenance links

Gate: parity deltas are documented and accepted as either equivalent or
intentional product changes.

### Phase F: Old Runtime Retirement

After Phases A-E pass:

- stop starting Postgres for the default ontology-native path
- remove or archive FastAPI route code
- remove SQLAlchemy/Alembic runtime paths
- remove Python semantic projection helpers
- remove old backend Dockerfile if unused
- update README and legacy docs

Gate: `rg` checks prove old runtime references are either gone or clearly marked
legacy/reference.

## Deletion Gates

No tracked old runtime source should be deleted until all of these are true:

1. Semantic-service private endpoints exist for required UI workflows.
2. Phase 19 serializer is the only response boundary for endpoint payloads.
3. RDF fixtures and named graphs cover the current demo scenarios.
4. SHACL/provenance validation gates pass for promoted graph inputs.
5. UI runs against semantic-service endpoints without the old FastAPI process.
6. Old-vs-new parity tests pass or accepted deltas are documented.
7. `docker-compose.yml` has an ontology-native default path that does not need
   Postgres.
8. Documentation clearly labels any remaining old code as reference-only.
9. A separate deletion goal is approved with exact file removal scope.
10. The deletion branch has a rollback point through Git history.

## Verification Commands For The Future Deletion Goal

Run these before removing old code:

```bash
rg -n "VITE_API_BASE_URL|/api/|FastAPI|sqlalchemy|create_engine|postgres|alembic|psycopg|uvicorn" \
  README.md docs backend frontend docker-compose.yml semantic-service \
  --glob '!frontend/node_modules/**' \
  --glob '!frontend/dist/**' \
  --glob '!backend/.venv/**'

cd semantic-service && ./gradlew test

cd frontend && npm run build

cd backend && pytest

docker compose config
```

After the semantic-service endpoints exist, add a targeted parity command that
compares old FastAPI fixture responses against semantic-service fixture
responses before any deletion.

## Recommended Next Goal

The next implementation goal should not delete old code. It should create the
route parity matrix and the first private semantic-service endpoint scaffold
using the Phase 19 serializer.

Suggested next objective:

```text
Create the post-Phase-20 route parity /goal: map every old FastAPI /api route to semantic-service query IDs, response envelopes, provenance requirements, migration status, and tests, then identify the first private semantic endpoint slice. Do not delete old runtime code, redesign UI, commit, or push.
```
