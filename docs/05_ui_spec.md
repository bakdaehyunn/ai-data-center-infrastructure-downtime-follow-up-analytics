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
- Delayed follow-ups
- Critical follow-ups
- Capacity at risk
- Affected GPUs

Operational exposure strip:

- Redundancy lost
- Vendor ETA missed
- Spare/vendor wait hours
- Evidence status

## Follow-up Queue

The queue ranks open incidents by return-to-service delay, blocker stage, zone impact, urgency, repeat failure, spare risk, capacity exposure, redundancy risk, thermal risk, vendor ETA risk, and mitigation credit.

The queue is the primary work surface. It uses incident cards instead of a wide table so the next action and evidence status remain visible without horizontal scanning. Each card is organized as an operational sentence:

- which incident is open
- which asset and zone are affected
- where recovery is blocked
- what infrastructure impact is exposed
- what the next follow-up action is
- whether the impact evidence is trusted, needs review, or is unverified

`recommended_action` is the next operational follow-up based on the active workflow blocker. Impact exposure such as GPU capacity, redundancy loss, thermal breach, vendor ETA, and mitigation state explains why the incident matters, but it should not replace the workflow action unless the active blocker is spare/vendor follow-up.

## Drilldown

The incident drilldown sits in the right operational stack beside the main follow-up and analytics stack. Selecting a queue row tells the incident story in this order:

- incident summary
- next operational action
- why the incident matters
- recovery blocker evidence from stage lead times, work order state, and spare status
- impact evidence from redundancy, capacity, GPU exposure, vendor state, mitigation state, thermal breach, and telemetry
- trust and source evidence from quality flags and impact confidence
- priority score evidence as supporting detail

Evidence supports the operational decision. It should not be presented before the action, impact, and blocker are clear.

## Analytics Panels

Supporting analytics panels are split between the main stack and right stack so the page does not collapse into a one-sided layout. Data trust stays in the main stack because it is a dashboard-level pipeline signal, while spare/vendor waiting, topology dependencies, and impact summary stay near the incident drilldown as operational context.

- Active stage bottlenecks
- Asset impact
- Zone impact
- Spare/vendor waiting
- Infrastructure topology
- Impact summary
- Data trust

The topology panel lists compact dependency paths. Each row shows the dependent asset, the upstream dependency asset, dependency type, and whether either side has active incidents. This is not a free-form graph editor; it is a scanning aid for power and cooling blast-radius context.

## Trust Wording

User-facing trust labels should explain operational meaning before exposing internal source names.

- `PASS` appears as `Trusted`
- `FAILED` appears as `Needs review`
- `TRUSTED` appears as `Trusted`
- `WARNING` appears as `Review evidence`
- unverified impact context appears as `Unverified`

The data trust panel explains source data issues found in the latest analysis run. Internal table and check names can remain available as secondary detail, but the first visible label should use operational language such as `Incident source feed`, `Stage event history`, or `Stage events arrived out of order`.

The impact trust section explains whether the selected incident's impact context is trusted, needs review, or is unverified for the same latest pipeline run.
