# Workflow Ontology and State Model

## Purpose

The workflow ontology defines how an AI infrastructure incident moves from report to safe return-to-service. It exists so the analytics layer can reconstruct state from events instead of trusting a single mutable status field.

This is an application workflow ontology with an additive RDF/OWL-lite semantic export. It is not a graph database or SPARQL-backed ontology platform. The enforceable contract lives in `backend/app/domain/infrastructure_ontology.py` and is used by pipeline quality checks and reconciliation. The Turtle export at `/api/semantic/infrastructure.ttl` projects the relational model for semantic review without changing the persistence layer.

## Lifecycle

```text
INCIDENT_REPORTED
-> FACILITIES_TRIAGE
-> ENGINEER_ASSIGNED
-> SPARE_VENDOR_WAITING
-> REPAIR_IN_PROGRESS
-> VALIDATION
-> RESTORED
```

`RESTORED` is terminal. Restored incidents remain available in timelines and lead-time records, but they are excluded from the active follow-up queue and active bottleneck summaries.

## Allowed Transitions

| Current stage | Exit event | Next stage | Operator meaning |
| --- | --- | --- | --- |
| `INCIDENT_REPORTED` | `INCIDENT_ACCEPTED` | `FACILITIES_TRIAGE` | Monitoring or operations accepted the incident for facilities review. |
| `FACILITIES_TRIAGE` | `TRIAGE_COMPLETED` | `ENGINEER_ASSIGNED` | Owning team and initial recovery path are known. |
| `ENGINEER_ASSIGNED` | `ENGINEER_ASSIGNED` | `SPARE_VENDOR_WAITING` or `REPAIR_IN_PROGRESS` | A repair owner exists; the next blocker is either material/vendor dependency or repair execution. |
| `SPARE_VENDOR_WAITING` | `SPARE_OR_VENDOR_READY` | `REPAIR_IN_PROGRESS` | Required spare or vendor support is available for repair. |
| `REPAIR_IN_PROGRESS` | `REPAIR_COMPLETED` | `VALIDATION` | Physical repair is complete and needs return-to-service validation. |
| `VALIDATION` | `VALIDATION_PASSED` | `RESTORED` | Validation passed and capacity can return to service. |
| Any active stage | `INCIDENT_RESTORED` | `RESTORED` | Incident is terminal if restoration evidence exists. |

The implementation uses the latest `ENTERED_STAGE` event as the reconstructed current stage and stage-specific exit events to calculate duration and delay.

## Controlled Vocabulary

The backend centralizes the controlled vocabulary for:

- workflow stages and terminal status
- workflow and impact event types
- event statuses
- priority and criticality levels
- work order, validation, telemetry, vendor, mitigation, redundancy, and spare-stock states
- reconciliation issue types

Core quality checks now verify that incidents, zones, assets, spares, work orders, validation records, telemetry alerts, stage events, and impact snapshots use this vocabulary. Reconciliation also converts invalid workflow evidence into operator-visible trust issues.

## Transition Validation

Transition validation checks the event history before it is treated as trusted workflow evidence:

- incidents must enter through `INCIDENT_REPORTED`
- `ENTERED_STAGE` events must follow the configured lifecycle order
- a stage cannot have duplicate entered-stage evidence for the same incident
- event types must be allowed for the stage where they appear
- restored incidents must have terminal restore evidence
- active incidents must not enter the terminal `RESTORED` stage

Invalid transition evidence does not create a new workflow stage. It becomes a quality or reconciliation issue so operators can see that the analytics row needs source review.

## Exception States

Exception states are represented as quality or reconciliation issues rather than as extra workflow stages:

- Missing stage event: no reliable reconstruction is possible.
- Stage mismatch: the incident current stage conflicts with latest event history.
- Active with completion event: the incident is open but event history says it was restored.
- Restored without completion event: the incident is terminal without restoration evidence.
- Event before incident report: sequence evidence is not trustworthy.
- Validation without completed work: validation happened before repair completion evidence.

These exceptions reduce trust in the row and appear as quality flags or reconciliation flags.

## External Dependency States

External dependency states enrich priority and recommended action without replacing the lifecycle:

- Spare dependency: required spare is linked, low stock, out of stock, or missing.
- Vendor dependency: `NOT_REQUIRED`, `ETA_CONFIRMED`, `WAITING_VENDOR_DISPATCH`, or `ETA_MISSED`.
- Mitigation state: `NONE`, `LOAD_SHIFTED`, `RUNNING_DEGRADED`, or `VERIFIED_NORMAL`.
- Redundancy state: `N+1`, `N`, `N-1`, plus explicit power or cooling redundancy loss flags.
- Telemetry state: alerts and impact readings show warning or critical thermal, power, or sensor evidence.

External dependency events such as `VENDOR_ETA_UPDATED`, `VENDOR_ETA_MISSED`, `REDUNDANCY_LOST`, and `LOAD_SHIFTED` are timeline evidence. They do not change stage lead-time calculations unless they are also workflow transition events.

## Infrastructure Topology

Physical and operational dependencies are represented as directed asset edges:

```text
dependent asset -> dependency asset
```

Examples in the sample topology include:

- `ASSET-RACK-01 -> ASSET-PDU-01 -> ASSET-UPS-01 -> ASSET-SWGR-01 -> ASSET-GEN-01`
- `ASSET-RACK-01 -> ASSET-CRAH-01 -> ASSET-CHILLER-01`
- `ASSET-RACK-01 -> ASSET-CDU-01 -> ASSET-CHILLER-01`

The topology vocabulary currently supports `POWER_PATH`, `COOLING_PATH`, `CONTROL_TELEMETRY`, and `REDUNDANCY_SUPPORT` dependency types, with `PRIMARY`, `SECONDARY`, and `BACKUP` roles. These edges explain blast-radius and dependency context, but they do not rewrite workflow stage reconstruction.

## Priority Rules

The follow-up queue scores active incidents with these components:

- Asset criticality.
- Estimated downtime.
- Delay in the current stage.
- Zone priority.
- Needed-by urgency.
- Repeat failure signal.
- Spare and vendor risk.
- Capacity risk from affected GPUs and kW at risk.
- Redundancy risk.
- Thermal breach risk.
- Vendor ETA risk.
- Mitigation credit that reduces priority when evidence shows exposure was reduced.

The recommended action is tied to the active workflow blocker. Impact context explains why the incident matters, but it should not replace the workflow action unless the active blocker is spare or vendor follow-up.

This pass keeps the ranking weights unchanged. Future ranking improvements should be evaluated during trust calibration, especially how overdue needed-by commitments are scored once an incident is already late.

## Final Restoration Conditions

An incident is considered restored when:

- Current status is `RESTORED`.
- Event history includes `INCIDENT_RESTORED` or the `VALIDATION_PASSED` path into `RESTORED`.
- Validation evidence supports return-to-service when validation was required.
- Impact context is either verified normal or no longer needed for active follow-up.

If these conditions conflict, reconciliation creates an issue and the row should not be treated as fully trusted until the source evidence is corrected.
