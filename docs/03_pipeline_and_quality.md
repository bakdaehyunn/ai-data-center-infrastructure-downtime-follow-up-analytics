# Pipeline and Data Quality

The pipeline turns scattered maintenance source records into follow-up analytics that can be queried quickly and reviewed by pipeline run.

## Pipeline Steps

1. Generate deterministic maintenance sample data.
2. Read source-shaped JSON records.
3. Run raw quality checks.
4. Load raw records with duplicate rejection.
5. Transform valid raw records into core tables.
6. Run core quality checks.
7. Build analytics tables.
8. Record pipeline run status and load counts.

## Raw Quality Checks

Raw checks protect ingestion trust before source records become normalized entities.

- unknown source system
- duplicate source record
- missing required fields
- invalid date format
- missing maintenance request references

## Core Quality Checks

Core checks protect analytical trust after records are normalized.

- maintenance request without stage event
- stage event timestamp before request reporting
- work order without request
- inspection without completed work
- parts waiting without required part
- sensor alert without equipment

## Analytics Calculations

Stage lead time:

```text
duration_hours = exited_at_or_as_of - entered_at
delay_hours = max(duration_hours - stage_threshold_hours, 0)
```

Follow-up score combines:

- equipment criticality
- estimated downtime
- current stage delay
- production line impact
- needed-by urgency
- repeat failure
- parts risk

## Terminal Stage Behavior

Terminal `COMPLETED` stage records remain available in request timelines and current-state reconstruction. They are excluded from bottleneck summaries so the stage chart focuses on waiting or execution stages where follow-up is still actionable.

## Latest-Run Trust

Data quality endpoints default to the latest pipeline run. Historical checks can still be requested, but dashboard trust indicators should represent the data behind the current analytics output, not stale failures from older runs.
