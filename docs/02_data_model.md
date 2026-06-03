# Data Model

## Raw Tables

- `raw_infrastructure_incidents`
- `raw_incident_stage_events`
- `raw_facility_work_orders`
- `raw_validation_results`
- `raw_telemetry_alerts`

Raw tables keep source-shaped payloads for traceability and duplicate detection.

## Core Tables

- `infrastructure_zones`: AI data center halls, power paths, cooling loops, backup power areas, and monitoring zones
- `infrastructure_assets`: CRAH, UPS, PDU, chiller, CDU, generator, rack sensor, and switchgear assets
- `facilities_engineers`: facilities teams and skill groups
- `critical_spares`: cooling, power, generator, sensor, and metering spares
- `infrastructure_incidents`: normalized downtime follow-up incidents
- `incident_stage_events`: event history used for state reconstruction
- `facility_work_orders`: assigned facilities work and spare/vendor state
- `validation_results`: return-to-service validation evidence
- `telemetry_alerts`: linked monitoring evidence

## Analytics Tables

- `incident_current_status`: reconstructed current state and delay signal
- `incident_stage_lead_times`: stage duration, threshold, and bottleneck signal
- `downtime_follow_up_queue`: ranked actionable incidents and recommended actions
- `infrastructure_bottleneck_summary`: grouped stage delay by operational dimensions
- `asset_delay_summary`: downtime concentration by infrastructure asset
- `zone_delay_summary`: downtime concentration by data center zone
- `spare_waiting_summary`: spare/vendor wait impact

## Ops Tables

- `pipeline_runs`
- `data_quality_check_results`
- `infrastructure_reconciliation_issues`

## Relationship Summary

- An incident belongs to one infrastructure asset and one infrastructure zone.
- Stage events belong to an incident and reconstruct its timeline.
- Work orders belong to an incident and may reference a facilities engineer and critical spare.
- Validation results belong to an incident and indicate restore readiness.
- Telemetry alerts belong to an asset and may link to an incident.
- Reconciliation issues are tied to a pipeline run and may link to an incident and asset.
