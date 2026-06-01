# Industrial Maintenance Bottleneck Analytics V2 Design

## 1. Project Objective

Industrial Maintenance Bottleneck Analytics extends the existing procurement bottleneck analytics system into a manufacturing and industrial operations domain.

The V2 objective is to analyze equipment maintenance workflow data and answer:

```text
Which equipment maintenance requests are delayed, where is the bottleneck, and what should operations teams handle next?
```

The Korean product explanation is:

```text
설비 정비 요청이 어디서 지연되고 있고, 어떤 요청을 먼저 처리해야 하는지 분석하는 운영 데이터 시스템
```

This V2 should remain an operational data system. It should not become a maintenance request CRUD app, CMMS clone, IoT platform, or predictive maintenance ML demo.

The system should ingest, validate, model, and analyze maintenance workflow data, then expose the result through read-only analytics APIs and an operational dashboard.

## 2. Why This V2

The procurement V1 already demonstrates the important pattern:

```text
workflow event history
-> current state reconstruction
-> stage lead time calculation
-> bottleneck detection
-> priority queue
-> request drilldown
-> data quality observability
```

Industrial maintenance is a stronger V2 domain because the operational impact is more direct:

- delayed maintenance can stop a production line
- parts waiting can extend equipment downtime
- technician assignment delay can block urgent repairs
- repeated equipment failures can reveal systemic operational risk
- inspection delay can keep repaired equipment unavailable

This also maps well to the developer story behind the project. The original experience was workflow status, approval state, external system follow-up, and exception handling. V2 keeps that state-management strength, but moves it into a domain that feels closer to manufacturing, industrial AI, and field operations.

The goal is not to abandon procurement V1. The goal is to show that the same operational data product pattern can be transferred to a higher-impact industrial workflow.

## 3. Target Users

Primary users:

- Maintenance operations managers
- Plant operations teams
- Reliability engineers
- Production line supervisors
- Maintenance planners
- Operational data analysts

These users need to answer questions such as:

- Which maintenance request should be handled first?
- Which line or equipment is blocked by delayed maintenance?
- Is delay caused by review, technician assignment, parts waiting, active repair, or inspection?
- Are the same equipment assets repeatedly creating downtime?
- Are certain teams, lines, or parts categories causing concentrated delay?
- Can the dashboard data be trusted after the latest pipeline run?

## 4. Maintenance Workflow

Recommended V2 workflow:

```text
Maintenance Request Submitted
-> Maintenance Review
-> Technician Assigned
-> Parts Waiting
-> Maintenance In Progress
-> Inspection
-> Completed
```

The workflow starts at maintenance request submission, not at sensor alert creation.

Reason:

- Request-to-completion is the clearest operational workflow.
- It maps directly to the existing event-history design.
- It keeps V2 scoped enough to implement well.
- Sensor alerts can still exist as supporting context.

Sensor alerts should be modeled as optional evidence that can trigger or explain a maintenance request, but they should not become the main state machine in V2.

Recommended stage definitions:

```text
MAINTENANCE_REQUEST_SUBMITTED
MAINTENANCE_REVIEW
TECHNICIAN_ASSIGNED
PARTS_WAITING
MAINTENANCE_IN_PROGRESS
INSPECTION
COMPLETED
```

Potential terminal or exception states:

```text
CANCELLED
REJECTED
DUPLICATE_REQUEST
DEFERRED
```

These exception states can be designed but do not need full dashboard support in the first V2 implementation.

## 5. State and Event Model

The core table is `maintenance_stage_events`.

The design should follow the same principle as `procurement_stage_events`:

```text
event history is the source of truth
current state is derived from event history
analytics are built from derived state and lead times
```

Each maintenance request should have ordered stage events.

Example event sequence:

```text
REQ-MNT-0005 entered MAINTENANCE_REQUEST_SUBMITTED
REQ-MNT-0005 entered MAINTENANCE_REVIEW
REQ-MNT-0005 exited MAINTENANCE_REVIEW
REQ-MNT-0005 entered TECHNICIAN_ASSIGNED
REQ-MNT-0005 entered PARTS_WAITING
REQ-MNT-0005 entered MAINTENANCE_IN_PROGRESS
```

The pipeline should derive:

- current stage
- current status
- days or hours in current stage
- stage entered timestamp
- stage exited timestamp
- stage duration
- threshold for that stage
- delay hours
- whether the stage is a bottleneck

