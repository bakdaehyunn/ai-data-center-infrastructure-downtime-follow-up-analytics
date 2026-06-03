# UI Specification

## Primary Screen

The dashboard opens directly into the operational follow-up view. It is not a landing page and does not include record-entry workflows.

## Filters

- Zone
- Asset
- Priority
- Active stage

Terminal `RESTORED` stages are not exposed as actionable stage filters.

## KPI Row

The dashboard separates primary return-to-service indicators from secondary exposure indicators so the first screen stays scannable.

Primary KPI cards:

- Open incidents
- Delayed incidents
- Critical delayed assets
- Capacity at risk
- Affected GPUs

Operational exposure strip:

- Redundancy lost
- Missed vendor ETA
- Spare/vendor wait hours
- Latest-run data trust

## Follow-up Queue

The queue ranks open incidents by return-to-service delay, blocker stage, zone impact, urgency, repeat failure, spare risk, capacity exposure, redundancy risk, thermal risk, vendor ETA risk, and mitigation credit.

Each row shows rank, incident number, priority, asset and zone, current blocker, compact impact context, delay, recommended action, and impact confidence.

`recommended_action` is the next operational follow-up based on the active workflow blocker. Impact exposure such as GPU capacity, redundancy loss, thermal breach, vendor ETA, and mitigation state explains why the incident matters, but it should not replace the workflow action unless the active blocker is spare/vendor follow-up.

## Drilldown

Selecting a queue row shows:

- incident summary
- recommended action
- reason summary explaining why the incident matters
- quality flags
- latest impact snapshot
- affected racks, affected GPUs, estimated kW at risk, redundancy state, vendor status, mitigation status, and thermal breach minutes
- impact confidence summary
- structured impact trust flags for stale, missing, or contradictory impact evidence
- score components
- impact telemetry readings
- stage lead times
- facilities work order context
- required spare and stock status
- validation and telemetry context from the API

## Analytics Panels

- Active stage bottlenecks
- Asset impact
- Zone impact
- Spare/vendor waiting
- Impact summary
- Data trust

The data trust panel explains latest-run raw/core/workflow quality. The impact trust section explains whether the selected incident's impact context is trusted, warning, or unverified for the same latest pipeline run.
