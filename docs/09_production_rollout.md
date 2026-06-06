# Production Rollout Plan

## Production Intent

This system is a read-only operational intelligence layer. In production it should sit beside the incident, work order, inventory, vendor, telemetry, and validation systems. It should not mutate those systems until operators trust the reconstructed state and follow-up recommendations.

## Deployment Shape

Minimum practical deployment:

```text
source extracts
  -> scheduled pipeline container
  -> PostgreSQL analytics database
  -> FastAPI read-only API
  -> React static frontend
  -> operator follow-up workflow
```

The current repository supports the database with Docker Compose and exposes a health endpoint at `/api/health`. Backend and frontend Dockerfiles provide a portable build target for local or platform deployment.

## Scheduled Pipeline

Run the pipeline on a schedule that matches operator handoff needs. A practical first cadence is every 15 minutes during active operations and hourly during low-risk periods.

Example command:

```bash
cd backend
python -m app.pipeline run --generate-sample --sample-dir generated/sample_data
```

Production would replace `--generate-sample` with mounted extracts or connector output from the real source systems. The pipeline is idempotent at the raw layer through source-system and source-record IDs.

## Health and Readiness

Required checks:

- API liveness: `GET /api/health` returns `status=ok`.
- Latest pipeline status: `GET /api/pipeline-runs` shows the newest run and whether it is `SUCCESS`, `PARTIAL_SUCCESS`, or `FAILED`.
- Data quality status: `GET /api/data-quality/checks?status=FAILED` shows current source and reconciliation trust issues.
- Queue freshness: newest pipeline run finished within the expected schedule interval.
- Follow-up availability: `GET /api/follow-ups` returns ranked active incidents or an empty list without API errors.

## Basic Observability

The first production signals should be simple and tied to operator trust:

- Pipeline duration, status, rows extracted, rows loaded, and rows rejected.
- Failed data quality check count by target table and check name.
- Open reconciliation issue count by issue type and severity.
- Follow-up queue size and count of high-priority active incidents.
- Count of `WARNING` and `UNVERIFIED` impact-confidence rows.
- API request errors and latency for read-only endpoints.

Tracing or a metrics backend can be added later, but the first release should prove that operators can see whether the latest decision output is fresh and trustworthy.

## Data Quality Report

The data quality report should answer:

- Did the latest pipeline run finish?
- Which source feeds failed quality checks?
- Which incidents have state reconstruction or impact trust issues?
- Which issues block use of a recommendation versus merely requiring source review?

The API already exposes the report inputs through `/api/pipeline-runs` and `/api/data-quality/checks`. A production job can export those responses to a shift-handoff note or incident-review packet.

## Rollout Phases

1. Shadow mode: run the pipeline from source extracts and compare the queue with manual shift-handoff decisions.
2. Operator review: let supervisors use the queue while keeping existing source systems as the authority.
3. Trust calibration: tune thresholds, priority weights, and reconciliation labels based on false positives and missed blockers.
4. Operational adoption: make the queue the default shift-handoff view for infrastructure downtime.
5. Automation candidates: only after trust is proven, consider notifications, ticket comments, or workflow nudges.

## Rollback

Rollback is operationally simple because the API is read-only:

- Stop the scheduled pipeline.
- Serve the previous frontend build.
- Point operators back to existing systems of record.
- Keep the analytics database for post-incident review unless data retention rules require deletion.

No rollback should mutate incident, work order, inventory, vendor, telemetry, or validation systems.

## Later Kubernetes Option

A Kubernetes `CronJob` can run the scheduled pipeline after the Dockerized job is stable. Kubernetes should remain a deployment mechanism, not the main project story. Add it when operations need cluster-native scheduling, secrets management, resource limits, and restart policy.