Example:

```text
Stage: PARTS_WAITING
Threshold: 24 hours
Actual duration: 86 hours
Delay: 62 hours
```

This lets the system explain not just that a maintenance request is delayed, but where the delay happened.

## 6. Data Model

V2 should add maintenance-specific domain tables while reusing the existing raw/core/analytics layering pattern.

### 6.1 Core Domain Entities

Recommended tables:

```text
equipment
production_lines
maintenance_requests
maintenance_stage_events
technicians
parts
maintenance_work_orders
inspection_results
sensor_alerts
```

### 6.2 equipment

Represents physical equipment that may require maintenance.

Important fields:

```text
equipment_id
equipment_code
equipment_name
equipment_type
line_id
criticality_level
installed_at
manufacturer
model_number
current_status
```

Why it matters:

- maintenance priority depends on equipment criticality
- delays can be grouped by equipment type
- repeat failure analysis needs equipment identity

### 6.3 production_lines

Represents manufacturing lines or operational areas.

Important fields:

```text
line_id
line_code
line_name
plant_area
line_priority
current_status
```

Why it matters:

- delayed maintenance has different impact depending on line priority
- line-level bottleneck concentration is a strong operational signal

### 6.4 maintenance_requests

Represents the maintenance demand or ticket.

Important fields:

```text
maintenance_request_id
request_number
equipment_id
line_id
request_title
request_type
priority_level
failure_mode
reported_at
needed_by_at
current_stage
current_status
business_impact
estimated_downtime_hours
actual_downtime_hours
```

Possible request types:

```text
BREAKDOWN
CORRECTIVE
PREVENTIVE
INSPECTION_FINDING
SENSOR_TRIGGERED
```

### 6.5 maintenance_stage_events

Represents workflow state history.

Important fields:

```text
event_id
maintenance_request_id
stage
event_type
event_status
occurred_at
actor_type
actor_id
reason_code
metadata_json
```

Example event types:

```text
REQUEST_SUBMITTED
ENTERED_STAGE
EXITED_STAGE
ASSIGNED
PARTS_RESERVED
WORK_STARTED
WORK_COMPLETED
INSPECTION_PASSED
INSPECTION_FAILED
REQUEST_COMPLETED
```

### 6.6 technicians

Represents maintenance workers or teams.

Important fields:

```text
technician_id
technician_name
team_name
skill_group
shift
active_status
```

Why it matters:

- technician assignment delay is a target bottleneck
- skill mismatch or team concentration can explain delays

### 6.7 parts

Represents maintenance parts and consumables.

Important fields:

```text
part_id
part_number
part_name
part_category
stock_status
lead_time_days
critical_spare
```

Why it matters:

- parts waiting delay is expected to be one of the most important V2 bottlenecks
- parts shortages can explain maintenance downtime

### 6.8 maintenance_work_orders

Represents execution work tied to a maintenance request.

Important fields:

```text
work_order_id
maintenance_request_id
assigned_team
assigned_technician_id
work_order_status
planned_start_at
actual_start_at
actual_completed_at
required_part_id
```

### 6.9 inspection_results

Represents post-maintenance inspection.

Important fields:

```text
inspection_id
maintenance_request_id
inspection_status
inspector_id
inspection_started_at
inspection_completed_at
failure_reason
```

### 6.10 sensor_alerts

Represents optional alert evidence related to equipment.

Important fields:

```text
sensor_alert_id
equipment_id
alert_type
severity
triggered_at
resolved_at
linked_maintenance_request_id
metadata_json
```

Sensor alerts should not drive the main V2 workflow at first. They should support drilldown and seeded scenarios.

## 7. Analytics Metrics

V2 should create maintenance analytics tables or views that answer operational questions directly.

### 7.1 Overview Metrics

Dashboard overview should include:

```text
open maintenance requests
delayed maintenance requests
critical equipment delayed
top bottleneck stage
average downtime hours
parts-waiting delay hours
repeat failure equipment count
technician assignment delay hours
```

### 7.2 Stage Bottleneck Metrics

For each maintenance stage:

```text
stage
request_count
delayed_count
delay_rate
avg_duration_hours
p90_duration_hours
total_delay_hours
```

Expected important stages:

```text
MAINTENANCE_REVIEW
TECHNICIAN_ASSIGNED
PARTS_WAITING
MAINTENANCE_IN_PROGRESS
INSPECTION
```

