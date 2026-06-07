# Ontology-Native AI Semantic Operations Platform Rewrite ExecPlan

This ExecPlan is a living document. During execution, keep `Progress`,
`Surprises & Discoveries`, `Decision Log`, and `Outcomes & Retrospective`
current.

## Purpose / Big Picture

Rewrite the project as a complete ontology-native AI semantic operations
platform for AI data center infrastructure follow-up decisions.

The finished platform must use RDF named graphs as the runtime system of
record. OWL/RDFS defines the domain model, SHACL gates graph quality,
SPARQL drives runtime query and update behavior, reasoning produces inferred
operational facts, provenance explains where facts came from, and an
AI-governed interaction layer helps users query and propose graph changes
without making the language model the source of truth.

The existing FastAPI/Postgres/SQLAlchemy implementation is not preserved as
runtime architecture. It is reference material for the operational domain,
sample scenarios, field language, and lessons learned.

## Progress

- [x] Existing system classified as reference-only for the rewrite.
- [x] Full rewrite direction selected over incremental migration.
- [x] Target semantic stack selected: Apache Jena/Fuseki/TDB2, OWL/RDFS,
      SHACL, SPARQL, reasoning, named graphs, provenance, and AI governance.
- [x] Planning artifacts drafted for review.
- [ ] Architecture artifacts approved.
- [ ] Runtime implementation started.
- [ ] Ontology-native runtime completed.
- [ ] Verification completed.
- [ ] Old runtime removed or archived.
- [ ] Handoff written.

## Surprises & Discoveries

- Observation: The current repo already has useful domain vocabulary and
  sample scenarios, but the runtime remains SQL-first.
  Evidence: `backend/app/models`, `backend/app/pipeline`, and
  `backend/app/api/routes.py` own most operational reads today, while
  `backend/app/domain/semantic_graph.py` projects SQL state into RDF.

- Observation: The rewrite should not mutate the existing architecture docs
  into future-tense claims.
  Evidence: Current docs describe a working hybrid implementation. The rewrite
  needs separate planning artifacts until implementation begins.

- Observation: The first planning pass named the semantic stack, but needed
  tighter boundaries for graph versioning, write transactions, environment
  promotion, direct SPARQL exposure, and AI security.
  Evidence: The target architecture now includes graph release units,
  transaction gates, service-only write access, environment promotion, and AI
  threat controls.

## Decision Log

- Decision: Treat FastAPI, Postgres, SQLAlchemy, Alembic, and SQL analytics
  tables as disposable runtime architecture.
  Rationale: The requested end state is ontology-native, not a SQL app with a
  semantic projection.
  Date/Author: 2026-06-07 / Codex

- Decision: Use Apache Jena/Fuseki/TDB2 as the default open-source semantic
  runtime.
  Rationale: Jena provides an RDF store, SPARQL services, persistent TDB2
  storage, SHACL support, inference capabilities, and a credible local
  deployment story.
  Date/Author: 2026-06-07 / Codex

- Decision: Use a Java or Kotlin semantic service for the new runtime.
  Rationale: A JVM service aligns directly with Jena APIs for graph
  transactions, query execution, validation, inference, and graph-store
  operations.
  Date/Author: 2026-06-07 / Codex

- Decision: Preserve the follow-up decision domain, not old API contracts or
  dashboard structure.
  Rationale: The user explicitly requested a complete rewrite and said not to
  preserve the existing system.
  Date/Author: 2026-06-07 / Codex

- Decision: Do not expose unrestricted SPARQL directly to the browser.
  Rationale: The UI needs operational workflows, not raw graph mutation power.
  The semantic service should own query templates, graph scopes, update policy,
  audit records, and AI guardrails.
  Date/Author: 2026-06-07 / Codex

- Decision: Treat ontology, shapes, queries, reasoning rules, and graph
  migrations as versioned release artifacts.
  Rationale: In an ontology-native platform, schema drift and query drift are
  production risks equivalent to database migrations in a SQL system.
  Date/Author: 2026-06-07 / Codex

## Outcomes & Retrospective

To be completed after implementation. Expected outcome: the old SQL-first
runtime is no longer needed for local operation, and all primary workflows are
backed by RDF named graphs, SPARQL, SHACL, and reasoning.

## Context and Orientation

Current reference-only domain assets:

- `backend/app/sample_data`: synthetic source scenarios and operational cases.
- `ontology/`: first-pass ontology assets that can inform, but should not
  constrain, the rewrite.
