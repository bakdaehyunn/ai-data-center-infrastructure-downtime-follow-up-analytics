# AI Data Center Infrastructure Semantic Operations Platform

AI Data Center Infrastructure Semantic Operations Platform is a semantic ontology platform for AI data center facilities follow-up decisions.

It answers one practical question:

> Which AI infrastructure incidents are delaying return-to-service, where is the blocker, and what should the team follow up next?

![AI data center infrastructure semantic operations dashboard](docs/assets/dashboard-preview.png)

![Selected follow-up detail page](docs/assets/follow-up-detail-preview.png)

## Why This Exists

AI data center downtime evidence rarely lives in one clean system. Incident records, workflow events, facility work orders, critical spares, vendor waits, validation results, telemetry alerts, impact snapshots, infrastructure assets, and facility zones are often scattered across different operational tools.

That creates a real follow-up problem: teams may know that work is open, but they cannot quickly tell whether GPU capacity risk is blocked by triage, engineer assignment, a spare/vendor wait, repair execution, validation, missed vendor ETA, lost redundancy, or unreliable source data.

This project builds a semantic operations layer for that problem. It preserves raw source records, normalizes them into a data center infrastructure model, reconstructs state from event history, validates the RDF graph with SHACL, exposes SPARQL-backed semantic evidence, and produces a ranked follow-up queue.

## Customer Problem

The fictional customer is an AI infrastructure operations team responsible for GPU data halls. During downtime, facilities supervisors, reliability engineers, capacity operations, and data engineers each see part of the truth:

- incident tickets show priority and current status
- work orders show team ownership and repair state
- spare and vendor notes show external dependencies
- telemetry shows power, cooling, thermal, and sensor evidence
- validation records show whether return-to-service is safe
- impact snapshots show affected racks, GPUs, kW at risk, redundancy, and mitigation

Before this system, the blocked operational decision was:

> Which open infrastructure incident should the operator chase next so GPU capacity can safely return to service?

The follow-up queue is the core product answer. Summaries, selected-row context, and detail pages support the decision, but they are not the main product surface.

## Operating Scenario

The modeled AI data center infrastructure workflow is:

```text
Incident Reported
-> Facilities Triage
-> Engineer Assigned
-> Spare/Vendor Waiting
-> Repair In Progress
-> Validation
-> Restored
```

The workflow labels are not the main value. The value is turning every transition into analytical evidence:

- how long an incident waited
- where delay accumulated
- whether the delay is still actionable
- which asset and zone are affected
- how much rack, GPU, power, thermal, redundancy, and vendor exposure is attached to the incident
- whether the evidence is trustworthy
- what follow-up action is most useful now

## What It Analyzes

- Open infrastructure incidents and delayed incidents
- Current stage and hours in current stage
- Stage lead time compared with threshold hours
- Actionable bottlenecks, excluding terminal restored work from active follow-up surfaces
- Downtime concentration by infrastructure asset and facility zone
- Spare/vendor waiting impact and stock risk
- Capacity-at-risk, affected GPU, redundancy-loss, thermal-breach, vendor ETA, and mitigation context
- Impact confidence status that separates trusted, warning, and unverified impact context
- Repeat failure signals
- Facilities engineer assignment and validation delays
- Latest-run data quality and reconciliation issues
- Ranked downtime follow-up queue with recommended actions

## Architecture

```text
scattered AI infrastructure source records
  -> source-to-canonical RDF mappings
  -> named RDF graphs in Fuseki/TDB2
  -> OWL/RDFS ontology modules
  -> SHACL validation gates
  -> approved SPARQL read models
  -> Kotlin/JVM semantic-service
  -> React dashboard
```

The RDF graph store is the source of truth. The Kotlin/JVM semantic-service is the controlled API facade over approved query IDs, typed result envelopes, provenance, and semantic error contracts.

## Source Integration Model

The simulated sources represent the systems an operator normally has to reconcile manually:

- incident system
- workflow event history
- facility work order system
- critical spare and inventory context
- vendor ETA context
- telemetry alerts and readings
- validation results
- impact snapshots

See `docs/01_architecture.md` for the source-to-question mapping and trust risks.

## Ontology-Native Runtime

