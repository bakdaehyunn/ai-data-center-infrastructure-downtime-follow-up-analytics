# Operational Case Study

## Problem

AI data center incidents were delayed because facilities, reliability, and capacity teams could not see blocker, owner, spare/vendor status, validation state, impact, and data trust in one place. Operators knew incidents were open, but they could not quickly decide which incident to chase next to restore GPU capacity safely.

## Discovery

The customer's shift handoff depended on manual checks across incident tickets, work orders, spare inventory notes, vendor updates, validation records, telemetry alerts, and capacity-impact snapshots. The most expensive delay was not a single repair task. It was decision latency: supervisors spent time reconstructing state before they could take action.

The core discovery question became:

> What follow-up action should the operator take next, and how much should they trust the evidence behind that recommendation?

## Data Sources

The prototype simulates fragmented source systems:

- Incident records for priority, current status, asset, zone, downtime, and needed-by time.
- Stage events for workflow reconstruction.
- Facility work orders for owner, team, execution status, and spare links.
- Critical spares for category, stock status, lead time, and criticality.
- Vendor ETA context for confirmed, waiting, or missed recovery support.
- Validation results for return-to-service readiness.
- Telemetry alerts for thermal, power, and sensor evidence.
- Impact snapshots for affected racks, GPUs, kW at risk, redundancy state, mitigation, and telemetry readings.

Raw records are preserved before transformation so data engineers can trace an analytics output back to source evidence.

## Workflow Model

The workflow model reconstructs active state from event history:

```text
Incident Reported
-> Facilities Triage
-> Engineer Assigned
-> Spare/Vendor Waiting
-> Repair In Progress
-> Validation
-> Restored
```

Each stage has a threshold. Delay is calculated from stage entry to stage exit, or to the analytics as-of time for open stages. Restored incidents remain visible in timelines but are excluded from active bottleneck and follow-up surfaces.

## System Design

The system builds a decision layer:

```text
raw source records
  -> canonical infrastructure model
  -> state reconstruction
  -> follow-up scoring
  -> reconciliation and trust flags
  -> read-only API
  -> queue-first operator UI
```

The follow-up queue is the product core. It ranks active incidents by recovery delay, blocker stage, asset and zone impact, needed-by urgency, repeat failure, spare/vendor risk, capacity risk, redundancy risk, thermal risk, vendor ETA risk, and mitigation credit.

The queue separates:

- Action: what the operator should do next.
- Rationale: why the incident matters.
- Trust: whether the evidence is reliable enough for decision-making.

## Tradeoffs

- Batch pipeline over streaming: chosen to prove reconciliation, state reconstruction, and trust logic before adding operational complexity.
- Read-only API over workflow mutation: chosen because the product should not become a new system of record before operators trust it.
- Deterministic sample data over live connectors: chosen to make tests, demos, and technical review reproducible.
- Queue-first UI over dashboard-first UI: chosen because the operational decision is the primary value.
- Latest-run trust over historical trust blending: chosen so stale quality issues do not contaminate the current shift view.

## Production Rollout Plan

Rollout starts in shadow mode. The pipeline runs on scheduled extracts, and supervisors compare the ranked queue with their manual handoff decisions. After the team trusts the queue, the product becomes the default return-to-service follow-up view.

Production monitoring focuses on:

- Pipeline freshness and status.
- Rows extracted, loaded, and rejected.
- Failed quality checks.
- Open reconciliation issues.
- Follow-up queue size and high-priority count.
- Impact-confidence distribution.
- API health and read latency.

Kubernetes, CronJobs, and richer observability are later deployment choices. They should be added when they improve reliability, not to make the story look more technical.

## Measured Impact

Expected first-release measurements:

- Shift-handoff reconstruction time decreases because blocker, owner, spare/vendor, validation, impact, and trust context are joined.
- Missed vendor ETA follow-ups decrease because stale or missed ETA evidence is flagged.
- Validation delays become visible because validation is modeled as an explicit stage.
- Capacity risk is prioritized more consistently because GPU, kW, redundancy, and thermal exposure are part of the score.
- Data trust improves because duplicate records, missing events, stale snapshots, and inconsistent statuses are visible in the same workflow.

In the deterministic sample data, the system correctly ranks `INC-0007`, `INC-0004`, and `INC-0006` as the top follow-ups because they combine active blockers with high infrastructure impact and trust-sensitive vendor or mitigation context.
