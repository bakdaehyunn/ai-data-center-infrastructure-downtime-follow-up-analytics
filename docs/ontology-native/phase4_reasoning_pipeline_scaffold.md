# Phase 4 Reasoning Pipeline Scaffold

This document records the Phase 4 ontology-native rewrite scaffold. It adds
reasoning pipeline documentation, placeholder rule/query structure, fixture
expectations, query-manifest references, release metadata, and verification
commands.

This phase does not implement executable reasoning, production SPARQL rule
logic, RDF ingestion, graph promotion, Java/Kotlin service runtime, UI redesign,
or old-runtime removal.

## Reasoning Pipeline Boundary

Target flow:

```text
canonical graph
  -> reasoning candidate generation
  -> reasoning audit graph
  -> SHACL/provenance validation
  -> approved reasoning graph
  -> semantic API facade in a later phase
```

Phase 4 only documents that flow. It does not add executable rule code.

## Reasoning Outputs

The scaffold defines five future reasoning outputs:

- dependency exposure: future `dcai:DependencyImpactFinding` facts that explain
  dependency path exposure for power, cooling, telemetry, redundancy, and GPU
  capacity impact.
- recovery blocker: future `dcai:RecoveryBlocker` and `dcai:FollowUpDecision`
  facts that identify the current blocker and next operational action.
- restore readiness: future `dcai:RestoreReadinessFinding` facts that explain
  whether validation, mitigation, evidence, and dependency state support
  return-to-service readiness.
- impact trust: future `dcai:TrustFinding` facts that separate trusted,
  unsupported, stale, contradictory, and low-confidence impact context.
- blast radius: future `dcai:BlastRadiusFinding` facts that identify affected
  downstream assets, zones, dependency paths, GPU capacity, and redundancy
  exposure.

## Placeholder Artifacts

- `reasoning/README.md`
- `reasoning/manifest.ttl`
- `reasoning/rules/README.md`
- `queries/reasoning/README.md`
- `queries/manifest.ttl`
- `ontology/releases/2026-06-phase4-reasoning-pipeline-scaffold.ttl`

The manifest and release files are parseable Turtle metadata. The README files
reserve future executable rule and query paths without implementing them.

## Fixture Expectations

Current Phase 3 fixtures are sufficient for scaffold-level reasoning
expectations:

- `fixtures/rdf/valid/minimal-incident.ttl`: future recovery blocker and
  follow-up decision reasoning.
- `fixtures/rdf/valid/dependency-path.ttl`: future dependency exposure and
  blast-radius reasoning.
- `fixtures/rdf/valid/evidence-provenance.ttl`: future restore readiness and
  impact trust reasoning.
- `fixtures/rdf/invalid/missing-asset-link.ttl`: future blocker that prevents
  canonical promotion and therefore prevents reasoning output generation.
- `fixtures/rdf/invalid/unknown-workflow-stage.ttl`: future blocker that
  prevents workflow-stage reasoning.
- `fixtures/rdf/invalid/ai-proposed-write.ttl`: future AI governance and trust
  failure expectation.

## Query Manifest References

`queries/manifest.ttl` includes Phase 4 placeholder query entries for:

- dependency exposure reasoning
- recovery blocker reasoning
- restore readiness reasoning
- impact trust reasoning
- blast-radius reasoning
- reasoning finding lineage lookup

The query entries are metadata placeholders only.

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

Check reasoning scaffold references:

```bash
rg -n "reasoning pipeline|dependency exposure|recovery blocker|restore readiness|impact trust|blast radius|fixture expectations|validation commands" docs/ontology-native/phase4_reasoning_pipeline_scaffold.md reasoning queries/manifest.ttl ontology/releases
rg -n "DependencyImpactFinding|RecoveryBlocker|RestoreReadinessFinding|TrustFinding|BlastRadiusFinding|ReasoningActivity" ontology/modules reasoning docs/ontology-native/phase4_reasoning_pipeline_scaffold.md
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

Phase 4 is complete when reasoning pipeline scaffold docs and placeholder
metadata parse, query/release metadata references the five reasoning outputs,
fixture expectations and validation commands are documented, Phase 1 Compose
still validates, and no executable reasoning, Java/Kotlin service, UI redesign,
old-runtime removal, commit, or push has occurred.
