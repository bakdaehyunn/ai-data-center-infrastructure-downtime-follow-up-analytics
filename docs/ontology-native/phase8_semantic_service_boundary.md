# Phase 8 Semantic Service Boundary Contract

This document records the Phase 8 ontology-native rewrite scaffold. It defines
a non-runtime semantic service boundary contract for a future Java/Kotlin
implementation.

This phase does not implement Java/Kotlin service runtime, executable reasoning
orchestration, RDF ingestion, graph promotion, scheduled jobs, API endpoints,
UI redesign, or old-runtime removal.

## Boundary Position

The future semantic service is a controlled facade over the ontology-native
graph system. It is not the source of truth.

Source of truth:

- Apache Jena Fuseki/TDB2 named graphs
- OWL/RDFS ontology modules
- SHACL shape graphs
- approved SPARQL query files
- provenance and AI audit graphs

The service boundary exists to control graph scope, query authorization,
validation gates, promotion review, AI governance handoff, timeouts, and stable
view-model mapping for future clients.

## Future Endpoint and Use Case Contract

These endpoint names are boundary placeholders. Phase 8 does not add route
handlers, controllers, clients, OpenAPI specs, or executable service code.

| Use case | Boundary endpoint | Responsibility |
| --- | --- | --- |
| Query execution | `POST /semantic/query/{queryId}` | Execute approved read-only SPARQL query IDs with controlled graph scope and timeout policy. |
| Reasoning validation | `POST /semantic/reasoning/validate` | Validate candidate reasoning outputs against SHACL shapes before promotion review. |
| Provenance lookup | `GET /semantic/provenance/{resourceId}` | Return lineage for canonical facts, reasoning findings, source records, and AI decisions. |
| Promotion review | `POST /semantic/promotion/review` | Review candidate findings from `urn:dcai:graph:reasoning-audit` against promotion gates. |
| AI governance handoff | `POST /semantic/ai-governance/handoff` | Hand AI-proposed graph changes or high-impact findings into approval/audit workflow. |

## Query Execution Boundary

Future query execution must:

- accept approved query identifiers, not arbitrary browser-supplied SPARQL
- load query metadata from `queries/manifest.ttl`
- execute only against allowed named graph scopes
- preserve configured timeout and result-size policy
- map results to stable DTO/view-model contracts in a future implementation
- record provenance or audit metadata when a query participates in reasoning,
  promotion review, or AI governance

The Phase 5 query files remain the current placeholder query inventory.

## Reasoning Validation Boundary

Future reasoning validation must:

- read candidate findings from `urn:dcai:graph:reasoning-audit`
- validate candidate findings with `shapes/reasoning-output-validation.ttl`
- validate source/canonical facts with existing SHACL shapes as needed
- reject candidate findings missing `prov:wasDerivedFrom`,
  `prov:wasGeneratedBy`, or `dcai:ReasoningActivity` lineage
- produce validation reports without promoting graph data directly

This boundary is a service facade over the Phase 6 execution contract and Phase
7 reasoning-output validation shapes.

## Provenance Lookup Boundary

Future provenance lookup must expose:

- source record lineage for canonical facts
- promotion activity lineage for canonical graph writes
- reasoning activity lineage for derived facts
- query file identity or hash for generated findings
- AI proposal, validation, approval, or rejection lineage where applicable

The lookup boundary is read-only. It must not repair or synthesize missing
provenance.

## Promotion Review Boundary

Future promotion review must:

- read candidate findings from the reasoning audit graph
- require successful reasoning-output SHACL validation
- require provenance and approval status
- keep previous approved reasoning graph state if review fails
- separate review decisions from query execution

Promotion review is not graph promotion code in Phase 8. It is the contract for
what a later promotion implementation must protect.

## AI Governance Handoff Boundary

Future AI governance handoff must:

- accept only structured AI proposals or high-impact findings
- validate proposed graph changes before approval
- keep AI-generated writes in audit graphs until approved
- record policy/operator approval or rejection
- never bypass SHACL validation, provenance requirements, or promotion gates

This boundary is where future AI interaction work connects to graph governance.

## Explicit Non-goals

Phase 8 does not:

- choose Spring Boot, Ktor, Micronaut, Quarkus, or any Java/Kotlin framework
- define authentication, authorization, or deployment implementation
- implement HTTP routes, DTOs, OpenAPI, clients, queues, schedulers, or jobs
- execute SPARQL against Fuseki
- promote graph data
- replace or remove the existing old runtime

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

Check service boundary references:

```bash
rg -n "semantic service boundary|Java/Kotlin|query execution|reasoning validation|provenance lookup|promotion review|AI governance handoff|endpoint|use case" docs/ontology-native/phase8_semantic_service_boundary.md semantic-service ontology/releases README.md
rg -n "queries/manifest.ttl|reasoning-output-validation|reasoning-audit|provenance|promotion gates|Fuseki|TDB2" docs/ontology-native/phase8_semantic_service_boundary.md semantic-service docs/ontology-native/phase6_reasoning_execution_contract.md docs/ontology-native/phase7_reasoning_output_validation.md
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

Phase 8 is complete when the non-runtime semantic service boundary contract
exists, contract metadata parses, endpoint/use-case boundaries cover query
execution, reasoning validation, provenance lookup, promotion review, and AI
governance handoff, the release manifest references Phase 8, current
RDF/SPARQL/SHACL checks still pass, Phase 1 Compose still validates, and no
Java/Kotlin service, executable orchestration, UI redesign, old-runtime
removal, commit, or push has occurred.
