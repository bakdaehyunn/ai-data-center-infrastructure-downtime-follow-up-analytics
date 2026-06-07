# Phase 3 RDF Fixtures and Graph Promotion Scaffold

This document records the Phase 3 ontology-native rewrite scaffold. It adds
RDF fixture files, source-to-canonical mapping documentation, graph promotion
documentation, query-manifest references, and validation commands. It does not
implement executable ingestion, graph promotion, reasoning, Java/Kotlin service
runtime, UI redesign, or old-runtime removal.

## RDF Fixtures

Valid fixtures:

- `fixtures/rdf/valid/minimal-incident.ttl`
- `fixtures/rdf/valid/dependency-path.ttl`
- `fixtures/rdf/valid/evidence-provenance.ttl`

Invalid fixtures:

- `fixtures/rdf/invalid/missing-asset-link.ttl`
- `fixtures/rdf/invalid/unknown-workflow-stage.ttl`
- `fixtures/rdf/invalid/ai-proposed-write.ttl`

## Source-to-Canonical Mapping Scaffold

The mapping scaffold is documented in `rdf-mapping/README.md`.

Target flow:

```text
source extract
  -> source graph
  -> source SHACL validation
  -> canonical graph promotion
  -> provenance graph write
```

Phase 3 only documents that flow. It does not add executable mapping or
promotion code.

## Graph Promotion Scaffold

Future graph promotion should use these boundaries:

- `urn:dcai:graph:source`: raw source-shaped facts and source records
- `urn:dcai:graph:canonical`: validated operational facts
- `urn:dcai:graph:provenance`: source lineage and promotion activity
- `urn:dcai:graph:ai-audit`: AI proposed writes and approval records

Promotion requirements:

- Source graph must validate before canonical promotion.
- Invalid source facts remain source validation findings.
- Canonical graph must remain last-known-good when validation fails.
- Provenance is required for promoted facts.
- AI proposed writes must validate before promotion and remain auditable.

## Query Manifest References

`queries/manifest.ttl` now includes Phase 3 placeholder query entries for:

- source-to-canonical promotion
- fixture conformance validation
- invalid fixture expectation validation
- provenance lineage lookup

The manifest entries are metadata placeholders only. They do not implement
SPARQL query files or runtime query behavior.

## Validation Commands

Run from the repository root.

Parse all RDF artifacts:

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
]
for pattern in patterns:
    for path in sorted(Path().glob(pattern)):
        graph = Graph()
        graph.parse(path, format="turtle")
        print(f"{path}: {len(graph)} triples")
PY
```

Run SHACL validation for current skeleton shapes:

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

valid = sorted(Path("fixtures/rdf/valid").glob("*.ttl"))
invalid = sorted(Path("fixtures/rdf/invalid").glob("*.ttl"))

for path in valid:
    data = Graph()
    data.parse(path, format="turtle")
    conforms, _, _ = validate(data, shacl_graph=shapes, ont_graph=ontology, inference="rdfs")
    assert conforms, f"Expected valid fixture to conform: {path}"
    print(f"valid conforms: {path}")

for path in invalid:
    data = Graph()
    data.parse(path, format="turtle")
    conforms, _, _ = validate(data, shacl_graph=shapes, ont_graph=ontology, inference="rdfs")
    assert not conforms, f"Expected invalid fixture to fail: {path}"
    print(f"invalid fails as expected: {path}")
PY
```

Check scaffold references:

```bash
rg -n "minimal-incident|dependency-path|evidence-provenance|missing-asset-link|unknown-workflow-stage|ai-proposed-write" fixtures/rdf docs/ontology-native/phase3_rdf_mapping_graph_promotion.md
rg -n "source-to-canonical|graph promotion|source graph|canonical graph|provenance|query manifest" rdf-mapping docs/ontology-native/phase3_rdf_mapping_graph_promotion.md queries/manifest.ttl ontology/releases
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

Phase 3 is complete when valid and invalid RDF fixtures parse, valid fixtures
conform against the current skeleton shapes, invalid fixtures fail against the
current skeleton shapes, mapping and graph promotion docs are ready for review,
Phase 3 release/query metadata exists, Phase 1 Compose still validates, and no
runtime implementation or old-runtime removal has occurred.
