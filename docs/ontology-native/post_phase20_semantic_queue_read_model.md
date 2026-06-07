# Post-Phase-20 Semantic Queue Read Model

## Purpose

This checkpoint records the first product read-model query in the
ontology-native semantic service transition.

## Implemented Query

Query ID:

- `semanticFollowUpQueueList`

SPARQL file:

- `queries/read-model/semantic_follow_up_queue_list.select.rq`

Manifest entry:

- `queries/manifest.ttl`

Runtime access:

- private/internal `POST /semantic/query/semanticFollowUpQueueList`

## Current Payload Boundary

The query returns canonical graph fields currently available in RDF fixtures:

- graph URI
- incident URI
- incident identifier
- asset URI
- asset identifier
- zone URI
- zone identifier
- current workflow stage URI
- optional current workflow stage label
- source record URI for row provenance

The typed envelope is `FollowUpQueueEnvelope`; serialized result type is
`follow-up-queue`.

## Current Limitation

This is not full old FastAPI `/api/follow-ups` parity yet.

The old route still includes fields that are not yet present as canonical or
reasoning graph facts in this slice:

- priority rank
- request title
- current status
- delay hours
- blocker state
- impact scores
- trust status
- recommended action
- KPI filter booleans

Those fields should be added only after the corresponding ontology facts,
SHACL contracts, source mappings, or reasoning outputs exist.

## Non-Goals

This slice does not:

- switch the React dashboard to semantic-service
- delete FastAPI/Postgres/SQLAlchemy/React runtime code
- execute reasoning
- write graphs
- expose public endpoints
- add other product read models
- commit or push

## Verification

Required checks:

```bash
PYTHONPATH=/tmp/dcai-rdf-tools python3 queries/validate_sparql.py

PYTHONPATH=/tmp/dcai-rdf-tools python3 - <<'PY'
from pathlib import Path
from rdflib import Graph

Graph().parse("queries/manifest.ttl", format="turtle")
for path in sorted(Path("semantic-service").glob("**/*.ttl")):
    Graph().parse(path, format="turtle")
PY

docker run --rm \
  -v "$PWD":/workspace \
  -w /workspace/semantic-service \
  gradle:8.10.2-jdk17 \
  gradle --no-daemon test

git diff --check
```

## Next Slice

Expand `semanticFollowUpQueueList` toward old route parity by adding canonical
or reasoning-backed facts for priority rank, blocker, impact, trust, and
recommended action. Do not switch the UI until fixture parity tests prove the
semantic response can support the current Follow-up Queue workflow.
