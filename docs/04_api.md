# API

The FastAPI service exposes read-only analytics endpoints.

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

The queue supports filters by `zone_id`, `asset_id`, `priority_level`, and active `stage`. Queue rows include impact context fields such as redundancy state, affected GPUs, estimated kW at risk, mitigation status, and vendor status.

Drilldown returns the selected incident, stage lead times, timeline events, work orders, validation results, telemetry alerts, the latest impact snapshot, impact telemetry readings, and quality flags.

## Downtime and Impact

```text
GET /api/downtime/stages
GET /api/impact/summary
GET /api/assets/delays
GET /api/zones/delays
GET /api/spares/waiting
```

These endpoints explain where delay and operational exposure are accumulating across workflow stages, infrastructure assets, data center zones, critical spares, capacity risk, redundancy state, vendor ETA, and mitigation status.

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
