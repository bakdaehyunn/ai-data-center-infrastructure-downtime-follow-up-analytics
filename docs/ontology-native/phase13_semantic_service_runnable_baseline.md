# Phase 13 Semantic Service Runnable Baseline

This document records the Phase 13 ontology-native rewrite implementation
slice. It turns the Kotlin/JVM semantic-service scaffold into a runnable,
testable contract-validation baseline.

This phase does not implement public HTTP endpoints, controllers, runtime DTOs,
Fuseki clients, SPARQL execution, graph-store operations, RDF ingestion, graph
promotion, reasoning orchestration, UI redesign, old-runtime removal, commit,
or push.

## Runtime Boundary

The semantic service can now run as a local command-line JVM application. The
application starts, locates the repository root, validates the Phase 8-12
contract artifacts, prints readiness state, and exits non-zero if validation
fails.

The runtime mode is:

```text
contract-validation-runtime
```

This is deliberately not a web service yet. It is the first executable baseline
for the future ontology-native semantic service.

## Implementation Artifacts

- `semantic-service/build.gradle.kts`: applies the Gradle application plugin and
  points to the runnable Kotlin main class.
- `semantic-service/src/main/kotlin/com/dcai/semanticservice/runtime/SemanticServiceApplication.kt`:
  runnable contract-validation application and runtime readiness report.
- `semantic-service/src/test/kotlin/com/dcai/semanticservice/runtime/SemanticServiceApplicationTest.kt`:
  focused tests for startup/readiness behavior.
- `semantic-service/src/main/kotlin/com/dcai/semanticservice/contracts/SemanticServiceContractCatalog.kt`:
  keeps endpoint and graph-client markers forbidden while allowing the Phase 13
  application entry point.

## What Runs

The Phase 13 application:

- checks the required semantic-service contract files
- checks the contract files contain expected markers
- checks Kotlin source does not introduce forbidden web or graph-client markers
- reports `graphExecutionEnabled=false`
- reports `httpEndpointsEnabled=false`

## What Still Does Not Run

Phase 13 still does not:

- expose HTTP endpoints
- execute SPARQL
- connect to Fuseki/TDB2
- read or write named graphs
- run SHACL through the JVM service
- promote source graphs to canonical graphs
- materialize reasoning outputs
- serve UI view models

## Local Tooling Status

The host machine still needs a Java runtime and Gradle to run the service
directly with local commands. If those tools are unavailable, use the Docker
verification path below.

## Validation Commands

Run from the repository root.

Check local JVM tooling:

```bash
command -v java || true
java -version || true
command -v gradle || true
gradle -version || true
```

Run with local Gradle when Java and Gradle are available:

```bash
cd semantic-service
gradle test
gradle run --args="$(pwd)/.."
```

Run with Docker when local Java or Gradle is unavailable:

```bash
docker run --rm \
  -v "$PWD":/workspace \
  -w /workspace/semantic-service \
  gradle:8.10.2-jdk17 \
  gradle --no-daemon test run --args=/workspace
```

Check forbidden runtime boundaries:

```bash
rg -n "@RestController|@Controller|@SpringBootApplication|HttpClient|RDFConnection|SPARQLRepository|SPARQLUpdate" semantic-service/src/main/kotlin --glob '*.kt'
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

## Phase 13 Completion Criteria

Phase 13 is complete when:

- semantic-service has an executable Kotlin/JVM application baseline
- contract/static validation tests pass through local Gradle or Docker
- the application reports readiness without exposing HTTP endpoints
- graph execution remains disabled
- existing RDF/OpenAPI/SPARQL/Compose/diff checks still pass
- old FastAPI/Postgres/SQLAlchemy runtime code remains intact
- no commit or push has occurred

## Phase 14 Handoff

The next phase can add graph access only after Phase 13 tests pass. Phase 14
should introduce a graph-client boundary and read-only Fuseki/TDB2 connectivity
without public semantic endpoints or graph writes.
