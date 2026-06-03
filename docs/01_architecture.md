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

## Layer Responsibilities

- Raw layer preserves source payloads, source record IDs, pipeline run IDs, and ingestion timestamps.
- Core layer normalizes source records into incidents, stage events, work orders, assets, zones, spares, engineers, validations, and telemetry alerts.
- Analytics layer stores calculated current status, lead times, bottlenecks, follow-up scores, and impact summaries.
- Control layer persists reconciliation issues when core state, event history, and analytics outputs do not agree.
- API layer serves read-only analytics and drilldown views.

## Pipeline Order

```text
generate/read sample source files
  -> raw quality checks
  -> raw load
  -> core transform
  -> core quality checks
  -> analytics build
  -> reconciliation issue detection
  -> pipeline run commit
```

Reconciliation runs after analytics materialization because some issues require comparing core incidents with generated analytics rows, for example a core incident missing `incident_current_status`.

## Design Choices

### Event History as Analytical Evidence

The current state can be stored on an incident, but stage events explain how the incident reached that state. The analytics builder uses stage entry and exit events to calculate lead time, delay, bottlenecks, and timelines.

### Pipeline-Computed Analytics

The pipeline computes analytics before API reads. This makes API responses stable, fast, and auditable by pipeline run.

### Read-Only API

The API does not mutate incidents, work orders, inventory, or telemetry. The product is an analytics control and follow-up layer above operational systems of record.

### Latest-Run Trust Scope

Data quality checks and reconciliation flags are scoped to the latest pipeline run by default. This prevents stale failures from polluting current dashboard trust signals.
