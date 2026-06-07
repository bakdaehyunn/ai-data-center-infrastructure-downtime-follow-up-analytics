# Phase 7 Reasoning Output Validation

This document records the Phase 7 ontology-native rewrite scaffold. It adds
SHACL shapes and fixture expectations for validating future reasoning outputs.

This phase does not implement Java/Kotlin service runtime, executable reasoning
orchestration, RDF ingestion, graph promotion, scheduled jobs, API endpoints,
UI redesign, or old-runtime removal.

## Validation Boundary

Phase 7 validates the output contract for future reasoning findings produced by
the Phase 5 SPARQL queries and governed by the Phase 6 execution contract.

Covered classes:

- `dcai:DependencyImpactFinding`
- `dcai:RecoveryBlocker`
- `dcai:FollowUpDecision`
- `dcai:RestoreReadinessFinding`
- `dcai:TrustFinding`
- `dcai:BlastRadiusFinding`
- `dcai:ReasoningActivity`

## Shape File

`shapes/reasoning-output-validation.ttl` adds:

- finding summary requirements for reasoning findings
- recommended action requirement for follow-up decisions
- source-fact lineage through `prov:wasDerivedFrom`
- generation lineage through `prov:wasGeneratedBy`
- `dcai:ReasoningActivity` requirements for `prov:used`,
  `prov:generated`, and `prov:generatedAtTime`

The shapes are intentionally strict enough to reject candidate findings that
cannot explain what source facts and reasoning activity produced them.

## Fixture Expectations

Valid fixture:

- `fixtures/rdf/valid/reasoning-output.ttl`: includes all target reasoning
  output classes and a `dcai:ReasoningActivity` that uses source facts and
  generates each finding.

Invalid fixture:

- `fixtures/rdf/invalid/reasoning-output-missing-provenance.ttl`: includes a
  `dcai:DependencyImpactFinding` without required `prov:wasDerivedFrom` or
  `prov:wasGeneratedBy` lineage.

Existing fixture updated:

- `fixtures/rdf/valid/evidence-provenance.ttl`: the existing trust finding now
  has explicit `prov:wasDerivedFrom` lineage, and its reasoning activity records
  the generated finding.

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

Check reasoning validation references:

```bash
rg -n "DependencyImpactFinding|RecoveryBlocker|FollowUpDecision|RestoreReadinessFinding|TrustFinding|BlastRadiusFinding|ReasoningActivity" shapes/reasoning-output-validation.ttl fixtures/rdf docs/ontology-native/phase7_reasoning_output_validation.md
rg -n "reasoning output validation|fixture expectations|wasDerivedFrom|wasGeneratedBy|prov:used|prov:generated" shapes fixtures/rdf docs/ontology-native/phase7_reasoning_output_validation.md ontology/releases README.md
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

Phase 7 is complete when reasoning output validation shapes parse, valid
reasoning output fixtures conform, invalid reasoning output fixtures fail,
current RDF/SPARQL/SHACL checks still pass, release metadata references Phase 7,
Phase 1 Compose still validates, and no Java/Kotlin service, executable
orchestration, UI redesign, old-runtime removal, commit, or push has occurred.
