# Verification Plan

## Semantic-Service Tests

```bash
docker run --rm \
  -v "$PWD":/workspace \
  -w /workspace/semantic-service \
  gradle:8.10.2-jdk17 \
  gradle --no-daemon test
```

## Frontend Build

```bash
cd frontend
npm run build
```

## SPARQL Parse Validation

```bash
PYTHONPATH=/tmp/dcai-rdf-tools python3 queries/validate_sparql.py
```

## RDF And SHACL Checks

Parse all Turtle artifacts and run representative SHACL checks for valid and
invalid fixtures:

```bash
PYTHONPATH=/tmp/dcai-rdf-tools python3 - <<'PY'
from pathlib import Path
from rdflib import Graph

for path in sorted(Path(".").glob("**/*.ttl")):
    if ".git" in path.parts:
        continue
    Graph().parse(path, format="turtle")
    print(f"parsed: {path}")
PY
```

## Runtime Config Checks

```bash
docker compose config
rg -n "VITE_API_BASE_URL|localhost:8000|from fastapi|sqlalchemy|create_engine|psycopg|uvicorn" \
  README.md .env.example docker-compose.yml frontend semantic-service
git diff --check
```

## Acceptance Criteria

- Fuseki is the only Compose-managed data runtime.
- The frontend points at `VITE_SEMANTIC_API_BASE_URL`, not an old `/api`
  proxy.
- Approved query IDs parse and are covered by semantic-service tests.
- Result envelopes and error envelopes remain stable.
- No old FastAPI/Postgres/SQLAlchemy runtime code remains active.
