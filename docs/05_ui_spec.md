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

V1 screens:

```text
1. Operations Overview
2. Bottleneck Analysis
3. Critical Request Queue
4. Request Detail
5. Vendor / Department Analysis
6. Pipeline & Data Quality
```

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
- Critical Delayed Requests
- Total Delay Hours
- Average Cycle Time
- Top Bottleneck Stage

Primary chart:
- Stage Bottleneck Bar Chart

Secondary sections:
- Top 5 Critical Blockers
- Delay Trend
- Pipeline Status Badge
- Data Quality Status Badge
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

- Stage bottleneck table
- Stage duration chart
- Delay rate by stage
- Threshold vs actual duration chart
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
Department
Current Stage
Days in Stage
Needed By
Criticality
Priority Score
Recommended Action
Reason
```

Filters:

```text
Stage
Department
Vendor
Criticality
Business Impact
```

Interaction:

- Row click opens Request Detail.

Design rule:

- This is the core screen. It must explain why each request is prioritized.

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
Current Status
Criticality
Needed By Date
Priority Score
Recommended Action
```

Sections:

```text
Stage Timeline
Stage Lead Time Breakdown
Related PO Summary
Vendor Info
Receipt / Inspection Summary
Quality Flags
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

Department table:

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

Status badges:

```text
SUCCESS
FAILED
PARTIAL_SUCCESS
WARNING
CRITICAL
```

## 10. Global Filters

Common filters:

```text
Date Range
Department
Vendor
Item Category
Criticality Level
Stage
```

Filters should be preserved in URL query state when practical.

## 11. Interaction Rules

- Clicking a KPI card opens the relevant filtered view.
- Clicking a critical request opens Request Detail.
- Clicking a stage chart bar filters Critical Request Queue by stage.
- Clicking a vendor row applies a vendor filter.
- Clicking a data quality badge opens Pipeline & Data Quality.

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

- Empty filter result: "No requests match current filters."
- Failed pipeline: show warning banner on overview.
- Critical data quality issue: show analytics trust warning.

## 14. UI Success Criteria

The UI is successful when:

- The overview shows the most important procurement blockers.
- Stage bottlenecks are visually comparable.
- Critical Request Queue explains priority and reason.
- Request Detail shows timeline and stage lead time.
- Vendor and department delay patterns are visible.
- Pipeline and data quality state are visible.
- The product does not look like a purchase approval CRUD app.
