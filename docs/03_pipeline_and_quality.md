# Pipeline and Quality

## Pipeline Steps

1. Read or generate deterministic AI data center source files.
2. Run raw quality checks before insertion.
3. Load raw records with duplicate rejection.
4. Transform valid raw records into the core model.
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

## Latest-Run Scoping

API quality endpoints default to the latest pipeline run. Drilldown quality flags also use latest-run data quality and reconciliation results.
