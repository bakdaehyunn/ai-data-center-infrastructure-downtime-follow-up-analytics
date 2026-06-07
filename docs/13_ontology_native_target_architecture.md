# Ontology-Native Target Architecture

This document defines the target architecture for the full rewrite. It is not
a description of the current implementation.

## Architecture Position

The new platform is ontology-native:

- RDF named graphs are the system of record.
- OWL/RDFS defines the domain model.
- SHACL validates graph shape, vocabulary, required relationships, and write
  eligibility.
- SPARQL is the primary runtime query and update language.
- Reasoning derives operational state and dependency impact.
- Provenance explains every source and derived fact.
- AI interactions are governed, audited, and validated.

The existing FastAPI/Postgres/SQLAlchemy stack is not preserved. It may be used
as domain reference only while the new platform is designed and implemented.

## System Boundary

```text
external source extracts / connectors
  -> RDF mapping layer
  -> Jena Fuseki/TDB2 dataset
  -> ontology, shapes, source, canonical, inferred, operations, provenance, ai-audit graphs
  -> Java/Kotlin semantic service
  -> semantic operations UI
  -> AI-governed graph assistant
```

The semantic service is not the source of truth. It is a controlled application
boundary over the RDF dataset.

## Runtime Stack

### Graph Store

- Apache Jena Fuseki exposes SPARQL Query, SPARQL Update, and Graph Store
  Protocol operations.
- TDB2 provides persistent local RDF storage.
- Dataset startup must load ontology and SHACL graphs before source data is
  promoted.
- Fuseki is not exposed as an unrestricted application API. Browser clients
  interact through the semantic service, which owns graph scopes, query
  authorization, timeouts, write policy, and audit records.
- Dev, test, and production datasets use distinct graph IRI prefixes or dataset
  names so test loads cannot pollute production-like graphs.
- Backups, restores, graph reset, and compaction are runtime responsibilities,
  not ad hoc developer actions.

### Semantic Service

Preferred implementation: Java or Kotlin.

Responsibilities:

- Load versioned SPARQL query files.
- Execute SPARQL queries and map bindings to UI view models.
- Run SHACL validation before graph promotion and writes.
- Execute reasoning refreshes and materialize derived facts.
- Apply graph-scope and update-policy controls.
- Record provenance and AI audit events.
- Manage transaction boundaries for source load, canonical promotion,
  reasoning refresh, operations graph refresh, and proposed write promotion.
- Enforce query metadata: parameter requirements, graph scope, read/write
  class, timeout class, and result shape.

Non-responsibilities:

- It must not recreate SQL tables.
- It must not hide a relational runtime behind the ontology language.
- It must not let AI-generated changes bypass validation.
- It must not permit arbitrary browser-supplied SPARQL Update.
- It must not treat generated JSON view models as the source of truth.

### UI

The UI should be redesigned as a semantic operations workbench, not preserved
as the current dashboard.

Primary tasks:

- Find the next operational follow-up.
- Understand why the graph infers that follow-up.
- Inspect source evidence and provenance.
- Inspect dependency and blast-radius reasoning.
- Review SHACL, trust, and AI audit signals.
- Ask governed graph questions.

## Ontology Modules

Target module layout:

```text
ontology/modules/core.ttl
ontology/modules/infrastructure.ttl
ontology/modules/topology.ttl
ontology/modules/workflow.ttl
ontology/modules/impact.ttl
ontology/modules/evidence.ttl
ontology/modules/provenance.ttl
ontology/modules/ai-interaction.ttl
ontology/modules/operations.ttl
```

### Core

Defines shared identifiers, labels, timestamps, source-system concepts, and
cross-module superclasses.

Primary classes:

- `dcai:OperationalEntity`
- `dcai:InfrastructureEntity`
- `dcai:OperationalEvent`
- `dcai:EvidenceArtifact`
- `dcai:DerivedFact`

### Infrastructure

Defines physical and logical AI data center entities.

Primary classes:

- `dcai:Facility`
- `dcai:InfrastructureZone`
- `dcai:InfrastructureAsset`
- `dcai:PowerAsset`
- `dcai:CoolingAsset`
- `dcai:ControlTelemetryAsset`
- `dcai:ComputeCapacityGroup`

### Topology

Defines dependency edges and paths.

Primary classes:

- `dcai:DependencyEdge`
- `dcai:DependencyPath`
- `dcai:PowerPath`
- `dcai:CoolingPath`
- `dcai:TelemetryPath`
- `dcai:RedundancyPath`

Primary properties:

- `dcai:dependsOn`
- `dcai:supports`
- `dcai:hasDependencyRole`
- `dcai:hasImpactScope`
- `dcai:hasPathStep`

