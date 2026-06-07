# Phase 15 Controlled Fixture Loading

This document records the Phase 15 ontology-native rewrite implementation
slice. It adds controlled RDF fixture loading into Fuseki named graphs through
the runnable Kotlin/JVM semantic service.

This phase does not implement public HTTP endpoints, controllers, runtime DTOs,
unrestricted graph writes, general SPARQL Update, reasoning orchestration, UI
redesign, old-runtime removal, commit, or push.

## Runtime Boundary

Phase 15 introduces the first graph-write boundary, but it is deliberately
small:

- it is CLI-only through `--load-fixtures`
- it loads only the Phase 3 valid fixture files
- it validates each fixture in memory before writing
- it requires SHACL conformance
- it applies validation-only RDFS type closure so Kotlin/Jena validation matches
  the existing pySHACL `inference="rdfs"` contract
- it requires source-record/import-activity provenance
- it writes only controlled fixture named graph URIs
- it promotes only after validation passes

The boundary is not application query execution and not a general graph write
API. Approved query execution from `queries/manifest.ttl` remains a later
phase.

## Named Graph Strategy

Each valid fixture has two controlled named graph targets:

- `urn:dcai:graph:fixture:source:<fixture-id>`
- `urn:dcai:graph:fixture:canonical:<fixture-id>`

The service validates the full Phase 3 fixture load plan first, writes each
source graph, then writes each canonical graph. If any fixture validation fails,
no graph is written. If a source write fails, canonical promotion for that
fixture is skipped and the runtime reports the load as blocked.

## Implementation Artifacts

- `semantic-service/src/main/kotlin/com/dcai/semanticservice/fixtures/FixtureGraphLoadPlan.kt`:
  controlled fixture list and graph URI targets.
- `semantic-service/src/main/kotlin/com/dcai/semanticservice/fixtures/FixtureValidationGate.kt`:
  SHACL and provenance validation gate.
- `semantic-service/src/main/kotlin/com/dcai/semanticservice/fixtures/ControlledFixtureGraphLoader.kt`:
  source write and canonical promotion orchestration.
- `semantic-service/src/main/kotlin/com/dcai/semanticservice/graph/FusekiGraphStoreConfig.kt`:
  graph-store endpoint configuration.
- `semantic-service/src/main/kotlin/com/dcai/semanticservice/graph/FusekiNamedGraphWriter.kt`:
  controlled Graph Store Protocol named graph replacement.
- `semantic-service/src/main/kotlin/com/dcai/semanticservice/runtime/SemanticServiceApplication.kt`:
  optional `--load-fixtures` runtime path.
- `semantic-service/src/test/kotlin/com/dcai/semanticservice/fixtures/`:
  load-plan, validation-gate, and controlled-promotion tests.

## What Runs

Phase 15 can:

- validate local valid fixtures against SHACL shapes
- enforce minimal source-record/import-activity provenance
- replace controlled fixture source named graphs
- replace controlled fixture canonical named graphs after validation
- report fixture loading status from the runtime
- keep `graphExecutionEnabled=false` for application query execution
- keep `httpEndpointsEnabled=false`

## What Still Does Not Run

Phase 15 still does not:

- expose public service endpoints
- accept arbitrary graph writes
- run SPARQL Update
- execute approved application query IDs
- run reasoning
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

Run controlled fixture loading against a local Fuseki service when you intend
to write the fixture named graphs:

```bash
docker run --rm \
  -v "$PWD":/workspace \
  -w /workspace/semantic-service \
  -e DCAI_FUSEKI_DATASET_URL=http://host.docker.internal:3030/infrastructure \
  gradle:8.10.2-jdk17 \
  gradle --no-daemon run --args="--repo-root=/workspace --load-fixtures"
```

Check forbidden runtime boundaries:

```bash
rg -n "@RestController|@Controller|@SpringBootApplication|HttpClient|HttpURLConnection|openConnection\\(|SPARQLRepository|RDFConnection|SPARQLUpdate|UpdateFactory|UpdateExecutionFactory|DatasetAccessor" semantic-service/src/main/kotlin --glob '*.kt' \
  | rg -v 'SemanticServiceContractCatalog.kt|FusekiNamedGraphWriter.kt' || true
```

`HttpURLConnection` and `openConnection(` are allowed only in the controlled
`FusekiNamedGraphWriter`; the static contract validator blocks those markers in
other semantic-service source files.

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

## Phase 15 Completion Criteria

Phase 15 is complete when:

- semantic-service has a controlled fixture loading package
- fixture loading validates SHACL and provenance before promotion
- invalid fixtures cannot be written by the controlled loader
- the runnable app can optionally invoke the fixture loading path
- no public endpoints, unrestricted graph writes, SPARQL Update, reasoning, UI
  changes, or old-runtime removal has occurred
- existing backend/frontend/RDF/SPARQL/OpenAPI/Compose/diff checks pass
- no commit or push has occurred

## Phase 16 Handoff

Phase 16 should add controlled query execution over the fixture-loaded named
graphs. It should use the existing query manifest, allow read-only approved
query IDs only, preserve provenance visibility, and still avoid public service
endpoints until the service boundary is ready.
