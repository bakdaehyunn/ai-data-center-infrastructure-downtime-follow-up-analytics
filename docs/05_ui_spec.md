# UI Specification

## Primary Screen

The dashboard opens directly into the operational follow-up view. It is not a landing page and does not include record-entry workflows.

## Filters

- Zone
- Asset
- Priority
- Active stage

Terminal `RESTORED` stages are not exposed as actionable stage filters.

## KPI Row

- Open incidents
- Delayed incidents
- Critical delayed assets
- Spare/vendor wait hours
- Latest-run data trust

## Follow-up Queue

The queue ranks open incidents by return-to-service delay, blocker stage, zone impact, urgency, repeat failure, and spare risk.

Each row shows rank, incident number, priority, asset, zone, current stage, delay, recommended action, and score.

## Drilldown

Selecting a queue row shows:

- incident summary
- quality flags
- score components
- stage lead times
- facilities work order context
- required spare and stock status
- validation and telemetry context from the API

## Analytics Panels

- Active stage bottlenecks
- Asset impact
- Zone impact
- Spare/vendor waiting
- Data trust
