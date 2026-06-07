# Post-Phase-20 Route Parity Plan

## Purpose

This document maps the old FastAPI `/api` surface to the ontology-native
semantic service transition path. It started as a planning artifact. The first
post-Phase-20 private query endpoint slice now exists, but this document still
does not authorize old runtime deletion, UI redesign, reasoning execution,
graph writes, commit, or push.

## Current Boundary

The old FastAPI backend still owns the dashboard runtime. The React frontend
currently calls `http://localhost:8000/api/*` through `frontend/src/api.ts`.

The Kotlin/JVM semantic service can load approved query definitions, execute
controlled read-only queries against fixture-loaded Fuseki graphs, shape three
query-result envelope types, serialize those envelopes into Phase 18 response
maps, and serve those same responses through an internal loopback
`POST /semantic/query/{queryId}` endpoint when explicitly started.

Current Phase 16 approved runtime query IDs:

- `fixtureNamedGraphInventory`
- `fixtureIncidentSummary`
- `fixtureProvenanceSourceRecords`

Current Phase 17/18/19 response result types:

- `named-graph-inventory`
- `incident-summary`
- `provenance-source-records`

Everything else in this parity plan requires new query IDs, new typed result
envelopes, SHACL/provenance gates, or command-boundary design before the old
FastAPI route can be retired.

## Migration Status Legend

- **Existing query support**: An approved query ID and typed envelope already
  exist.
- **New read-model query**: Needs a new approved SELECT query and typed
  envelope.
- **Reasoning-backed read model**: Needs reasoning output first, then a SELECT
  view over reasoning/canonical/provenance graphs.
- **Command boundary**: Should not be a generic query endpoint; needs a
  controlled service operation.
- **Compatibility alias**: Old synonym route. Prefer one semantic query and
  optional compatibility adapter only while the old UI/API contract is being
  retired.
- **Retire/reference**: Preserve as reference or documentation only; do not
  rebuild as a long-term endpoint unless product usage proves it is needed.

## Route Parity Matrix

