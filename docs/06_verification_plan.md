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
- latest-run data quality scoping
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
- stage filter excludes `Completed`
- filtering the queue updates the request drilldown selection
- dashboard wording stays focused on maintenance downtime follow-up analytics

## Source Scan

Search active source and docs for removed domain framing:

```bash
rg -n "<removed-domain-term>" backend/app backend/tests frontend/src README.md docs
```

Expected result: no active source or documentation references to removed domain framing.
