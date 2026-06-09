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
  subclasses
- incident source records map to `dcai:InfrastructureIncident`
- topology source records map to `dcai:DependencyEdge` and
  `dcai:DependencyPath` subclasses
- workflow event source records map to `dcai:WorkflowEvent`
- telemetry, validation, and work-order evidence source records map to
  evidence subclasses
- impact source records map to `dcai:ImpactObservation`

## Promotion Rules

- Source graph validation must run before canonical promotion.
- Failed validation must not mutate the canonical graph.
- Canonical graph facts must preserve source lineage with PROV-O-compatible
  provenance.
- Promotion writes are limited to managed `urn:dcai:graph:source:*`,
  `urn:dcai:graph:canonical:*`, and `urn:dcai:graph:provenance:*` graph URIs.
- Promotion snapshots existing target graphs and restores or deletes them on a
  failed multi-graph write.
- Derived facts are out of scope for Phase 3 and belong to the later reasoning
  scaffold phase.

## Non-Goals

- No frontend redesign.
- No public semantic API expansion.
- No raw SPARQL exposure.
- No executable reasoning or AI governance workflow.
- No old FastAPI/Postgres/SQLAlchemy runtime restoration.
