# Phase 9 API Contract Scaffold

This document records the Phase 9 ontology-native rewrite scaffold. It adds a
non-runtime API contract for the future Java/Kotlin semantic service.

This phase does not implement Java/Kotlin service runtime, executable reasoning
orchestration, RDF ingestion, graph promotion, scheduled jobs, API endpoints,
controllers, DTO classes, clients, production SPARQL execution, UI redesign, or
old-runtime removal.

## Contract Artifacts

- `semantic-service/openapi.semantic-service.yaml`: OpenAPI-style endpoint and
  schema scaffold.
- `semantic-service/api-dtos.md`: request/response DTO documentation.
- `semantic-service/boundary-contract.ttl`: Phase 8 semantic service boundary
  metadata that Phase 9 expands into endpoint shape.

The OpenAPI-style file is for contract review only. It must not be treated as
generated service code or an implemented route surface.

## Endpoint Coverage

| Use case | Endpoint shape | Request DTO | Response DTO |
| --- | --- | --- | --- |
| Query execution | `POST /semantic/query/{queryId}` | `QueryExecutionRequest` | `QueryExecutionResponse` |
| Reasoning validation | `POST /semantic/reasoning/validate` | `ReasoningValidationRequest` | `ReasoningValidationResponse` |
| Provenance lookup | `GET /semantic/provenance/{resourceId}` | path parameter only | `ProvenanceLookupResponse` |
| Promotion review | `POST /semantic/promotion/review` | `PromotionReviewRequest` | `PromotionReviewResponse` |
| AI governance handoff | `POST /semantic/ai-governance/handoff` | `AIGovernanceHandoffRequest` | `AIGovernanceHandoffResponse` |

## DTO Boundary Rules

Future DTOs must:

- accept query IDs rather than arbitrary browser-supplied SPARQL
- reference graph scopes by controlled names
- keep validation findings explicit instead of hiding SHACL failure detail
- include provenance or graph release metadata where query output is returned
- keep promotion review separate from graph promotion
- keep AI governance handoff separate from approval or write execution

## Explicit Non-goals

Phase 9 does not:

- choose a Java/Kotlin web framework
- define authentication or authorization implementation
- define deployment behavior
- generate DTO classes or OpenAPI clients
- add route handlers or API tests
- execute SPARQL or write graph data
- change the current UI or old runtime

## Validation Commands

Run from the repository root.

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
    "semantic-service/*.ttl",
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
for endpoint in [
    "/semantic/query/{queryId}",
    "/semantic/reasoning/validate",
    "/semantic/provenance/{resourceId}",
    "/semantic/promotion/review",
    "/semantic/ai-governance/handoff",
]:
    assert endpoint in document["paths"], endpoint
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

Check API contract references:

```bash
rg -n "API contract|OpenAPI|DTO|request|response|query execution|reasoning validation|provenance lookup|promotion review|AI governance handoff|endpoint" docs/ontology-native/phase9_api_contract_scaffold.md semantic-service ontology/releases README.md
rg -n "QueryExecutionRequest|ReasoningValidationRequest|ProvenanceLookupResponse|PromotionReviewRequest|AIGovernanceHandoffRequest" semantic-service docs/ontology-native/phase9_api_contract_scaffold.md
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

Phase 9 is complete when the non-runtime API contract scaffold exists,
OpenAPI-style syntax parses, DTO documentation covers all five semantic service
use cases, release metadata references Phase 9, current RDF/SPARQL/SHACL checks
still pass, Phase 1 Compose still validates, and no Java/Kotlin service,
executable orchestration, UI redesign, old-runtime removal, commit, or push has
occurred.
