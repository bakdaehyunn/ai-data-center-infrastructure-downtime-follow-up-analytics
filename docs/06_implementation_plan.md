# Implementation Plan

## 1. Implementation Principle

Build the data system before the UI.

Recommended order:

```text
data model
-> pipeline
-> analytics
-> API
-> UI
-> verification
```

The project depth comes from data modeling, pipeline logic, analytics, and operational decision support.

## 2. Phase 0: Repository Setup

Goal:

- Create the baseline project structure.

Expected structure:

```text
backend/
frontend/
docs/
docker-compose.yml
README.md
```

Backend stack:

```text
Python
FastAPI
SQLAlchemy
Alembic
Pydantic
pytest
```

Frontend stack:

```text
React
TypeScript
Vite
Recharts
TanStack Table
```

Database:

```text
PostgreSQL
```

Infra:

```text
Docker Compose
```

Deliverables:

- Local PostgreSQL can start.
- Backend health check works.
- Frontend dev server works.
- Basic README exists.

## 3. Phase 1: Database Schema

Goal:

- Create raw, core, analytics, and ops schemas.

Tasks:

```text
Define SQLAlchemy models
Create Alembic migration
Create raw tables
Create core tables
Create analytics tables
Create ops tables
Add indexes for dashboard queries
```

Priority tables:

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

Verification:

```text
alembic upgrade head
schema exists in PostgreSQL
basic model import test passes
```

## 4. Phase 2: Sample Data Generator

Goal:

- Generate realistic data that contains meaningful bottlenecks.

Tasks:

```text
Generate departments
Generate requesters
Generate items
Generate vendors
Generate purchase requests
Generate stage events
Generate purchase orders
Generate receipts
Inject delay scenarios
Inject quality issue scenarios
```

Required scenarios:

```text
normal completed request
budget review delay
procurement review correction
PO creation delay
vendor confirmation delay
delivery delay
receiving delay
inspection delay
critical request delayed
duplicate raw record
timestamp out-of-order event
missing stage event
```

Verification:

```text
sample generation is deterministic with seed
generated data includes all required scenarios
row counts are predictable
```

## 5. Phase 3: Pipeline

Goal:

- Transform source-like data into raw, core, and analytics tables.

Tasks:

```text
Implement raw load
Implement raw quality checks
Implement core transformation
Implement core quality checks
Implement analytics build
Implement pipeline run logging
Implement rejected row handling or minimum error logging
```

Command:

```bash
python -m app.pipeline run --generate-sample --sample-dir generated/sample_data
```

Verification:

```text
pipeline creates raw/core/analytics rows
pipeline_runs records SUCCESS/PARTIAL_SUCCESS/FAILED
data_quality_check_results records expected warnings/errors
critical_request_queue is populated
```

## 6. Phase 4: Analytics Logic

Goal:

- Calculate bottlenecks and priority.

Tasks:

```text
Calculate current request status from events
Calculate stage lead times
Calculate delay hours against thresholds
Calculate bottleneck summaries
Calculate vendor delay summaries
Calculate department summaries
Calculate critical request priority score
Generate recommended_action and reason_summary
```

Priority score:

```text
total_priority_score =
  criticality_score
+ delay_score
+ business_impact_score
+ needed_by_urgency_score
+ vendor_risk_score
```

Verification:

```text
known delayed sample requests appear in critical queue
highest-risk sample request ranks near top
stage bottleneck summary matches seeded scenarios
vendor delay summary reflects seeded delays
```

## 7. Phase 5: Backend API

Goal:

- Expose analytics as read-only API.

Tasks:

```text
Create FastAPI app
Create DB session setup
Create Pydantic response schemas
Implement /api/health
Implement /api/overview
Implement /api/bottlenecks/stages
Implement /api/bottlenecks/vendors
Implement /api/requests/critical
Implement /api/requests/{request_id}
Implement /api/requests/{request_id}/timeline
Implement /api/pipeline-runs
Implement /api/data-quality/checks
Implement /api/data-quality/checks/{check_result_id}
Implement /api/metadata/filters
```

Department-level bottleneck endpoint can be added after the first real-data dashboard foundation.

Verification:

```text
pytest API tests pass
OpenAPI docs render
dashboard endpoints return seeded data
request detail returns timeline and lead time breakdown
```

## 8. Phase 6: Frontend Dashboard

Goal:

- Build an operational dashboard that uses real API data.

Tasks:

```text
Set up Vite React TypeScript app
Create API client
Create layout and navigation
Build Operations Overview
Build Bottleneck Analysis
Build Critical Request Queue
Build Request Detail
Build Vendor / Department Analysis
Build Pipeline & Data Quality
Add loading, empty, and error states
Add filters
```

Verification:

```text
frontend runs locally
all screens load real API data
critical queue row navigates to detail
charts match API data
pipeline/data quality warnings are visible
```

## 9. Phase 7: Documentation

Goal:

- Explain the project clearly.

Tasks:

```text
Write README
Finalize project brief
Finalize architecture
Finalize data model
Finalize pipeline spec
Finalize OpenAPI contract
Finalize UI spec
Finalize verification plan
```

README should explain:

```text
what problem this solves
what it is not
how to run locally
how to run pipeline
how to open dashboard
how to run tests
key design decisions
```

## 10. Phase 8: Verification

Goal:

- Ensure the project is reproducible and portfolio-ready.

Checks:

```text
docker compose up works
database migrations run
pipeline runs from clean DB
backend API tests pass
frontend builds
dashboard displays seeded bottlenecks
data quality page shows expected checks
```

Optional checks:

```text
ruff or formatter
mypy or pyright
frontend lint
Playwright smoke test
```

## 11. Suggested Build Order

```text
1. docs
2. docker compose + PostgreSQL
3. backend skeleton
4. Alembic schema
5. sample data generator
6. pipeline
7. analytics SQL/service logic
8. API endpoints
9. frontend dashboard
10. verification and README
```

## 12. V1 Completion Criteria

V1 is complete when:

- Sample data can be generated.
- Pipeline can load and transform data.
- Data quality checks are recorded.
- Analytics tables are populated.
- API exposes overview, bottlenecks, critical queue, request detail, pipeline runs, and data quality.
- React dashboard uses real API data.
- Seeded bottleneck scenarios are visible in the UI.
- Documentation explains the business problem and design decisions.
