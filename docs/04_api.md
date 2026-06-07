# API

The FastAPI service exposes read-only operational analytics and semantic ontology endpoints.

## Overview

```text
GET /api/overview
```

Returns open incident count, delayed incident count, critical delayed assets, average downtime, top bottleneck stage, spare/vendor wait hours, capacity at risk, affected GPUs, redundancy-loss count, missed vendor ETA count, latest pipeline status, and latest-run data quality status.

## Follow-up Queue

```text
GET /api/follow-ups
GET /api/follow-ups/{incident_id}
GET /api/follow-ups/{incident_id}/timeline
```

The queue supports filters by `zone_id`, `asset_id`, `priority_level`, active `stage`, and row-level queue predicates:

- `delayed_only=true`
- `critical_asset_delayed=true`
- `capacity_risk=true`
- `affected_gpu=true`
- `evidence_review=true`
- `redundancy_lost=true`
- `vendor_eta_missed=true`

Queue rows include impact context fields such as redundancy state, affected GPUs, estimated kW at risk, mitigation status, vendor status, `impact_confidence_status`, and `impact_trust_issue_count`.

The UI exposes only the predicates that clearly narrow or reset the visible queue as queue scope controls. KPI cards remain read-only visible-queue summaries.

`recommended_action` is the next workflow follow-up. `reason_summary` explains why the row matters, including delay and impact context. This keeps operational action separate from impact rationale.

The dedicated follow-up detail endpoint powers `/follow-ups/{incident_id}` in the UI. Drilldown returns the selected incident, stage lead times, timeline events, work orders, validation results, telemetry alerts, the latest impact snapshot, impact telemetry readings, general quality flags, `impact_confidence_status`, and structured `impact_trust_flags`.

## Downtime and Impact

```text
GET /api/downtime/stages
GET /api/impact/summary
GET /api/assets/delays
GET /api/zones/delays
GET /api/spares/waiting
```

These endpoints explain where delay and operational exposure are accumulating across workflow stages, infrastructure assets, data center zones, critical spares, capacity risk, redundancy state, vendor ETA, mitigation status, and impact-confidence state.

## Topology, Semantic Ontology, and Connector Contracts

```text
GET /api/topology/dependencies
GET /api/semantic/infrastructure.ttl
GET /api/semantic/validation
GET /api/semantic/query/dependency-impact/{asset_id}
GET /api/semantic/query/incident-evidence/{incident_id}
GET /api/semantic/query/blast-radius/{asset_id}
POST /api/semantic/graph/sync
GET /api/connectors/contracts
```

Topology dependencies expose directed asset relationships such as rack -> PDU -> UPS -> switchgear -> generator and rack -> CRAH/CDU/chiller. Each row returns the dependent asset, dependency asset, dependency type, dependency role, impact scope, current asset statuses, and active incident counts on both sides of the edge.

The semantic Turtle endpoint returns RDF/OWL and SHACL vocabulary plus instance triples generated through RDF APIs from the current canonical infrastructure records.

Semantic validation runs SHACL against the generated graph and returns conformance plus validation issues.

Semantic query endpoints are backed by SPARQL over the generated RDF graph:

- dependency impact returns direct dependency edges and inferred downstream assets for an asset.
- incident evidence returns the RDF incident-to-asset, stage, status, priority, and trust issue links for an incident.
- blast radius returns inferred downstream assets and affected incidents reachable from the selected asset.

Graph sync builds the RDF graph and pushes Turtle to the configured graph-store URL, for example `http://localhost:3030/infrastructure/data`. If no target URL is configured, it returns `NOT_CONFIGURED` with the local triple count.

Connector contracts describe expected mounted extract files, target raw/core tables, required payload fields, cadence, and notes. They do not contain credentials and do not perform live source-system access.

Compatibility aliases remain available for older local clients, but they are not the primary AI infrastructure product surface:

```text
GET /api/equipment/delays
GET /api/lines/delays
GET /api/parts/waiting
```

## Metadata and Trust

```text
GET /api/metadata/filters
GET /api/pipeline-runs
GET /api/data-quality/checks
GET /api/data-quality/checks/{check_result_id}
```

Metadata powers dashboard filters. Data quality responses default to the latest pipeline run unless `all_runs=true` is supplied.

Impact trust flags are also latest-run scoped. General `quality_flags` remain text labels for raw/core/workflow trust issues, while `impact_trust_flags` expose structured impact-context evidence such as stale snapshot IDs, vendor ETA status, missing mitigation evidence, or thermal context gaps.
