# Phase 16 Controlled Read-only Query Execution

This document records the Phase 16 ontology-native rewrite implementation
slice. It adds controlled read-only query execution over fixture-loaded Fuseki
named graphs through the runnable Kotlin/JVM semantic service.

This phase does not implement public HTTP endpoints, controllers, runtime DTOs,
graph writes, unrestricted query execution, SPARQL Update, reasoning
orchestration, UI redesign, old-runtime removal, commit, or push.

## Runtime Boundary

Phase 16 introduces query execution, but it is deliberately constrained:

- it is CLI-only through `--run-query=<query-id>`
- it loads approved query IDs from `queries/manifest.ttl`
- executable entries must use `implementationStatus "phase16-approved"`
- executable entries must be SELECT or ASK
- query files must resolve under `queries/`
- placeholder reasoning queries remain non-executable
- update queries remain non-executable
- query execution reads Fuseki through the query endpoint only

The boundary is not a public semantic API. Public endpoints remain a later
service phase after the CLI runtime is stable.

## Approved Phase 16 Queries

Phase 16 adds these approved inspection queries:

- `fixtureNamedGraphInventory`
- `fixtureIncidentSummary`
- `fixtureProvenanceSourceRecords`

These queries inspect `urn:dcai:graph:fixture:source:*` and
`urn:dcai:graph:fixture:canonical:*` named graphs loaded by Phase 15. They do
not construct reasoning findings and do not write graphs.

## Implementation Artifacts

- `queries/manifest.ttl`: marks the Phase 16 query IDs as approved.
- `queries/inspection/*.select.rq`: read-only fixture inspection queries.
- `semantic-service/src/main/kotlin/com/dcai/semanticservice/query/ApprovedQueryCatalog.kt`:
  manifest loader and read-only query validation.
- `semantic-service/src/main/kotlin/com/dcai/semanticservice/query/JenaFusekiReadOnlyQueryExecutor.kt`:
  Jena-backed Fuseki query execution for approved SELECT/ASK queries.
- `semantic-service/src/main/kotlin/com/dcai/semanticservice/runtime/SemanticServiceApplication.kt`:
  optional `--run-query=<query-id>` runtime path.
- `semantic-service/src/test/kotlin/com/dcai/semanticservice/query/`:
  approved catalog and unapproved-query rejection tests.

## What Runs

Phase 16 can:

- load approved query metadata from the query manifest
- reject unapproved query IDs
- reject non-SELECT/ASK approved runtime queries
- execute approved SELECT queries against Fuseki
- report query ID, query mode, and row count from the runtime
- keep `graphExecutionEnabled=false` for reasoning/application graph execution
- keep `httpEndpointsEnabled=false`

## What Still Does Not Run

Phase 16 still does not:

- expose public service endpoints
- accept arbitrary SPARQL text
- execute placeholder reasoning queries
- run CONSTRUCT reasoning output
- write RDF graphs
- run SPARQL Update
- promote production source graphs
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

Run controlled fixture loading and then an approved query against a disposable
Fuseki service when you intend to verify the full local graph loop:

```bash
docker rm -f phase16-fuseki-test >/dev/null 2>&1 || true
docker run -d --name phase16-fuseki-test -p 13031:3030 atomgraph/fuseki:latest --update --mem /infrastructure
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
docker rm -f phase16-fuseki-test >/dev/null
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

Parse placeholder and approved SPARQL queries:

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

## Phase 16 Completion Criteria

Phase 16 is complete when:

- semantic-service has an approved read-only query catalog
- the runtime can execute approved query IDs only
- unapproved reasoning/update placeholders remain non-executable
- no public endpoints, graph writes, SPARQL Update, reasoning, UI changes, or
  old-runtime removal has occurred
- existing backend/frontend/RDF/SPARQL/OpenAPI/SHACL/Compose/diff checks pass
- no commit or push has occurred

## Phase 17 Handoff

Phase 17 should add query-result contract shaping for future service responses.
It should keep execution CLI-only unless a later phase explicitly opens public
endpoints, and it should define stable result envelopes for incident,
provenance, and named-graph inspection use cases.
