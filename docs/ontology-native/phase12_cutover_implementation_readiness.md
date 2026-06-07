# Phase 12 Cutover and Implementation Readiness

This document records the Phase 12 ontology-native rewrite checkpoint. It
decides how the old runtime is treated during the cutover and what must be true
before real semantic service endpoints or graph execution can begin.

This phase does not remove old runtime code, implement service endpoints,
execute graph operations, add Fuseki clients, add RDF ingestion, run reasoning
orchestration, redesign the UI, commit, or push.

## Checkpoint Decision

The old FastAPI/Postgres/SQLAlchemy/React runtime remains in the repository as
domain reference only until the ontology-native runtime can pass its own
readiness gates.

The old runtime must not be extended as the future semantic source of truth. New
implementation work after this checkpoint should target the ontology-native
runtime path: Jena/Fuseki/TDB2 named graphs, OWL/RDFS modules, SHACL validation,
approved SPARQL query files, reasoning outputs, provenance graphs, AI audit
graphs, and the Java/Kotlin semantic service.

## Old Runtime Remains as Reference

These existing areas remain intact for now because they contain useful domain
behavior, sample data, UX references, or verification examples:

| Area | Reference value | Cutover rule |
| --- | --- | --- |
| `backend/app/api/` | Existing follow-up and analytics response shape examples. | Reference only; do not add new ontology-native endpoints here. |
| `backend/app/models/`, `backend/alembic/` | Relational domain vocabulary and historical analytics materialization. | Reference only; do not treat SQL tables as the future source of truth. |
| `backend/app/pipeline/` | Source loading, reconciliation, stage reconstruction, and scoring behavior examples. | Reference only; future ingestion must map sources into RDF named graphs. |
| `backend/app/domain/semantic_*` and `ontology/*.ttl` | Earlier RDF/SHACL projection concepts and semantic query examples. | Reference only where compatible with Phase 1-11 ontology modules. |
| `backend/generated/sample_data/` and `fixtures/rdf/` | Operational scenario examples and fixture seeds. | Keep as fixture input until graph-native fixture coverage replaces it. |
| `frontend/src/` | Follow-up workflow UX reference. | Reference only; future UI should read semantic-service view models. |
| `docs/00_project_brief.md` through `docs/11_topology_semantic_connectors.md` | Product problem, operational workflow, source-system story, and earlier implementation rationale. | Reference only; Phase 12+ architecture docs govern new runtime decisions. |

## Remove Later

Removal should happen only after ontology-native parity and cutover approval.
These areas are expected to be deleted, retired, or moved to archived reference
docs later:

| Area | Removal trigger |
| --- | --- |
| FastAPI application runtime and old REST endpoints | Java/Kotlin semantic service exposes approved semantic endpoints with equivalent follow-up workflow support. |
| SQLAlchemy models, Alembic migrations, and SQL analytics materialization | RDF named graphs, SPARQL queries, SHACL validation, and reasoning outputs become the accepted source of truth. |
| Python RDF projection and optional graph-sync code | Graph-native ingestion, promotion, and reasoning execution replace projection-from-SQL behavior. |
| Old pipeline execution path | Source-to-canonical RDF mapping and graph promotion can load equivalent operational scenarios with provenance. |
| Current React dashboard runtime | Semantic operations UI can preserve the follow-up workflow against semantic-service view models. |
| Compatibility docs that describe SQL or FastAPI as authoritative | Ontology-native docs and runtime checks supersede them. |

The deletion phase must be a separate approved goal. This checkpoint does not
authorize deletion.

## Readiness Gates Before Semantic Endpoints

Real semantic service endpoints may start only after these gates pass:

1. Java runtime and Gradle are available locally or in CI, and the Phase 11
   contract-loading/static-validation tests run successfully.
2. `semantic-service/openapi.semantic-service.yaml` and
   `semantic-service/api-dtos.md` are reviewed as the endpoint/DTO contract.
