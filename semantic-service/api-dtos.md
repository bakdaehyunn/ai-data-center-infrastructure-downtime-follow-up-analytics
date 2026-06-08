# Semantic Service API DTO Scaffold

This document describes request and response DTO boundaries for the Kotlin
semantic service. Phase 18 defined the response contract before HTTP runtime
existed. Post-Phase-20 now implements an internal-only private query endpoint
for approved fixture inspection and product read-model query IDs. Public
exposure, DTO generation, reasoning endpoints, and graph-write commands remain
out of scope.

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
- `follow-up-queue`
- `dashboard-overview`
- `filter-metadata`
- `follow-up-detail`
- `impact-summary`
- `topology-dependencies`
- `trust-findings`
- `stage-bottlenecks`
- `asset-delay-summary`
- `zone-delay-summary`
- `spare-wait-summary`
- `validation-summary`
- `incident-evidence`
- `incident-timeline`
- `dependency-impact`
- `blast-radius`

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
  `fixtureIncidentSummary`, `fixtureProvenanceSourceRecords`, and
  product read-model query IDs currently approved in `queries/manifest.ttl`
- success responses are produced by `SemanticResponseSerializer`
- semantic errors use the Phase 18 error envelope
- request bodies must not contain raw SPARQL, arbitrary query text, SPARQL
  Update, or replacement query definitions
- request bodies may include string-valued `parameters` for approved lookup
  query IDs; unsupported parameter names are rejected before execution
- product dashboard view-model query IDs are implemented only when backed by
  approved SPARQL, typed envelopes, shaper support, serializer support, and
  private endpoint tests

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

Follow-up queue record:

- `graphUri`: named graph IRI
- `incidentUri`: incident resource IRI
- `incidentId`: incident identifier
- `assetUri`: affected asset resource IRI
- `assetId`: asset identifier
- `zoneUri`: infrastructure zone resource IRI
- `zoneId`: zone identifier
- `stageUri`: current workflow stage resource IRI
- `stageLabel`: optional current stage label
- `sourceRecordUri`: source record resource IRI for row provenance
- `priorityRank`: optional graph-backed follow-up queue rank
- `requestTitle`: optional graph-backed follow-up title
- `currentStatus`: optional graph-backed operational status
- `hoursInCurrentStage`: optional current-stage duration in hours
- `neededByAt`: optional needed-by timestamp
- `priorityLevel`: optional priority level
- `businessImpact`: optional business impact summary
- priority score inputs: optional `assetCriticalityScore`, `downtimeScore`,
  `stageDelayScore`, `infrastructureZoneImpactScore`,
  `neededByUrgencyScore`, `repeatFailureScore`, `spareRiskScore`,
  `capacityRiskScore`, `redundancyRiskScore`, `thermalRiskScore`,
  `vendorEtaRiskScore`, `mitigationCreditScore`, and `totalPriorityScore`

Dashboard overview record:

- `graphUri`: named graph IRI
- `totalIncidents`: count of canonical infrastructure incidents
- `assetCount`: count of canonical infrastructure assets
- `zoneCount`: count of canonical infrastructure zones
- `impactObservationCount`: count of impact observations
- `capacityRiskKw`: summed capacity risk in kW
- `affectedGpuCount`: summed affected GPU count
- `dependencyEdgeCount`: count of dependency edges
- `trustFindingCount`: count of trust findings
- optional runtime totals: `avgDurationHours`, `totalDurationHours`,
  `totalDelayHours`, `mitigatedIncidentCount`, `affectedRackCount`,
  `thermalBreachMinutes`, `redundancyLostIncidentCount`, and
  `vendorEtaMissedCount`
- optional specialty counters: `repeatFailureAssetCount` and
  `engineerAssignmentDelayHours`

Filter metadata record:

- `graphUri`: named graph IRI
- `filterType`: filter group such as `zone`, `asset`, `assetType`, or `stage`
- `resourceUri`: resource IRI backing the option
- `id`: stable filter identifier
- `label`: optional display label
- `sourceRecordUri`: optional source record resource IRI

