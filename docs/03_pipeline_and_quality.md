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

## Operational Cadence

In production, the pipeline should run on a schedule that matches shift handoff and incident response needs. A first production cadence can be every 15 minutes during active operations and hourly during quiet periods.

The pipeline is batch-oriented by design. That keeps the V1 operating contract simple:

- each run has a `pipeline_run_id`
- raw records preserve source IDs
- duplicate records are rejected idempotently
- data quality and reconciliation results are scoped to the latest run
- the API reads already-materialized analytics outputs

Streaming or orchestration tools should be added only when source latency or operational scale requires them.

## Raw Quality Checks

- Unknown source system
- Duplicate source record
- Missing required payload fields
- Invalid date format
- Missing source incident references

## Core Quality Checks

- Incident without stage event
- Stage event timestamp before incident reporting
- Workflow ontology incident vocabulary
- Workflow ontology stage event vocabulary
- Workflow ontology impact vocabulary
- Workflow ontology transition rules
- Workflow ontology zone and asset vocabulary
- Workflow ontology topology dependency vocabulary
- Workflow ontology spare, work order, validation, and telemetry vocabulary
- Work order without incident
- Spare/vendor waiting without required spare
- Validation without completed infrastructure work
- Telemetry alert without known asset

Infrastructure dependency edges are loaded as master/reference data after assets are known. Invalid topology references are skipped before analytics is built. Core quality checks then validate dependency type, dependency role, known-asset references, and self-dependency errors.

Impact snapshots are loaded after core incidents, assets, and zones are known. Invalid incident, asset, or zone references are skipped before analytics is built.

The workflow ontology checks are application-level checks backed by `backend/app/domain/infrastructure_ontology.py`. They validate controlled vocabulary, event progression, and topology edge semantics without introducing graph storage or a new ontology runtime dependency. RDF/OWL-lite output is exposed separately as an additive semantic export.

## Reconciliation Checks

- Core current stage does not match latest entered-stage event
- Restored incident missing restore event
- Active incident contains restore event
- Stage event occurred before incident reporting
- Spare/vendor wait lacks required spare evidence
- Validation exists before completed work
- Core incident missing generated current-status analytics row
- Invalid workflow vocabulary
- Invalid stage event type for a stage
- Duplicate entered-stage evidence
- Invalid stage progression
- Invalid restored-state evidence
- Active high-impact incident missing impact snapshot
- Material impact event newer than latest impact snapshot
- Redundancy event and impact snapshot disagree
- Vendor ETA event and impact snapshot disagree
- Vendor ETA is past but not marked missed
- Mitigation status lacks matching event evidence
- Thermal breach lacks abnormal telemetry evidence
- Critical GPU/capacity incident has unexplained zero impact

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

The ranking model was reviewed during the ontology hardening pass, but scoring weights and queue order are intentionally unchanged. Tuning overdue commitment scoring, false positives, or missed blockers should happen as a separate trust-calibration change after operator review.

## Impact Confidence

Impact confidence is derived from latest-run reconciliation issues:

- `TRUSTED`: latest impact snapshot exists and no open impact reconciliation issue exists for the incident
- `WARNING`: latest impact snapshot exists, but one or more impact reconciliation issues are open
- `UNVERIFIED`: active incident has no usable impact snapshot

The dashboard uses this confidence state to separate the operational priority score from the trustworthiness of the impact evidence behind that score.

## Latest-Run Scoping

API quality endpoints default to the latest pipeline run. Drilldown quality flags also use latest-run data quality and reconciliation results.

## Data Quality Report

The latest-run report should be used during shift handoff:

```text
GET /api/pipeline-runs
GET /api/data-quality/checks?status=FAILED
GET /api/impact/summary
```

Operators should treat `PARTIAL_SUCCESS` as usable only after reviewing failed checks. A warning or unverified impact row can still be operationally important, but the source evidence should be checked before relying on the impact context.

## Production Acceptance Signals

The pipeline is production-ready only when the team can answer:

- Did the latest scheduled run finish within the expected interval?
- How many source rows were extracted, loaded, and rejected?
- Which quality checks failed, and which incidents are affected?
- Which reconciliation issues are open by severity?
- How many follow-up rows have trusted, warning, or unverified impact context?
- Does the top-ranked follow-up match operator judgment during shadow mode?
