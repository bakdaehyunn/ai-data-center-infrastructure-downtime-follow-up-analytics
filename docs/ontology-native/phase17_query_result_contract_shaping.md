# Phase 17 Query Result Contract Shaping

This document records the Phase 17 ontology-native rewrite implementation
slice. It adds stable query-result envelopes for future semantic service
responses while keeping execution CLI-only.

This phase does not implement public HTTP endpoints, controllers, runtime DTO
generation, graph writes, unrestricted query execution, SPARQL Update,
reasoning orchestration, UI redesign, old-runtime removal, commit, or push.

## Runtime Boundary

Phase 17 shapes approved query results into typed contracts after Phase 16
read-only execution:

- `fixtureNamedGraphInventory` -> `NamedGraphInventoryEnvelope`
- `fixtureIncidentSummary` -> `IncidentSummaryEnvelope`
- `fixtureProvenanceSourceRecords` -> `ProvenanceSourceRecordsEnvelope`

The envelopes are Kotlin data contracts only. They are not exposed through HTTP
routes and do not change the old FastAPI/React runtime.

## Result Envelope Contract

All envelopes share:

- `queryId`: approved query identifier
- `resultType`: stable semantic result category
- `recordCount`: number of typed records
- `provenance`: query id, graph scope, and contract version

Envelope-specific records:

- named graph inventory: graph URI and subject count
- incident summary: graph URI, incident URI, incident id, asset URI, stage URI,
  and optional source record URI
- provenance source records: graph URI, source record URI, source record id,
  source system URI, payload hash, and import activity URI

The Phase 17 contract version is
`2026.06.phase17-result-envelope`.

## Implementation Artifacts

- `semantic-service/src/main/kotlin/com/dcai/semanticservice/query/QueryResultEnvelope.kt`:
  stable envelope and record contracts.
- `semantic-service/src/main/kotlin/com/dcai/semanticservice/query/QueryResultShaper.kt`:
  shaping logic from query binding rows into typed envelopes.
- `semantic-service/src/main/kotlin/com/dcai/semanticservice/runtime/SemanticServiceApplication.kt`:
  CLI reporting for shaped result type, record count, and contract version.
- `semantic-service/src/test/kotlin/com/dcai/semanticservice/query/QueryResultShaperTest.kt`:
  supported envelope shaping and unsupported-shaping rejection tests.

## What Runs

Phase 17 can:

- shape approved query execution rows into stable typed envelopes
- reject unsupported query IDs without result-envelope contracts
- reject rows missing required bindings
- report shaped result type, record count, and contract version from the CLI
- keep `graphExecutionEnabled=false` for reasoning/application graph execution
- keep `httpEndpointsEnabled=false`

## What Still Does Not Run

Phase 17 still does not:

- expose public service endpoints
- emit JSON HTTP responses
- accept arbitrary SPARQL text
- execute placeholder reasoning queries
- run CONSTRUCT reasoning output
- write RDF graphs
- run SPARQL Update
- serve UI view models

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

Run controlled fixture loading and then an approved shaped query against a
disposable Fuseki service:

```bash
docker rm -f phase17-fuseki-test >/dev/null 2>&1 || true
docker run -d --name phase17-fuseki-test -p 13031:3030 atomgraph/fuseki:latest --update --mem /infrastructure
docker run --rm \
  -v "$PWD":/workspace \
  -w /workspace/semantic-service \
  -e DCAI_FUSEKI_DATASET_URL=http://host.docker.internal:13031/infrastructure \
  gradle:8.10.2-jdk17 \
  gradle --no-daemon run --args="--repo-root=/workspace --load-fixtures"
docker run --rm \
  -v "$PWD":/workspace \
  -w /workspace/semantic-service \
  -e DCAI_FUSEKI_DATASET_URL=http://host.docker.internal:13031/infrastructure \
  gradle:8.10.2-jdk17 \
  gradle --no-daemon run --args="--repo-root=/workspace --run-query=fixtureNamedGraphInventory"
docker rm -f phase17-fuseki-test >/dev/null
```

Check forbidden runtime boundaries:

```bash
rg -n "@RestController|@Controller|@SpringBootApplication|HttpClient|HttpURLConnection|openConnection\\(|SPARQLRepository|RDFConnection|SPARQLUpdate|UpdateFactory|UpdateExecutionFactory|DatasetAccessor" semantic-service/src/main/kotlin --glob '*.kt' \
  | rg -v 'SemanticServiceContractCatalog.kt|FusekiNamedGraphWriter.kt' || true
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

Run SHACL fixture validation:

```bash
backend/.venv/bin/python - <<'PY'
from pathlib import Path
from rdflib import Graph
from pyshacl import validate

ontology = Graph()
for path in sorted(Path("ontology/modules").glob("*.ttl")):
    ontology.parse(path, format="turtle")

shapes = Graph()
for path in sorted(Path("shapes").glob("*.ttl")):
    shapes.parse(path, format="turtle")

for path in sorted(Path("fixtures/rdf/valid").glob("*.ttl")):
    data = Graph()
    data.parse(path, format="turtle")
    conforms, _, report = validate(data, shacl_graph=shapes, ont_graph=ontology, inference="rdfs")
    assert conforms, f"Expected valid fixture to conform: {path}\n{report}"
    print(f"valid conforms: {path}")

for path in sorted(Path("fixtures/rdf/invalid").glob("*.ttl")):
    data = Graph()
    data.parse(path, format="turtle")
    conforms, _, _ = validate(data, shacl_graph=shapes, ont_graph=ontology, inference="rdfs")
    assert not conforms, f"Expected invalid fixture to fail: {path}"
    print(f"invalid fails as expected: {path}")
PY
```

Keep the Phase 1 runtime scaffold valid:

```bash
docker compose config
```

Check formatting:

```bash
git diff --check
```

## Phase 17 Completion Criteria

Phase 17 is complete when:

- semantic-service has stable typed result envelopes for the three Phase 16
  inspection query IDs
- unsupported query IDs cannot be shaped accidentally
- missing required row bindings fail during shaping
- no public endpoints, graph writes, SPARQL Update, reasoning, UI changes, or
  old-runtime removal has occurred
- existing backend/frontend/RDF/SPARQL/OpenAPI/SHACL/Compose/diff checks pass
- no commit or push has occurred

## Phase 18 Handoff

Phase 18 should add a semantic service response contract review/checkpoint for
when CLI-only envelopes become internal service DTOs. It should decide whether
the next implementation phase remains CLI-only or starts private/internal HTTP
endpoint scaffolding.
