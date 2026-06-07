# Post-Phase-20 Private Semantic Query Endpoint

## Purpose

This checkpoint records the first private endpoint implementation after the
Phase 20 endpoint-readiness decision. It implements only the approved-query
inspection slice identified in the route parity plan.

## Implemented Boundary

The Kotlin semantic service now has an internal-only endpoint boundary:

- `POST /semantic/query/{queryId}`
- implemented by `PrivateSemanticQueryEndpoint`
- optionally served by `PrivateSemanticQueryEndpointServer`
- loopback-only bind host, defaulting to `127.0.0.1`
- success responses through `SemanticResponseSerializer`
- errors through the Phase 18 semantic error envelope

The endpoint is opt-in through:

```bash
--serve-private-query-endpoint
```

Optional runtime flags:

```bash
--private-endpoint-host=127.0.0.1
--private-endpoint-port=18080
```

## Allowed Query IDs

Only these approved query IDs are allowed:

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
- `semanticDependencyImpactByAsset`
- `semanticBlastRadiusByAsset`

The endpoint rejects any other query ID with `unapproved-query-id`.

The product read-model queries return canonical graph-backed dashboard and
detail fields through typed envelopes. `semanticFollowUpQueueList` and
`semanticFollowUpDetail` now include graph-backed rank, title, status, current
stage hours, priority level, business impact, priority score inputs, impact,
trust, blocker, recommendation, redundancy, mitigation, vendor, and thermal
fields when those facts exist in the graph.

## Explicit Non-Goals

This checkpoint does not:

- expose public endpoints
- accept raw SPARQL request bodies
- execute SPARQL Update
- execute reasoning
- write RDF graphs
- redesign the UI
- commit or push

## Error Handling

The endpoint maps failures to the existing semantic error envelope:

- unapproved query id -> `unapproved-query-id`
- unsupported result envelope -> `unsupported-result-envelope`
- missing required binding -> `missing-required-binding`
- graph query failure -> `graph-unavailable`
- invalid method, path, or raw SPARQL body -> `contract-validation-failed`

## Verification

Focused tests cover:

- approved query response serialization
- unapproved query rejection
- raw SPARQL request body rejection
- missing binding error mapping
- unsupported envelope error mapping
- graph unavailable error mapping
- non-POST rejection
- loopback HTTP serving
- non-loopback bind rejection
- JSON escaping

Verification command:

```bash
docker run --rm \
  -v "$PWD":/workspace \
  -w /workspace/semantic-service \
  gradle:8.10.2-jdk17 \
  gradle --no-daemon test
```

## Next Implementation Slice

The next implementation slice should replace remaining frontend defensive
defaults with graph facts for telemetry alert records, repeat-failure and
engineer-assignment specialty counters, data-quality finding details, and
parameterized incident/asset lookup. Keep SPARQL read-only and keep the
endpoint private/internal through `POST /semantic/query/{queryId}`.