3. Endpoint use cases remain limited to approved query execution, reasoning
   validation, provenance lookup, promotion review, and AI governance handoff.
4. Endpoint implementation forbids arbitrary browser-supplied SPARQL and
   arbitrary SPARQL Update.
5. Auth, graph-scope, timeout, result-size, and audit policy decisions are
   explicitly documented before exposing any HTTP route.
6. DTOs map graph-backed view models; they do not recreate SQL source-of-truth
   contracts.
7. Old FastAPI endpoints remain unchanged unless a separate cutover goal
   explicitly authorizes compatibility removal or routing changes.

## Readiness Gates Before Graph Execution

Fuseki/TDB2 graph execution, SPARQL execution, graph promotion, or reasoning
orchestration may start only after these gates pass:

1. Phase 1 Fuseki/TDB2 Compose configuration validates and the persistent TDB2
   volume strategy is accepted.
2. OWL/RDFS modules parse and the module boundaries remain stable enough for
   implementation.
3. SHACL shapes validate all valid fixtures and reject all invalid fixtures.
4. Query manifest metadata and SPARQL query files parse, and each executable
   query has an approved graph scope, parameter contract, timeout class, and
   result shape.
5. Reasoning output validation covers dependency impact, recovery blocker,
   follow-up decision, restore readiness, trust finding, blast radius, and
   reasoning activity provenance.
6. Graph promotion gates define source graphs, canonical graphs, inferred
   graphs, operations graphs, provenance graphs, and AI audit graphs.
7. Failure modes are documented for invalid source data, failed SHACL
   validation, failed reasoning validation, graph-store outage, stale named
   graphs, partial promotion, and rejected AI proposals.
8. A rollback or non-promotion path is defined before any code can write derived
   facts into approved graph state.

## Implementation Sequence After This Checkpoint

The next implementation work should follow this order:

1. Fix local or CI Java/Gradle availability so the semantic-service scaffold can
   run tests.
2. Add semantic-service contract tests that assert endpoint and graph execution
   boundaries remain non-SQL and graph-governed.
3. Implement read-only contract-backed query catalog loading before any HTTP
   endpoint.
4. Implement a Fuseki client behind an interface with test doubles before any
   real graph operation.
5. Add one read-only query endpoint for a low-risk approved query ID.
6. Add SHACL validation execution for fixture graphs.
7. Add reasoning validation and promotion-review flows.
8. Plan UI replacement only after semantic-service view models exist.

## Stop Conditions

Do not proceed into endpoint or graph execution implementation if any of these
conditions are true:

- Java or Gradle cannot run the semantic-service tests.
- The OpenAPI/DTO contract is still disputed.
- Query IDs, graph scopes, timeout policy, or update policy are undefined.
- SHACL fixture validation is failing.
- SPARQL placeholder parsing is failing.
- Provenance requirements for reasoning outputs are incomplete.
- The implementation would need to mutate or delete old runtime code without a
  separate cutover goal.

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

Check cutover and readiness references:

```bash
rg -n "cutover|implementation readiness|old runtime|reference only|remove later|semantic service endpoints|graph execution|readiness gate|FastAPI|SQLAlchemy|React|Java|Gradle" docs/ontology-native/phase12_cutover_implementation_readiness.md semantic-service ontology/releases README.md
```

Keep the Phase 1 runtime scaffold valid:

```bash
docker compose config
```

Check formatting:

```bash
git diff --check
```

## Phase 12 Completion Criteria

Phase 12 is complete when:

- the cutover/readiness checkpoint exists
- old runtime reference-only areas are identified
- later-removal areas and triggers are identified
- endpoint readiness gates are explicit
- graph execution readiness gates are explicit
- release metadata references Phase 12
- current RDF/OpenAPI/SPARQL/SHACL/Compose/diff checks pass
- no old runtime removal, endpoint implementation, graph execution, UI
  redesign, commit, or push has occurred
