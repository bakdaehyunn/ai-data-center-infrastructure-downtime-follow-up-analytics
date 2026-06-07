# Architecture

## Flow

```text
scattered AI infrastructure source records
  -> source-to-canonical RDF mappings
  -> named RDF graphs in Fuseki/TDB2
  -> OWL/RDFS ontology modules
  -> SHACL validation gates
  -> approved read-only SPARQL queries
  -> Kotlin/JVM semantic-service
  -> React follow-up dashboard
```

The RDF graph store is the source of truth. The semantic-service is the
controlled application boundary over approved query IDs, typed result
envelopes, provenance, and semantic error contracts.

## Source System Integration Model

The project models source families that are commonly fragmented in AI data
center operations:

| Source family | Canonical semantic target | Operational question answered | Trust risk |
| --- | --- | --- | --- |
| Incident system | `dcai:InfrastructureIncident` | What is open, which asset and zone are affected, and what state is current? | Missing required fields, stale current stage, duplicate source incident |
| Workflow event history | workflow stages and evidence records | Which state transitions actually happened and when? | Missing stage evidence, event before incident report, state mismatch |
| Facility work orders | `dcai:WorkOrderEvidence` | Who owns repair work and whether work is waiting, started, or complete? | Work order without incident, waiting state without spare evidence |
| Spare and inventory context | work-order spare fields and blocker findings | Is the blocker stock, critical spare availability, or vendor dispatch? | Out-of-stock spare, missing required spare link |
| Vendor ETA context | impact/vendor state fields | Is external recovery late, confirmed, or not required? | ETA in the past without missed status, event/snapshot mismatch |
| Telemetry | `dcai:TelemetryEvidence` | Is thermal, power, or redundancy exposure supported by monitoring evidence? | Alert without known asset, thermal breach without abnormal reading |
| Validation and impact | `dcai:ValidationEvidence` and `dcai:ImpactObservation` | Is return-to-service safe, and how much rack/GPU/capacity exposure remains? | Validation before completed work, stale or missing impact snapshot |
| Infrastructure topology | dependency paths and dependency impact findings | Which upstream power, cooling, telemetry, or redundancy assets does an affected asset depend on? | Missing asset reference, invalid dependency type, stale topology extract |

Each source is mapped into canonical RDF with source-record provenance. Graph
promotion requires parseable RDF, SHACL conformance, and provenance links.

## Runtime Responsibilities

- Fuseki/TDB2 stores persistent named RDF graphs.
- OWL/RDFS modules define the domain vocabulary.
- SHACL shapes validate canonical, evidence, topology, provenance, reasoning,
  and AI interaction contracts.
- Approved SPARQL files under `queries/` define read models.
- `queries/manifest.ttl` is the allowlist for executable query IDs.
- The Kotlin/JVM semantic-service loads contracts, reads Fuseki graphs,
  executes approved read-only SPARQL, shapes typed envelopes, serializes
  semantic responses, and rejects unapproved query IDs.
- The React dashboard preserves the follow-up workflow UX while reading from
  the semantic-service private endpoint.

## Design Choices

### RDF as Runtime Authority

The old relational backend has been removed from the active source tree.
Current product reads must come from named graphs and approved semantic-service
queries.

### Approved Query Boundary

The service executes query IDs, not arbitrary browser-supplied SPARQL. This
keeps graph access inspectable, testable, and safe for a future private API.

### Provenance as Product Data

Follow-up rows, evidence details, trust findings, topology dependencies, and
reasoning outputs carry graph/source provenance so operators can see why a
decision is trusted or needs review.

### Follow-Up Workflow First

The UI should not become an ontology diagram for its own sake. It exposes
semantic evidence where it supports the field decision: which incident to chase
next, what is blocking recovery, whether impact evidence is trustworthy, and
which dependencies increase operational exposure.
