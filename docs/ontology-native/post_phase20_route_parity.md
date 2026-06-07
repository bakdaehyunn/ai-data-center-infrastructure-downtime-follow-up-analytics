# Post-Phase-20 Route Parity Plan

## Purpose

This document maps the removed FastAPI `/api` surface to the ontology-native
semantic-service replacement path. It started as a planning artifact; after the
runtime cutover, it is retained as a parity checklist for fields and behaviors
that still need richer semantic modeling.

## Current Boundary

The old FastAPI backend no longer owns the dashboard runtime and the tracked
`backend/` package has been removed. The React frontend now calls the
loopback-only Kotlin/JVM semantic-service endpoint through
`VITE_SEMANTIC_API_BASE_URL`.

The Kotlin/JVM semantic service can load approved query definitions, execute
controlled read-only queries against fixture-loaded Fuseki graphs, shape typed
query-result envelopes, serialize those envelopes into Phase 18 response maps,
and serve those same responses through an internal loopback
`POST /semantic/query/{queryId}` endpoint when explicitly started.

Current fixture inspection query IDs:

- `fixtureNamedGraphInventory`
- `fixtureIncidentSummary`
- `fixtureProvenanceSourceRecords`

Current response result types include:

- `named-graph-inventory`
- `incident-summary`
- `provenance-source-records`
- `follow-up-queue`
- `dashboard-overview`
- `filter-metadata`
- `follow-up-detail`
- `impact-summary`
- `topology-dependencies`
- `trust-findings`
- `stage-bottlenecks`
- `asset-delay-summary`
- `zone-delay-summary`
- `spare-wait-summary`
- `validation-summary`
- `incident-evidence`
- `dependency-impact`
- `blast-radius`

Remaining parity work is field-level and behavior-level, not old-runtime
ownership. The current frontend adapter fills some missing old fields with
compatibility defaults until RDF fixtures and SPARQL read models expose those
facts natively.

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
| `GET /api/follow-ups` | Dashboard primary queue | `semanticFollowUpQueueList` | `FollowUpQueueEnvelope` | incident, asset, zone, stage, and source-record provenance per row now; impact/trust/reasoning lineage later | Partial product read model implemented | current semantic payload shape, then ranked order, filters, limit handling, queue scope counts, selected preview fields before UI cutover |
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
- `semanticFollowUpQueueList` - implemented first canonical read-model slice
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
- it creates the contract surface that product read models use before they can
  replace the removed FastAPI routes

The first product parity slice on that boundary is `semanticFollowUpQueueList`,
because it supports the primary workflow and starts migration of the Follow-up
Queue without redesigning the dashboard.

Current limitation: the semantic-service now has first product read-model
contracts for queue, overview, filters, detail, impact, topology, and trust,
but they are still fixture/canonical graph-backed slices. They do not yet
provide full semantic parity for ranking, queue filtering, stage delay
analytics, spare wait analytics, detailed timeline/work-order/validation
records, or all dashboard fields without compatibility defaults.

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

## Semantic Parity Gates

Do not treat the cutover as semantically complete until all are true:

1. Every former route has a mapped semantic query or explicit retire/reference decision.
2. Each query is approved in `queries/manifest.ttl` or the command boundary has
   a service contract.
3. The response envelope has a Kotlin type and serializer support.
4. Provenance requirements are tested or intentionally waived.
5. Fixture parity tests compare accepted demo scenarios against semantic-service
   output.
6. The frontend contains no compatibility defaults for required operational
   fields.
7. Any legacy alias has either a compatibility adapter or an accepted deletion
   decision.
8. `rg` checks show no active Python/Postgres runtime references.

## Verification Commands

For route parity and read-model checks:

```bash
rg -n "GET /api|POST /api|semanticFollowUpQueueList|fixtureIncidentSummary|First Private Semantic Endpoint Slice" \
  docs/ontology-native/post_phase20_route_parity.md

git diff --check
```

For endpoint and read-model implementation checks:

```bash
docker run --rm \
  -v "$PWD":/workspace \
  -w /workspace/semantic-service \
  gradle:8.10.2-jdk17 \
  gradle --no-daemon test

python3 queries/validate_sparql.py

python3 - <<'PY'
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
Start the semantic follow-up queue parity expansion /goal: extend semanticFollowUpQueueList and semanticFollowUpDetail so priority rank, blocker, impact, trust, recommended action, filters, durations, and selected-detail fields come directly from RDF graph facts instead of frontend compatibility defaults. Keep the private endpoint internal-only, do not redesign the UI, do not execute graph writes, commit, or push.
```
