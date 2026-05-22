# Architecture

## 1. Architecture Goal

Critical Procurement Bottleneck Analytics is not a transaction system for creating or approving purchase requests.

It is an operational analytics system that ingests procurement process data, stores it in PostgreSQL, validates it, transforms it into a clean domain model, and exposes bottleneck analysis through an API and dashboard.

Goals:

- Reconstruct procurement request state flow.
- Calculate stage duration and delay.
- Identify bottlenecks by request, stage, department, vendor, and item category.
- Rank critical requests by operational priority.
- Show pipeline run logs and data quality results.

## 2. High-Level Architecture

```text
Sample Data / CSV-like Source
        |
        v
Python Pipeline
        |
        v
PostgreSQL
  - raw tables
  - core tables
  - analytics tables
  - ops tables
        |
        v
FastAPI Backend
        |
        v
React Dashboard
```

## 3. Main Components

### 3.1 Data Source

V1 does not integrate with a real ERP or procurement system.

Data is generated locally as realistic source-like procurement data. The generated data must include normal records, delayed records, rejected or corrected records, vendor delays, receiving delays, inspection delays, and intentional data quality issues.

### 3.2 Python Pipeline

The pipeline starts as Python scripts rather than Dagster.

Main steps:

```text
generate sample data
-> load raw data
-> validate raw data
-> transform into core model
-> validate core data
-> calculate analytics
-> record pipeline run result
```

Every execution records a `pipeline_run_id`.

Pipeline run metadata includes:

- Start and finish time
- Status
- Row counts
- Rejected row count
- Error message
- Data quality results
- Analytics build timestamp

### 3.3 PostgreSQL

PostgreSQL is the center of the project.

Table layers:

```text
raw
core
analytics
ops
```

Layer responsibilities:

- `raw`: source-like ingested records
- `core`: normalized procurement domain model
- `analytics`: precomputed API and dashboard models
- `ops`: pipeline runs and data quality results

Example tables:

```text
raw_purchase_requests
raw_purchase_orders
raw_vendor_updates
raw_receipts
raw_stage_events

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

### 3.4 FastAPI Backend

The backend exposes read-only analytics APIs.

It does not handle:

- Purchase request creation
- Approval or rejection commands
- Purchase order creation
- Vendor updates
- Receipt registration

Expected endpoints:

```text
GET /api/overview
GET /api/bottlenecks/stages
GET /api/bottlenecks/vendors
GET /api/bottlenecks/departments
GET /api/requests/critical
GET /api/requests/{request_id}
GET /api/requests/{request_id}/timeline
GET /api/pipeline-runs
GET /api/data-quality/checks
GET /api/metadata/filters
```

Complex calculations should be handled by the pipeline and analytics tables where practical.

### 3.5 React Dashboard

The dashboard helps operators understand what to act on first.

Screens:

- Operations Overview
- Bottleneck Analysis
- Critical Request Queue
- Request Detail
- Vendor and Department Analysis
- Pipeline and Data Quality

## 4. Data Flow

```text
1. Sample procurement data is generated.
2. Source-like records are loaded into raw tables.
3. Raw data quality checks run.
4. Raw data is transformed into normalized core tables.
5. Core data quality checks run.
6. Analytics tables are built:
   - current status
   - stage lead times
   - bottleneck summaries
   - critical request queue
   - vendor delay summaries
7. FastAPI exposes analytics data.
8. React dashboard visualizes operational blockers.
```

## 5. Why Python Scripts First

Python scripts are enough for V1.

Reasons:

- They keep the project focused.
- They make pipeline logic easy to inspect.
- They reduce orchestration overhead.
- They work cleanly in Docker Compose.
- They keep attention on data modeling, quality checks, and analytics.

Dagster can be considered later if scheduling, retries, dependency visualization, or multiple jobs become important.

## 6. Local Runtime

V1 uses Docker Compose.

Expected services:

```text
postgres
backend
frontend
```

Pipeline execution can be handled as a separate script entrypoint:

```bash
docker compose run pipeline python -m app.pipeline run --generate-sample
```

## 7. V1 Exclusions

Excluded from V1:

- Real ERP integration
- Real supplier integration
- Kafka or real-time streaming
- Kubernetes
- Complex authentication
- Role-based access control
- ML prediction
- LLM recommendations
- Full procurement transaction management

## 8. Architectural Principle

The system does not create the procurement process. It observes and analyzes procurement process data.

Implementation priority:

1. Model procurement state events correctly.
2. Store data in an analysis-friendly PostgreSQL schema.
3. Calculate bottlenecks and priorities.
4. Expose the analytical model through API and UI.
