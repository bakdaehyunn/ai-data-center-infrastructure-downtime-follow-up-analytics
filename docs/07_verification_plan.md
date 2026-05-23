# Verification Plan

## 1. Verification Goal

Verification should prove more than "the app runs."

It must prove:

- Procurement state events are loaded correctly.
- The pipeline builds raw, core, analytics, and ops data.
- Data quality issues are detected and recorded.
- Bottleneck analysis matches seeded scenarios.
- Critical Request Queue ranks meaningful blockers.
- API responses support the dashboard.
- UI shows seeded bottleneck scenarios clearly.

## 2. Verification Levels

```text
1. Schema verification
2. Pipeline verification
3. Data quality verification
4. Analytics verification
5. API verification
6. UI verification
7. End-to-end verification
```

## 3. Schema Verification

Goal:

- Confirm PostgreSQL schema has the intended layers.

Checks:

```text
alembic upgrade head succeeds
required tables exist
foreign key constraints exist
important indexes exist
model imports do not fail
```

Required tables:

```text
purchase_requests
purchase_orders
vendors
departments
items
receipts
procurement_stage_events
request_current_status
request_stage_lead_times
critical_request_queue
bottleneck_summary
vendor_delay_summary
pipeline_runs
data_quality_check_results
```

## 4. Pipeline Verification

Goal:

- Confirm a clean database can be populated and analyzed.

Checks:

```text
sample data generation is deterministic
raw tables are populated
core tables are populated
analytics tables are populated
pipeline_runs has one completed run
rows_extracted, rows_loaded, rows_rejected are recorded
```

Expected command:

```bash
python -m app.pipeline run --generate-sample --sample-dir generated/sample_data
```

Expected result:

```text
pipeline status = SUCCESS or PARTIAL_SUCCESS
critical_request_queue row count > 0
bottleneck_summary row count > 0
request_stage_lead_times row count > 0
```

## 5. Data Quality Verification

Goal:

- Confirm seeded data quality issues are detected.

Seeded quality issues:

```text
duplicate source record
missing required field
event timestamp out of order
request without stage event
```

Additional core quality checks exist for purchase order references, receipt references, closed request evidence, and date consistency. In the current seeded dataset these additional checks are expected to pass.

Checks:

```text
data_quality_check_results contains expected check names
severity is assigned correctly
WARNING does not stop pipeline
CRITICAL stops analytics build if configured
failed_row_count is greater than 0 for seeded issues
sample_failed_keys are recorded
```

## 6. Analytics Verification

Goal:

- Confirm bottleneck and priority calculations match seeded scenarios.

Checks:

```text
known vendor confirmation delay appears in bottleneck summary
known delivery delay appears in bottleneck summary
known critical delayed request appears in critical queue
priority score ordering is stable
needed_by_date overdue requests receive higher score
vendor with seeded delays has higher delay rate
stage lead time duration is calculated correctly
```

Example assertions:

```text
CRITICAL request delayed in VENDOR_CONFIRMATION ranks in top 5
request with needed_by_date in the past has is_delayed = true
stage duration over threshold has is_bottleneck = true
vendor with repeated delayed deliveries has delay_rate > baseline vendors
```

## 7. API Verification

Goal:

- Confirm FastAPI endpoints return correct shape and data.

Test targets:

```text
GET /api/health
GET /api/overview
GET /api/bottlenecks/stages
GET /api/bottlenecks/vendors
GET /api/requests/critical
GET /api/requests/{request_id}
GET /api/requests/{request_id}/timeline
GET /api/pipeline-runs
GET /api/data-quality/checks
GET /api/metadata/filters
```

Checks:

```text
status code is 200 for valid requests
response matches schema
filters work
unknown request_id returns 404
critical queue is ordered by priority rank
request detail includes timeline and lead time breakdown
```

## 8. UI Verification

Goal:

- Confirm the dashboard displays real API data and supports operational judgment.

Manual checks:

```text
Operations Overview loads KPI values
Top bottleneck stage is visible
Critical Request Queue displays priority, reason, and recommended action
Clicking a critical request opens Request Detail
Request Detail shows timeline
Bottleneck Analysis chart matches API result
Vendor delay table shows repeated delay patterns
Pipeline and Data Quality status shows latest failed checks
Loading, empty, and error states are handled
```

Build checks:

```text
frontend build succeeds
TypeScript check succeeds
frontend lint succeeds
```

Optional smoke test:

```text
Open dashboard
Verify overview rendered
Click first critical request
Verify drilldown panel rendered
Verify data quality failures are visible
```

## 9. End-to-End Verification

Goal:

- Confirm the full project is reproducible from a clean environment.

Expected flow:

```bash
docker compose up -d postgres

cd backend
source .venv/bin/activate
python -m alembic upgrade head
python -m app.pipeline run --generate-sample --sample-dir generated/sample_data
python -m pytest
uvicorn app.main:app --reload

cd ../frontend
npm run lint
npm run build
npm run dev
```

End-to-end success criteria:

```text
database starts
schema migration succeeds
pipeline succeeds
API returns analytics data
frontend displays dashboard
seeded bottleneck scenario is visible
data quality results are visible
clicking a queue row updates the request drilldown
```

## 10. Non-Functional Verification

Checks:

```text
README run instructions work
pipeline can be rerun without corrupting data
API response time is acceptable for sample dataset
SQL queries use indexes where needed
no secrets are committed
sample data contains no real personal information
```

## 11. Portfolio Review Checklist

Before presenting the project:

```text
The project is not described as a purchase approval system.
The core problem is procurement bottleneck analytics.
The dashboard answers what to act on first.
Data model shows event history, not only current status.
Pipeline logs and data quality are visible.
README explains why this is business-useful.
Screenshots show seeded bottleneck scenarios.
V1 exclusions are clear.
```

## 12. V1 Done Definition

V1 is done when:

```text
A new developer can run the project locally from README.
Sample procurement data can be generated deterministically.
Pipeline produces raw, core, analytics, and ops records.
Data quality checks detect seeded issues.
Critical request queue ranks high-impact blockers.
API exposes required dashboard data.
Frontend renders overview, bottleneck analysis, critical queue, request drilldown, vendor delay, and data quality sections.
Tests cover pipeline, analytics, and API basics.
The project story connects stateful business workflows to operational bottleneck analysis.
```
