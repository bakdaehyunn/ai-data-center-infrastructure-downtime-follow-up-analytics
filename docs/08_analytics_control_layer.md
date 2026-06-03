# Analytics Control Layer

## Purpose

The analytics control layer handles scattered AI data center infrastructure evidence before the dashboard relies on it.

It connects four concerns:

- source preservation
- canonical core modeling
- event-based state reconstruction
- reconciliation checks for trusted analytics outputs

## Scattered Evidence

Downtime follow-up may depend on:

- incident records
- stage transition events
- facility work orders
- critical spare and vendor status
- validation results
- telemetry alerts
- impact snapshots for capacity, redundancy, vendor ETA, mitigation, and telemetry readings
- infrastructure asset master data
- data center zone context

No single source answers which incident is blocked, why it is blocked, and what the team should do next.

## Canonical Model

Canonical means the product's standard internal format. The current core model uses:

- `infrastructure_zones`
- `infrastructure_assets`
- `facilities_engineers`
- `critical_spares`
- `infrastructure_incidents`
- `incident_stage_events`
- `facility_work_orders`
- `validation_results`
- `telemetry_alerts`
- `infrastructure_impact_snapshots`

This keeps analytics independent from source-specific message formats.

## State Reconstruction

`analytics_builder.py` reconstructs workflow state from `incident_stage_events`.

Implementation examples:

- `_events_by_request()` groups events by `incident_id` and sorts by `(occurred_at, event_id)`.
- `_build_lead_time_records()` treats `ENTERED_STAGE` as the stage start.
- `_find_stage_exit_time()` searches for the configured stage exit event or `INCIDENT_RESTORED`.
- Open stages use `as_of_time` as the temporary exit time.
- The default `as_of_time` is calculated from workflow transition events only, so evidence events such as `REDUNDANCY_LOST`, `LOAD_SHIFTED`, or `VENDOR_ETA_MISSED` do not accidentally lengthen stage durations.

The lead-time rule is:

```text
duration_hours = exited_at_or_as_of - entered_at
delay_hours = max(duration_hours - threshold_hours, 0)
```

Current stage output is materialized into `incident_current_status`. Stage durations are materialized into `incident_stage_lead_times`.

## Analytics Materialization

`analytics_builder.build_analytics()` clears and rebuilds calculated tables:

- `incident_current_status`
- `incident_stage_lead_times`
- `downtime_follow_up_queue`
- `infrastructure_bottleneck_summary`
- `asset_delay_summary`
- `zone_delay_summary`
- `spare_waiting_summary`

The follow-up queue excludes `RESTORED` incidents and scores active incidents using asset criticality, estimated downtime, current stage delay, zone impact, needed-by urgency, repeat failure, spare risk, capacity risk, redundancy risk, thermal risk, vendor ETA risk, and mitigation credit.

V1.1 impact context uses the latest `infrastructure_impact_snapshots` row per incident and materializes these score components into `downtime_follow_up_queue`:

- `capacity_risk_score`
- `redundancy_risk_score`
- `thermal_risk_score`
- `vendor_eta_risk_score`
- `mitigation_credit_score`

The mitigation score is a credit. It reduces final priority when evidence shows load shifting, degraded operation, or verified normal state has reduced immediate exposure.

Concrete examples in the deterministic sample data:

- `INC-0007` has `N-1` redundancy, 320 affected GPUs, 900 kW at risk, and `ETA_MISSED`, so it ranks first with a missed-vendor-ETA action.
- `INC-0004` has cooling redundancy loss, 256 affected GPUs, 620 kW at risk, thermal breach evidence, and `LOAD_SHIFTED`, so the queue still ranks it high while recording a mitigation credit.
- `INC-0006` has thermal validation risk and load-shift mitigation, so its drilldown separates validation delay from impact context.

## Data Quality

Raw checks validate source records before core transformation:

- duplicate source record
- missing required fields
- invalid date format
- missing source references
- unknown source system

Core checks validate normalized records:

- incident without stage event
- event before incident reporting
- work order without incident
- spare/vendor waiting without required spare
- validation without completed work
- telemetry alert without known asset

Impact snapshots are loaded after incident, asset, and zone references exist. Snapshots with unknown references are skipped before analytics output is materialized.

## Reconciliation

`reconciler.run_reconciliation_checks()` runs after analytics materialization. It persists issues in `infrastructure_reconciliation_issues` and scopes them to the pipeline run.

Current issue types:

- `state_reconstruction_missing_stage_event`
- `state_reconstruction_stage_mismatch`
- `state_reconstruction_missing_completion_event`
- `state_reconstruction_active_with_completion_event`
- `event_sequence_before_request`
- `spare_waiting_missing_required_spare`
- `validation_without_completed_work`
- `analytics_output_missing_current_status`

Examples from the seeded data:

- `INC-QA-NO-STAGE` creates a missing-stage-event issue and a missing-current-status analytics issue.
- `INC-0004` creates `spare_waiting_missing_required_spare` because `MWO-QA-NO-PART` is waiting on a spare/vendor without a required spare.
- `INC-0002` creates `validation_without_completed_work` because a validation record exists before completed work evidence.

## API Exposure

Drilldown quality flags combine latest-run failed data quality checks and latest-run open reconciliation issues.

Drilldown also exposes the latest impact snapshot and its telemetry readings. This makes the follow-up row explain both the workflow blocker and the operational exposure attached to that blocker.

`routes._quality_flags_for_request()` translates issue types into operator-facing labels such as:

- `Spare or vendor evidence mismatch`
- `State reconstruction mismatch`
- `State reconstruction gap`
- `Validation sequence mismatch`

## Trust Boundary

The analytics output should be treated as trusted only after raw checks, core checks, impact snapshot loading, analytics build, and reconciliation checks have run for the same pipeline run.