Follow-up detail record:

- includes the follow-up queue row fields
- `impactUri`: optional impact observation IRI
- `capacityRiskKw`: optional selected incident capacity risk
- `affectedGpuCount`: optional affected GPU count
- `followUpDecisionUri`: optional derived follow-up decision IRI
- `recommendedAction`: optional graph-backed recommended action
- `recoveryBlockerUri`: optional recovery blocker IRI
- `blockerSummary`: optional recovery blocker summary
- `trustFindingUri`: optional trust finding IRI
- `trustSummary`: optional trust finding summary
- specialty counters: optional `repeatFailureAssetCount` and
  `engineerAssignmentDelayHours`
- impact state fields: optional `redundancyState`, `affectedRackCount`,
  `estimatedGpuCapacityRiskPct`, `thermalBreachMinutes`,
  `powerRedundancyLost`, `coolingRedundancyLost`, `mitigationStatus`,
  `vendorEtaAt`, and `vendorStatus`

Impact summary record:

- `graphUri`: named graph IRI
- `impactObservationCount`: count of impact observations
- `incidentCount`: count of incidents with impact observations
- `capacityRiskKw`: summed capacity risk in kW
- `affectedGpuCount`: summed affected GPU count
- `trustFindingCount`: count of trust findings tied to impacts
- optional impact totals: `affectedRackCount`, `thermalBreachMinutes`,
  `redundancyLostIncidentCount`, `vendorEtaMissedCount`, and
  `mitigatedIncidentCount`

Topology dependency record:

- `graphUri`: named graph IRI
- `dependencyEdgeUri`: dependency edge IRI
- `dependencyId`: dependency edge identifier
- `dependentAssetUri`: dependent/downstream asset IRI
- `dependentAssetId`: dependent/downstream asset identifier
- `dependencyAssetUri`: dependency/upstream asset IRI
- `dependencyAssetId`: dependency/upstream asset identifier
- `dependencyRole`: role of the dependency
- `impactScope`: optional impact scope
- `dependencyPathUri`: optional dependency path IRI
- `pathId`: optional dependency path identifier
- `sourceRecordUri`: source record resource IRI for row provenance

Trust finding record:

- `graphUri`: named graph IRI
- `trustFindingUri`: trust finding IRI
- `trustFindingId`: optional stable trust finding identifier
- `summary`: finding summary
- `sourceFactUri`: source fact IRI used by the finding
- `activityUri`: optional reasoning activity IRI
- `severity`: optional semantic severity
- `status`: optional confidence or validation status
- `createdAt`: optional finding creation timestamp

Stage bottleneck record:

- `graphUri`: named graph IRI
- `stageUri`: workflow stage IRI
- `stageLabel`: optional stage label
- `incidentCount`: incident count currently at the stage
- optional duration fields: `delayedCount`, `avgDurationHours`,
  `p90DurationHours`, and `totalDelayHours`
- `sourceRecordUri`: sampled source record IRI for provenance

Asset delay summary record:

- `graphUri`: named graph IRI
- `assetUri`: asset IRI
- `assetId`: asset identifier
- `zoneUri`: zone IRI
- `zoneId`: zone identifier
- `incidentCount`: incident count linked to the asset
- `impactObservationCount`: impact observation count linked to the asset
- `capacityRiskKw`: summed capacity risk in kW
- `affectedGpuCount`: summed affected GPU count
- optional delay fields: `delayedIncidentCount`, `totalDurationHours`,
  `avgDurationHours`, and `topFailureMode`
- `repeatFailureCount`: optional repeat-failure count for the asset
- `sourceRecordUri`: source record IRI for asset provenance

Zone delay summary record:

- `graphUri`: named graph IRI
- `zoneUri`: zone IRI
- `zoneId`: zone identifier
- `assetCount`: asset count in the zone
- `incidentCount`: incident count linked to zone assets
- `impactObservationCount`: impact observation count linked to zone assets
- `capacityRiskKw`: summed capacity risk in kW
- `affectedGpuCount`: summed affected GPU count
- optional delay fields: `delayedIncidentCount`, `criticalIncidentCount`,
  `totalDurationHours`, and `topBottleneckStage`
