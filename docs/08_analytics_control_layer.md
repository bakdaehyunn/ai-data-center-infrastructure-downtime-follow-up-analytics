# Semantic Analytics Control Layer

The analytics control layer is now expressed as ontology modules, SHACL
contracts, approved SPARQL read models, and Kotlin result envelopes.

## Control Responsibilities

- reconstruct follow-up state from canonical graph facts
- rank active follow-up queue items
- expose impact, redundancy, capacity, GPU, vendor, mitigation, telemetry,
  validation, and work-order evidence
- separate trusted facts from findings that need review
- preserve source-record and reasoning provenance
- keep graph access behind approved query IDs

## Current Read Models

- `semanticDashboardOverview`
- `semanticFollowUpQueueList`
- `semanticFilterMetadata`
- `semanticFollowUpDetail`
- `semanticImpactSummary`
- `semanticTopologyDependencies`
- `semanticTrustFindingList`
- `semanticStageBottlenecks`
- `semanticAssetDelaySummary`
- `semanticZoneDelaySummary`
- `semanticSpareWaitSummary`
- `semanticValidationSummary`
- `semanticIncidentEvidence`
- `semanticIncidentTimeline`
- `semanticDependencyImpactByAsset`
- `semanticBlastRadiusByAsset`

## Remaining Control Gaps

The old FastAPI/Postgres analytics runtime has been removed. Remaining control
work is semantic enrichment, not relational-runtime parity work. Current
defensive defaults should be replaced by graph facts for:

- telemetry alert rows beyond telemetry readings
- data-quality detail identifiers beyond semantic trust finding IRIs
- parameterized incident and asset lookup
