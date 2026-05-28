# UI Spec

## 1. UI Goal

The dashboard should help operators answer:

> Which procurement request is blocking important work, where is it blocked, and what should be handled first?

The UI should feel like an operational decision tool, not a generic chart dashboard.

## 2. Target Users

Target users:

- Procurement operators
- Operations or site teams
- Budget and finance reviewers
- Department requesters
- Operational data analysts

They need priority, delay cause, owner, and data trust signals.

## 3. Navigation Structure

V1 is implemented as a single-page operational workbench with these sections:

```text
1. Operations Overview KPI strip
2. Global Filters
3. Stage Bottleneck Analysis
4. Pipeline Trust
5. Critical Request Queue
6. Request Drilldown
7. Vendor Delay Pattern
```

The broader screen list below remains the product direction, but Phase 8A-1 keeps the experience in one dense dashboard instead of adding routing.

## 4. Screen 1: Operations Overview

Purpose:

- Show the current procurement operating state and the biggest risk.

Main questions:

- How many open requests exist?
- How many are delayed?
- How many critical requests are delayed?
- What is the top bottleneck stage?
- Is the data fresh and trustworthy?

Components:

```text
KPI cards:
- Open Requests
- Delayed Requests
- Critical Open Requests
- Total Delay Hours
- Top Bottleneck Stage
- Data Quality Status

Primary chart:
- Stage Bottleneck Bar Chart

Secondary sections:
- Critical Request Queue
- Request Drilldown
- Pipeline Trust failed checks
- Vendor Delay Pattern
```

Design rule:

- The overview must show what to act on first, not only totals.

## 5. Screen 2: Bottleneck Analysis

Purpose:

- Compare delay by process stage.

Main questions:

- Which stage creates the most total delay?
- Which stage has high p90 duration?
- Which stage exceeds its threshold most often?
- Are delays concentrated by filter conditions?

Components:

- Stage duration chart
- Delay rate by stage
- Filters

Table columns:

```text
Stage
Request Count
Delayed Count
Delay Rate
Average Duration
P90 Duration
Threshold
Total Delay Hours
```

## 6. Screen 3: Critical Request Queue

Purpose:

- Show requests that need attention first.

Main questions:

- Which request should be handled first?
- Why is it high priority?
- Where is it currently stuck?
- Who or what owns the next action?

Table columns:

```text
Priority Rank
Request Number
Title
Current Stage
Days in Stage
Priority Score
Recommended Action
```

Filters:

```text
Stage
Department
Vendor
Criticality
Item Category
```

Interaction:

- Row click opens Request Detail.
- Empty filter result shows an explicit empty state.

Design rule:

- This is the core screen. It must explain why each request is prioritized.
- Priority must be explainable through score components, not only a total score.

## 7. Screen 4: Request Detail

Purpose:

- Explain one request's full state flow and delay reason.

Main questions:

- What stages has this request passed through?
- Where did it spend the most time?
- Why is it currently delayed?
- What PO, vendor, receipt, or inspection data is related?
- Are there quality flags?

Header:

```text
Request Number
Title
Current Stage
Criticality
Priority Score
Recommended Action
```

Sections:

```text
Priority Score Breakdown
Stage Lead Time Breakdown
Full Stage Timeline
Related PO Summary
Receipt / Inspection Summary
Quality Flags
```

Priority score components:

```text
Criticality Score
Delay Score
Business Impact Score
Needed By Urgency Score
Vendor Risk Score
Total Priority Score
```

Stage lead time row:

```text
Stage
Actual Duration
Threshold Duration
Delay Hours, when bottlenecked
```

Timeline item:

```text
Timestamp
Stage
Event Type
Actor Type
Reason Code
Message
```

## 8. Screen 5: Vendor / Department Analysis

Purpose:

- Find repeated delay patterns by vendor and department.

Main questions:

