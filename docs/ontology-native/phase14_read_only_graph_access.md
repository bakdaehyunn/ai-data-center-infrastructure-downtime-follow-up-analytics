# Phase 14 Read-only Graph Access Boundary

This document records the Phase 14 ontology-native rewrite implementation
slice. It adds a read-only Fuseki/TDB2 graph access boundary to the runnable
Kotlin/JVM semantic service.

This phase does not implement public HTTP endpoints, controllers, runtime DTOs,
RDF graph writes, SPARQL Update, fixture graph loading, graph promotion,
reasoning orchestration, UI redesign, old-runtime removal, commit, or push.

## Runtime Boundary

The semantic service can now construct and run a read-only graph connectivity
check against a Fuseki query endpoint. The check is intentionally limited to
connectivity and named graph count metadata.

The boundary is not application query execution. Approved query execution from
`queries/manifest.ttl` remains a later phase.

## Implementation Artifacts

- `semantic-service/build.gradle.kts`: adds Apache Jena dependencies.
- `semantic-service/src/main/kotlin/com/dcai/semanticservice/graph/FusekiReadOnlyConfig.kt`:
  dataset and query endpoint configuration.
- `semantic-service/src/main/kotlin/com/dcai/semanticservice/graph/ReadOnlyGraphClient.kt`:
  read-only graph client contract and connectivity result.
- `semantic-service/src/main/kotlin/com/dcai/semanticservice/graph/JenaFusekiReadOnlyGraphClient.kt`:
  Jena-backed read-only connectivity client.
- `semantic-service/src/main/kotlin/com/dcai/semanticservice/runtime/SemanticServiceApplication.kt`:
  optional `--check-graph` runtime path.
- `semantic-service/src/test/kotlin/com/dcai/semanticservice/graph/`:
  focused configuration and unreachable-endpoint tests.

The Phase 14 dependency is pinned to Jena `5.6.0` for the current JDK 17
verification image. Jena `6.1.0` was checked during implementation but required
a newer class-file runtime than the Phase 13/14 Docker test image provides.

## What Runs

Phase 14 can:

- configure a Fuseki dataset URL with `DCAI_FUSEKI_DATASET_URL`
- configure a query endpoint URL with `DCAI_FUSEKI_QUERY_URL`
- issue a read-only connectivity query against the Fuseki query endpoint
- report `graphReachable`, `graphDatasetUrl`, `graphQueryEndpointUrl`, and
  `namedGraphCount`
- keep `graphExecutionEnabled=false` for application query execution
- keep `httpEndpointsEnabled=false`

## What Still Does Not Run

Phase 14 still does not:

- expose public service endpoints
- write RDF graphs
- run SPARQL Update
- load fixtures into Fuseki
- execute approved application query IDs
- run reasoning
- promote source/canonical/inferred graphs
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

Run with a live local Fuseki service when available:

```bash
docker compose up -d fuseki
docker run --rm \
  -v "$PWD":/workspace \
  -w /workspace/semantic-service \
  -e DCAI_FUSEKI_DATASET_URL=http://host.docker.internal:3030/infrastructure \
  gradle:8.10.2-jdk17 \
  gradle --no-daemon run --args="--repo-root=/workspace --check-graph"
```

Check forbidden runtime boundaries:

```bash
rg -n "@RestController|@Controller|@SpringBootApplication|HttpClient|SPARQLRepository|RDFConnection|SPARQLUpdate|UpdateFactory|UpdateExecutionFactory|DatasetAccessor" semantic-service/src/main/kotlin --glob '*.kt' \
  | rg -v 'SemanticServiceContractCatalog.kt' || true
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

Parse placeholder SPARQL queries:

```bash
backend/.venv/bin/python queries/validate_sparql.py
```

Parse the OpenAPI-style YAML scaffold:

```bash
backend/.venv/bin/python - <<'PY'
from pathlib import Path
import yaml

path = Path("semantic-service/openapi.semantic-service.yaml")
document = yaml.safe_load(path.read_text(encoding="utf-8"))
assert document["openapi"].startswith("3.")
print(f"parsed OpenAPI scaffold: {path}")
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

## Phase 14 Completion Criteria

Phase 14 is complete when:

- semantic-service has a read-only graph access package
- tests prove configuration and safe unreachable-endpoint behavior
- the runnable app can optionally invoke the graph connectivity check
- no public endpoints, graph writes, SPARQL Update, reasoning, UI changes, or
  old-runtime removal has occurred
- existing backend/frontend/RDF/SPARQL/OpenAPI/Compose/diff checks pass
- no commit or push has occurred

## Phase 15 Handoff

Phase 15 should add controlled RDF fixture loading into named graphs. It should
start from the Phase 14 read-only boundary, then add write capability only
inside a fixture-loading/promotion gate that validates SHACL and provenance
before canonical graph promotion.
