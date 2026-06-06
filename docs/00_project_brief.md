# Project Brief

## Product

AI Data Center Infrastructure Downtime Follow-up Analytics is a read-only operational analytics layer for AI data center facilities incidents.

It answers:

> Which AI infrastructure incidents are delaying return-to-service, where is the blocker, and what should the team follow up next?

## Operating Need

AI data center downtime evidence is scattered across incident records, workflow events, facility work orders, critical spares, vendor waits, validation records, telemetry alerts, impact snapshots, infrastructure assets, and facility zones.

The product turns that scattered evidence into a trusted follow-up view. It does not replace the systems of record. It helps operators decide which open incident needs attention first, why it matters, and whether GPU capacity, power/cooling redundancy, vendor ETA, or mitigation status changes the follow-up priority.

## Customer Discovery Brief

The fictional target customer is a regional AI infrastructure operations team running two GPU data halls for model training and hosted inference workloads. The facilities team owns power, cooling, rack sensors, and critical spare coordination. The reliability team owns incident review. The platform operations team owns customer-facing capacity commitments.

Before this system existed, the blocked decision was:

> Which open infrastructure incident should the operator chase next so GPU capacity can safely return to service?

That decision was delayed during shift handoff because no single system showed blocker, owner, spare/vendor state, validation state, evidence quality, and impact in one place. Supervisors could see open tickets, but they still had to ask separate teams whether a work order had an engineer, whether a spare was in stock, whether the vendor ETA was stale, whether thermal validation had passed, and whether capacity or redundancy exposure was real.

Discovery sessions found recurring questions:

- Facilities supervisor: "Which incident is stuck because nobody owns the next step?"
- Shift lead: "Is the vendor really late, or did the ETA just not get updated?"
- Capacity operations lead: "How many GPUs and how much power capacity are still exposed?"
- Reliability engineer: "Is this a repeat asset failure or a one-off event?"
- Data engineer: "Can operators trust the joined data, or are source events missing?"

The product requirement is not a prettier incident dashboard. It is a decision layer that reconstructs workflow state, attaches impact context, scores priority, and tells the operator the next follow-up action with the trust caveats needed to use that recommendation safely.

## Users

- Facilities supervisors who need to unblock triage, assignment, repair, and validation
- Reliability engineers who need repeat failure and asset impact signals
- Operations leads who need zone-level return-to-service risk
- Capacity and infrastructure operations leads who need affected rack, GPU, redundancy, and thermal exposure signals
- Data/platform engineers who need traceable analytics outputs from messy operational records

## Success Questions

The project should prove these questions:

- What operational decision was blocked before the system existed?
- Which source systems were fragmented?
- Which workflow states had to be reconstructed?
- Which rules decide priority?
- Which data quality issues reduce trust?
- Which follow-up action should the operator take?
- How would the system be deployed, monitored, and improved in production?

The current answer is the ranked follow-up queue. Supporting analytics explain delay and exposure, but the product succeeds only when the queue helps an operator choose the next recovery action faster and with fewer source-system checks.

## In Scope

- AI data center infrastructure incidents
- Event-based state reconstruction
- Stage lead time and threshold-based delay
- Bottleneck summaries by stage, asset, zone, team, failure mode, priority, and spare category
- Spare/vendor waiting risk
- Impact context for affected racks, affected GPUs, capacity-at-risk, redundancy state, thermal breach, vendor ETA, and mitigation status
- Data quality checks and reconciliation issues
- Read-only API and dashboard

## Out of Scope

- CRUD incident management
- Work order execution
- Inventory transactions
- Telemetry ingestion at production scale
- Automated dispatch or ticket mutation
