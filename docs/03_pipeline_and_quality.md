# Graph Pipeline And Quality

The active pipeline direction is graph-native:

```text
source extract or fixture
  -> source-to-canonical RDF mapping
  -> source named graph
  -> SHACL/provenance validation
  -> canonical named graph promotion
  -> approved SPARQL read model
  -> semantic-service response envelope
```

## Quality Gates

- RDF files parse as Turtle.
- Ontology modules parse and remain versioned.
- SHACL shapes validate canonical graph structure, evidence links,
  provenance, topology, reasoning outputs, and AI governance boundaries.
- Query files parse as SPARQL and remain read-only unless explicitly marked as
  future reasoning scaffolds.
- Query IDs are approved through `queries/manifest.ttl`.
- Kotlin result shapers reject missing required bindings.
- The semantic response serializer emits stable success and error envelopes.

## Trust Model

Trust is product data. A follow-up decision should expose whether its graph
facts came from source records, validation evidence, telemetry evidence,
work-order evidence, impact observations, or reasoning findings.

The dashboard should prefer graph-backed fields. Compatibility defaults are
temporary and should be removed as RDF fixtures and SPARQL read models gain
field-level parity.

## Current Verification

```bash
docker run --rm \
  -v "$PWD":/workspace \
  -w /workspace/semantic-service \
  gradle:8.10.2-jdk17 \
  gradle --no-daemon test

PYTHONPATH=/tmp/dcai-rdf-tools python3 queries/validate_sparql.py

cd frontend
npm run build
```
