# Ontology Modules

Phase 1 scaffold for the ontology-native rewrite.

This directory will hold the versioned OWL/RDFS modules that become the domain
contract for the graph-native platform. The current hybrid ontology files in
`ontology/` remain reference material until Phase 2 migrates domain semantics
into this module layout.

Planned modules:

- `core.ttl`
- `infrastructure.ttl`
- `topology.ttl`
- `workflow.ttl`
- `impact.ttl`
- `evidence.ttl`
- `provenance.ttl`
- `ai-interaction.ttl`
- `operations.ttl`

Phase 1 does not implement domain ontology logic here. It only establishes the
tracked directory boundary for the rewrite.
