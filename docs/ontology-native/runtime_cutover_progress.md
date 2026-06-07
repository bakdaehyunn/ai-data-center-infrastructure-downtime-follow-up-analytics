# Ontology-Native Runtime Cutover Progress

## Current Status

The ontology-native semantic-service now owns the first private read-model
contracts for several active product surfaces. The React dashboard data adapter
now calls the private semantic-service endpoint instead of the old FastAPI
`/api/*` routes.

This is now an active runtime cutover state. The frontend adapter maps semantic
envelopes into the existing UI contracts, while the tracked
FastAPI/Postgres/SQLAlchemy backend has been removed from the active tree. The
remaining work is semantic enrichment for a few optional operational fields,
not preserving or reactivating the old relational runtime.

## Semantic-Service Read Models Implemented

Approved private query IDs:

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

These read models are backed by parseable read-only SPARQL, query manifest
entries, typed Kotlin envelopes, `QueryResultShaper` support,
`SemanticResponseSerializer` support, private endpoint allowlist entries, and
focused tests.

## Former Active Frontend Routes Now Routed Through Semantic-Service

`frontend/src/api.ts` no longer calls these old FastAPI routes directly:

- `GET /api/overview`
- `GET /api/follow-ups`
- `GET /api/downtime/stages`
- `GET /api/assets/delays`
- `GET /api/zones/delays`
- `GET /api/spares/waiting`
- `GET /api/data-quality/checks`
- `GET /api/impact/summary`
- `GET /api/topology/dependencies`
- `GET /api/metadata/filters`
- `GET /api/follow-ups/{incident_id}`
- `GET /api/semantic/validation`
- `GET /api/semantic/query/incident-evidence/{incident_id}`
- `GET /api/semantic/query/dependency-impact/{asset_id}`
- `GET /api/semantic/query/blast-radius/{asset_id}`

The new semantic-service read models cover first semantic slices for overview,
queue, filters, detail, impact, topology, trust, stage bottlenecks, asset delay
summaries, zone delay summaries, spare/vendor wait summaries, validation
summaries, incident evidence lookup, incident timeline lookup, dependency
impact lookup, and blast-radius lookup.

## Compatibility Adapter Gaps

The active frontend cutover now reads graph-backed values for priority rank,
request title, current status, hours in current stage, needed-by time, priority
level, business impact, priority score inputs, capacity risk, GPU impact,
redundancy, mitigation, vendor state, thermal exposure, stage thresholds,
stage history, aggregate downtime/wait-hour summaries, evidence timestamps,
work-order assignment, validation-result rows, and telemetry readings when
those fields exist in the semantic graph.

It still keeps defensive defaults for:

1. telemetry alert rows beyond telemetry readings
2. repeat-failure and engineer-assignment specialty counters
3. old data-quality check detail identifiers beyond semantic trust finding IDs
4. parameterized incident and asset lookup instead of client-side filtering

## Deletion Status

The old tracked runtime package has been deleted from the active worktree. The
remaining gate is to avoid deleting semantic contracts or frontend adapter
guards until replacement graph facts and tests exist.

Current checks should prove:

1. Every active frontend route has a semantic-service query or command
   operation.
2. React no longer calls old `/api/*` routes.
3. Old backend tests are migrated to semantic-service/frontend checks or
   retired with documented reason.
4. `rg` scans prove remaining FastAPI/Postgres/SQLAlchemy references are
   historical/reference documentation, not active runtime requirements.

## Next Implementation Slice

The next cutover slice should expand fixture/domain coverage for optional
dashboard fields that are still defensive-default backed:

1. telemetry alert rows beyond telemetry readings
2. repeat-failure and engineer-assignment specialty counters
3. data-quality/trust detail records equivalent to old failed-check detail
   pages
4. parameterized private query execution for incident and asset lookup

Only after those contracts exist and pass fixture parity checks should the
frontend compatibility defaults be removed.
