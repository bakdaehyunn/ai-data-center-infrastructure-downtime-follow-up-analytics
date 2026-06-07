# Semantic Service API DTO Scaffold

This document describes request and response DTO boundaries for the future
Java/Kotlin semantic service. It is documentation only. Phase 9 does not add
DTO classes, controllers, route handlers, clients, code generation, or runtime
service behavior.

## Query Execution

Endpoint shape: `POST /semantic/query/{queryId}`

Request DTO:

- `queryId`: approved query identifier from `queries/manifest.ttl`
- `parameters`: string-valued query parameters
- `graphScopes`: allowed graph scopes such as canonical, provenance,
  reasoning, reasoning-audit, and ai-audit
- `timeoutMs`: optional timeout budget

Response DTO:

- `queryId`: executed query identifier
- `rows`: string-valued binding rows or view-model fields
- `provenance`: graph release, query version, and generated timestamp

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