- `docs/07_workflow_ontology.md`: workflow vocabulary and state logic.
- `docs/08_analytics_control_layer.md`: current scoring and trust logic.
- `docs/11_topology_semantic_connectors.md`: topology and connector concepts.
- `frontend/src/App.tsx`: current workflow interaction patterns to evaluate,
  not preserve by default.

Current architecture to replace:

- `backend/app/models/*.py`: SQLAlchemy runtime models.
- `backend/app/pipeline/*.py`: SQL load, transform, analytics, and
  reconciliation pipeline.
- `backend/app/api/routes.py`: SQL-backed API routes.
- `backend/app/domain/semantic_graph.py`: generated RDF projection from SQL.
- `docker-compose.yml`: Postgres-first local stack with optional/memory Fuseki.
- `frontend/src/api.ts`: REST response contracts from the old runtime.

## Target Architecture

```text
source extracts / connectors
  -> RDF mapping and source graph load
  -> source SHACL validation
  -> canonical graph promotion
  -> OWL/RDFS/rule reasoning
  -> inferred and operations named graphs
  -> SPARQL query and update library
  -> Java/Kotlin semantic service
  -> AI-governed graph interaction layer
  -> semantic operations UI
```

Runtime source of truth:

- Apache Jena Fuseki with TDB2 persistence.
- RDF named graphs, not SQL tables, own operational state.
- SPARQL is the primary query/update language.
- SHACL is the write and quality gate.
- Reasoning materializes derived operational facts.

## Plan of Work

### Phase 0: Rewrite Preparation

- Freeze the old implementation as reference-only.
- Add an explicit rewrite status section to project docs.
- Define acceptance criteria for removing old runtime paths.
- Decide Java vs Kotlin for the semantic service.

### Phase 1: Semantic Runtime Foundation

- Replace the local semantic runtime with persistent Jena/Fuseki/TDB2.
- Define dataset names, graph IRIs, auth assumptions, and graph lifecycle.
- Define dev/test/prod graph namespaces and graph promotion policy.
- Define backup, restore, graph reset, and dataset compaction assumptions.
- Add graph reset/load scripts as planning-approved implementation artifacts.
- Keep Postgres only if explicitly needed for source-file audit during early
  transition; it must not remain a runtime source of truth.

### Phase 2: Ontology and SHACL Contract

- Rewrite ontology modules as source-of-truth domain contracts.
- Split ontology by infrastructure, topology, workflow, impact, evidence,
  provenance, and AI interaction.
- Define SHACL shapes for required facts, state vocabulary, workflow
  transitions, dependency integrity, evidence completeness, provenance, and
  AI-proposed triples.
- Define ontology release metadata, deprecation policy, IRI stability rules,
  and graph migration rules for changed classes and properties.

### Phase 3: RDF Mapping and Graph Promotion

- Convert sample/source JSON directly into RDF.
- Load raw source triples into `graph:source`.
- Validate source graph with SHACL.
- Promote valid operational facts into `graph:canonical`.
- Attach provenance for every source and derived fact.
- Make graph promotion transactional: failed validation must leave canonical,
  inferred, and operations graphs unchanged.
- Define delete/tombstone behavior for source facts that disappear from later
  extracts.

### Phase 4: Reasoning Pipeline

- Define inference rules for dependency exposure, blocked recovery state,
  redundancy loss, restore readiness, blast radius, and trust status.
- Materialize inferred facts into `graph:inferred`.
- Record rule/provenance metadata for derived facts.

### Phase 5: SPARQL Query Library

- Build versioned SPARQL files for queue, incident detail, impact, trust,
  dependencies, topology, provenance, AI context retrieval, and graph health.
- Use SELECT for UI views, CONSTRUCT for derived graph views, ASK for guards,
  and UPDATE only through controlled service paths.
- Add query metadata for graph scope, read/write mode, expected parameters,
  timeout class, and result contract.
- Add slow-query and cardinality checks before any query becomes a UI path.

### Phase 6: Java/Kotlin Semantic Service

- Implement graph client, query loader, validation runner, reasoning runner,
  and UI-facing endpoints.
- Return application-friendly JSON, but do not recreate the old API contract
  unless the new UI intentionally needs it.
- Centralize graph updates behind validation and provenance gates.
- Own all write transactions, graph promotion, query authorization, and audit
  writes.
- Prevent browser clients from sending arbitrary SPARQL Update.