- `ontology/modules/`: OWL/RDFS modules for core, infrastructure, topology, workflow, impact, evidence, provenance, AI interaction, and operations concepts
- `shapes/`: SHACL contracts for source, canonical, reasoning, and service-boundary graph validation
- `fixtures/` and `rdf-mapping/`: source-to-canonical RDF fixtures and mapping contracts
- `queries/manifest.ttl`: approved query catalog with read-only SPARQL files under `queries/`
- `reasoning/`: reasoning pipeline contracts and placeholder reasoning query/rule structure
- `semantic-service/`: Kotlin/JVM runtime that loads approved queries, talks to Fuseki/TDB2, shapes typed result envelopes, serializes success/error responses, and serves the private semantic query endpoint
- `frontend/`: React/Vite dashboard that reads the semantic-service private endpoint through `VITE_SEMANTIC_API_BASE_URL`

## Semantic-Service Responsibilities

- Load and statically validate semantic service contracts
- Connect to Fuseki/TDB2 through a read-only graph access boundary
- Load controlled RDF fixtures through validation/provenance gates
- Execute only approved read-only SPARQL query IDs from the manifest
- Shape graph bindings into typed Kotlin result envelopes
- Serialize all endpoint responses through the semantic response serializer
- Reject raw SPARQL, unapproved query IDs, graph writes, public exposure, and non-loopback endpoint binding
- Provide graph-backed read models for dashboard overview, follow-up queue, filters, selected detail, impact, topology, trust findings, validation summary, incident evidence, dependency impact, and blast radius

## Production Story

The practical production path is intentionally modest:

- Dockerized Fuseki/TDB2 graph store
- Kotlin/JVM semantic-service runtime
- React frontend build target
- controlled RDF fixture/source loading through validation gates
- approved SPARQL read-model execution
- provenance-aware semantic response envelopes
- SHACL and query contract checks
- deployment and rollback notes

Kubernetes, Airflow, Kafka, and OpenTelemetry can be added later if they solve a specific operational need. They are deployment and integration choices, not the story. The story is faster, more trusted return-to-service follow-up.

Run semantic-service checks:

```bash
docker run --rm \
  -v "$PWD":/workspace \
  -w /workspace/semantic-service \
  gradle:8.10.2-jdk17 \
  gradle --no-daemon test
```

Run Fuseki locally:

```bash
docker compose up fuseki
```

Run the private semantic endpoint after Fuseki has fixture graphs loaded:

```bash
docker run --rm \
  -v "$PWD":/workspace \
  -w /workspace/semantic-service \
  -e DCAI_FUSEKI_DATASET_URL=http://host.docker.internal:3030/infrastructure \
  gradle:8.10.2-jdk17 \
  gradle --no-daemon run --args="--repo-root=/workspace --serve-private-query-endpoint"
```

## Semantic API Surface

Current private endpoint:

```text
POST /semantic/query/{queryId}
```

Approved product read-model query IDs include:

- `semanticFollowUpQueueList`
- `semanticDashboardOverview`
- `semanticFilterMetadata`
- `semanticFollowUpDetail`
- `semanticImpactSummary`
- `semanticTopologyDependencies`
- `semanticTrustFindingList`
- `semanticStageBottlenecks`
- `semanticAssetDelaySummary`
- `semanticZoneDelaySummary`
- `semanticSpareWaitSummary`
- `semanticValidationSummary`
- `semanticIncidentEvidence`
- `semanticIncidentTimeline`
- `semanticDependencyImpactByAsset`
- `semanticBlastRadiusByAsset`

The endpoint is internal/loopback only. It accepts approved query IDs, not raw SPARQL text.

## Dashboard

The React dashboard is built for follow-up decisions:

- Read-only KPI and exposure summaries for the currently visible follow-up queue
- Queue Intelligence cards that summarize the visible queue or the selected row
- Queue scope controls for clear queue subsets such as vendor ETA missed, spare/vendor wait, evidence review, and N-1 exposure
- Compact desktop follow-up table with one value per column and explicit `View details` links
- Dedicated follow-up detail route with Summary, Impact, Trust, and Dependencies tabs
- Detail evidence for stage history, work order context, spare context, impact snapshot context, telemetry evidence, vendor/mitigation status, impact trust flags, dependency paths, SHACL validation status, semantic incident evidence, and SPARQL-backed blast-radius context

Run the frontend build:

```bash
cd frontend
npm run build
```

## Tech Stack

- RDF/OWL
- SHACL
- SPARQL
- Apache Jena/Fuseki/TDB2
- Kotlin/JVM
- Gradle
- React
- TypeScript
- Vite
- Docker Compose

## Reading Path

