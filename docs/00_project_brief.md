# Project Brief

## Product

AI Data Center Infrastructure Downtime Follow-up Analytics is a read-only operational analytics layer for AI data center facilities incidents.

It answers:

> Which AI infrastructure incidents are delaying return-to-service, where is the blocker, and what should the team follow up next?

## Operating Need

AI data center downtime evidence is scattered across incident records, workflow events, facility work orders, critical spares, vendor waits, validation records, telemetry alerts, infrastructure assets, and facility zones.

The product turns that scattered evidence into a trusted follow-up view. It does not replace the systems of record. It helps operators decide which open incident needs attention first and why.

## Users

- Facilities supervisors who need to unblock triage, assignment, repair, and validation
- Reliability engineers who need repeat failure and asset impact signals
- Operations leads who need zone-level return-to-service risk
- Data/platform engineers who need traceable analytics outputs from messy operational records

## In Scope

- AI data center infrastructure incidents
- Event-based state reconstruction
- Stage lead time and threshold-based delay
- Bottleneck summaries by stage, asset, zone, team, failure mode, priority, and spare category
- Spare/vendor waiting risk
- Data quality checks and reconciliation issues
- Read-only API and dashboard

## Out of Scope

- CRUD incident management
- Work order execution
- Inventory transactions
- Telemetry ingestion at production scale
- Automated dispatch or ticket mutation