### 7.3 Critical Maintenance Queue

The queue should rank maintenance requests by operational urgency.

Recommended scoring components:

```text
equipment_criticality_score
downtime_score
stage_delay_score
production_line_impact_score
needed_by_urgency_score
repeat_failure_score
parts_risk_score
```

Example total:

```text
total_priority_score =
equipment_criticality_score
+ downtime_score
+ stage_delay_score
+ production_line_impact_score
+ needed_by_urgency_score
+ repeat_failure_score
+ parts_risk_score
```

This is similar to V1 priority scoring, but more industrial:

- equipment criticality replaces procurement criticality
- downtime becomes a first-class factor
- production line impact becomes more important
- repeat failure adds reliability context
- parts risk explains waiting delay

### 7.4 Equipment and Line Analysis

Equipment summary:

```text
equipment_id
equipment_name
line_name
request_count
delayed_request_count
repeat_failure_count
total_downtime_hours
avg_repair_duration_hours
top_failure_mode
```

Production line summary:

```text
line_id
line_name
open_request_count
delayed_request_count
critical_equipment_delayed_count
total_downtime_hours
top_bottleneck_stage
```

### 7.5 Parts Waiting Analysis

Parts waiting is a key V2 differentiator.

Metrics:

```text
part_id
part_name
part_category
waiting_request_count
total_wait_hours
avg_wait_hours
critical_spare
stock_status
```

The dashboard should make it clear when maintenance is delayed because the team cannot start work without parts.

## 8. API Changes

The existing FastAPI backend should be extended with read-only maintenance analytics endpoints.

The V2 API should be namespaced under `/api/v2/maintenance` so the procurement V1 API remains stable while maintenance-specific contracts are added.

Recommended new endpoints:

```text
GET /api/v2/maintenance/overview
GET /api/v2/maintenance/bottlenecks/stages
GET /api/v2/maintenance/requests/critical
GET /api/v2/maintenance/requests/{maintenance_request_id}
GET /api/v2/maintenance/requests/{maintenance_request_id}/timeline
GET /api/v2/maintenance/equipment/delays
GET /api/v2/maintenance/lines/delays
GET /api/v2/maintenance/parts/waiting
GET /api/v2/maintenance/metadata/filters
```

Recommended filters:

```text
stage
line_id
equipment_id
equipment_type
technician_team
part_category
priority_level
request_type
failure_mode
from_date
to_date
```

The V2 API should keep the same product principle as V1:

```text
read-only analytics API
no maintenance request creation
no workflow command execution
no real CMMS integration in V2
```

## 9. Dashboard Changes

V2 should add a top-level domain mode switch inside the existing frontend:

```text
Procurement
Maintenance
```

Reason:

- V1 remains visible as proof of the original operational data pattern.
- V2 becomes a domain expansion instead of a disconnected replacement.
- The portfolio story becomes stronger: the same system pattern transfers from procurement to industrial maintenance.
- A mode switch avoids premature routing complexity while the app is still one operational dashboard product.

Recommended dashboard sections:

### 9.1 Overview KPIs

```text
Open requests
Delayed requests
Critical equipment delayed
Average downtime hours
Top bottleneck stage
Data quality status
```

### 9.2 Maintenance Filters

```text
Stage
Production line
Equipment
Equipment type
Technician team
Part category
Priority
Request type
```

### 9.3 Stage Bottlenecks

Chart:

```text
Total delay hours by maintenance stage
```

Expected useful visual:

```text
Parts Waiting
Technician Assigned
Maintenance Review
Maintenance In Progress
Inspection
```

### 9.4 Critical Maintenance Queue

Table columns:

```text
Rank
Request
Equipment
Line
Current Stage
Downtime
Score
Recommended Action
```

### 9.5 Maintenance Request Drilldown

Drilldown should show:

```text
request summary
equipment and line context
priority score breakdown
recommended action
stage lead times
timeline
assigned technician or team
required part and stock status
inspection result
sensor alert context
quality flags
```

### 9.6 Equipment and Line Delay Pattern

Table or chart:

```text
equipment with repeat failures
lines with concentrated maintenance delays
equipment types with high downtime
```

### 9.7 Parts Waiting Panel

This should be prominent because parts waiting is one of the most concrete maintenance bottlenecks.

Table columns:

```text
Part
Category
Stock Status
Waiting Requests
Total Wait Hours
Critical Spare
```

