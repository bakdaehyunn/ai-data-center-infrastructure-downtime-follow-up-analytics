# Verification Plan

## Backend

```bash
cd backend
.venv/bin/python -m pytest
```

Expected coverage:

- schema registration
- deterministic sample data
- raw quality checks
- pipeline load counts
- analytics table counts
- follow-up ranking
- workflow-blocker recommended actions
- impact rationale in follow-up summaries
- latest-run data quality scoping
- latest-run impact confidence scoping
- structured impact trust flags
- terminal-stage analytics behavior
- API endpoints
- health endpoint

## Frontend

```bash
cd frontend
npm run build
```

Expected coverage:

- TypeScript compile
- Vite production build
- API type usage
- dashboard component build

## Browser Check

Use the local dashboard to verify:

- dashboard loads without failed API fetches
- follow-up queue renders
- recommended action reads as the next operational follow-up
- impact confidence badges render in queue rows
- impact trust flags render in incident drilldown
- stage filter excludes `Restored`
- filtering the queue updates the incident drilldown selection
- dashboard wording stays focused on AI data center infrastructure semantic operations

## Production Artifacts

Build Docker images when validating deployment packaging:

```bash
docker build -t ai-infra-semantic-ops-api ./backend
docker build -t ai-infra-semantic-ops-frontend ./frontend
```

The Docker build confirms packaging, not full production readiness. Production readiness still depends on configured database connectivity, scheduled pipeline execution, health checks, and latest-run data quality review.

## Source Scan

Search active source and docs for removed domain framing:

```bash
rg -n -i "procurement|manufacturing|ev battery|production line|parts waiting|portfolio|interview" backend/app backend/tests frontend/src README.md docs --glob '!docs/06_verification_plan.md'
```

Expected result: no active source or documentation references to removed domain framing. Backward-compatible endpoint aliases may remain in API code, but the primary product surface should use infrastructure assets, zones, and critical spares.
