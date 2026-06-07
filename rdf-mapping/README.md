# Source-to-Canonical RDF Mapping Scaffold

Phase 3 adds mapping documentation only. It does not implement executable RDF
ingestion or graph promotion code.

## Mapping Boundary

The future mapper converts source extracts into RDF facts in the source graph.
Those source facts are validated before any canonical graph promotion occurs.

```text
source extract record
  -> source RDF facts in urn:dcai:graph:source
  -> source SHACL validation
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

## Promotion Rules

- Source graph validation must run before canonical promotion.
- Failed validation must not mutate the canonical graph.
- Canonical graph facts must preserve source lineage with PROV-O-compatible
  provenance.
- Derived facts are out of scope for Phase 3 and belong to the later reasoning
  scaffold phase.

## Non-Goals

- No Java/Kotlin semantic service code.
- No executable RDF ingestion.
- No SPARQL promotion implementation.
- No old FastAPI/Postgres/SQLAlchemy runtime removal.