## 10. Data Quality Rules

V2 should include raw and core data quality checks.

### 10.1 Raw Quality Checks

Examples:

```text
duplicate_source_record
missing_required_fields
invalid_timestamp_format
unknown_source_table
```

### 10.2 Core Quality Checks

Examples:

```text
maintenance_request_without_stage_event
stage_event_timestamp_out_of_order
stage_event_before_request_submission
work_order_without_request
inspection_without_completed_work
parts_waiting_without_required_part
unknown_equipment_reference
unknown_production_line_reference
sensor_alert_without_equipment
```

### 10.3 Quality Drilldown Requirements

V2 should reuse the existing Pipeline Trust pattern.

Each failed check should expose:

```text
check name
target table
severity
status
failed row count
sample failed keys
message
pipeline run id
```

When possible, sampled keys should link to:

```text
maintenance request detail
equipment detail
production line detail
```

## 11. Seeded Scenarios

The sample data generator should create deterministic maintenance scenarios with a fixed seed.

Required scenarios:

```text
normal completed maintenance request
maintenance review delay
technician assignment delay
parts waiting delay
maintenance in progress delay
inspection delay
critical equipment delayed
repeat failure equipment
line-level delay concentration
sensor-triggered maintenance request
duplicate source record
missing required fields
request without stage event
event timestamp out of order
parts waiting without required part
inspection without completed work
```

Known scenario expectations:

```text
known critical maintenance request appears near the top of the critical queue
parts waiting appears as a top bottleneck stage
repeat failure equipment appears in equipment delay analysis
data quality failures are visible in Pipeline Trust
request drilldown shows stage lead times and quality flags
```

The sample data should be realistic but small enough for quick local development.

Recommended scale:

```text
20 to 40 maintenance requests
8 to 12 equipment assets
3 to 5 production lines
6 to 10 technicians
8 to 15 parts
1 to 3 pipeline runs during local demo
```

## 12. Implementation Phases

V2 should not be implemented as one large change.

Recommended phases:

### Phase V2-1: Design Finalization

Scope:

```text
finalize workflow
finalize entities
finalize analytics metrics
finalize API shape
finalize dashboard scope
```

Output:

```text
approved design document
```

### Phase V2-2: Schema and Sample Data

Scope:

```text
add maintenance core tables
add raw source definitions if needed
extend sample data generator
add seeded maintenance scenarios
add migration
```

Verification:

```text
migration applies
sample data is deterministic
expected scenario records exist
```

### Phase V2-3: Pipeline and Quality Checks

Scope:

```text
load maintenance raw records
transform maintenance core records
run raw quality checks
run core quality checks
record pipeline results
```

Verification:

```text
raw/core tables are populated
expected quality checks pass or fail as designed
pipeline result is reproducible
```

### Phase V2-4: Maintenance Analytics Build

Scope:

```text
derive current maintenance status
calculate stage lead times
build maintenance bottleneck summaries
build critical maintenance queue
build equipment and line delay summaries
build parts waiting summary
```

Verification:

```text
known delayed maintenance request appears in critical queue
parts waiting delay appears in bottleneck summary
repeat failure equipment appears in equipment summary
```

### Phase V2-5: Backend API

Scope:

```text
add read-only maintenance analytics endpoints
add request detail and timeline endpoints
add filters
add tests
```

Verification:

```text
API returns expected maintenance overview
filters work across queue and bottleneck endpoints
unknown request returns 404
API values match analytics tables
```

### Phase V2-6: Dashboard

Scope:

```text
add maintenance dashboard mode or route
add KPIs
add filters
add stage bottleneck chart
add critical maintenance queue
add request drilldown
add equipment/line delay panel
add parts waiting panel
reuse Pipeline Trust pattern
```

Verification:

```text
dashboard renders real API data
filters affect queue and bottleneck analysis
clicking a request opens detail
quality check drilldown links to affected maintenance request where possible
```

### Phase V2-7: Documentation and Portfolio Packaging

Scope:

```text
update README
update OpenAPI contract
update UI spec
update portfolio package
refresh screenshots
write V2 demo flow
```

Verification:

```text
docs match implemented behavior
screenshots show maintenance workflow
demo script explains V1 to V2 evolution
```

## 13. Verification Plan

V2 should be considered successful only if the system can be verified from data through UI.

Required checks:

