# Architecture

## Flow

```text
scattered AI infrastructure source records
  -> raw source-preserving tables
  -> core AI infrastructure tables
  -> analytics materialization
  -> reconciliation checks
  -> read-only FastAPI API
  -> React dashboard
```

## Source System Integration Model

The project simulates seven source families that are commonly fragmented in AI data center operations:

| Source family | Simulated records | Operational question answered | Trust risk |
| --- | --- | --- | --- |
| Incident system | `raw_infrastructure_incidents` | What is open, priority, asset, zone, needed-by time, and current system-of-record status? | Missing required fields, stale current stage, duplicate source incident |
| Workflow event history | `raw_incident_stage_events` | Which state transitions actually happened and when? | Missing stage event, event before incident report, state mismatch |
| Facility work orders | `raw_facility_work_orders` | Who owns repair work and whether work is waiting, started, or complete? | Work order without incident, waiting state without spare evidence |
| Spare and inventory context | `critical_spares` plus work-order spare links | Is the blocker stock, critical spare availability, or vendor dispatch? | Out-of-stock spare, missing required spare link |
| Vendor ETA context | stage-event metadata and `infrastructure_impact_snapshots` | Is external recovery late, confirmed, or not required? | ETA in the past without missed status, event/snapshot mismatch |
| Telemetry | `raw_telemetry_alerts` and impact telemetry readings | Is thermal, power, or redundancy exposure supported by monitoring evidence? | Alert without known asset, thermal breach without abnormal reading |
| Validation and impact | `raw_validation_results` and `infrastructure_impact_snapshots` | Is return-to-service safe, and how much rack/GPU/capacity exposure remains? | Validation before completed work, stale or missing impact snapshot |
| Infrastructure topology | `infrastructure_dependencies` | Which upstream power, cooling, telemetry, or redundancy assets does an affected asset depend on? | Missing asset reference, invalid dependency type, stale topology extract |

Each feed remains source-shaped in the raw layer, then maps into a canonical infrastructure model. The pipeline is intentionally batch-oriented for the case study: it proves the reconciliation and follow-up decision logic before introducing streaming or orchestration technology.

## Layer Responsibilities

- Raw layer preserves source payloads, source record IDs, pipeline run IDs, and ingestion timestamps.
- Core layer normalizes source records into incidents, stage events, work orders, assets, zones, topology dependencies, spares, engineers, validations, telemetry alerts, and impact snapshots.
- Analytics layer stores calculated current status, lead times, bottlenecks, follow-up scores, impact score components, and impact summaries.
- Control layer persists reconciliation issues when core state, event history, impact snapshots, and analytics outputs do not agree.
- API layer serves read-only analytics, topology, semantic export, connector-contract, and drilldown views.

## Pipeline Order

```text
generate/read sample source files
  -> raw quality checks
  -> raw load
  -> core transform and impact snapshot load
  -> core quality checks
  -> analytics build
  -> reconciliation issue detection
  -> pipeline run commit
```

Reconciliation runs after analytics materialization because some issues require comparing core incidents with generated analytics rows, for example a core incident missing `incident_current_status`.

Impact snapshots are loaded into the core layer before analytics materialization. The analytics builder uses the latest snapshot per incident to add capacity risk, redundancy risk, thermal risk, vendor ETA risk, and mitigation credit to the follow-up queue.

Topology dependencies are loaded as reference data after assets are known. They are exposed through read-only API and UI surfaces and through the RDF/OWL-lite semantic export. They do not replace SQL persistence or add a graph database runtime.

The control layer then validates those impact snapshots against event evidence. This is where V1.2 confidence is assigned: impact context is `TRUSTED` when the latest snapshot has no open impact reconciliation issue, `WARNING` when the snapshot exists but contradicts or lags event evidence, and `UNVERIFIED` when no usable snapshot exists for the active incident.

## Design Choices

### Event History as Analytical Evidence

The current state can be stored on an incident, but stage events explain how the incident reached that state. The analytics builder uses stage entry and exit events to calculate lead time, delay, bottlenecks, and timelines.

### Pipeline-Computed Analytics

The pipeline computes analytics before API reads. This makes API responses stable, fast, and auditable by pipeline run.

### Read-Only API

The API does not mutate incidents, work orders, inventory, or telemetry. The product is an analytics control and follow-up layer above operational systems of record.

### Latest-Run Trust Scope

Data quality checks and reconciliation flags are scoped to the latest pipeline run by default. This prevents stale failures from polluting current dashboard trust signals.

### Technology Boundary

Docker, scheduled execution, observability, and future Kubernetes CronJobs are production support choices. They are not the system's value proposition. The value proposition is the decision model: reconstruct state, rank follow-up work, expose trust issues, and make the next operator action clear.
