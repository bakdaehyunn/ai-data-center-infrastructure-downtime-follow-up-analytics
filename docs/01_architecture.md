# Architecture

## Flow

```text
scattered maintenance source records
  -> raw maintenance tables
  -> core maintenance tables
  -> analytics tables
  -> analytics control checks
  -> read-only FastAPI API
  -> React dashboard
```

## Design Choices

### Raw/Core/Analytics/Ops Layers

The layer split keeps each responsibility clear:

- raw preserves source-shaped records, source IDs, and pipeline run traceability
- core normalizes maintenance entities into a consistent operational model
- analytics stores calculated state, lead time, bottleneck, impact, and follow-up outputs
- ops records pipeline runs, data quality results, and reconciliation issues

This mirrors the operating problem: the value comes from connecting scattered records without pretending they came from one perfect source table.

### Analytics Control Layer

The analytics control layer runs after analytics materialization and before API consumers rely on the output. It checks whether the core records, event history, and generated analytics rows agree with each other before users rely on the dashboard.

Current reconciliation outputs are stored in `maintenance_reconciliation_issues` and scoped to the latest pipeline run. Request-level issues are exposed as drilldown quality flags.

The control layer currently detects:

- current state that cannot be reconstructed from stage events
- current stage mismatches between core request state and event history
- completion status conflicts between request records and event history
- stage events that occur before the request was reported
- parts-waiting work orders without a required part
- inspections without completed maintenance work
- core requests missing a generated current-status analytics row

This is separate from raw/core data quality checks. Data quality checks validate source and normalized records; reconciliation checks validate whether those records can safely support the analytics output.

### Event History as Source of Truth

The current state is reconstructed from maintenance stage events. A single current-status field can say where a request is now, but it cannot explain how it got there, how long each stage took, or where delay accumulated.

Event history gives the project the analytical surface it needs:

- stage entry and exit timestamps
- current stage reconstruction
- stage lead time
- terminal versus actionable states
- request timeline drilldown

### Pipeline-Computed Analytics

The pipeline calculates lead time, bottlenecks, impact summaries, reconciliation flags, and priority scores before API reads. This keeps the API read-optimized and predictable, and it makes the analytics outputs auditable by pipeline run.

### Read-Only Analytics API

The API exposes operational analytics only. It does not mutate maintenance records because the project is not trying to replace a maintenance system of record. Its job is to show what needs follow-up, why it matters, and whether the supporting data is trustworthy.

### Dashboard as Decision Support

The dashboard is intentionally centered on a follow-up queue and drilldown. It is not a maintenance entry screen. It helps a user move from broad delay visibility to a specific request, blocker, and recommended action.
