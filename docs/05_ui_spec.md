# UI Specification

## Workbench Structure

The dashboard opens directly into the operational follow-up queue. It is not a landing page and does not include record-entry workflows.

Primary hierarchy:

- Follow-up Queue is the parent screen.
- Each queue item exposes a `View details` action.
- `View details` is a real link to `/follow-ups/{incident_id}` so browser back/forward, direct reload, and new-tab comparison work normally.
- Detail page tabs provide selected-incident context:
  - Summary
  - Impact
  - Trust
  - Dependencies

The detail tabs are not equal top-level app views. They depend on the selected follow-up item, so they live inside the selected-incident detail page. This keeps the queue as the primary workflow and prevents analytics, evidence, and topology from competing with the parent screen.

## Filters

- Zone
- Asset
- Priority
- Active stage

Terminal `RESTORED` stages are not exposed as actionable stage filters.

## Queue Summary

The dashboard separates visible-queue summary indicators from secondary exposure indicators so the first screen stays scannable.

KPI cards and exposure metrics are read-only summaries of the currently visible follow-up queue. They are not clickable. This prevents a mismatch where a number appears to represent one queue population but a click shows a different population.

Filters, Dashboard Summary, Queue Intelligence, and Follow-up Queue should use small section labels immediately above their bordered content areas. These labels should not be placed inside the bordered section. Dashboard Summary covers both the primary KPI cards and the operational exposure strip so those two rows read as one top-level dashboard summary block.

Primary KPI cards:

- Queue items
- Delayed queue items
- Critical priority
- Capacity at risk
- Affected GPUs

Operational exposure strip:

- N-1 exposure
- Vendor ETA missed
- Spare/vendor wait
- Evidence review

## Queue Intelligence

The dashboard includes a compact Queue Intelligence section between the Dashboard Summary block and Follow-up Queue controls. It defaults to a read-only operational brief generated from the currently visible queue rows. The section should use terse single-field cards rather than explanatory helper copy.

Queue Intelligence may wrap to two rows on desktop. Selected follow-up previews should not be forced into a single compressed row. Mobile stacks the cards in one column.

Queue Intelligence signals:

- Top blocker: the stage with the highest visible queue time.
- Capacity risk: visible queue capacity impact.
- Affected GPUs: visible queue GPU impact.
- Trust load: visible incidents that require evidence review.
- Primary risk: the dominant operational risk signal, such as N-1 exposure, missed vendor ETA, or spare/vendor wait.

This section must not introduce new semantic analytics logic, charts, navigation, or clickable KPI behavior. It exists to make the queue-first dashboard read as an analytic workbench rather than a plain incident list.

When an operator selects a queue row, Queue Intelligence changes into a selected follow-up preview. Row selection must not navigate. The preview should show enough context for fast triage while preserving `View details` as the explicit route to the full incident page.

Selected follow-up preview signals should remain separate single-field cards:

- Incident ID.
- Incident summary.
- Next action.
- Current blocker.
- Time in stage.
- Affected GPUs.
- Capacity risk.
- Trust status.

## Queue Scope Controls

Queue scope controls are explicit buttons below the summary cards. They are allowed only when the scope meaning and returned queue rows match clearly.

Supported queue scopes:

- All queue resets the queue filters.
- Critical asset delay applies `critical_asset_delayed=true`.
- Vendor ETA missed applies `vendor_eta_missed=true`.
- Spare/vendor wait applies `stage=SPARE_VENDOR_WAITING`.
- Evidence review applies `evidence_review=true`.
- N-1 exposure applies `redundancy_lost=true`.

Capacity at risk and affected GPUs remain read-only summaries because all current queue rows can have positive impact values, so those controls would not meaningfully narrow the queue.

## Work Queue

The queue ranks open incidents by return-to-service delay, blocker stage, zone impact, urgency, repeat failure, spare risk, capacity exposure, redundancy risk, thermal risk, vendor ETA risk, and mitigation credit.

The queue is the primary work surface. On desktop, it uses a compact comparison table with one shared header row so operators can scan incidents against the same fields without repeated mini-headers. On mobile, each row stacks into a card-like layout with the same field order. Each row has an explicit `View details` link in a stable action column on desktop, and an action row on mobile, that opens the dedicated selected-incident page.

Desktop queue columns:

- Rank
- Priority
- Incident
- Asset
- Zone
- Blocker
- Time
- Action

Each queue row is organized as a compact selection record:

- which incident is open
- which asset is affected
- which zone is affected
- where recovery is blocked

On the main queue, incident summary, next action, impact, and trust are exposed through the selected Queue Intelligence preview rather than separate desktop columns. This keeps the table compact while preserving the same data for row-level triage.

`recommended_action` is the next operational follow-up based on the active workflow blocker. Impact exposure such as GPU capacity, redundancy loss, thermal breach, vendor ETA, and mitigation state explains why the incident matters, but it should not replace the workflow action unless the active blocker is spare/vendor follow-up.

## Detail Page

The detail page opens from a queue row link and supports direct reload, browser back/forward, and new-tab comparison. It is a focused inspection page, not a popup, drawer, or separate ontology workspace.

Detail tabs:

- Summary
- Impact
- Trust
- Dependencies

The `Summary` tab is a compact operational brief with constrained content width. It tells the incident story in this order:

- incident summary
- next operational action
- at-a-glance context for asset/zone, current blocker, time in blocker, impact, and trust
- why the incident matters
- recovery blocker evidence from compact stage cards where each stage and duration stay together
- work order and spare context as compact cards

Trust supports the operational decision. It should not be presented before the action, impact, and blocker are clear.

## Impact

Impact is a selected-incident detail tab with a restrained evidence-report layout. It answers whether the selected incident creates material operational exposure without turning every metric into a separate card.

- impact question
- neutral at-a-glance fact strip for redundancy, capacity risk, affected GPUs, and thermal breach
- row-based operational state evidence for vendor, mitigation, power redundancy, and cooling redundancy
- row-based telemetry evidence
- compact priority score strip

## Trust

Trust is a selected-incident detail tab with the same compact operational-brief structure as Summary. It separates source-quality and confidence review from the summary action so operators can decide whether the recommendation needs source-system review before use.

- impact confidence
- impact evidence issues
- source quality flags
- validation records
- meaningful empty states when no evidence issues are present

## Dependencies

Dependencies is a selected-incident detail tab with a path-evidence layout. It lists compact power and cooling dependency paths and selected incident impact context so topology explains blast-radius evidence without becoming the visual center of the dashboard. This is not a free-form graph editor or ontology map; it is supporting context for follow-up prioritization.

- dependency question
- neutral dependency fact strip for path count, active path incidents, capacity risk, and redundancy state
- compact power and cooling path cards as the primary content

## Trust Wording

User-facing trust labels should explain operational meaning before exposing internal source names.

- `PASS` appears as `Trusted`
- `FAILED` appears as `Needs review`
- `TRUSTED` appears as `Trusted`
- `WARNING` appears as `Review evidence`
- unverified impact context appears as `Unverified`

The data trust panel explains source data issues found in the latest analysis run. Internal table and check names can remain available as secondary detail, but the first visible label should use operational language such as `Incident source feed`, `Stage event history`, or `Stage events arrived out of order`.

The impact trust section explains whether the selected incident's impact context is trusted, needs review, or is unverified for the same latest pipeline run.
