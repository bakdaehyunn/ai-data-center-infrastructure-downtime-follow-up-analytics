# Phase 6 Reasoning Execution Contract

This document records the Phase 6 ontology-native rewrite scaffold. It defines
a non-runtime contract for running the Phase 5 SPARQL reasoning queries in a
future implementation phase.

This phase does not implement Java/Kotlin service runtime, executable reasoning
orchestration, RDF ingestion, graph promotion, scheduled jobs, API endpoints,
UI redesign, or old-runtime removal.

## Contract Purpose

Phase 5 made the reasoning queries parseable. Phase 6 defines the execution
rules those queries must follow later:

- which named graphs they can read
- where candidate findings should be written
- when candidate findings can be promoted
- what provenance every promoted finding requires
- how failure modes should be handled
- which future service boundaries own execution, exposure, and governance

## Graph Inputs and Outputs

| Contract role | Named graph | Purpose |
| --- | --- | --- |
| Primary input | `urn:dcai:graph:canonical` | Validated operational facts promoted from source records. |
| Lineage input | `urn:dcai:graph:provenance` | Source, promotion, and future reasoning activity lineage. |
| Candidate output | `urn:dcai:graph:reasoning-audit` | Candidate findings, query version, evidence links, validation reports, and rejected findings. |
| Approved output | `urn:dcai:graph:reasoning` | Approved derived facts that semantic APIs can expose later. |

Future execution must not write directly from a Phase 5 `CONSTRUCT` query into
the approved reasoning graph. Candidate output must pass gates first.

## Phase 5 Query Execution Boundary

The future reasoning runner may execute these Phase 5 query files:

- `queries/reasoning/dependency_exposure.construct.rq`
- `queries/reasoning/recovery_blocker.construct.rq`
- `queries/reasoning/restore_readiness.construct.rq`
- `queries/reasoning/impact_trust.construct.rq`
- `queries/reasoning/blast_radius.construct.rq`
- `queries/reasoning/reasoning_finding_lineage.select.rq`

The five `CONSTRUCT` queries are candidate-producing queries. The lineage
`SELECT` query is read-only and must not change graph state.

## Promotion Gates

Future candidate findings must pass these gates before promotion:

- canonical conformance gate: canonical graph is the last-known-good graph and
  passes SHACL validation for the relevant fixture contract.
- SPARQL parse gate: the query file parses before execution.
- reasoning output shape gate: constructed findings use the expected ontology
  classes and required evidence/provenance properties.
- provenance required gate: every finding records source facts and a future
  `dcai:ReasoningActivity`.
- human or policy approval gate: AI-generated or high-impact findings remain in
  the audit graph until approved by policy or operator review.

Promotion must be all-or-nothing for a reasoning run. If any gate fails, the
previous approved reasoning graph remains last-known-good.

## Provenance Requirements

Every approved reasoning finding must eventually include:

- the query file path and version or content hash
- the reasoning run identifier
- the input graph release identifier
- source facts through `prov:wasDerivedFrom`
- generation activity through `dcai:ReasoningActivity`
- validation status for the candidate output graph
- approval status for high-impact or AI-governed findings

Phase 6 only documents those requirements. It does not add provenance-writing
code.

## Failure Modes

Future execution must handle these failure modes explicitly:

- stale canonical graph: do not run reasoning against an old or unpromoted
  canonical graph unless the run is marked audit-only.
- invalid canonical graph: stop before query execution.
- query parse failure: stop before query execution and preserve previous
  approved reasoning graph.
- empty reasoning output: record an audit result, but do not treat it as a
  successful operational finding without policy.
- missing provenance: reject candidate promotion.
- conflicting finding: keep candidates in the audit graph for operator or
  policy resolution.

## Expected Service Boundaries

Future implementation should keep these boundaries separate:

- reasoning runner: loads approved query files, runs them against Fuseki/TDB2,
  writes candidate findings to the reasoning audit graph, and records run
  status.
- promotion gate service: validates candidate output, checks provenance and
  policy, and promotes approved findings to the reasoning graph.
- semantic API facade: reads approved reasoning findings and lineage only; it
  does not run reasoning.
- AI governance layer: reviews AI-proposed writes or high-impact findings,
  records approvals/rejections, and never bypasses SHACL/provenance gates.

No boundary is implemented in Phase 6.

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

Check contract references:

```bash
rg -n "graph inputs|graph outputs|promotion gates|provenance requirements|failure modes|service boundaries|reasoning execution contract|Phase 5" docs/ontology-native/phase6_reasoning_execution_contract.md reasoning ontology/releases README.md
rg -n "canonical|reasoning-audit|reasoning graph|ReasoningActivity|dependency_exposure|recovery_blocker|restore_readiness|impact_trust|blast_radius|reasoning_finding_lineage" docs/ontology-native/phase6_reasoning_execution_contract.md reasoning queries/reasoning
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

Phase 6 is complete when the non-runtime reasoning execution contract exists,
contract metadata parses, graph inputs/outputs, promotion gates, provenance
requirements, failure modes, and service boundaries are documented, the
contract references the Phase 5 query files, current RDF/SPARQL/SHACL checks
still pass, Phase 1 Compose still validates, and no Java/Kotlin service,
executable orchestration, UI redesign, old-runtime removal, commit, or push has
occurred.