- `sourceRecordUri`: source record IRI for zone provenance

Spare wait summary record:

- `graphUri`: named graph IRI
- `stageUri`: workflow stage IRI
- `stageLabel`: optional stage label
- `incidentCount`: incidents in spare/vendor/waiting stages
- `recoveryBlockerCount`: recovery blocker count linked to those incidents
- optional wait fields: `totalWaitHours`, `avgWaitHours`, and `stockStatus`
- `sourceRecordUri`: sampled source record IRI for provenance

Validation summary record:

- `graphUri`: named graph IRI
- `sourceRecordCount`: source record count
- `incidentCount`: incident count
- `incidentWithProvenanceCount`: incidents carrying source provenance
- `assetCount`: asset count
- `assetWithProvenanceCount`: assets carrying source provenance

Incident evidence record:

- `graphUri`: named graph IRI
- `incidentUri`: incident IRI
- `incidentId`: incident identifier
- `stageUri`: current workflow stage IRI
- `stageLabel`: optional current workflow stage label
- `sourceRecordUri`: incident source record IRI
- `impactUri`: optional impact observation IRI
- `evidenceUri`: optional supporting evidence IRI
- `evidenceClassUri`: optional evidence class IRI
- `evidenceTimestamp`: optional evidence timestamp
- `confidenceState`: optional evidence confidence state
- telemetry fields: optional `metricName`, `metricValue`, `metricUnit`, and
  `telemetryStatus`
- telemetry alert fields: optional `telemetryAlertId`, `alertType`,
  `alertSeverity`, `alertTriggeredAt`, and `alertResolvedAt`
- validation fields: optional `validationId`, `validationStatus`,
  `validatorId`, `validationStartedAt`, `validationCompletedAt`, and
  `failureReason`
- work-order fields: optional `workOrderId`, `assignedTeam`,
  `assignedEngineerId`, `workOrderStatus`, `plannedStartAt`, `actualStartAt`,
  `actualCompletedAt`, `requiredSpareId`, `requiredSpareName`, and
  `stockStatus`
- `trustFindingUri`: optional trust finding IRI
- `trustSummary`: optional trust finding summary

Incident timeline record:

- `graphUri`: named graph IRI
- `incidentUri`: incident IRI
- `incidentId`: incident identifier
- `eventUri`: workflow event IRI
- `eventId`: optional source/system event identifier
- `stageUri`: workflow stage IRI
- `stageLabel`: optional workflow stage label
- `eventStatus`: optional event status
- `enteredAt`: optional stage entry timestamp
- `exitedAt`: optional stage exit timestamp
- `durationHours`: optional stage duration in hours
- `thresholdHours`: optional stage threshold in hours
- `delayHours`: optional duration above threshold
- `sourceRecordUri`: source record IRI for event provenance

Dependency impact record:

- `graphUri`: named graph IRI
- `assetUri`: asset IRI
- `assetId`: asset identifier
- `dependencyEdgeUri`: optional dependency edge IRI
- `dependencyId`: optional dependency edge identifier
- `dependencyAssetUri`: optional upstream dependency asset IRI
- `dependencyAssetId`: optional upstream dependency asset identifier
- `dependencyRole`: optional dependency role
- `impactScope`: optional dependency impact scope
- `findingUri`: optional dependency impact finding IRI
- `findingSummary`: optional dependency impact finding summary
- `sourceRecordUri`: optional dependency source record IRI

Blast radius record:

- `graphUri`: named graph IRI
- `assetUri`: asset IRI
- `assetId`: asset identifier
- `downstreamAssetUri`: optional downstream asset IRI
- `downstreamAssetId`: optional downstream asset identifier
- `incidentUri`: optional incident IRI
- `incidentId`: optional incident identifier
- `findingUri`: optional blast-radius finding IRI
- `findingSummary`: optional blast-radius finding summary

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
  approved inspection and product read-model queries.

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