- `docs/00_project_brief.md`: customer problem, users, success questions, and scope
- `docs/07_workflow_ontology.md`: lifecycle, allowed transitions, semantic ontology runtime, dependency states, and restoration rules
- `docs/01_architecture.md`: source integration model and layer responsibilities
- `docs/08_analytics_control_layer.md`: state reconstruction, scoring, reconciliation, and trust boundary
- `docs/09_production_rollout.md`: deployment, scheduling, health, observability, data quality reporting, and rollback
- `docs/10_operational_case_study.md`: Problem -> Discovery -> Data sources -> Workflow model -> System design -> Tradeoffs -> Production rollout plan -> Measured impact
- `docs/11_topology_semantic_connectors.md`: topology graph, semantic ontology API, Fuseki sync, and connector contracts
- `docs/12_ontology_native_rewrite_execplan.md`: full rewrite ExecPlan for an ontology-native AI semantic operations platform
- `docs/13_ontology_native_target_architecture.md`: target ontology-native architecture, graph model, modules, reasoning, AI governance, and old-runtime removal plan
- `docs/14_ontology_native_verification_plan.md`: rewrite verification gates for ontology, SHACL, SPARQL, reasoning, AI governance, UI, and old-runtime removal
- `docs/ontology-native/phase1_semantic_runtime_scaffold.md`: Phase 1 scaffold for persistent Jena/Fuseki/TDB2 runtime, graph release manifest, ontology module boundary, SHACL boundary, and query manifest placeholder
- `docs/ontology-native/phase2_ontology_shacl_contract.md`: Phase 2 parseable OWL/RDFS module and SHACL shape skeletons, fixture expectations, and validation commands
- `docs/ontology-native/phase3_rdf_mapping_graph_promotion.md`: Phase 3 RDF fixtures, source-to-canonical mapping scaffold, graph promotion documentation, and validation commands
- `docs/ontology-native/phase4_reasoning_pipeline_scaffold.md`: Phase 4 reasoning pipeline scaffold, placeholder rule/query structure, fixture expectations, and validation commands
- `docs/ontology-native/phase5_sparql_query_validation_scaffold.md`: Phase 5 parseable placeholder SPARQL query files and non-runtime query validation scaffold
- `docs/ontology-native/phase6_reasoning_execution_contract.md`: Phase 6 non-runtime reasoning execution contract for graph inputs/outputs, promotion gates, provenance requirements, failure modes, and service boundaries
- `docs/ontology-native/phase7_reasoning_output_validation.md`: Phase 7 SHACL shapes and fixture expectations for validating future reasoning outputs and reasoning activity provenance
- `docs/ontology-native/phase8_semantic_service_boundary.md`: Phase 8 non-runtime semantic service boundary contract for future Java/Kotlin query, validation, provenance, promotion review, and AI governance use cases
- `docs/ontology-native/phase9_api_contract_scaffold.md`: Phase 9 non-runtime OpenAPI-style endpoint shape and request/response DTO scaffold for the future semantic service
- `docs/ontology-native/phase10_semantic_service_project_scaffold.md`: Phase 10 minimal non-running Java/Kotlin semantic service project scaffold with build metadata, package layout placeholders, and contract wiring
- `docs/ontology-native/phase11_contract_loading_static_validation.md`: Phase 11 first Kotlin implementation slice for contract loading and static validation only
- `docs/ontology-native/phase12_cutover_implementation_readiness.md`: Phase 12 cutover and implementation-readiness checkpoint for old-runtime reference use, later-removal triggers, and gates before real semantic endpoints or graph execution
- `docs/ontology-native/phase13_semantic_service_runnable_baseline.md`: Phase 13 runnable Kotlin/JVM semantic-service baseline for contract validation before graph access
- `docs/ontology-native/phase14_read_only_graph_access.md`: Phase 14 read-only Jena/Fuseki graph access boundary before fixture loading or query execution
- `docs/ontology-native/phase15_controlled_fixture_loading.md`: Phase 15 controlled RDF fixture loading into Fuseki named graphs with SHACL/provenance gates before promotion
- `docs/ontology-native/phase16_controlled_read_only_query_execution.md`: Phase 16 controlled read-only query execution over fixture named graphs using approved manifest query IDs
- `docs/ontology-native/phase17_query_result_contract_shaping.md`: Phase 17 stable query-result envelopes for future incident, provenance, and named-graph inspection responses
- `docs/ontology-native/phase18_semantic_response_contract_checkpoint.md`: Phase 18 semantic response contract checkpoint for future typed query DTOs, error envelopes, versioning rules, and OpenAPI alignment
- `docs/ontology-native/phase19_internal_response_serialization.md`: Phase 19 internal-only response serialization from typed query envelopes and semantic errors into Phase 18-shaped payloads
- `docs/ontology-native/phase20_endpoint_readiness_decision.md`: Phase 20 endpoint readiness decision checkpoint for whether to remain internal-only or later start private semantic query endpoint scaffolding
