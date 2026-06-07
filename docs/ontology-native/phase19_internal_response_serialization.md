# Phase 19 Internal Response Serialization

This document records the Phase 19 ontology-native rewrite implementation
slice. It adds an internal-only response serialization boundary that converts
Phase 17 query-result envelopes and semantic errors into Phase 18-shaped
in-memory response payloads.

This phase does not implement HTTP controllers, runtime endpoint handlers,
graph writes, unrestricted query execution, SPARQL Update, reasoning
orchestration, UI redesign, old-runtime removal, commit, or push.

## Runtime Boundary

Phase 19 keeps the semantic service CLI-only. The new response serializer is
plain Kotlin code that returns deterministic in-memory maps. It does not use a
web framework, JSON library, controller, route handler, HTTP client, or graph
client.

Supported response payload conversions:

- `NamedGraphInventoryEnvelope` -> Phase 18 `NamedGraphInventoryResponse`
  shape
- `IncidentSummaryEnvelope` -> Phase 18 `IncidentSummaryResponse` shape
- `ProvenanceSourceRecordsEnvelope` -> Phase 18
  `ProvenanceSourceRecordsResponse` shape
- `SemanticErrorCode` -> Phase 18 `SemanticErrorResponse` shape

## Payload Shape

Successful query response payloads contain:

- `queryId`
- `resultType`
- `recordCount`
- `records`
- `provenance`

Error response payloads contain:

- `error.code`
- `error.message`
- `error.detail`, when provided
- `error.queryId`, when provided
- `error.contractVersion`

The error contract version remains `2026.06.phase18-error-envelope` because
Phase 19 implements the Phase 18 error shape instead of changing it.

## Implementation Artifacts

- `semantic-service/src/main/kotlin/com/dcai/semanticservice/response/SemanticResponseSerializer.kt`:
  internal response serialization and semantic error code definitions.
- `semantic-service/src/test/kotlin/com/dcai/semanticservice/response/SemanticResponseSerializerTest.kt`:
  contract tests for result payload keys, records, provenance, and error
  payloads.
- `semantic-service/api-dtos.md`: Phase 19 note that the serializer is
  internal-only and not HTTP/JSON/controller behavior.

## What Runs

Phase 19 can:

- convert typed query-result envelopes to in-memory response maps
- convert approved semantic error codes to in-memory error maps
- verify response keys and payload values in unit tests
- keep the existing CLI validation runtime runnable

## What Still Does Not Run

Phase 19 still does not:

- expose public semantic service endpoints
- serialize HTTP JSON responses
- generate runtime DTO classes
- accept arbitrary SPARQL text
- execute placeholder reasoning queries
- write RDF graphs beyond the existing controlled fixture-loading CLI boundary
- redesign or reconnect the UI
- remove the old FastAPI/Postgres/SQLAlchemy runtime

## Validation Commands

Run from the repository root.

Run semantic-service tests and baseline through Docker:

```bash
docker run --rm \
  -v "$PWD":/workspace \
  -w /workspace/semantic-service \
  gradle:8.10.2-jdk17 \
  gradle --no-daemon test run --args=/workspace
```

Parse the OpenAPI scaffold:

```bash
backend/.venv/bin/python - <<'PY'
import yaml
from pathlib import Path

path = Path("semantic-service/openapi.semantic-service.yaml")
with path.open() as handle:
    doc = yaml.safe_load(handle)
assert doc["openapi"] == "3.1.0"
assert "SemanticErrorResponse" in doc["components"]["schemas"]
print("phase19 openapi contract still parses")
PY
```

Parse all RDF artifacts and manifests:

```bash
backend/.venv/bin/python - <<'PY'
from pathlib import Path
from rdflib import Graph

patterns = [
    "fixtures/rdf/**/*.ttl",
    "ontology/modules/*.ttl",
    "shapes/*.ttl",
    "ontology/releases/*.ttl",
    "queries/*.ttl",
    "reasoning/*.ttl",
    "semantic-service/**/*.ttl",
]
for pattern in patterns:
    for path in sorted(Path().glob(pattern)):
        Graph().parse(path, format="turtle")
PY
```

Parse SPARQL queries:

```bash
backend/.venv/bin/python queries/validate_sparql.py
```

Check forbidden runtime boundaries:

```bash
rg -n "@RestController|@Controller|@SpringBootApplication|HttpClient|HttpURLConnection|openConnection\\(|SPARQLRepository|RDFConnection|SPARQLUpdate|UpdateFactory|UpdateExecutionFactory|DatasetAccessor" semantic-service/src/main/kotlin --glob '*.kt' \
  | rg -v 'SemanticServiceContractCatalog.kt|FusekiNamedGraphWriter.kt' || true
```

Check formatting:

```bash
git diff --check
```

## Phase 19 Completion Criteria

Phase 19 is complete when:

- internal serialization exists for the three Phase 17 envelope categories
- semantic error payload shaping exists for the approved Phase 18 error codes
- tests verify response keys, `resultType`, `recordCount`, records,
  provenance, and error envelope fields
- no public endpoints, graph writes, SPARQL Update, reasoning, UI changes, or
  old-runtime removal has occurred
- semantic-service/OpenAPI/RDF/SPARQL/backend/frontend/diff checks pass
- no commit or push has occurred

## Phase 20 Handoff

Phase 20 should be the endpoint readiness decision checkpoint. It should decide
whether the next implementation step is still internal-only or whether to add a
private semantic query endpoint scaffold. If endpoints are approved later, they
must use the Phase 19 serializer rather than returning raw query bindings.
