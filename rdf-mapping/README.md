# Source-to-Canonical RDF Mapping

Phase 3 added mapping documentation only. The production ingestion v1 slice now
adds executable Kotlin source extract DTOs, RDF mapping, SHACL/provenance
validation, controlled source/canonical/provenance graph promotion, and rollback
tests in `semantic-service`.

## Mapping Boundary

The mapper converts source extracts into RDF facts in the source graph. The
combined source, canonical, and provenance candidate graph is validated before
canonical graph promotion occurs.

```text
source extract record
  -> source RDF facts in urn:dcai:graph:source
  -> source/canonical/provenance SHACL and provenance validation
  -> canonical RDF facts in urn:dcai:graph:canonical
  -> provenance records in urn:dcai:graph:provenance
```

Recorded connector simulation v1 adds a local adapter layer before this mapper:

```text
local recorded source-system CSV exports
  -> connector-style row validation and quarantine report
  -> SourceExtractBatch DTOs
  -> existing source/canonical/provenance RDF mapper and promotion lifecycle
```

This adapter is deterministic and local-only. It simulates source-system exports
without adding a real external connector or bypassing managed graph gates.
Seeded recorded scenario generation v1 can create these local exports at demo,
MVP, and stress sizes before the same adapter and mapper run.
AI data center ontology hardening v1 extends the canonical mapping with
controlled vocabulary resources and deeper topology facts for facility halls,
rows, racks, GPU capacity groups, power assets, cooling dependencies,
telemetry bridges, workflow states, evidence confidence, validation status, and
work-order status.

## Initial Source Families

- incident source records map to `dcai:InfrastructureIncident`
- asset source records map to `dcai:InfrastructureAsset`
- zone source records map to `dcai:InfrastructureZone`
- topology source records map to `dcai:DependencyEdge` and `dcai:DependencyPath`
- evidence source records map to `dcai:EvidenceRecord` subclasses
- impact source records map to `dcai:ImpactObservation`
- AI proposal records map to `dcai:ProposedTripleSet` in the AI audit graph

Implemented v1 source families:

- facility source records map to `dcai:Facility`
- zone source records map to `dcai:InfrastructureZone`
- asset source records map to `dcai:InfrastructureAsset` and supported asset
  subclasses such as UPS, PDU, chilled-water loop, telemetry bridge, and GPU
  pod where the source `assetType` supports it
- incident source records map to `dcai:InfrastructureIncident`
- topology source records map to `dcai:DependencyEdge` and
  `dcai:DependencyPath` subclasses
- workflow event source records map to `dcai:WorkflowEvent`
- telemetry, validation, and work-order evidence source records map to
  evidence subclasses
- impact source records map to `dcai:ImpactObservation`
- optional hall, row, rack, and capacity group source fields map to
  `dcai:DataHall`, `dcai:InfrastructureRow`, `dcai:Rack`, and
  `dcai:ComputeCapacityGroup`/`dcai:GpuPod`
- operational string states are preserved and also mapped to typed controlled
  vocabulary resources, including criticality, operational status, incident
  stage, workflow event status, dependency role, impact scope, redundancy,
  mitigation, vendor, evidence confidence, telemetry, validation, and
  work-order status

## Promotion Rules

- Source graph validation must run before canonical promotion.
- Failed validation must not mutate the canonical graph.
- Canonical graph facts must preserve source lineage with PROV-O-compatible
  provenance.
- Promotion writes are limited to managed `urn:dcai:graph:source:*`,
  `urn:dcai:graph:canonical:*`, and `urn:dcai:graph:provenance:*` graph URIs.
- Promotion snapshots existing target graphs and restores or deletes them on a
  failed multi-graph write.
- Recorded connector simulation rows must pass adapter-level field parsing and
  duplicate natural-key checks before they can enter the canonical promotion
  lifecycle.
- Generated recorded scenarios must be deterministic by profile and seed, and
  must remain compatible with the same source-to-canonical mapper rather than a
  separate ingestion path.
- Derived facts are produced by the separate internal reasoning lifecycle, not
  by the source-to-canonical mapper.

## Non-Goals

- No frontend redesign.
- No public semantic API expansion.
- No raw SPARQL exposure.
- No AI governance workflow.
- No old FastAPI/Postgres/SQLAlchemy runtime restoration.
