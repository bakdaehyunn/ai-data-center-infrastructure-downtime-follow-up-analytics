# API Package

Contains the post-Phase-20 private semantic query endpoint boundary.

Implemented boundary:

- `PrivateSemanticQueryEndpoint`
- internal `POST /semantic/query/{queryId}` request handling
- loopback-only `PrivateSemanticQueryEndpointServer`
- success/error payloads through `SemanticResponseSerializer`
- optional string-valued `parameters` for approved lookup queries only

Allowed query IDs:

- `fixtureNamedGraphInventory`
- `fixtureIncidentSummary`
- `fixtureProvenanceSourceRecords`
- `semanticFollowUpQueueList`
- `semanticDashboardOverview`
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

Non-goals:

- no public endpoints
- no raw SPARQL request body
- no SPARQL Update
- no graph writes
- no reasoning execution
