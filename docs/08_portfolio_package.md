# Portfolio Package

## GitHub Repository Description

Operational procurement bottleneck analytics system with a Python pipeline, PostgreSQL analytical model, FastAPI API, and React dashboard.

## GitHub Topics

```text
fastapi
postgresql
sqlalchemy
alembic
react
typescript
vite
data-pipeline
data-quality
operational-analytics
procurement
dashboard
```

## Pinned Repository Blurb

Critical Procurement Bottleneck Analytics is an operational data system that answers: which procurement requests are blocking important work, where are they delayed, and what should teams handle first? It includes deterministic source data generation, raw/core/analytics PostgreSQL modeling, Python pipeline execution, data quality checks, FastAPI analytics endpoints, and a React dashboard backed by real API data.

## 2-Minute Demo Script

### 1. Problem

This project is not a purchase approval CRUD app. It starts after procurement workflow data already exists.

The operational problem is:

> When many purchase requests are moving through budget review, procurement review, PO creation, vendor confirmation, delivery, receiving, and inspection, which delayed request matters most and where should the team act first?

### 2. Data System

The system generates deterministic procurement source data with realistic scenarios: normal completed requests, budget review delay, vendor confirmation delay, delivery delay, receiving delay, inspection delay, and intentionally bad records.

The Python pipeline then:

- loads source-like records into raw tables
- runs raw data quality checks
- transforms records into normalized core tables
- runs core data quality checks
- builds analytics tables for current status, stage lead times, bottleneck summaries, vendor delay summaries, and the critical request queue
- records pipeline runs and check results

### 3. Backend

The FastAPI backend is read-only. It exposes analytics endpoints such as:

- `/api/overview`
- `/api/requests/critical`
- `/api/requests/{request_id}`
- `/api/bottlenecks/stages`
- `/api/bottlenecks/vendors`
- `/api/data-quality/checks`

The backend does not create purchase requests or approvals. It exposes the operational analysis layer.

### 4. Dashboard

The React dashboard uses real API data.

The first screen shows:

- open requests
- delayed requests
- critical open requests
- total delay hours
- top bottleneck stage
- data quality status

The critical request queue ranks requests by criticality, delay, urgency, business impact, and vendor risk.

Clicking a row opens the request drilldown, which shows:

- current stage and priority score
- recommended action
- stage lead times
- event timeline
- related purchase order and receipt state
- quality flags

### 5. Technical Point

The main technical point is stateful operational modeling. The system reconstructs process state from event history, validates data quality, calculates delays against thresholds, and turns that into an action queue.

This is the next level beyond CRUD: not just storing workflow state, but analyzing workflow behavior and helping operators decide where to act.

## Short Interview Explanation

I built this because my work experience involved approval workflows, status transitions, and external system follow-up. I wanted to move that experience into a more operationally critical domain.

So instead of building another transaction system, I built a data system around procurement bottlenecks. It models workflow events, calculates stage lead times, checks data quality, records pipeline runs, exposes analytics through FastAPI, and visualizes the output in React.

The project shows that I can think about business process state, data reliability, backend APIs, and operational decision support as one system.

## Suggested Demo Flow

1. Open the README and explain the core question.
2. Show the architecture diagram in README.
3. Run or show the pipeline output:

```bash
python -m app.pipeline run --generate-sample --sample-dir generated/sample_data
```

4. Show `/api/overview` or FastAPI docs.
5. Open the dashboard.
6. Point to `Vendor Confirmation` as the top bottleneck.
7. Click `PR-2026-0005`.
8. Explain the request drilldown: stage lead time, timeline, PO state, quality flags.
9. Close with the design idea: event history becomes operational priority.

## Next Improvements

- Add department bottleneck endpoint and dashboard section.
- Split the dashboard into routed views.
- Add automated browser smoke tests.
- Add a short demo video or hosted deployment.
