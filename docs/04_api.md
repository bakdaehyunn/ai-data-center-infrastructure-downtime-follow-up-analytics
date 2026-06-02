# API

The API is read-only and analytics-oriented. It exists to answer follow-up questions, not to edit maintenance transactions.

## Operational Overview

```text
GET /api/overview
```

Returns the top-level operating picture: open requests, delayed requests, critical delayed equipment, average downtime, top active bottleneck stage, parts waiting hours, latest pipeline run status, and latest-run data quality status.

## Follow-up Queue

```text
GET /api/follow-ups
GET /api/follow-ups/{maintenance_request_id}
GET /api/follow-ups/{maintenance_request_id}/timeline
```

Returns ranked maintenance requests that need follow-up, plus drilldown context for a selected request. The detail endpoints support the dashboard path from "what should I handle first?" to "why is this request ranked here?"

## Bottleneck and Impact

```text
GET /api/downtime/stages
GET /api/equipment/delays
GET /api/lines/delays
GET /api/parts/waiting
```

Returns delay concentration by active workflow stage, equipment, production line, and part. These endpoints explain where downtime risk is accumulating beyond the individual request queue.

## Filter Metadata

```text
GET /api/metadata/filters
```

Returns filter choices for line, equipment, priority, and active request stage. Terminal completed stages are not exposed as actionable stage filters.

## Observability and Trust

```text
GET /api/pipeline-runs
GET /api/data-quality/checks
GET /api/data-quality/checks/{check_result_id}
```

Returns pipeline run history and data quality check results. Data quality list endpoints default to the latest pipeline run unless `all_runs=true` or a specific `pipeline_run_id` is supplied.
