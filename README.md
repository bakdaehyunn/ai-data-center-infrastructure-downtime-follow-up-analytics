# AI Data Center Infrastructure Downtime Follow-up Analytics

AI Data Center Infrastructure Downtime Follow-up Analytics is an operational analytics product for data center facilities teams.

It answers one practical question:

> Which AI infrastructure incidents are delaying return-to-service, where is the blocker, and what should the team follow up next?

## Why This Exists

AI data center downtime evidence rarely lives in one clean system. Incident records, workflow events, facility work orders, critical spares, vendor waits, validation results, telemetry alerts, impact snapshots, infrastructure assets, and facility zones are often scattered across different operational tools.

That creates a real follow-up problem: teams may know that work is open, but they cannot quickly tell whether GPU capacity risk is blocked by triage, engineer assignment, a spare/vendor wait, repair execution, validation, missed vendor ETA, lost redundancy, or unreliable source data.

This project builds an analytics layer for that problem. It preserves raw source records, normalizes them into a data center infrastructure model, reconstructs state from event history, checks trust issues, and produces a ranked follow-up queue.

## Operating Scenario

The modeled AI data center infrastructure workflow is:

```text
Incident Reported
-> Facilities Triage
-> Engineer Assigned
-> Spare/Vendor Waiting
-> Repair In Progress
-> Validation
-> Restored
```

The workflow labels are not the main value. The value is turning every transition into analytical evidence:

- how long an incident waited
- where delay accumulated
- whether the delay is still actionable
- which asset and zone are affected
- how much rack, GPU, power, thermal, redundancy, and vendor exposure is attached to the incident
- whether the evidence is trustworthy
- what follow-up action is most useful now

## What It Analyzes

- Open infrastructure incidents and delayed incidents
- Current stage and hours in current stage
- Stage lead time compared with threshold hours
- Actionable bottlenecks, excluding terminal restored work from bottleneck charts
- Downtime concentration by infrastructure asset and facility zone
- Spare/vendor waiting impact and stock risk
- Capacity-at-risk, affected GPU, redundancy-loss, thermal-breach, vendor ETA, and mitigation context
- Repeat failure signals
- Facilities engineer assignment and validation delays
- Latest-run data quality and reconciliation issues
- Ranked downtime follow-up queue with recommended actions

## Architecture

```text
scattered AI infrastructure source records
  -> raw source-preserving tables
  -> core AI infrastructure tables
  -> analytics tables
  -> reconciliation issues
  -> read-only FastAPI endpoints
  -> React dashboard
```

The pipeline computes analytics before API reads. The API is read-only because the product is an operational decision layer, not a replacement for the incident, work order, telemetry, or inventory systems of record.

## Data Layers

- `raw_*`: source-shaped records with source IDs and pipeline run IDs for ingestion traceability
- core tables: `infrastructure_zones`, `infrastructure_assets`, `infrastructure_incidents`, `incident_stage_events`, `facilities_engineers`, `critical_spares`, `facility_work_orders`, `validation_results`, `telemetry_alerts`, and `infrastructure_impact_snapshots`
- analytics tables: current status, stage lead times, follow-up queue with impact score components, bottleneck summary, asset delay summary, zone delay summary, and spare waiting summary
- ops tables: pipeline runs, data quality check results, and reconciliation issues

## Backend Responsibilities

- Generate deterministic AI data center infrastructure sample data
- Load source-shaped raw records with duplicate rejection
- Run raw and core data quality checks
- Reconstruct current incident state from workflow events
- Calculate stage lead time and delay hours
- Build downtime, bottleneck, asset, zone, and spare summaries
- Detect reconciliation issues between core state, event history, and analytics outputs
- Score follow-up priority using downtime, criticality, urgency, repeat failure, spare/vendor risk, capacity risk, redundancy risk, thermal risk, vendor ETA risk, and mitigation credit
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
GET /api/follow-ups/{incident_id}
GET /api/follow-ups/{incident_id}/timeline
GET /api/impact/summary
GET /api/downtime/stages
GET /api/assets/delays
GET /api/zones/delays
GET /api/spares/waiting
GET /api/metadata/filters
GET /api/pipeline-runs
GET /api/data-quality/checks
GET /api/data-quality/checks/{check_result_id}
```

Compatibility routes for the earlier naming are still available for asset, zone, and spare summaries.

## Dashboard

The React dashboard is built for follow-up decisions:

- KPI summary for open incidents, delayed incidents, critical delayed assets, capacity at risk, affected GPUs, redundancy loss, missed vendor ETA, spare/vendor wait hours, and latest-run data trust
- Filterable downtime follow-up queue with compact impact badges
- Incident drilldown with stage history, score components, work order context, spare context, impact snapshot context, telemetry evidence, vendor/mitigation status, and quality flags
- Stage bottleneck chart focused on active delay stages
- Asset and zone impact summaries
- Spare/vendor waiting and data trust panels

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
