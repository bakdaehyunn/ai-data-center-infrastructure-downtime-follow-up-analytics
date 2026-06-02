# Data Model

The data model supports one analytical workflow: connect scattered maintenance records, reconstruct request state, and rank downtime follow-up work.

## Source-Shaped Raw Tables

Raw tables preserve what arrived from upstream-style sources. They keep source IDs and pipeline run IDs so ingestion can be traced and quality checks can point back to the affected records.

- `raw_maintenance_requests`
- `raw_maintenance_stage_events`
- `raw_maintenance_work_orders`
- `raw_inspection_results`
- `raw_sensor_alerts`

## Core Operational Tables

Core tables normalize the maintenance domain into consistent relationships.

- `production_lines`
- `equipment`
- `technicians`
- `parts`
- `maintenance_requests`
- `maintenance_stage_events`
- `maintenance_work_orders`
- `inspection_results`
- `sensor_alerts`

## Analytics Tables

Analytics tables store computed outputs used by the API and dashboard.

- `maintenance_current_status`: reconstructed current stage and request state
- `maintenance_stage_lead_times`: duration, threshold, delay, and bottleneck flags by stage
- `downtime_follow_up_queue`: ranked actionable requests with score components and recommended action
- `maintenance_bottleneck_summary`: delay concentration by active workflow stage
- `equipment_delay_summary`: downtime concentration by equipment
- `production_line_delay_summary`: downtime concentration by line
- `parts_waiting_summary`: wait hours and blocked request count by part

## Ops Tables

Ops tables make the pipeline observable and keep data trust visible.

- `pipeline_runs`
- `data_quality_check_results`

## Main Relationships

- Maintenance request belongs to equipment and production line.
- Stage events belong to a maintenance request.
- Work order belongs to a maintenance request and may reference technician and part.
- Inspection result belongs to a maintenance request.
- Sensor alert belongs to equipment and may link to a maintenance request.

## Modeling Notes

- Event history is used for state reconstruction because stage duration and delay cannot be trusted from a single current-status field.
- Terminal `COMPLETED` requests remain available in timelines, but completed stages are excluded from actionable bottleneck summaries.
- The follow-up queue is an analytics table rather than an editable task list. It represents what the pipeline recommends based on the latest trusted run.
