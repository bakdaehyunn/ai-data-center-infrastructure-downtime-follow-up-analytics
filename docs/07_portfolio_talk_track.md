# Portfolio Talk Track

## Two-Minute Explanation

This project is Maintenance Downtime Follow-up Analytics. It focuses on a practical operations problem: maintenance downtime evidence is scattered across requests, workflow events, work orders, parts, inspections, sensor alerts, equipment, and production lines. A team may know that work is open, but not which request is delaying return-to-service, why it is stuck, or what should be followed up first.

I built an analytics layer that reconstructs request state from event history, calculates stage lead time and bottlenecks, checks data quality, and produces a ranked follow-up queue. The API is read-only because the product is decision support, not transaction entry. The React dashboard shows the operating picture, the ranked queue, bottleneck and impact summaries, data trust, and request-level drilldown.

## Five-Minute Technical Explanation

The backend uses SQLAlchemy models across four layers: raw, core, analytics, and ops. Raw tables preserve source-shaped records and ingestion traceability. Core tables normalize maintenance entities. Analytics tables store current status, stage lead times, bottleneck summaries, equipment and line delay summaries, parts waiting summaries, and the downtime follow-up queue. Ops tables record pipeline runs and data quality results.

The pipeline starts with deterministic sample data, loads raw records, rejects duplicates, runs quality checks, transforms records into core tables, reconstructs stage state from events, computes lead time against thresholds, and calculates priority scores. The score combines equipment criticality, estimated downtime, current stage delay, line impact, needed-by urgency, repeat failure, and parts risk.

One important design choice is that completed stages remain in timelines but are excluded from bottleneck summaries. That keeps historical traceability while making the dashboard focus on active delay stages where follow-up is still possible.

The API exposes read-only endpoints for overview, follow-ups, request drilldown, stage downtime, equipment delays, line delays, parts waiting, pipeline runs, and data quality checks. Data quality defaults to the latest pipeline run so dashboard trust reflects the current analytics output.

## Skills Demonstrated

- workflow and state modeling
- event-history reconstruction
- operational analytics design
- data quality and data trust
- pipeline observability
- analytics API design
- backend/data platform thinking
- frontend drilldown for operational decision support

## Short Portfolio Description

Maintenance Downtime Follow-up Analytics is a backend/data portfolio project that turns scattered maintenance workflow records into a ranked follow-up queue. It uses event history to reconstruct request state, calculates stage delay and downtime impact, checks data quality, and exposes read-only analytics through FastAPI and a React dashboard.
