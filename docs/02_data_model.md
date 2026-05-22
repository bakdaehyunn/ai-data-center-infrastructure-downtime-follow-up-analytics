# Data Model

## 1. Data Model Goal

The data model must support process analysis, not just current status lookup.

It should answer:

- Which stages did a request pass through?
- How long did it stay in each stage?
- Which stage caused the most delay?
- Which vendors, departments, and item categories create repeated delay?
- Which critical requests need action first?
- Are there missing or invalid state events?

## 2. Modeling Principle

Do not model state only as a single `current_status` column.

V1 uses both:

```text
purchase_requests.current_status
procurement_stage_events
```

`purchase_requests.current_status` supports quick lookup. `procurement_stage_events` is the source for timeline, lead time, bottleneck, and quality analysis.

## 3. Core Business Entities

### 3.1 Purchase Request

Main procurement request entity.

Fields:

```text
request_id
request_number
request_title
request_type
department_id
requester_id
item_id
quantity
estimated_amount
currency
criticality_level
business_impact
needed_by_date
submitted_at
current_stage
current_status
created_at
updated_at
```

Important concepts:

- `criticality_level`: LOW, MEDIUM, HIGH, CRITICAL
- `business_impact`: maintenance delay, project delay, production risk, license risk, safety risk
- `needed_by_date`: date when operational impact becomes serious

### 3.2 Department

Fields:

```text
department_id
department_name
department_type
cost_center
```

Analysis use:

- Department-level delay
- Request quality by department
- Critical request concentration

### 3.3 Requester

Fields:

```text
requester_id
requester_name
department_id
role
```

V1 uses synthetic people only.

### 3.4 Item

Fields:

```text
item_id
item_name
item_category
is_critical_item
standard_lead_time_days
```

Example categories:

```text
MAINTENANCE_PART
IT_EQUIPMENT
SOFTWARE_LICENSE
OFFICE_SUPPLY
SAFETY_EQUIPMENT
PRODUCTION_MATERIAL
```

### 3.5 Vendor

Fields:

```text
vendor_id
vendor_name
vendor_type
reliability_tier
default_lead_time_days
```

Analysis use:

- Vendor confirmation delays
- Delivery delays
- Vendor reliability comparison

### 3.6 Purchase Order

Fields:

```text
po_id
po_number
request_id
vendor_id
po_created_at
vendor_confirmed_at
expected_delivery_date
actual_delivery_date
po_status
```

V1 assumes one purchase request maps to one purchase order. Split orders and partial orders are out of scope.

### 3.7 Receipt and Inspection

Fields:

```text
receipt_id
po_id
received_at
received_quantity
inspection_status
inspection_completed_at
rejection_reason
```

Receiving and inspection are modeled separately because they can create operational bottlenecks.

### 3.8 Procurement Stage Event

This is the key table for state flow analysis.

Fields:

```text
event_id
request_id
stage
event_type
event_status
occurred_at
actor_type
actor_id
reason_code
metadata_json
source_system
created_at
```

Stages:

```text
REQUEST_SUBMITTED
BUDGET_REVIEW
PROCUREMENT_REVIEW
PO_CREATION
VENDOR_CONFIRMATION
DELIVERY
RECEIVING
INSPECTION
CLOSED
```

Event types:

```text
ENTERED_STAGE
EXITED_STAGE
APPROVED
REJECTED
RETURNED_FOR_CORRECTION
PO_CREATED
VENDOR_CONFIRMED
DELIVERY_DELAYED
GOODS_RECEIVED
INSPECTION_PASSED
INSPECTION_FAILED
CLOSED
```

Why this matters:

- Current status alone cannot explain where time was spent.
- Event history supports stage lead time calculation.
- Rejections and rework can be represented.
- Missing, duplicated, and out-of-order events can be detected.

## 4. Raw Tables

Raw tables preserve source-like records.

Tables:

```text
raw_purchase_requests
raw_purchase_orders
raw_vendor_updates
raw_receipts
raw_stage_events
```

Common fields:

```text
raw_id
source_record_id
source_system
payload_json
ingested_at
pipeline_run_id
```

Raw tables keep weak constraints so malformed data can be inspected rather than silently dropped.

## 5. Core Tables

Core tables represent the normalized domain model.

Tables:

```text
departments
requesters
items
vendors
purchase_requests
purchase_orders
receipts
procurement_stage_events
```

Core tables are the trusted source for analytics.

## 6. Analytics Tables

Analytics tables support fast API and dashboard reads.

### 6.1 Request Current Status

```text
request_id
current_stage
current_status
stage_entered_at
days_in_current_stage
is_delayed
delay_days
needed_by_date
criticality_level
business_impact
next_owner_type
next_owner_id
```

### 6.2 Request Stage Lead Times

```text
request_id
stage
entered_at
exited_at
duration_hours
threshold_hours
is_bottleneck
delay_hours
```

### 6.3 Critical Request Queue

```text
request_id
priority_rank
criticality_score
delay_score
business_impact_score
needed_by_urgency_score
vendor_risk_score
total_priority_score
recommended_action
reason_summary
```

### 6.4 Bottleneck Summary

```text
summary_date
dimension_type
dimension_id
stage
request_count
delayed_count
avg_duration_hours
p90_duration_hours
total_delay_hours
```

Dimension examples:

```text
STAGE
DEPARTMENT
VENDOR
ITEM_CATEGORY
CRITICALITY_LEVEL
```

### 6.5 Vendor Delay Summary

```text
vendor_id
total_po_count
delayed_po_count
delay_rate
avg_confirmation_hours
avg_delivery_delay_days
reliability_tier
```

## 7. Ops Tables

### 7.1 Pipeline Runs

```text
pipeline_run_id
pipeline_name
started_at
finished_at
status
rows_extracted
rows_loaded
rows_rejected
error_message
created_at
```

### 7.2 Data Quality Check Results

```text
check_result_id
pipeline_run_id
check_name
target_table
severity
status
failed_row_count
sample_failed_keys
message
created_at
```

Example checks:

```text
missing_required_fields
duplicate_source_record
invalid_stage_transition
event_timestamp_out_of_order
request_without_stage_event
po_without_request
receipt_without_po
closed_request_without_receipt
negative_stage_duration
```

## 8. Important Constraints

Important V1 constraints:

- `purchase_orders.request_id` references `purchase_requests.request_id`.
- `receipts.po_id` references `purchase_orders.po_id`.
- `procurement_stage_events.request_id` references `purchase_requests.request_id`.
- Stage events should be time-ordered within a request.
- A closed request should have receiving or inspection completion evidence.
- Current status should be recalculable from event history.

## 9. Deliberate Simplifications

V1 simplifies:

- One purchase request to one purchase order
- No partial delivery
- No multi-currency conversion
- No complex budget hierarchy
- No full approval hierarchy
- No invoice or payment processing
- No real ERP integration

## 10. Data Model Success Criteria

The model is successful when SQL or API can answer:

- Which critical request has been stuck the longest?
- Which stage has the highest total delay hours?
- Which vendor repeatedly delays confirmation or delivery?
- Which department has many returned requests?
- Which requests are past `needed_by_date`?
- Can current status be recalculated from event history?
- Can missing or invalid events be detected?