```text
sample data is reproducible with the same seed
each planned delay scenario exists in generated data
pipeline execution fills raw, core, and analytics tables
pipeline run logs are recorded
data quality issue results are recorded
known delayed maintenance request appears near the top of the critical queue
parts waiting delay appears in stage bottleneck summary
repeat failure equipment appears in equipment delay analysis
API overview matches analytics table values
API filters narrow queue and bottleneck results correctly
dashboard KPI values match API responses
request drilldown shows timeline, lead times, parts, technician, inspection, and quality flags
browser smoke test verifies dashboard load and drilldown interaction
```

Recommended automated verification:

```text
pytest backend tests
frontend lint
frontend build
browser smoke test
```

Recommended manual verification:

```text
run pipeline with fixed seed
open FastAPI docs
open maintenance dashboard
select top critical maintenance request
verify bottleneck stage and recommended action
select a failed quality check
verify sampled key links to affected request where possible
```

## 14. Open Decisions

This section records the V2 design checkpoint decisions that must be approved before implementation starts.

Current recommendation:

```text
Approve all three core V2 decisions and proceed to Phase V2-2 through /goal.
```

If approved, these decisions should not be reopened during implementation unless a concrete technical conflict appears.

### 14.1 Domain Name

Recommended decision:

```text
Industrial Maintenance Bottleneck Analytics
```

Reason:

- clear industrial/manufacturing signal
- close to the existing procurement bottleneck naming
- avoids sounding like a generic CMMS
- keeps focus on analytics and operations

### 14.2 Workflow Starting Point

Recommended decision:

```text
Start from Maintenance Request Submitted.
```

Sensor alerts should be supporting evidence, not the main workflow entry point.

Reason:

- smaller implementation scope
- clearer state machine
- easier to explain in a portfolio walkthrough
- still allows sensor-triggered scenarios

### 14.3 Repository Strategy

Recommended decision:

```text
Extend the existing repository as V2.
```

Reason:

- reuses the proven pipeline/API/dashboard pattern
- shows domain transferability
- avoids splitting attention across two repos
- makes the project look like an evolving operational data product

### 14.4 Dashboard Strategy

Recommended decision:

```text
Add a top-level domain mode switch between Procurement and Maintenance.
```

Reason:

- keeps V1 and V2 visible in one product
- makes the domain expansion explicit
- avoids splitting the frontend into separate apps
- keeps implementation smaller than adding a routed multi-page product

### 14.5 Naming in Existing Code

Recommended decision:

```text
Keep existing procurement-specific names and add maintenance-specific modules first.
```

Implementation rule:

```text
Do not abstract too early.
Add maintenance-specific modules first.
Extract shared workflow logic only after duplication becomes concrete.
```

This avoids turning V2 into a framework exercise. The priority is a credible industrial maintenance analytics product.

### 14.6 Implementation Boundary

Recommended decision:

```text
V2 implementation should start with schema and deterministic sample data only.
```

Reason:

- schema and seeded scenarios determine whether the domain model is credible
- pipeline, API, and dashboard work depend on stable maintenance entities
- a small implementation phase is easier to verify and less likely to damage the existing V1 behavior

The next implementation goal should be:

```text
Phase V2-2: Schema and Sample Data
```

### 14.7 Recommended /goal Envelope

After design approval, implementation should be delegated with a bounded goal.

Recommended objective:

```text
Implement Phase V2-2 for Industrial Maintenance Bottleneck Analytics:
add the maintenance domain schema and deterministic sample data scenarios
inside the existing critical-procurement-bottleneck-analytics repository.
```

Approved scope:

```text
maintenance domain SQLAlchemy models
Alembic migration for maintenance core tables
deterministic seeded maintenance scenario definitions
sample data generator extension if needed for Phase V2-2
focused backend tests for schema import and deterministic scenario data
documentation updates only where needed to match Phase V2-2 behavior
```

Forbidden scope:

```text
no maintenance analytics builder yet
no maintenance API endpoints yet
no dashboard changes yet
no predictive maintenance ML
no CMMS write workflow
no external IoT integration
no commit or push unless separately approved
```

Required verification:

```text
model imports succeed
Alembic upgrade applies on a clean database
sample data generation is deterministic with the same seed
required seeded scenarios are present
existing procurement tests still pass or any unrelated existing failures are documented
```

Stop condition:

```text
Phase V2-2 is complete when schema, migration, deterministic scenario data,
and focused verification are ready for review without changing V1 behavior.
```