### Workflow

Defines incidents, stages, events, allowed transitions, and recovery state.

Primary classes:

- `dcai:InfrastructureIncident`
- `dcai:WorkflowStage`
- `dcai:WorkflowEvent`
- `dcai:RecoveryBlocker`
- `dcai:FollowUpDecision`

Primary properties:

- `dcai:hasCurrentStage`
- `dcai:enteredStage`
- `dcai:exitedStage`
- `dcai:hasAllowedNextStage`
- `dcai:hasRecommendedAction`

### Impact

Defines operational exposure.

Primary classes:

- `dcai:ImpactObservation`
- `dcai:CapacityExposure`
- `dcai:GpuExposure`
- `dcai:ThermalExposure`
- `dcai:RedundancyExposure`
- `dcai:VendorExposure`

Primary properties:

- `dcai:estimatedCapacityRiskKw`
- `dcai:affectedGpuCount`
- `dcai:hasRedundancyState`
- `dcai:hasMitigationState`
- `dcai:hasVendorState`

### Evidence

Defines trust and source evidence.

Primary classes:

- `dcai:EvidenceRecord`
- `dcai:TelemetryEvidence`
- `dcai:ValidationEvidence`
- `dcai:WorkOrderEvidence`
- `dcai:SourceQualityIssue`
- `dcai:TrustFinding`

Primary properties:

- `dcai:supportsFact`
- `dcai:contradictsFact`
- `dcai:hasConfidenceState`
- `dcai:hasEvidenceSeverity`

### Provenance

Specializes PROV-O-compatible lineage for imports and derived facts.

Primary classes:

- `dcai:SourceExtract`
- `dcai:ImportActivity`
- `dcai:PromotionActivity`
- `dcai:ReasoningActivity`
- `dcai:SourceRecord`

Primary properties:

- `prov:wasDerivedFrom`
- `prov:wasGeneratedBy`
- `prov:used`
- `prov:generatedAtTime`

### AI Interaction

Defines governed AI actions.

Primary classes:

- `dcai:AIInteraction`
- `dcai:AIQuestion`
- `dcai:GeneratedSparql`
- `dcai:ProposedTripleSet`
- `dcai:AIApprovalDecision`
- `dcai:AIGuardrailViolation`

Primary properties:

- `dcai:generatedQuery`
- `dcai:proposesTriple`
- `dcai:hasApprovalState`
- `dcai:blockedByGuardrail`
- `dcai:validatedAgainstShape`

### Operations

Defines graph-native operational views.

Primary classes:

- `dcai:FollowUpQueueItem`
- `dcai:OperationalPriorityScore`
- `dcai:DependencyImpactFinding`
- `dcai:RestoreReadinessFinding`
- `dcai:BlastRadiusFinding`

## Named Graph Strategy

```text
urn:dcai:graph:ontology
urn:dcai:graph:shapes
urn:dcai:graph:source
urn:dcai:graph:canonical
urn:dcai:graph:inferred
urn:dcai:graph:operations
urn:dcai:graph:provenance
urn:dcai:graph:ai-audit
```

Graph IRIs are environment-scoped during implementation, for example:

```text
urn:dcai:dev:graph:canonical
urn:dcai:test:graph:canonical
urn:dcai:prod:graph:canonical
```

The exact namespace may change, but environment separation is required.

### Graph Lifecycle

1. Load ontology into `graph:ontology`.
2. Load SHACL shapes into `graph:shapes`.
3. Convert source extracts to RDF in `graph:source`.
4. Validate source graph.
5. Promote valid normalized facts into `graph:canonical`.
6. Run reasoning from ontology and canonical facts.
7. Materialize inferred facts into `graph:inferred`.
8. Generate operational decision views into `graph:operations`.
9. Record all source, promotion, reasoning, and AI activity in provenance and
   audit graphs.

### Graph Release Units

Each release is a coordinated set of:

- ontology modules
- SHACL shapes
- SPARQL query files
- reasoning rules or CONSTRUCT queries
- RDF mapping rules
- graph migration scripts
- fixture data and expected query snapshots

The release manifest records:

- release ID and semantic version
- ontology module versions
- shape graph version
- query manifest version
- required graph migrations
- compatible semantic service version
- fixture snapshot baseline

Breaking ontology changes require graph migration steps and fixture updates.
Class/property deprecations should remain query-compatible for at least one
release unless the implementation phase explicitly approves a hard break.

### Transaction and Promotion Model

Graph writes are staged before promotion:

