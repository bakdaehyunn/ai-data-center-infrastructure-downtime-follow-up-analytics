# Phase 10 Semantic Service Project Scaffold

This document records the Phase 10 ontology-native rewrite scaffold. It adds a
minimal non-running Java/Kotlin semantic service project scaffold.

This phase does not implement Java/Kotlin service runtime, endpoints,
controllers, DTO classes, graph execution, RDF ingestion, graph promotion,
reasoning orchestration, scheduled jobs, clients, tests that execute a service,
production SPARQL execution, UI redesign, or old-runtime removal.

## Scaffold Artifacts

Build metadata:

- `semantic-service/settings.gradle.kts`
- `semantic-service/build.gradle.kts`
- `semantic-service/gradle.properties`

Package layout placeholders:

- `semantic-service/src/main/kotlin/com/dcai/semanticservice/api/`
- `semantic-service/src/main/kotlin/com/dcai/semanticservice/contracts/`
- `semantic-service/src/main/kotlin/com/dcai/semanticservice/query/`
- `semantic-service/src/main/kotlin/com/dcai/semanticservice/reasoning/`
- `semantic-service/src/main/kotlin/com/dcai/semanticservice/provenance/`
- `semantic-service/src/main/kotlin/com/dcai/semanticservice/governance/`
- `semantic-service/src/test/kotlin/com/dcai/semanticservice/`

Contract wiring:

- `semantic-service/src/main/resources/contracts/semantic-service-contracts.ttl`
- `semantic-service/src/main/resources/contracts/README.md`

The scaffold points back to:

- Phase 8 service boundary: `semantic-service/boundary-contract.ttl`
- Phase 9 API contract: `semantic-service/openapi.semantic-service.yaml`
- Phase 9 DTO documentation: `semantic-service/api-dtos.md`

## Non-running Boundary

The Gradle files are metadata only. Phase 10 deliberately does not add:

- Kotlin source files
- application entry point
- framework plugin
- route handlers
- DTO classes
- generated clients
- Fuseki/TDB2 graph clients
- executable tests
- SPARQL execution

This keeps the scaffold useful for project structure review without pretending
the semantic service exists.

## Validation Commands

Run from the repository root.

Check required scaffold files:

```bash
test -f semantic-service/settings.gradle.kts
test -f semantic-service/build.gradle.kts
test -f semantic-service/gradle.properties
test -f semantic-service/src/main/resources/contracts/semantic-service-contracts.ttl
test -f semantic-service/src/main/kotlin/com/dcai/semanticservice/README.md
test -f semantic-service/src/test/kotlin/com/dcai/semanticservice/README.md
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
        graph = Graph()
        graph.parse(path, format="turtle")
        print(f"{path}: {len(graph)} triples")
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

Run SHACL validation for valid and invalid fixtures:

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

Check scaffold references:

```bash
rg -n "Java/Kotlin|build metadata|package layout|placeholder contract|Phase 8|Phase 9|boundary-contract|API contract|non-running" semantic-service docs/ontology-native/phase10_semantic_service_project_scaffold.md ontology/releases README.md
find semantic-service/src -type f | sort
```

Keep the Phase 1 runtime scaffold valid:

```bash
docker compose config
```

Check formatting:

```bash
git diff --check
```

## Stop Condition

Phase 10 is complete when the minimal non-running Java/Kotlin scaffold exists,
build metadata exists, package layout placeholders exist, contract manifest
references Phase 8-9 contracts, release metadata references Phase 10, current
RDF/OpenAPI/SPARQL/SHACL checks still pass, Phase 1 Compose still validates,
and no endpoints, graph execution, reasoning orchestration, UI redesign,
old-runtime removal, commit, or push has occurred.
