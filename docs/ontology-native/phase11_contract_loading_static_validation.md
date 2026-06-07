# Phase 11 Contract Loading and Static Validation

This document records the Phase 11 ontology-native rewrite slice. It adds the
first real Kotlin semantic-service implementation code, limited to contract
loading and static validation.

This phase does not implement HTTP endpoints, controllers, route handlers, DTO
classes for runtime API, graph execution, Fuseki clients, RDF ingestion, graph
promotion, reasoning orchestration, scheduled jobs, UI redesign, or old-runtime
removal.

## Implementation Boundary

Phase 11 adds Kotlin code under `semantic-service/src/main/kotlin` for:

- `ContractArtifact`: describes a contract file path and required markers.
- `SemanticServiceContractCatalog`: catalogs Phase 8-10 contract artifacts and
  forbidden runtime markers.
- `ContractFileLoader`: loads contract files from a repository root.
- `StaticContractValidator`: verifies required contract files exist, are
  non-empty, contain expected markers, and do not introduce runtime endpoint or
  graph-client markers in Kotlin source files.
- `StaticContractValidatorTest`: validates the catalog and static validator.

The validator currently checks local files only. It does not parse RDF, parse
OpenAPI, open network connections, execute SPARQL, or call Fuseki/TDB2.

## Contract Inputs

The static validator is wired to these existing contract artifacts:

- `semantic-service/boundary-contract.ttl`
- `semantic-service/openapi.semantic-service.yaml`
- `semantic-service/api-dtos.md`
- `semantic-service/src/main/resources/contracts/semantic-service-contracts.ttl`

Those artifacts represent the Phase 8 semantic service boundary, Phase 9 API
contract, and Phase 10 project scaffold wiring.

## Build Metadata

`semantic-service/build.gradle.kts` now applies the Kotlin JVM plugin and
configures `kotlin("test")` for the focused static validation tests.

No web framework plugin, application plugin, runtime entry point, controller,
DTO class, graph client, or executable service test is added.

## Validation Commands

Run from the repository root.

Run the semantic-service test when Java and Gradle are available:

```bash
cd semantic-service
gradle test
```

If Java or Gradle is unavailable, run static source checks from the repository
root and report the missing tool:

```bash
command -v java || true
command -v gradle || true
rg -n "class StaticContractValidator|class ContractFileLoader|object SemanticServiceContractCatalog|ContractArtifact" semantic-service/src/main/kotlin semantic-service/src/test/kotlin
rg -n "@RestController|@Controller|@SpringBootApplication|fun main\\(|RDFConnection|SPARQLRepository" semantic-service/src/main/kotlin --glob '*.kt'
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

Check implementation boundaries:

```bash
rg -n "contract loading|static validation|StaticContractValidator|ContractFileLoader|SemanticServiceContractCatalog|Phase 8|Phase 9|Phase 10" semantic-service docs/ontology-native/phase11_contract_loading_static_validation.md ontology/releases README.md
rg -n "RestController|SpringBootApplication|RDFConnection|SPARQLRepository|Fuseki" semantic-service/src/main/kotlin --glob '*.kt'
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

Phase 11 is complete when contract loading/static validation code exists, it is
tested or statically checked, contract artifacts from Phase 8-10 are referenced,
release metadata references Phase 11, current RDF/OpenAPI/SPARQL/SHACL checks
still pass, Phase 1 Compose still validates, and no HTTP endpoints, graph
execution, reasoning orchestration, UI redesign, old-runtime removal, commit,
or push has occurred.
