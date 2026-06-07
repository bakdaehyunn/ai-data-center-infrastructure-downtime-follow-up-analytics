# Phase 20 Endpoint Readiness Decision

This document records the Phase 20 ontology-native rewrite checkpoint. It is
the final checkpoint in the Phase 13-20 runtime transition batch.

Phase 20 decides whether the semantic service should remain internal-only or
proceed later to a private semantic query endpoint scaffold. The decision for
this phase is: remain internal-only now, and allow a private endpoint scaffold
only in a later explicitly approved phase.

This phase does not implement public endpoints, private endpoint code, graph
writes, unrestricted query execution, SPARQL Update, reasoning orchestration,
UI redesign, old-runtime removal, commit, or push.

## Decision

Current runtime mode remains `cli-only`.

The next allowed implementation, after approval, is a private semantic query
endpoint scaffold. It must be private/internal first, not public.

Any future endpoint must:

- execute only approved query IDs from `queries/manifest.ttl`
- use the Phase 19 `SemanticResponseSerializer`
- return Phase 18-shaped semantic response payloads
- return Phase 18-shaped semantic error payloads
- reject arbitrary browser-supplied SPARQL
- reject SPARQL Update
- avoid returning raw SPARQL bindings
- preserve audit-ready query id, graph scope, serializer contract version,
  error code, and caller context

## Endpoint Readiness Artifact

The parseable checkpoint lives at:

- `semantic-service/endpoint-readiness.ttl`

The static contract validator requires this artifact and checks for:

- `remain-internal-only-for-this-phase`
- `private-semantic-query-endpoint-scaffold-after-approval`
- `SemanticResponseSerializer.kt`
- no raw SPARQL bindings
- no arbitrary browser-supplied SPARQL
- no bypass of the approved query manifest
- no endpoint implementation in Phase 20
- no old-runtime removal in Phase 20

## Required Gates Before Public Endpoint Exposure

Public endpoint exposure is still blocked until these gates are accepted:

- authentication policy
- graph-scope policy
- timeout and result-limit policy
- audit policy
- private endpoint scaffold review

These gates intentionally sit after Phase 20. Passing Phase 20 does not
authorize public endpoint implementation.

## Implementation Artifacts

- `semantic-service/endpoint-readiness.ttl`: parseable Phase 20 endpoint
  readiness decision checkpoint.
- `semantic-service/src/main/kotlin/com/dcai/semanticservice/contracts/SemanticServiceContractCatalog.kt`:
  static marker requirements for endpoint readiness.
- `semantic-service/src/main/resources/contracts/semantic-service-contracts.ttl`:
  contract manifest reference to endpoint readiness.
- `semantic-service/src/test/kotlin/com/dcai/semanticservice/contracts/EndpointReadinessCheckpointTest.kt`:
  guardrail tests for the Phase 20 decision and future endpoint rules.

## What Runs

Phase 20 can:

- validate the endpoint readiness checkpoint as a static contract artifact
- run semantic-service tests and CLI validation runtime
- parse RDF, OpenAPI, and SPARQL artifacts
- keep all endpoint implementation work blocked

## What Still Does Not Run

Phase 20 still does not:

- expose public semantic service endpoints
- implement private endpoint code
- serialize HTTP JSON responses
- generate runtime DTO classes
- accept arbitrary SPARQL text
- execute placeholder reasoning queries
- write RDF graphs beyond the existing controlled fixture-loading CLI boundary
- redesign or reconnect the UI
- remove the old FastAPI/Postgres/SQLAlchemy runtime

## Validation Commands

Run from the repository root.

Run semantic-service tests and baseline through Docker:

```bash
docker run --rm \
  -v "$PWD":/workspace \
  -w /workspace/semantic-service \
  gradle:8.10.2-jdk17 \
  gradle --no-daemon test run --args=/workspace
```

Parse all RDF artifacts and manifests:

```bash
backend/.venv/bin/python - <<'PY'
from pathlib import Path
from rdflib import Graph

patterns = [
    "fixtures/rdf/**/*.ttl",
    "ontology/modules/*.ttl",
    "shapes/*.ttl",
    "ontology/releases/*.ttl",
    "queries/*.ttl",
    "reasoning/*.ttl",
    "semantic-service/**/*.ttl",
]
for pattern in patterns:
    for path in sorted(Path().glob(pattern)):
        Graph().parse(path, format="turtle")
PY
```

Parse the OpenAPI scaffold:

```bash
backend/.venv/bin/python - <<'PY'
import yaml
from pathlib import Path

path = Path("semantic-service/openapi.semantic-service.yaml")
with path.open() as handle:
    doc = yaml.safe_load(handle)
assert doc["openapi"] == "3.1.0"
print("phase20 openapi contract still parses")
PY
```

Parse SPARQL queries:

```bash
backend/.venv/bin/python queries/validate_sparql.py
```

Check forbidden runtime boundaries:

```bash
rg -n "@RestController|@Controller|@SpringBootApplication|HttpClient|HttpURLConnection|openConnection\\(|SPARQLRepository|RDFConnection|SPARQLUpdate|UpdateFactory|UpdateExecutionFactory|DatasetAccessor" semantic-service/src/main/kotlin --glob '*.kt' \
  | rg -v 'SemanticServiceContractCatalog.kt|FusekiNamedGraphWriter.kt' || true
```

Check formatting:

```bash
git diff --check
```

## Phase 20 Completion Criteria

Phase 20 is complete when:

- endpoint readiness checkpoint exists and parses as Turtle
- checkpoint states the service remains internal-only for Phase 20
- checkpoint states a private endpoint scaffold can happen only after later
  approval
- future endpoint guardrails require the Phase 19 serializer
- future endpoint guardrails forbid raw SPARQL bindings, arbitrary
  browser-supplied SPARQL, SPARQL Update, and query-manifest bypass
- tests enforce the checkpoint markers
- no endpoint code, graph writes, SPARQL Update, reasoning, UI changes, or
  old-runtime removal has occurred
- semantic-service/OpenAPI/RDF/SPARQL/backend/frontend/diff checks pass
- no commit or push has occurred

## Post-Phase-20 Handoff

The Phase 13-20 batch is complete after this checkpoint.

The next approved work should be one of:

- review and commit Phase 20
- push the accumulated local commits
- start a new batch for private endpoint scaffolding
- pause implementation and audit the ontology-native transition state

If private endpoint scaffolding starts later, it must remain private/internal,
use `SemanticResponseSerializer`, and avoid public exposure until the endpoint
readiness gates are accepted.