### Phase 7: AI-Governed Graph Interaction

- Add AI query assistance with approved SPARQL templates first.
- Add generated SPARQL only behind syntax checks, graph-scope guards, and
  read/write policy.
- Stage AI-proposed triples in `graph:ai-audit`.
- Promote proposed triples only after SHACL validation and approval policy.
- Add prompt-injection controls for source text, retrieved graph literals, and
  user-provided instructions.
- Require cited graph facts and provenance in AI answers that influence
  operational decisions.

### Phase 8: Semantic Operations UI

- Redesign the UI around semantic operations, not the old dashboard layout.
- Primary workflow should still answer which incident or infrastructure fact
  needs follow-up, why, what evidence supports it, and what dependency/risk is
  inferred.
- Expose graph conformance, provenance, inferred facts, and AI audit results
  as operational trust signals.

### Phase 9: Old Runtime Removal

- Remove or archive FastAPI/Postgres/SQLAlchemy/Alembic runtime paths.
- Remove SQL analytics table dependency.
- Remove Python pipeline paths unless retained only as sample-data generators.
- Update README and docs so the ontology-native architecture is the primary
  documented system.
- Remove old runtime only after graph-backed fixture parity exists for the
  source scenarios that are still part of the product story.

## Concrete Steps

Planned implementation commands will be finalized after this planning phase.
The implementation goal should start with:

```bash
docker compose config
```

Expected implementation-era commands:

```bash
# Semantic runtime
docker compose up -d fuseki

# JVM service
./gradlew test
./gradlew run

# Frontend
cd ui
npm run build
npm run lint
```

Exact paths may change after the Java/Kotlin service and redesigned UI
directories are created.

## Validation and Acceptance

Acceptance requires evidence for each requirement:

- Fuseki/TDB2 is the only runtime source of truth.
- Ontology modules load without parse errors.
- SHACL fixtures pass and fail as expected.
- RDF mapping produces expected named graph triples.
- Source-to-canonical graph promotion is repeatable.
- Reasoning produces dependency, blocker, recovery, and trust inferences.
- SPARQL queue and detail queries return expected operational facts.
- Provenance exists for source facts and inferred facts.
- AI query/proposal flow is audited and cannot bypass SHACL validation.
- UI runs against graph-backed semantic service.
- Old FastAPI/Postgres/SQLAlchemy runtime is removed, archived, or clearly
  marked non-runtime.

## Idempotence and Recovery

- Graph reset and load scripts must be safe to rerun in local development.
- Ontology and SHACL files must be versioned and reloadable.
- SPARQL query snapshots should detect semantic drift.
- Old code should remain recoverable from Git history, not mixed into the new
  runtime as a compatibility crutch.
- Each phase should end with validation before moving forward.

## Artifacts and Notes

Planning artifacts:

- `docs/12_ontology_native_rewrite_execplan.md`
- `docs/13_ontology_native_target_architecture.md`
- `docs/14_ontology_native_verification_plan.md`

Implementation artifacts to create later:

- `semantic-service/`
- `semantic-service/src/main/`
- `semantic-service/src/test/`
- `ontology/modules/`
- `ontology/releases/`
- `shapes/`
- `queries/`
- `rules/`
- `rdf-mapping/`
- `fixtures/rdf/`
- `ui/`
- `docs/ontology-native/`

## Interfaces and Dependencies

Target dependencies:

- Apache Jena Fuseki
- Apache Jena TDB2
- Jena SHACL
- Jena inference/rules
- Java or Kotlin
- Gradle or Maven
- OWL/RDFS
- SHACL
- SPARQL 1.1 Query and Update
- PROV-O-compatible provenance vocabulary
- React or equivalent frontend runtime selected during UI redesign

Interfaces to define:

- Graph Store Protocol load/update paths.
- SPARQL query endpoint usage.
- Semantic service JSON view endpoints.
- AI query/proposal endpoints.
- Graph health and conformance endpoints.
- Graph release manifest format.
- Query metadata manifest format.
- Approval policy format for AI-proposed writes.

## Stopping Condition

Stop the rewrite when the platform runs locally with Apache Jena/Fuseki/TDB2 as
the only runtime source of truth, operational screens read graph-backed
semantic facts, SHACL gates graph writes, reasoning produces useful inferred
operational facts, AI interactions are audited and validated, and docs/tests
prove FastAPI/Postgres/SQLAlchemy are not preserved as runtime authorities.
