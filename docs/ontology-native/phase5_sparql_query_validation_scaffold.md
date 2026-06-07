# Phase 5 SPARQL Query Validation Scaffold

This document records the Phase 5 ontology-native rewrite scaffold. It adds
parseable placeholder SPARQL query files and a non-runtime validation helper for
future reasoning outputs.

This phase does not implement Java/Kotlin service runtime, executable reasoning
orchestration, RDF ingestion, graph promotion, production reasoning, UI
redesign, or old-runtime removal.

## Query Files

The Phase 5 placeholder queries live under `queries/reasoning/`:

- `dependency_exposure.construct.rq`
- `recovery_blocker.construct.rq`
- `restore_readiness.construct.rq`
- `impact_trust.construct.rq`
- `blast_radius.construct.rq`
- `reasoning_finding_lineage.select.rq`

The `CONSTRUCT` files produce placeholder derived fact shapes for the future
reasoning graph. The `SELECT` file describes future reasoning lineage lookup.
They are syntactically parseable SPARQL, but they are not wired into a service,
scheduled job, graph promotion step, or reasoning orchestrator.

## Non-runtime Validation Scaffold

`queries/validate_sparql.py` parses every `queries/reasoning/*.rq` file through
the current Python RDF/SPARQL tooling. It is a developer verification helper
only; it does not execute queries against Fuseki and does not write graph data.

## Query-to-Output Contract

| Query | Future output |
| --- | --- |
| `dependency_exposure.construct.rq` | `dcai:DependencyImpactFinding` |
| `recovery_blocker.construct.rq` | `dcai:RecoveryBlocker` and `dcai:FollowUpDecision` |
| `restore_readiness.construct.rq` | `dcai:RestoreReadinessFinding` |
| `impact_trust.construct.rq` | `dcai:TrustFinding` |
| `blast_radius.construct.rq` | `dcai:BlastRadiusFinding` |
| `reasoning_finding_lineage.select.rq` | lineage rows for approved reasoning facts |

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

Run SHACL validation for current fixture expectations:

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
    conforms, _, _ = validate(data, shacl_graph=shapes, ont_graph=ontology, inference="rdfs")
    assert conforms, f"Expected valid fixture to conform: {path}"
    print(f"valid conforms: {path}")

for path in sorted(Path("fixtures/rdf/invalid").glob("*.ttl")):
    data = Graph()
    data.parse(path, format="turtle")
    conforms, _, _ = validate(data, shacl_graph=shapes, ont_graph=ontology, inference="rdfs")
    assert not conforms, f"Expected invalid fixture to fail: {path}"
    print(f"invalid fails as expected: {path}")
PY
```

Check query scaffold references:

```bash
rg -n "dependency exposure|recovery blocker|restore readiness|impact trust|blast radius|reasoning lineage|query validation" docs/ontology-native/phase5_sparql_query_validation_scaffold.md queries reasoning ontology/releases
rg -n "DependencyImpactFinding|RecoveryBlocker|FollowUpDecision|RestoreReadinessFinding|TrustFinding|BlastRadiusFinding|ReasoningActivity" queries/reasoning ontology/modules docs/ontology-native/phase5_sparql_query_validation_scaffold.md
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

Phase 5 is complete when placeholder SPARQL query files exist and parse,
non-runtime query validation docs/helper exist, query/release metadata references
Phase 5, current RDF and SHACL fixture expectations still pass, Phase 1 Compose
still validates, and no Java/Kotlin service, executable reasoning
orchestration, UI redesign, old-runtime removal, commit, or push has occurred.