| Old route | Current consumer | Target semantic query or operation | Target response envelope | Provenance requirement | Migration status | Tests before retirement |
| --- | --- | --- | --- | --- | --- | --- |
| `GET /api/health` | Runtime/operator | `semanticServiceHealth` service operation, no SPARQL | `SemanticHealthEnvelope` | service version, graph endpoint, contract versions, readiness state | Command boundary | health succeeds without exposing graph internals; degraded graph returns typed error/status |
| `GET /api/overview` | Dashboard | `semanticDashboardOverview` | `DashboardOverviewEnvelope` | canonical incidents/assets, latest reasoning findings, quality/provenance graph references | New read-model query | old-vs-new counts for open, delayed, critical, capacity, GPU, redundancy, vendor ETA, quality |
| `GET /api/follow-ups` | Dashboard primary queue | `semanticFollowUpQueueList` | `FollowUpQueueEnvelope` | incident, asset, stage, impact, trust, and reasoning activity lineage per row | New read-model query | ranked order, filters, limit handling, queue scope counts, selected preview fields |
| `GET /api/follow-ups/{incident_id}` | Detail route | `semanticFollowUpDetail` | `FollowUpDetailEnvelope` | source records for incident, asset, current state, stage evidence, work order, validation, telemetry, impact, trust | New read-model query | detail tabs render from semantic payload; 404/error envelope for unknown incident |
| `GET /api/follow-ups/{incident_id}/timeline` | Detail/reference | `semanticIncidentTimeline` | `IncidentTimelineEnvelope` | event source record and import activity for each event | New read-model query | chronological ordering, stage/event vocabulary, missing incident error |
| `GET /api/impact/summary` | Dashboard | `semanticImpactSummary` | `ImpactSummaryEnvelope` | impact snapshots, trust findings, reasoning activity for derived counts | Reasoning-backed read model | capacity/GPU/redundancy/vendor/trust counts match accepted fixture parity |
| `GET /api/downtime/stages` | Dashboard analytics context | `semanticStageBottlenecks` | `StageBottleneckEnvelope` | stage events, thresholds, delay reasoning activity | Reasoning-backed read model | stage sort order, delay rate, p90/avg/total duration parity |
| `GET /api/equipment/delays` | Legacy alias | `semanticAssetDelaySummary` | `AssetDelaySummaryEnvelope` | asset incidents, downtime events, source records | Compatibility alias | alias returns same payload as asset delay route while compatibility remains |
| `GET /api/assets/delays` | Dashboard analytics context | `semanticAssetDelaySummary` | `AssetDelaySummaryEnvelope` | asset incidents, downtime events, source records | New read-model query | total downtime, delayed count, repeat failure, top failure mode parity |
| `GET /api/lines/delays` | Legacy alias | `semanticZoneDelaySummary` | `ZoneDelaySummaryEnvelope` | zone incidents, stage delay evidence, source records | Compatibility alias | alias returns same payload as zone delay route while compatibility remains |
| `GET /api/zones/delays` | Dashboard analytics context | `semanticZoneDelaySummary` | `ZoneDelaySummaryEnvelope` | zone incidents, stage delay evidence, source records | New read-model query | open/delayed/critical counts and top bottleneck parity |
| `GET /api/parts/waiting` | Legacy alias | `semanticSpareWaitSummary` | `SpareWaitSummaryEnvelope` | spare records, work orders, waiting stage events | Compatibility alias | alias returns same payload as spare wait route while compatibility remains |
| `GET /api/spares/waiting` | Dashboard analytics context | `semanticSpareWaitSummary` | `SpareWaitSummaryEnvelope` | spare records, work orders, waiting stage events | New read-model query | wait hours, critical spare, stock status, average wait parity |
| `GET /api/metadata/filters` | Dashboard filters | `semanticFilterMetadata` | `FilterMetadataEnvelope` | canonical vocabulary graph, active queue graph scope | New read-model query | all filter option sets match current fixtures; stable sort order |
| `GET /api/topology/dependencies` | Dashboard/detail dependencies | `semanticTopologyDependencies` | `TopologyDependencyEnvelope` | dependency edge source records, active incident counts, graph scope | New read-model query | dependency filtering, role/type fields, active incident counts |
| `GET /api/semantic/infrastructure.ttl` | Developer/reference | `semanticNamedGraphExport` service operation | `NamedGraphExportEnvelope` or direct Turtle only for internal tooling | release manifest, graph URI, generated/export activity | Retire/reference or command boundary | graph export is internal-only; exported Turtle parses; no dashboard dependency |
| `GET /api/semantic/validation` | Detail trust context | `semanticValidationSummary` | `ValidationSummaryEnvelope` | SHACL shape set, validation activity, graph release manifest | Command boundary | conforms/issue count parity; validation errors use typed semantic error envelope |
| `GET /api/semantic/query/dependency-impact/{asset_id}` | Detail dependencies | `semanticDependencyImpactByAsset`; reads output from `dependencyExposureReasoning` | `DependencyImpactEnvelope` | canonical dependency edges, reasoning finding, reasoning activity | Reasoning-backed read model | direct dependencies, downstream assets, unknown asset error, provenance included |
| `GET /api/semantic/query/incident-evidence/{incident_id}` | Detail trust/summary | `semanticIncidentEvidence`; `fixtureIncidentSummary` is only partial support | `IncidentEvidenceEnvelope` | incident source record, stage/status evidence, trust finding IDs | New read-model query | found/not-found semantics, stage/status/priority/trust fields |
| `GET /api/semantic/query/blast-radius/{asset_id}` | Detail dependencies/impact | `semanticBlastRadiusByAsset`; reads output from `blastRadiusReasoning` | `BlastRadiusEnvelope` | reasoning finding, affected incident lineage, dependency path lineage | Reasoning-backed read model | downstream asset set, affected incident count/list, unknown asset error |
| `POST /api/semantic/graph/sync` | Developer/reference | `semanticGraphPromotionReview` plus controlled promotion operation | `PromotionReviewEnvelope` | source graph, candidate graph, validation activity, promotion decision | Command boundary | no unrestricted writes; requires SHACL/provenance gates; rejected graph leaves canonical graph unchanged |
| `GET /api/connectors/contracts` | Developer/reference | `semanticConnectorContractCatalog` | `ConnectorContractEnvelope` | contract artifact version and source-system vocabulary | Retire/reference or new read-model query | contract list parses from semantic contract graph; no dashboard dependency |
| `GET /api/pipeline-runs` | Ops/reference | `semanticIngestionActivityHistory` | `IngestionActivityEnvelope` | PROV activity, graph promotion, validation gates, source batch | New read-model query | latest activity ordering, status mapping, row/source counts |
| `GET /api/data-quality/checks` | Dashboard trust summary | `semanticTrustFindingList` | `TrustFindingEnvelope` | SHACL result, reconciliation/trust finding, source records, graph release | Reasoning-backed read model | failed-only filtering, latest-run default, limit handling, severity/status fields |
| `GET /api/data-quality/checks/{check_result_id}` | Ops/detail reference | `semanticTrustFindingDetail` | `TrustFindingDetailEnvelope` | SHACL result or trust finding IRI, source records, activity lineage | Reasoning-backed read model | found/not-found behavior, evidence payload, stable finding ID |

## Frontend Consumer Priority

The current dashboard directly consumes these routes:

1. `GET /api/overview`
2. `GET /api/follow-ups`
3. `GET /api/downtime/stages`
4. `GET /api/assets/delays`
5. `GET /api/zones/delays`
6. `GET /api/spares/waiting`
7. `GET /api/data-quality/checks`
8. `GET /api/impact/summary`
9. `GET /api/topology/dependencies`
10. `GET /api/metadata/filters`
11. `GET /api/follow-ups/{incident_id}`
12. `GET /api/semantic/validation`
13. `GET /api/semantic/query/incident-evidence/{incident_id}`
14. `GET /api/semantic/query/dependency-impact/{asset_id}`
15. `GET /api/semantic/query/blast-radius/{asset_id}`

These routes should be migrated before compatibility aliases, developer-only
graph export, connector contract listing, pipeline run history, and individual
data-quality detail routes.

## Query And Envelope Backlog

