# Pipeline and Quality

## Pipeline Steps

1. Read or generate deterministic AI data center source files.
2. Run raw quality checks before insertion.
3. Load raw records with duplicate rejection.
4. Transform valid raw records and impact context files into the core model.
5. Run core quality checks.
6. Build analytics tables.
7. Run reconciliation checks between core, event history, and analytics outputs.
8. Commit the pipeline run with load, quality, analytics, and reconciliation counts.

## Raw Quality Checks

- Unknown source system
- Duplicate source record
- Missing required payload fields
- Invalid date format
- Missing source incident references

## Core Quality Checks

- Incident without stage event
- Stage event timestamp before incident reporting
- Work order without incident
- Spare/vendor waiting without required spare
- Validation without completed infrastructure work
- Telemetry alert without known asset

Impact snapshots are loaded after core incidents, assets, and zones are known. Invalid incident, asset, or zone references are skipped before analytics is built.

## Reconciliation Checks

- Core current stage does not match latest entered-stage event
- Restored incident missing restore event
- Active incident contains restore event
- Stage event occurred before incident reporting
- Spare/vendor wait lacks required spare evidence
- Validation exists before completed work
- Core incident missing generated current-status analytics row

## Terminal Stage Behavior

Terminal `RESTORED` records remain available in timelines and lead-time outputs. They are excluded from actionable bottleneck summaries and follow-up queue rows so the dashboard focuses on active work.

Impact evidence events such as `REDUNDANCY_LOST`, `LOAD_SHIFTED`, `VENDOR_ETA_UPDATED`, and `VENDOR_ETA_MISSED` enrich the timeline but do not change stage lead-time calculations. The analytics builder calculates its default `as_of` time from workflow transition events only.

## Impact Context Behavior

The latest impact snapshot per incident is used during follow-up scoring. The queue adds:

- capacity risk from affected GPUs and estimated kW at risk
- redundancy risk from `N`, `N-1`, power redundancy loss, or cooling redundancy loss
- thermal risk from breach minutes
- vendor ETA risk from missed or waiting vendor statuses
- mitigation credit for load shifting, degraded operation, or verified normal state

The final priority score increases when capacity, redundancy, thermal, or vendor risk is high and decreases when mitigation evidence reduces immediate exposure.

## Latest-Run Scoping

API quality endpoints default to the latest pipeline run. Drilldown quality flags also use latest-run data quality and reconciliation results.