```text
source load transaction
  -> source SHACL validation
  -> canonical promotion transaction
  -> canonical SHACL validation
  -> reasoning refresh transaction
  -> operations refresh transaction
  -> provenance/audit commit
```

If validation fails at any gate, the service must leave canonical, inferred,
and operations graphs in the last known-good state. Source graph failures are
recorded as validation findings instead of partially promoted operational
facts.

Delete behavior must be explicit:

- withdrawn source facts should create tombstone or superseded records
- canonical facts should not disappear silently
- derived facts should be recalculated from the current canonical graph
- provenance must preserve the prior source state

## SPARQL Query Library

Target layout:

```text
queries/health/conformance.rq
queries/health/graph_counts.rq
queries/ingestion/promote_source_to_canonical.ru
queries/reasoning/dependency_exposure.construct.rq
queries/reasoning/recovery_blocker.construct.rq
queries/reasoning/restore_readiness.construct.rq
queries/operations/follow_up_queue.select.rq
queries/operations/follow_up_detail.select.rq
queries/operations/impact_evidence.select.rq
queries/operations/trust_evidence.select.rq
queries/operations/dependency_paths.select.rq
queries/operations/blast_radius.select.rq
queries/provenance/fact_lineage.select.rq
queries/ai/context_for_question.select.rq
queries/ai/validate_generated_query.ask.rq
queries/ai/stage_proposed_triples.ru
queries/manifest.ttl
```

Rules:

- SPARQL files are versioned artifacts.
- Application code loads queries by name, not inline string fragments.
- SELECT supports UI views.
- CONSTRUCT supports derived graph generation.
- ASK supports guardrails and readiness checks.
- UPDATE is allowed only through controlled service commands.
- Every query has manifest metadata: identifier, purpose, graph scope, query
  type, parameters, timeout class, result contract, and test fixture.
- Query changes require snapshot test review before they become UI-facing.

Example manifest concept:

```text
query:followUpQueue
  query:file "queries/operations/follow_up_queue.select.rq" ;
  query:mode "SELECT" ;
  query:scope graph:canonical, graph:inferred, graph:operations ;
  query:timeoutClass "interactive" ;
  query:requiresParameter query:asOfTime .
```

## SHACL Strategy

Target layout:

```text
shapes/source-required-fields.ttl
shapes/canonical-integrity.ttl
shapes/workflow-transitions.ttl
shapes/topology-integrity.ttl
shapes/impact-evidence.ttl
shapes/provenance-required.ttl
shapes/ai-proposed-write.ttl
```

Validation gates:

- Source graph gate: required identifiers, timestamps, source system, and
  payload classification.
- Canonical graph gate: valid incident, asset, zone, dependency, evidence, and
  impact relationships.
- Workflow gate: allowed stages, event semantics, transition order, and restore
  rules.
- Topology gate: dependency edge direction, path membership, asset references,
  and dependency role vocabulary.
- Evidence gate: confidence state, contradiction/support links, and validation
  evidence completeness.
- Provenance gate: every source and derived fact has traceable origin.
- AI write gate: proposed triples must be syntactically valid, graph-scoped,
  provenance-backed, and shape-conformant.

## Reasoning Pipeline

Reasoning outputs are materialized into `graph:inferred`.

Initial inference families:

- Dependency exposure: infer downstream assets affected by upstream power,
  cooling, control, or redundancy degradation.
- Recovery blocker: infer blocker class from stage, work evidence, spare state,
  vendor state, and validation state.
- Restore readiness: infer whether an incident has enough completed work and
  validation evidence to be considered restorable.
- Impact trust: infer trusted, warning, or invalid impact evidence based on
  source support and contradiction.
- Blast radius: infer incidents and capacity groups affected by dependency
  paths.

Reasoning must be deterministic and testable. If rules become too complex for
OWL/RDFS alone, use Jena rule reasoning or controlled SPARQL CONSTRUCT
materialization.

### Reasoning Boundaries

Use OWL/RDFS for stable class/property semantics and lightweight entailment.
Use Jena rules or SPARQL CONSTRUCT for operational decisions that depend on
thresholds, time windows, workflow ordering, or scoring. Those operational
rules must be versioned alongside SPARQL queries and tested with fixtures.

The platform should not hide critical decision logic inside UI code or
unversioned service branches.

## AI Governance Layer

AI can assist with graph interaction but cannot become the graph authority.

Read flow:

```text
user question
  -> classify intent
  -> choose approved SPARQL template or generate guarded SPARQL
  -> validate graph scope and query type
  -> execute read-only query
  -> answer with cited graph facts and provenance
  -> write AI interaction audit record
```

Write/proposal flow:

```text
user asks for graph update
  -> AI proposes triples
  -> stage proposed triples in ai-audit graph
  -> validate with SHACL
  -> require approval policy
  -> promote valid triples to target graph
  -> write provenance and audit records
```

Guardrails:

- No direct unrestricted SPARQL Update from AI.
- No write without provenance.
- No promotion without SHACL conformance.
- No cross-graph write outside approved graph scope.
- No hidden mutation by the UI or assistant.
- No model-provided instruction can override graph write policy.
- Retrieved source text and graph literals are treated as untrusted content for
  prompt-injection purposes.
- AI answers that recommend action must cite graph facts, provenance, and
  conformance status.

### AI Security Model

Threats to account for:

- prompt injection in source records, work-order notes, vendor text, telemetry
  descriptions, or user questions
- generated SPARQL that broadens graph scope
- generated SPARQL Update disguised as a read
- fabricated citations or unsupported operational recommendations
- stale graph context used as current operational evidence
- proposed triples that erase or override source provenance

Controls:

- template-first query flow for common operational questions
- parser-level query classification before execution
- graph allowlists per user action
- maximum query timeout and result-size limits
- provenance-required answer generation
- SHACL and approval gates for all proposed writes
- append-only audit records for AI interactions

## Security and Access Boundaries

The rewrite must define authorization before runtime implementation:

- read-only graph queries
- privileged graph load and promotion
- reasoning refresh
- AI proposed-write staging
- AI proposed-write approval
- graph administration and reset

Local development may use simplified credentials, but the architecture should
not assume anonymous write access to Fuseki. Production-like deployment must
separate read, write, admin, and AI proposal permissions.

## Observability and Operations

Operational telemetry should include:

- graph counts by named graph
- ontology, shape, query, and service release versions
- last source load status
- last SHACL validation status
- last reasoning refresh status
- slow SPARQL query events
- AI guardrail blocks
- proposed-write approvals and rejections
- graph backup and restore status

These are semantic platform health signals, not optional dashboard cosmetics.

## UI Direction

The UI should be redesigned after the ontology model and query library exist.

Recommended top-level areas:

- Follow-up Workbench: graph-derived operational follow-up queue.
- Incident Evidence: selected incident facts, source evidence, provenance, and
  SHACL status.
- Dependency Reasoning: inferred paths, blast radius, affected capacity, and
  reasoning explanation.
- Graph Trust: conformance, source quality, contradictions, and stale facts.
- AI Graph Assistant: governed query interface and proposed-change review.

Avoid a decorative ontology map as the center. The UI should expose semantic
evidence only where it helps users decide what to do next.

## Old Runtime Removal Plan

Removal should happen only after graph-backed equivalents pass tests.

Candidate archive/remove set:

- `backend/app/models/`
- `backend/app/db.py`
- `backend/app/pipeline/`
- `backend/app/api/routes.py`
- `backend/alembic/`
- `backend/requirements.txt`
- old FastAPI app entry points
- Postgres service from `docker-compose.yml`
- frontend API types tied to old REST contracts

Allowed retention:

- sample scenario content, if converted into RDF source fixtures.
- documentation snippets, if rewritten as target architecture or case-study
  context.
- screenshots only if replaced by new UI screenshots later.

Removal gates:

- RDF fixtures cover retained sample scenarios.
- SPARQL query snapshots cover follow-up, detail, impact, trust, dependency,
  provenance, and AI context views.
- UI no longer imports old REST API types.
- Docker Compose runs without Postgres as source of truth.
- Docs no longer describe the SQL-first runtime as the current platform.
- Search checks prove remaining FastAPI/Postgres/SQLAlchemy references are
  archived or historical only.

## Implementation Checkpoints

1. Planning artifacts approved.
2. Jena/Fuseki/TDB2 persistent runtime boots locally.
3. Ontology and SHACL modules load cleanly.
4. Source RDF fixtures load into `graph:source`.
5. Source graph validation passes/fails with expected fixtures.
6. Canonical graph promotion works.
7. Reasoning materializes inferred facts.
8. SPARQL operations return follow-up queue and detail facts.
9. Semantic service serves graph-backed views.
10. AI audit and proposal gates work.
11. New UI can complete primary follow-up workflow.
12. Old runtime paths are removed or archived.

## Stopping Condition

The target architecture is achieved when a local user can run the platform with
Jena/Fuseki/TDB2 as the source of truth, inspect graph-backed operational
follow-up decisions, validate facts with SHACL, see inferred dependency and
impact reasoning, trace provenance, use AI-governed graph queries/proposals,
and verify that FastAPI/Postgres/SQLAlchemy are not preserved as runtime
authorities.
