# API

The FastAPI service exposes read-only analytics endpoints.

## Overview

```text
GET /api/overview
```

Returns open incident count, delayed incident count, critical delayed assets, average downtime, top bottleneck stage, spare/vendor wait hours, latest pipeline status, and latest-run data quality status.

## Follow-up Queue

```text
GET /api/follow-ups
GET /api/follow-ups/{incident_id}
GET /api/follow-ups/{incident_id}/timeline
```

The queue supports filters by `zone_id`, `asset_id`, `priority_level`, and active `stage`. Drilldown returns the selected incident, stage lead times, timeline events, work orders, validation results, telemetry alerts, and quality flags.

## Downtime and Impact

```text
GET /api/downtime/stages
GET /api/assets/delays
GET /api/zones/delays
GET /api/spares/waiting
```

These endpoints explain where delay is accumulating across workflow stages, infrastructure assets, data center zones, and critical spares.

Compatibility routes remain available:

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
