# Semantic Service API DTO Scaffold

This document describes request and response DTO boundaries for the Kotlin
semantic service. Phase 18 defined the response contract before HTTP runtime
existed. Post-Phase-20 implements the first internal-only private query
endpoint for existing approved fixture inspection query IDs. Product dashboard
view-model endpoints, public exposure, DTO generation, reasoning endpoints, and
graph-write commands remain out of scope.

## Phase 18 Response Contract Checkpoint

Future semantic query responses use typed result envelopes instead of raw
binding rows. The response contract is intentionally stable before any HTTP
runtime exists.

Shared response fields:

- `queryId`: approved query identifier from `queries/manifest.ttl`
- `resultType`: stable semantic result category
- `recordCount`: number of typed records in `records`
- `records`: typed records for the selected result category
- `provenance`: query id, graph scope, and result contract version

Supported Phase 18 response result types:

- `named-graph-inventory`
- `incident-summary`
- `provenance-source-records`

Versioning rules:

- OpenAPI scaffold version: `2026-06-phase18-response-contract-checkpoint`
- Query result provenance contract: `2026.06.phase17-result-envelope`
- Error envelope contract: `2026.06.phase18-error-envelope`
- Any breaking field rename, required-field change, result type removal, or
  record shape change must create a new contract version.
- Additive optional fields may keep the same response checkpoint only when
  existing required fields and result-type names remain stable.

## Query Execution

Endpoint shape: `POST /semantic/query/{queryId}`

Post-Phase-20 implementation status:

- implemented as an internal/private loopback endpoint
- allowed query IDs are limited to `fixtureNamedGraphInventory`,
  `fixtureIncidentSummary`, and `fixtureProvenanceSourceRecords`
- success responses are produced by `SemanticResponseSerializer`
- semantic errors use the Phase 18 error envelope
- request bodies must not contain raw SPARQL, arbitrary query text, SPARQL
  Update, or replacement query definitions
- product dashboard view-model query IDs are not implemented yet

Request DTO:

- `queryId`: approved query identifier from `queries/manifest.ttl`
- `parameters`: string-valued query parameters
- `graphScopes`: allowed graph scopes such as canonical, provenance,
  reasoning, reasoning-audit, and ai-audit
- `timeoutMs`: optional timeout budget

Response DTO:

- `queryId`: executed query identifier
- `resultType`: one of the supported Phase 18 response result types
- `recordCount`: number of typed records
- `records`: typed records matching `resultType`
- `provenance`: `queryId`, `graphScope`, and `contractVersion`

Named graph inventory record:

- `graphUri`: named graph IRI
- `subjectCount`: subject count from the approved inspection query

Incident summary record:

- `graphUri`: named graph IRI
- `incidentUri`: incident resource IRI
- `incidentId`: incident identifier
- `assetUri`: affected asset resource IRI
- `stageUri`: workflow stage resource IRI
- `sourceRecordUri`: optional source record resource IRI

Provenance source record:

- `graphUri`: named graph IRI
- `sourceRecordUri`: source record resource IRI
- `sourceRecordId`: source-system record identifier
- `sourceSystemUri`: source system resource IRI
- `payloadHash`: source payload hash
- `activityUri`: provenance import activity resource IRI

Error DTO:

- `error.code`: stable machine-readable semantic service error code
- `error.message`: human-readable error text
- `error.detail`: optional diagnostic detail
- `error.queryId`: optional query id related to the failure
- `error.contractVersion`: error envelope contract version

Initial semantic query error codes:

- `unapproved-query-id`
- `unsupported-result-envelope`
- `missing-required-binding`
- `graph-unavailable`
- `contract-validation-failed`
- `internal-semantic-service-error`

Phase 19 internal serialization:

- `SemanticResponseSerializer` converts Phase 17 result envelopes into
  Phase 18-shaped in-memory response maps.
- It also converts approved semantic error codes into the Phase 18
  `SemanticErrorResponse` map shape.
- Post-Phase-20 wraps this serializer in a private loopback HTTP boundary for
  the three existing approved inspection queries only.

Phase 20 endpoint readiness:

- `endpoint-readiness.ttl` keeps the runtime internal-only for Phase 20.
- A later private endpoint scaffold must use `SemanticResponseSerializer`.
- A later endpoint must not return raw SPARQL bindings, accept arbitrary
  browser-supplied SPARQL, run SPARQL Update, or bypass the approved query
  manifest.

Post-Phase-20 private endpoint:

- the private scaffold now exists for the first approved-query slice
- it remains internal-only and loopback-bound
- the public endpoint gates in `endpoint-readiness.ttl` are still not accepted

## Reasoning Validation

Endpoint shape: `POST /semantic/reasoning/validate`

Request DTO:

- `candidateGraph`: expected to be `urn:dcai:graph:reasoning-audit`
- `shapeSet`: expected to reference `shapes/reasoning-output-validation.ttl`
- `candidateIds`: optional candidate resource identifiers

Response DTO:

- `conforms`: SHACL validation result
- `findings`: validation findings with severity, message, source shape, and
  focus node

## Provenance Lookup

Endpoint shape: `GET /semantic/provenance/{resourceId}`

Response DTO:

- `resourceId`: requested resource identifier or encoded IRI
- `lineage`: subject, predicate, object edges describing provenance

## Promotion Review

Endpoint shape: `POST /semantic/promotion/review`

Request DTO:

- `candidateGraph`: expected to be `urn:dcai:graph:reasoning-audit`
- `candidateIds`: candidate findings to review
- `reviewerId`: optional reviewer identity placeholder

Response DTO:

- `reviewStatus`: approved, rejected, or needs-review
- `promotionAllowed`: whether a future promotion step may proceed
- `reasons`: review explanations

## AI Governance Handoff

Endpoint shape: `POST /semantic/ai-governance/handoff`

Request DTO:

- `proposalId`: AI proposal identifier
- `proposedGraph`: expected to be an AI audit graph
- `riskClass`: low, medium, or high
- `requestedBy`: optional requester identity placeholder

Response DTO:

- `handoffId`: governance workflow identifier
- `governanceStatus`: queued, rejected, or needs-human-review
- `requiredGates`: required validation, provenance, or approval gates
