# Phase 18 Semantic Response Contract Checkpoint

This document records the Phase 18 ontology-native rewrite implementation
slice. It turns the Phase 17 CLI-only query-result envelopes into a stable
future semantic response contract without implementing public endpoints.

This phase does not implement HTTP controllers, runtime DTO generation, graph
writes, unrestricted query execution, SPARQL Update, reasoning orchestration,
UI redesign, old-runtime removal, commit, or push.

## Contract Boundary

Phase 18 keeps the runtime CLI-only. It updates the non-runtime OpenAPI and
DTO scaffold so future service responses are based on typed semantic result
envelopes, not raw SPARQL binding rows.

Supported future query response envelopes:

- `NamedGraphInventoryResponse`
- `IncidentSummaryResponse`
- `ProvenanceSourceRecordsResponse`

Shared future response fields:

- `queryId`
- `resultType`
- `recordCount`
- `records`
- `provenance`

The future error envelope is `SemanticErrorResponse`.

## Versioning Rules

- OpenAPI scaffold version: `2026-06-phase18-response-contract-checkpoint`
- Query result provenance contract: `2026.06.phase17-result-envelope`
- Error envelope contract: `2026.06.phase18-error-envelope`
- Breaking changes require a new response contract checkpoint.
- Additive optional fields may keep the same checkpoint only when existing
  required fields and result-type names stay stable.

## Implementation Artifacts

- `semantic-service/openapi.semantic-service.yaml`: future typed response
  schemas and semantic error envelope.
- `semantic-service/api-dtos.md`: DTO field definitions, error rules, and
  versioning rules.
- `semantic-service/src/main/kotlin/com/dcai/semanticservice/contracts/SemanticServiceContractCatalog.kt`:
  static marker requirements for Phase 18 response contract schemas.
- `semantic-service/src/test/kotlin/com/dcai/semanticservice/contracts/SemanticResponseContractTest.kt`:
  contract tests tying OpenAPI/DTO docs to the Phase 17 Kotlin envelope types.

## What Runs

Phase 18 can:

- validate that OpenAPI and DTO docs contain the stable response schema names
- validate that documented result type names match Kotlin `QueryResultType`
  values
- validate that error envelope codes and contract versions remain documented
- keep the semantic service runnable only as the existing CLI validation
  runtime

## What Still Does Not Run

Phase 18 still does not:

- expose public semantic service endpoints
- serialize envelopes to HTTP JSON responses
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
assert doc["info"]["version"] == "2026-06-phase18-response-contract-checkpoint"
schemas = doc["components"]["schemas"]
for name in [
    "NamedGraphInventoryResponse",
    "IncidentSummaryResponse",
    "ProvenanceSourceRecordsResponse",
    "SemanticErrorResponse",
    "SemanticResponseProvenance",
]:
    assert name in schemas, name
print("phase18 openapi response contract parsed")
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

## Phase 18 Completion Criteria

Phase 18 is complete when:

- OpenAPI and DTO docs define typed future response shapes for the three Phase
  17 envelope categories
- semantic error envelope rules and versioning rules are documented
- static tests pin schema names, result type values, error codes, and contract
  versions
- no public endpoints, graph writes, SPARQL Update, reasoning, UI changes, or
  old-runtime removal has occurred
- semantic-service/OpenAPI/RDF/SPARQL/backend/frontend/diff checks pass
- no commit or push has occurred

## Phase 19 Handoff

Phase 19 should add an internal-only response serialization boundary for the
Phase 18 contract. It should convert Phase 17 envelopes into in-memory
response payload maps or DTO-like values that can be tested locally, while
still avoiding public HTTP endpoints unless explicitly approved.
