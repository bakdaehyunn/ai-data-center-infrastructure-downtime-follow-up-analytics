# API Package

Contains the post-Phase-20 private semantic query endpoint boundary.

Implemented boundary:

- `PrivateSemanticQueryEndpoint`
- internal `POST /semantic/query/{queryId}` request handling
- loopback-only `PrivateSemanticQueryEndpointServer`
- success/error payloads through `SemanticResponseSerializer`

Allowed query IDs:

- `fixtureNamedGraphInventory`
- `fixtureIncidentSummary`
- `fixtureProvenanceSourceRecords`
- `semanticFollowUpQueueList`

Non-goals:

- no public endpoints
- no additional product dashboard view-model query IDs beyond `semanticFollowUpQueueList`
- no React dashboard switch
- no raw SPARQL request body
- no SPARQL Update
- no graph writes
- no reasoning execution
- no old FastAPI/Postgres/React removal
