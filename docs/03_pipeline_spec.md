# Pipeline Spec

## 1. Pipeline Goal

The pipeline loads source-like procurement data, validates it, transforms it into a normalized model, and builds analytics tables for bottleneck diagnosis.

It should demonstrate:

- Source-like data ingestion
- Raw and core data quality checks
- Domain transformation
- Stage lead time calculation
- Bottleneck and priority scoring
- Pipeline run logging

## 2. Pipeline Stages

```text
1. Generate sample source data
2. Load raw tables
3. Run raw data quality checks
4. Transform raw data into core tables
5. Run core data quality checks
6. Build analytics tables
7. Record pipeline run result
```

## 3. Sample Data Generation

V1 uses realistic generated data instead of a real ERP integration.

The generated data must include:

- Normal completed requests
- Budget review delays
- Procurement review correction or rejection
- PO creation delays
- Vendor confirmation delays
- Delivery delays
- Receiving delays
- Inspection delays
- Critical requests delayed behind lower-priority work
- Missing stage events
- Timestamp order issues
- Duplicate source records

Generation must be deterministic with a fixed seed.

## 4. Raw Load

Raw tables:

```text
raw_purchase_requests
raw_purchase_orders
raw_vendor_updates
raw_receipts
raw_stage_events
```

Rules:

- Every row has `pipeline_run_id`.
- Every row has `source_system`.
- Every row has `source_record_id`.
- Source payload is preserved as `payload_json`.
- Non-critical malformed data is retained for quality inspection when possible.

## 5. Data Quality Checks

### 5.1 Raw Checks

```text
missing_required_fields
duplicate_source_record
invalid_date_format
unknown_source_system
missing_request_reference
```

### 5.2 Core Checks

```text
po_without_request
receipt_without_po
request_without_stage_event
event_timestamp_out_of_order
negative_stage_duration
invalid_stage_transition
closed_request_without_receipt
needed_by_date_before_submitted_at
```

Each check writes a result into `data_quality_check_results`.

Severity levels:

```text
INFO
WARNING
ERROR
CRITICAL
```

V1 policy:

- `WARNING`: continue pipeline
- `ERROR`: reject or quarantine affected rows, continue when possible
- `CRITICAL`: stop analytics build

## 6. Core Transformation

Raw data is transformed into:

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

Transformation rules:

- Normalize source payload fields.
- Map source status codes to internal stages and events.
- Sort events by request and timestamp.
- Calculate current status from the latest valid event.
- Record rejected records with enough detail to debug.

## 7. Analytics Build

Analytics tables:

```text
request_current_status
request_stage_lead_times
critical_request_queue
bottleneck_summary
vendor_delay_summary
```

### 7.1 Stage Lead Time

```text
duration_hours = exited_at - entered_at
delay_hours = duration_hours - threshold_hours
```

Example thresholds:

```text
BUDGET_REVIEW: 24h
PROCUREMENT_REVIEW: 48h
PO_CREATION: 24h
VENDOR_CONFIRMATION: 72h
DELIVERY: item/vendor lead time
RECEIVING: 24h
INSPECTION: 48h
```

### 7.2 Bottleneck Detection

A bottleneck can be identified when:

- Stage duration exceeds threshold.
- `needed_by_date` is missed or nearly missed.
- Criticality is high and current wait time is long.
- Delay hours concentrate in a vendor, department, item category, or stage.

### 7.3 Critical Request Queue

V1 uses a rule-based score.

```text
total_priority_score =
  criticality_score
+ delay_score
+ business_impact_score
+ needed_by_urgency_score
+ vendor_risk_score
```

Output fields:

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

### 7.4 Recommended Action Rules

Examples:

```text
If current_stage = BUDGET_REVIEW and delay_hours > 24:
  recommended_action = "Escalate budget review"

If current_stage = VENDOR_CONFIRMATION and vendor delay rate is high:
  recommended_action = "Contact vendor or consider alternate supplier"

If current_stage = DELIVERY and needed_by_date is within 2 days:
  recommended_action = "Escalate delivery status"

If current_stage = INSPECTION and received_at exists but inspection is delayed:
  recommended_action = "Prioritize inspection completion"
```

## 8. Pipeline Run Logging

Every execution writes to `pipeline_runs`.

Fields:

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

Statuses:

```text
RUNNING
SUCCESS
FAILED
PARTIAL_SUCCESS
```

## 9. Failure Handling

V1 policy:

- Raw load failure: fail pipeline
- Raw quality warning: continue
- Some core transform failures: record rejected rows and continue when possible
- Critical quality failure: stop analytics build
- Analytics build failure: fail pipeline
- All failure reasons are written to run logs

## 10. Pipeline Commands

Possible commands:

```bash
python -m app.pipeline.generate_sample_data
python -m app.pipeline.run_pipeline
python -m app.pipeline.run_quality_checks
python -m app.pipeline.build_analytics
```

Preferred integrated command:

```bash
python -m app.pipeline run --generate-sample
```

Docker Compose:

```bash
docker compose run pipeline python -m app.pipeline run --generate-sample
```

## 11. Verification

Pipeline verification:

- Sample data is deterministic.
- Raw, core, analytics, and ops row counts match expectations.
- Seeded delays appear in analytics tables.
- Seeded quality issues appear in data quality results.
- Pipeline run status is recorded.
- Critical request queue is populated and ordered.
