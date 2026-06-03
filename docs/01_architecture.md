# Architecture

## Flow

```text
scattered maintenance source records
  -> raw maintenance tables
  -> core maintenance tables
  -> analytics tables
  -> read-only FastAPI API
  -> React dashboard
```

## Design Choices

### Raw/Core/Analytics/Ops Layers

The layer split keeps each responsibility clear:

- raw preserves source-shaped records, source IDs, and pipeline run traceability
- core normalizes maintenance entities into a consistent operational model
- analytics stores calculated state, lead time, bottleneck, impact, and follow-up outputs
- ops records pipeline runs and data quality results

This mirrors the operating problem: the value comes from connecting scattered records without pretending they came from one perfect source table.

### Event History as Source of Truth

The current state is reconstructed from maintenance stage events. A single current-status field can say where a request is now, but it cannot explain how it got there, how long each stage took, or where delay accumulated.

Event history gives the project the analytical surface it needs:

- stage entry and exit timestamps
- current stage reconstruction
- stage lead time
- terminal versus actionable states
- request timeline drilldown

### Pipeline-Computed Analytics

The pipeline calculates lead time, bottlenecks, impact summaries, quality flags, and priority scores before API reads. This keeps the API read-optimized and predictable, and it makes the analytics outputs auditable by pipeline run.

### Read-Only Analytics API

The API exposes operational analytics only. It does not mutate maintenance records because the project is not trying to replace a maintenance system of record. Its job is to show what needs follow-up, why it matters, and whether the supporting data is trustworthy.

### Dashboard as Decision Support

The dashboard is intentionally centered on a follow-up queue and drilldown. It is not a maintenance entry screen. It helps a user move from broad delay visibility to a specific request, blocker, and recommended action.
