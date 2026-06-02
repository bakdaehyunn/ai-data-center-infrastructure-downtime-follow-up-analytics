# UI Spec

## Dashboard Goal

The dashboard should help an operations user answer four questions:

- what maintenance work is delaying return-to-service?
- where is the current blocker?
- what should be followed up next?
- can the data behind the recommendation be trusted?

## Main Views

### Overview KPIs

- open requests
- delayed requests
- critical delayed equipment
- parts waiting hours
- latest-run data quality status

### Follow-up Queue

The queue ranks open maintenance requests and shows request, equipment, line, current stage, current delay, recommended action, and score.

The queue is the primary working surface. It should read like a daily follow-up list for a supervisor or planner, not like a generic table of records.

### Request Drilldown

The drilldown explains why the selected request is in the queue:

- request summary
- score components
- stage lead times
- work order context
- parts context
- sensor alert context
- quality flags

### Bottleneck and Impact Panels

- active stage bottlenecks
- equipment downtime concentration
- production line downtime concentration
- parts waiting impact
- failed latest-run data quality checks

## Interaction Rules

- Filters should narrow the queue and keep the drilldown aligned with the filtered result set.
- Terminal completed stages should not appear as actionable stage filters.
- Empty states should explain that no follow-up work matches the current filters.
