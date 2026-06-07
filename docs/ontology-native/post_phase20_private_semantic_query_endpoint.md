# Post-Phase-20 Private Semantic Query Endpoint

## Purpose

This checkpoint records the first private endpoint implementation after the
Phase 20 endpoint-readiness decision. It implements only the approved-query
inspection slice identified in the route parity plan.

## Implemented Boundary

The Kotlin semantic service now has an internal-only endpoint boundary:

- `POST /semantic/query/{queryId}`
- implemented by `PrivateSemanticQueryEndpoint`
- optionally served by `PrivateSemanticQueryEndpointServer`
- loopback-only bind host, defaulting to `127.0.0.1`
- success responses through `SemanticResponseSerializer`
- errors through the Phase 18 semantic error envelope

The endpoint is opt-in through:

```bash
--serve-private-query-endpoint
```

Optional runtime flags:

```bash
--private-endpoint-host=127.0.0.1
--private-endpoint-port=18080
```

## Allowed Query IDs

Only the existing Phase 16 approved inspection query IDs are allowed:

- `fixtureNamedGraphInventory`
- `fixtureIncidentSummary`
- `fixtureProvenanceSourceRecords`

The endpoint rejects any other query ID with `unapproved-query-id`.

## Explicit Non-Goals

This checkpoint does not:

- add product dashboard view-model queries
- expose public endpoints
- accept raw SPARQL request bodies
- execute SPARQL Update
- execute reasoning
- write RDF graphs
- redesign the UI
- remove old FastAPI/Postgres/SQLAlchemy/React runtime code
- commit or push

## Error Handling

The endpoint maps failures to the existing semantic error envelope:

- unapproved query id -> `unapproved-query-id`
- unsupported result envelope -> `unsupported-result-envelope`
- missing required binding -> `missing-required-binding`
- graph query failure -> `graph-unavailable`
- invalid method, path, or raw SPARQL body -> `contract-validation-failed`

## Verification

Focused tests cover:

- approved query response serialization
- unapproved query rejection
- raw SPARQL request body rejection
- missing binding error mapping
- unsupported envelope error mapping
- graph unavailable error mapping
- non-POST rejection
- loopback HTTP serving
- non-loopback bind rejection
- JSON escaping

Verification command:

```bash
docker run --rm \
  -v "$PWD":/workspace \
  -w /workspace/semantic-service \
  gradle:8.10.2-jdk17 \
  gradle --no-daemon test
```

## Next Implementation Slice

The next implementation slice should be the first product read model:

- query ID: `semanticFollowUpQueueList`
- SPARQL: read-only SELECT over canonical/provenance graphs
- envelope: `FollowUpQueueEnvelope`
- serializer support: required
- provenance fields: required per queue row
- endpoint: still private/internal through `POST /semantic/query/{queryId}`

Do not switch the React dashboard or delete old FastAPI code until the semantic
queue read model has parity tests against the current fixture-backed behavior.
