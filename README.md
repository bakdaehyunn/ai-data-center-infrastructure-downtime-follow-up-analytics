# Maintenance Downtime Follow-up Analytics

Maintenance Downtime Follow-up Analytics is an operational analytics product for maintenance downtime follow-up.

It answers one practical question:

> Which maintenance requests are delaying equipment return-to-service, where is the blocker, and what should the team follow up next?

## Why This Project Exists

In a production environment, downtime follow-up rarely lives in one clean table. The evidence is split across maintenance requests, workflow stage events, work orders, spare parts, inspection results, sensor alerts, equipment master data, and production line context.

That creates a common operational problem: teams can see that work is open, but they cannot quickly tell which request is hurting production, why it is stuck, whether the issue is waiting on parts or people, and which follow-up should happen first.

This project builds an analytics layer for that problem. It reconstructs the current state from event history, measures how long requests wait in each stage, checks whether the data can be trusted, and produces a ranked follow-up queue for maintenance supervisors, planners, reliability engineers, and operations teams.

## Operating Scenario

The modeled maintenance workflow is:

```text
Maintenance Request Submitted
-> Maintenance Review
-> Technician Assigned
-> Parts Waiting
-> Maintenance In Progress
-> Inspection
-> Completed
```

The key point is not the workflow labels themselves. The key point is that every stage transition becomes analytical evidence:

- how long the request waited
- where delay accumulated
- whether the delay is still actionable
- which asset or line is affected
- what follow-up action is most useful now

## What It Analyzes

- Open maintenance requests and delayed requests
- Current stage and hours in current stage
- Stage lead time compared with stage thresholds
- Actionable bottlenecks, excluding terminal completed work from bottleneck charts
- Downtime concentration by equipment and production line
- Parts waiting impact and stock risk
- Repeat failure signals
- Technician assignment and inspection delays
- Data quality issues that affect trust in the analytics
- Ranked downtime follow-up queue with recommended actions

## Architecture

```text
scattered maintenance source records
  -> raw maintenance tables
  -> core maintenance tables
  -> analytics tables
  -> read-only FastAPI endpoints
  -> React dashboard
```

The pipeline computes analytics before API reads. The API stays read-only because the product goal is operational decision support: surface what needs attention, explain why, and let existing maintenance systems remain the system of record.

## Data Layers

- `raw_*`: source-shaped records with source IDs and pipeline run IDs for ingestion traceability
- core tables: normalized maintenance entities such as equipment, production lines, requests, stage events, work orders, parts, inspections, and sensor alerts
- analytics tables: current status, stage lead times, follow-up queue, bottleneck summary, equipment delay summary, line delay summary, and parts waiting summary
- ops tables: pipeline run observability and data quality check results

## Backend Responsibilities

- Generate deterministic maintenance sample data
- Load source-shaped raw records with duplicate rejection
- Run raw and core data quality checks
- Reconstruct current request state from maintenance stage events
- Calculate stage lead time and delay hours
- Build downtime, bottleneck, equipment, line, and parts summaries
- Score follow-up priority using operational signals
- Expose read-only analytics endpoints

Run backend checks:

```bash
cd backend
.venv/bin/python -m pytest
```

Run the pipeline locally after PostgreSQL is available:

```bash
cd backend
.venv/bin/python -m app.pipeline run --generate-sample --sample-dir generated/sample_data
```

## API Surface

Primary read-only endpoints:

```text
GET /api/overview
GET /api/follow-ups
GET /api/follow-ups/{maintenance_request_id}
GET /api/follow-ups/{maintenance_request_id}/timeline
GET /api/downtime/stages
GET /api/equipment/delays
GET /api/lines/delays
GET /api/parts/waiting
GET /api/metadata/filters
GET /api/pipeline-runs
GET /api/data-quality/checks
GET /api/data-quality/checks/{check_result_id}
```

## Dashboard

The React dashboard is built for follow-up decisions:

- KPI summary for open work, delayed work, critical delayed equipment, parts wait hours, and data quality status
- Filterable downtime follow-up queue
- Request drilldown with stage history, score components, work order context, part context, and quality flags
- Stage bottleneck chart focused on active delay stages
- Equipment and production line impact summaries
- Parts waiting and data trust panels

Run the frontend build:

```bash
cd frontend
npm run build
```

## Tech Stack

- Python
- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- React
- TypeScript
- Vite
- Recharts
- Docker Compose
- pytest

## Operational Capabilities

The system is designed around production-support needs:

- reconstruct request state from workflow event history
- preserve raw source records for traceability
- normalize scattered maintenance records into a consistent operating model
- compute repeatable analytics outputs by pipeline run
- surface data quality and reconciliation flags before users rely on metrics
- expose read-only analytics APIs for dashboards and integration consumers
- rank follow-up work using downtime, delay, criticality, urgency, repeat failure, and parts risk signals
- provide drilldown context for maintenance supervisors, planners, reliability engineers, and operations teams
