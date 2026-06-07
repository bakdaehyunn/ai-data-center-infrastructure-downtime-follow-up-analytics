# Workflow Ontology

The workflow ontology models AI data center infrastructure recovery as semantic
state and evidence, not as SQL application code.

## Lifecycle

```text
Incident Reported
-> Facilities Triage
-> Engineer Assigned
-> Spare/Vendor Waiting
-> Repair In Progress
-> Validation
-> Restored
```

`RESTORED` is terminal. Restored incidents remain useful as evidence and
historical timeline facts, but active follow-up queue read models should focus
on unresolved work.

## Semantic Contract

- `dcai:InfrastructureIncident` links an incident to an affected asset and
  current workflow stage.
- `dcai:WorkflowStage` provides controlled stage resources and labels.
- `dcai:FollowUpQueueItem` captures graph-backed rank, title, current status,
  current-stage duration, priority level, business impact, and score inputs.
- `dcai:FollowUpDecision` captures the next recommended operational action.
- `dcai:RecoveryBlocker` captures the current blocker finding.
- `dcai:ImpactObservation` captures capacity, GPU, rack, redundancy, thermal,
  mitigation, and vendor exposure.
- `dcai:EvidenceRecord` subclasses capture telemetry, validation, and work
  order evidence linked to incidents or impact observations.
- PROV links explain source records and reasoning activity.

## Validation

Workflow and evidence correctness is enforced through RDF parse checks, SHACL
shape checks, approved SPARQL query tests, and semantic-service result-shaping
tests. The graph must preserve source provenance before it can be promoted or
used by product read models.

## UI Boundary

The UI should show workflow state only when it improves the follow-up decision:
which item is blocked, why it matters, what evidence supports it, what the next
action is, and whether dependency impact changes urgency.