- Which vendors often delay confirmation or delivery?
- Which departments have many delayed or corrected requests?
- Which departments own many critical requests?
- Are delay patterns repeated?

Vendor table:

```text
Vendor
Total PO Count
Delayed PO Count
Delay Rate
Average Confirmation Time
Average Delivery Delay
Reliability Tier
Total Delay Hours
```

Department analysis is not yet a separate dashboard table in Phase 8A-1. Department is available as a global filter and is supported by the filtered bottleneck APIs.

Future department table:

```text
Department
Request Count
Delayed Count
Critical Request Count
Average Cycle Time
Return for Correction Count
Total Delay Hours
```

Charts:

```text
Vendor Delay Rate
Department Cycle Time
Delay Hours by Item Category
```

## 9. Screen 6: Pipeline & Data Quality

Purpose:

- Show whether the dashboard data is fresh and trustworthy.

Main questions:

- Did the latest pipeline run succeed?
- How many rows were loaded or rejected?
- Which quality checks failed?
- Is the analytics result current?

Pipeline run table:

```text
Run ID
Pipeline Name
Started At
Finished At
Status
Rows Extracted
Rows Loaded
Rows Rejected
Error Message
```

Data quality table:

```text
Check Name
Target Table
Severity
Status
Failed Row Count
Sample Failed Keys
Message
Created At
```

Phase 8B implemented this inside the dashboard Pipeline Trust panel instead of adding a separate routed screen. Latest-run failed checks are selectable. The selected check shows target table, severity/status, failed row count, pipeline run id, message, sample failed keys, and related request buttons when sampled keys include request ids.

Status badges:

```text
SUCCESS
FAILED
PARTIAL_SUCCESS
WARNING
CRITICAL
```

## 10. Global Filters

Implemented filters:

```text
Stage
Department
Vendor
Item Category
Criticality Level
```

Date range remains an API capability for selected endpoints but is not yet exposed in the dashboard filter bar.

Filters apply to:

```text
Critical Request Queue
Stage Bottleneck Analysis
Vendor Delay Pattern
Request Drilldown selection
```

Filters should be preserved in URL query state in a future routed dashboard.

## 11. Interaction Rules

- Clicking a KPI card opens the relevant filtered view.
- Clicking a critical request opens Request Detail.
- Clicking a stage chart bar filters Critical Request Queue by stage.
- Clicking a vendor row applies a vendor filter.
- Clicking a data quality badge opens Pipeline & Data Quality.
- Applying the filter bar refreshes the queue and supported analytics sections.
- When the selected request is no longer in the filtered queue, Request Detail moves to the first filtered request.

## 12. Visual Design Direction

The UI should feel like a dense, work-focused SaaS operations dashboard.

Guidelines:

- No landing page or hero section.
- Avoid decorative card-heavy layouts.
- Prioritize tables, charts, filters, and status indicators.
- Use clear badges for status, severity, and criticality.
- Use Recharts for charts.
- Use TanStack Table or a focused table component for data-heavy views.
- Show loading, empty, and error states.

## 13. Empty, Loading, and Error States

States:

```text
loading
empty result
api error
data stale warning
pipeline failed warning
```

Examples:

- Empty critical queue result: "No critical requests match the current filters."
- Empty stage chart result: "No stage bottlenecks match the current filters."
- Empty vendor table result: "No vendor delay patterns match the current filters."
- Failed pipeline: show warning banner on overview.
- Critical data quality issue: show analytics trust warning.

## 14. UI Success Criteria

The UI is successful when:

- The overview shows the most important procurement blockers.
- Stage bottlenecks are visually comparable.
- Critical Request Queue explains priority and reason.
- Request Detail shows score breakdown, full timeline, and actual vs threshold stage lead time.
- Vendor delay patterns are visible.
- Department can be used as a filter across the queue and bottleneck analysis.
- Pipeline and data quality state are visible, with failed-check drilldown and request impact links where possible.
- The product does not look like a purchase approval CRUD app.
