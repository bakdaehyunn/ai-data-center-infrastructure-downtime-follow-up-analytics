# Semantic Analytics Control Layer

The analytics control layer is now expressed as ontology modules, SHACL
contracts, approved SPARQL read models, and Kotlin result envelopes.

## Control Responsibilities

- reconstruct follow-up state from canonical graph facts
- rank active follow-up queue items
- expose impact, redundancy, capacity, GPU, vendor, mitigation, telemetry,
  telemetry alert, validation, and work-order evidence
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

## Current Control Status

The old FastAPI/Postgres analytics runtime has been removed. Current control
work is semantic enrichment, not relational-runtime parity work. Telemetry
alerts, repeat-failure counters, engineer-assignment counters, data-quality
detail lookup, and parameterized incident/asset lookup are graph-backed through
approved read-only semantic queries. Remaining frontend null guards are
acceptable optional fallbacks for graph facts that may be absent from a fixture
or source extract.
