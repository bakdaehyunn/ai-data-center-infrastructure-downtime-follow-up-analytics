# Semantic API

The active runtime API is the Kotlin/JVM semantic-service private endpoint:

```text
POST /semantic/query/{queryId}
```

The endpoint accepts approved query IDs from `queries/manifest.ttl`. It does
not accept raw SPARQL, graph writes, SPARQL Update, or public endpoint binding.
All success and error payloads go through `SemanticResponseSerializer`.
Approved queries may accept string-valued `parameters`; raw SPARQL remains
forbidden.

## Product Read Models

Approved product read-model query IDs include:

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

## Follow-Up Workflow Support

The dashboard adapter uses these semantic read models to replace the old
analytics route surface:

- overview KPI and exposure summaries from graph-backed aggregate queries
- ranked follow-up queue rows from `semanticFollowUpQueueList`
- selected follow-up detail from `semanticFollowUpDetail`
- chronological stage history from `semanticIncidentTimeline`
- evidence, trust, validation, work-order, and telemetry context from
  `semanticIncidentEvidence`
- dependency and blast-radius context from topology and reasoning read models
- parameterized incident, asset, and trust-finding detail lookups through the
  same approved-query endpoint

## Response Contract

Every response envelope includes:

- `queryId`
- `resultType`
- `recordCount`
- `records`
- `provenance.contractVersion`
- `provenance.graphScope`

Semantic errors use stable machine-readable codes such as
`unapproved-query-id`, `missing-required-binding`, `graph-unavailable`, and
`internal-semantic-service-error`.

See `semantic-service/api-dtos.md` and
`semantic-service/openapi.semantic-service.yaml` for the current DTO scaffold.