Add these query IDs to `queries/manifest.ttl` only when the matching SPARQL and
typed envelope are implemented and tested:

- `semanticDashboardOverview`
- `semanticFollowUpQueueList`
- `semanticFollowUpDetail`
- `semanticIncidentTimeline`
- `semanticImpactSummary`
- `semanticStageBottlenecks`
- `semanticAssetDelaySummary`
- `semanticZoneDelaySummary`
- `semanticSpareWaitSummary`
- `semanticFilterMetadata`
- `semanticTopologyDependencies`
- `semanticValidationSummary`
- `semanticDependencyImpactByAsset`
- `semanticIncidentEvidence`
- `semanticBlastRadiusByAsset`
- `semanticConnectorContractCatalog`
- `semanticIngestionActivityHistory`
- `semanticTrustFindingList`
- `semanticTrustFindingDetail`

Do not mark any new product query `phase16-approved` until:

- the SPARQL is parseable and read-only
- graph scope is explicit
- result envelope has a Kotlin type
- `QueryResultShaper` supports the query ID
- `SemanticResponseSerializer` serializes the typed envelope
- contract tests cover required bindings and missing-binding failures
- provenance fields are present or the absence is explicitly accepted

## First Private Semantic Endpoint Slice

The first endpoint slice is the private approved-query execution endpoint, not
a dashboard migration endpoint.

Target slice:

- Endpoint shape: private/internal `POST /semantic/query/{queryId}`
- Implementation: `PrivateSemanticQueryEndpoint`
- Runtime wrapper: loopback-only `PrivateSemanticQueryEndpointServer`
- Allowed query IDs for the first slice:
  - `fixtureNamedGraphInventory`
  - `fixtureIncidentSummary`
  - `fixtureProvenanceSourceRecords`
- Response boundary: existing Phase 19 `SemanticResponseSerializer`
- Error boundary: existing Phase 18 semantic error envelope
- Runtime behavior: read-only SELECT execution only
- Explicitly forbidden: arbitrary SPARQL text, SPARQL Update, raw binding rows,
  graph writes, reasoning execution, UI adapter switch, public exposure

Why this is first:

- it uses only query IDs and envelope types that already exist
- it tests the private HTTP boundary without inventing dashboard view models at
  the same time
- it proves Phase 20's endpoint readiness rule that every endpoint response
  must go through `SemanticResponseSerializer`
- it creates the contract surface needed before product routes such as
  `semanticFollowUpQueueList` can safely replace FastAPI

The first product parity slice after that should be
`semanticFollowUpQueueList`, because it supports the primary workflow and
unblocks migration of the Follow-up Queue without redesigning the dashboard.

## Private Endpoint Tests For The First Slice

The first endpoint slice should keep tests for:

- approved query ID returns a Phase 19 serialized response map as JSON
- unapproved query ID returns `unapproved-query-id`
- unsupported query envelope returns `unsupported-result-envelope`
- missing required binding returns `missing-required-binding`
- graph unavailable returns `graph-unavailable`
- request body cannot provide raw SPARQL text
- query mode must be SELECT or ASK, with current response envelopes limited to
  SELECT
- response includes `queryId`, `resultType`, `recordCount`, `records`, and
  `provenance`
- no endpoint executes SPARQL Update or writes a named graph
- endpoint remains private/internal in docs and tests

## Retirement Gates For Old FastAPI Routes

Do not remove an old FastAPI route until all are true:

1. The route has a mapped semantic query or explicit retire/reference decision.
2. The query is approved in `queries/manifest.ttl` or the command boundary has
   a service contract.
3. The response envelope has a Kotlin type and serializer support.
4. Provenance requirements are tested or intentionally waived.
5. Fixture parity tests compare old FastAPI output with semantic-service
   output for accepted demo scenarios.
6. The frontend no longer calls the old route.
7. Any legacy alias has either a compatibility adapter or an accepted deletion
   decision.
8. A separate deletion goal approves exact files/routes to remove.

## Verification Commands

For this docs-only parity plan:

```bash
rg -n "GET /api|POST /api|semanticFollowUpQueueList|fixtureIncidentSummary|First Private Semantic Endpoint Slice" \
  docs/ontology-native/post_phase20_route_parity.md

git diff --check
```

For the future endpoint slice:

```bash
cd semantic-service && ./gradlew test

backend/.venv/bin/python queries/validate_sparql.py

backend/.venv/bin/python - <<'PY'
from pathlib import Path
from rdflib import Graph

for path in sorted(Path("queries").glob("*.ttl")):
    Graph().parse(path, format="turtle")
for path in sorted(Path("semantic-service").glob("**/*.ttl")):
    Graph().parse(path, format="turtle")
PY

git diff --check
```

## Recommended Next Goal

Suggested next implementation goal:

```text
Start the post-Phase-20 semantic queue read-model /goal: define and implement the first product read-model query for semanticFollowUpQueueList, including SPARQL, approved query manifest entry, typed result envelope, serializer support, provenance fields, and tests. Keep the private endpoint internal-only, do not redesign UI, do not remove old FastAPI/Postgres/React runtime code, do not execute reasoning or graph writes, commit, or push.
```
