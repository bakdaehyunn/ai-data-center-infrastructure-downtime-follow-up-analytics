# Topology, Semantic Graph, And Connectors

## Topology Graph

Topology is represented as RDF dependency paths and dependency edges. The
dashboard consumes topology through approved semantic read models, especially
`semanticTopologyDependencies`, `semanticDependencyImpactByAsset`, and
`semanticBlastRadiusByAsset`.

The intended dependency vocabulary covers paths such as:

```text
rack -> PDU -> UPS -> switchgear -> generator
rack -> CRAH/CDU/chiller
```

Topology should stay focused on explaining dependency impact, not replacing the
follow-up queue as the primary product workflow.

## Semantic Graph Runtime

- Fuseki/TDB2 stores named graphs.
- `ontology/modules/` defines OWL/RDFS vocabulary.
- `shapes/` validates source, canonical, topology, evidence, provenance,
  reasoning, and AI governance contracts.
- `queries/manifest.ttl` approves executable query IDs.
- `semantic-service/` executes approved read-only queries and shapes typed
  response envelopes.

## Connector Direction

Production connectors should map external extracts into RDF named graphs with
source-record provenance. A connector is not trusted just because it loads
data; it must pass parse, SHACL, provenance, and promotion gates before product
read models depend on it.

Required connector contract areas:

- incidents
- workflow events
- work orders and spares
- validation results
- telemetry alerts and readings
- impact observations
- topology dependencies
- source system provenance
