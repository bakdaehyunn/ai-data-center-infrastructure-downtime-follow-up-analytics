# SHACL Shapes

Phase 1 scaffold for the ontology-native rewrite.

This directory will hold SHACL shape graphs used to validate source, canonical,
workflow, topology, impact/evidence, provenance, and AI-proposed graph writes.

Planned shape files:

- `source-required-fields.ttl`
- `canonical-integrity.ttl`
- `workflow-transitions.ttl`
- `topology-integrity.ttl`
- `impact-evidence.ttl`
- `provenance-required.ttl`
- `ai-proposed-write.ttl`
- `reasoning-output-validation.ttl`

Phase 7 adds reasoning output validation for future derived findings and
`dcai:ReasoningActivity` provenance. It remains scaffold validation only and
does not implement a reasoning runtime.
