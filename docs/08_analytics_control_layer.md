# Analytics Control Layer

## Purpose

This document explains how the project handles scattered maintenance data before producing analytics.

The analytics control layer is responsible for:

- preserving raw source messages
- normalizing records into a consistent maintenance model
- reconstructing workflow state from event history
- detecting unreliable or conflicting data
- producing trusted analytics outputs for follow-up decisions

## Problem: Scattered Maintenance Evidence

Maintenance downtime data may come from multiple operational sources:

- maintenance requests
- stage transition events
- work orders
- spare parts status
- inspection results
- sensor alerts
- equipment master data
- production line context

The problem is that no single source fully answers:

> Which request is delaying return-to-service, why is it blocked, and what should be followed up next?

## Source Message Layer

The project preserves source-shaped records in raw tables.

Current implementation:

- `raw_maintenance_requests`
- `raw_maintenance_stage_events`
- `raw_maintenance_work_orders`
- `raw_inspection_results`
- `raw_sensor_alerts`

Each raw record keeps:

- source system
- source record ID
- original payload
- pipeline run ID
- ingestion timestamp

Design reason:

Raw data should be preserved before interpretation so analytics can be traced and quality issues can be investigated.

## Canonical Maintenance Model

Canonical means the project's standard internal format.

Different systems may describe the same business event differently. The project converts source-shaped records into one consistent maintenance model.

Current core tables:

- `production_lines`
- `equipment`
- `maintenance_requests`
- `maintenance_stage_events`
- `maintenance_work_orders`
- `parts`
- `inspection_results`
- `sensor_alerts`

Design reason:

Analytics should not depend directly on source-specific field names or message formats.

## Event Reconciliation

The project treats maintenance stage events as the basis for state reconstruction.

Current logic:

- group events by maintenance request
- sort events by timestamp
- pair stage entry with stage exit
- calculate stage duration
- use `as_of_time` for currently open stages

Important rule:

```text
duration_hours = exited_at_or_as_of - entered_at
```

Implementation example:

- `analytics_builder._events_by_request()` groups `MaintenanceStageEvent` rows by `maintenance_request_id`.
- It sorts each request's events by `(occurred_at, event_id)` so state reconstruction is based on event time, not ingestion order.
- `analytics_builder._build_lead_time_records()` only treats `ENTERED_STAGE` events as stage starts.
- `analytics_builder._find_stage_exit_time()` searches later events for the matching stage exit event or `REQUEST_COMPLETED`.
- If no exit event exists, the calculation uses `as_of_time` so open stages still get a current duration.

Design reason:

A current status field can say where a request is now, but event history explains how long it has been there.

## State Reconstruction

The project reconstructs current state into:

- `maintenance_current_status`
- `maintenance_stage_lead_times`

Current outputs include:

- current stage
- hours in current stage
- delay hours
- delayed flag
- needed-by timestamp
- next owner type
- next owner ID

Implementation example:

- `analytics_builder._build_current_status_rows()` creates a lookup keyed by `(request_id, stage)` from lead-time records.
- For each `MaintenanceRequest`, it finds the lead-time record for the request's current stage.
- `hours_in_current_stage` comes from that current stage duration.
- `is_delayed` is true when the current stage exceeds its threshold or the request is past `needed_by_at`.
- `next_owner_type` is derived from the current stage through `_next_owner_type()`.
- `next_owner_id` is resolved from the work order when the current owner is a technician or maintenance team.

Design reason:

Follow-up decisions need calculated state, not just raw status text.

## Data Quality Control

The project checks data quality before trusting analytics.

Current raw checks:

- duplicate source record
- missing required fields
- invalid date format
- missing maintenance request references
- unknown source system

Current core checks:

- request without stage event
- event timestamp before request reporting
- work order without request
- parts waiting without required part
- inspection without completed work
- sensor alert without equipment

Design reason:

If the underlying data is incomplete or inconsistent, the analytics output should show trust risk.

## Conflict and Reliability Rules

Current implementation handles basic reliability rules.

Examples:

- duplicate raw source records are rejected
- missing required payload fields are skipped
- completed stages are kept in timelines but excluded from active bottleneck summaries
- data quality results are scoped to the latest pipeline run by default

Implementation example:

- `analytics_builder._build_bottleneck_summary_rows()` skips records where `record.stage == "COMPLETED"`.
- This keeps terminal history available in request timelines and lead-time records while preventing completed work from appearing as an active bottleneck.
- `analytics_builder._build_downtime_follow_up_queue_rows()` skips requests where `request.current_status == "COMPLETED"`.
- This keeps the follow-up queue focused on actionable maintenance work.

Future realistic extensions:

- source priority rules
- late-arriving event handling
- current-status versus event-history mismatch detection
- confidence score per reconstructed state
- rejected/dead-letter message table

## Analytics Materialization

The project stores calculated analytics in dedicated tables.

Current analytics outputs:

- `downtime_follow_up_queue`
- `maintenance_bottleneck_summary`
- `equipment_delay_summary`
- `production_line_delay_summary`
- `parts_waiting_summary`

Implementation example:

- `analytics_builder.build_analytics()` loads core maintenance records, calculates analytics in memory, and writes the output rows with `session.add_all(...)`.
- `_clear_analytics_tables()` deletes the previous analytics snapshot before rebuilding the new one.
- The pipeline commits the analytics output as part of a `PipelineRun`, so downstream API responses are tied to a repeatable pipeline execution.

Design reason:

The API should read stable analytics outputs instead of recalculating complex workflow state on every request.

## Trusted Follow-up Outputs

The final trusted outputs answer:

- what is delayed?
- where is the blocker?
- what asset or line is affected?
- what should the team follow up next?
- can the data be trusted?

Current dashboard/API outputs:

- overview KPIs
- ranked follow-up queue
- request drilldown
- stage bottlenecks
- equipment and line impact
- parts waiting
- latest-run data quality checks

Implementation example:

- `analytics_builder._build_downtime_follow_up_queue_rows()` creates the ranked follow-up queue.
- It excludes completed requests and scores open requests using:
  - equipment criticality
  - estimated downtime
  - current stage delay
  - production line impact
  - needed-by urgency
  - repeat failure
  - parts risk
- It sorts requests by total score descending and assigns `priority_rank`.
- `_recommended_action()` converts the current stage and parts state into an operational next action.
- `_reason_summary()` explains why the request is considered delayed or important.

## Current Scope vs Future Scope

Current project implements:

- raw preservation
- core normalization
- event-based state reconstruction
- lead time calculation
- bottleneck grouping
- priority scoring
- data quality checks
- pipeline observability
- read-only analytics API

Future enhancements could include:

- explicit source message contracts
- canonical event mapping table
- identity resolution table
- late event reprocessing
- conflict resolution rules
- analytics lineage back to raw source records
- event confidence scoring
