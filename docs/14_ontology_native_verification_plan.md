# Ontology-Native Rewrite Verification Plan

This verification plan applies to the full rewrite. It does not validate the
current hybrid implementation.

## Acceptance Summary

The rewrite is acceptable only when:

- Apache Jena/Fuseki/TDB2 is the runtime source of truth.
- OWL/RDFS ontology modules load and represent the operational domain.
- SHACL gates source, canonical, workflow, topology, evidence, provenance, and
  AI-proposed write validity.
- SPARQL query files drive operational reads and controlled updates.
- Reasoning produces useful inferred dependency, recovery, impact, and trust
  facts.
- Provenance traces imported and derived facts.
- AI interactions are audited, graph-scoped, and validation-gated.
- The UI runs against graph-backed semantic service behavior.
- FastAPI/Postgres/SQLAlchemy are not preserved as runtime authorities.
- Browser clients cannot send arbitrary SPARQL Update to the graph store.
- Ontology, shapes, queries, rules, mappings, and graph migrations are handled
  as versioned release artifacts.

## Planning Artifact Verification

Before implementation starts, check:

```bash
rg -n "FastAPI|Postgres|SQLAlchemy|source of truth|not preserved|reference-only" docs/12_ontology_native_rewrite_execplan.md docs/13_ontology_native_target_architecture.md
rg -n "Jena|Fuseki|TDB2|OWL|RDFS|SHACL|SPARQL|reasoning|named graph|provenance|AI" docs/12_ontology_native_rewrite_execplan.md docs/13_ontology_native_target_architecture.md docs/14_ontology_native_verification_plan.md
rg -n "semantic-service|ontology/modules|shapes/|queries/|rdf-mapping|ui/" docs/12_ontology_native_rewrite_execplan.md docs/13_ontology_native_target_architecture.md
rg -n "transaction|promotion|release|manifest|direct SPARQL|arbitrary SPARQL|prompt-injection|authorization|observability" docs/12_ontology_native_rewrite_execplan.md docs/13_ontology_native_target_architecture.md docs/14_ontology_native_verification_plan.md
```

Expected result: the planning docs explicitly name the target architecture,
rewrite modules, verification gates, and old-runtime removal policy.

## Ontology Verification

Target checks:

```bash
# Example command shape; exact tool command finalized during implementation.
riot --validate ontology/modules/*.ttl
```

Acceptance:

- Every ontology file parses.
- Classes and properties use stable IRIs.
- Module imports are explicit.
- Core classes are not duplicated with conflicting names.
- Ontology profile choice is documented.
- Operational concepts are modeled as RDF/OWL terms, not hidden in service code.
- Ontology release metadata identifies module versions and compatible shape,
  query, rule, and service versions.
- Deprecated classes and properties have documented compatibility or migration
  rules.

Required test fixtures:

- Valid minimal incident graph.
- Valid dependency path graph.
- Valid evidence/provenance graph.
- Invalid graph with missing required asset link.
- Invalid graph with unknown workflow stage.

## SHACL Verification

Target checks:

```bash
# Example command shape; exact graph names finalized during implementation.
shacl validate --shapes shapes/canonical-integrity.ttl --data fixtures/valid/canonical.ttl
shacl validate --shapes shapes/workflow-transitions.ttl --data fixtures/invalid/workflow_skip.ttl
```

Acceptance:

- Valid fixtures conform.
- Invalid fixtures fail for the expected shape.
- Required identifiers, timestamps, source records, and graph relationships are
  enforced.
- Workflow transition and restore rules are enforced.
- Dependency edges cannot reference missing assets.
- AI-proposed writes cannot pass without provenance and allowed graph scope.

Required test groups:

- Source required fields.
- Canonical graph integrity.
- Workflow transition validity.
- Topology integrity.
- Impact/evidence support and contradiction.
- Provenance required.
- AI proposed write validation.
- Graph migration validation after ontology or shape changes.

## RDF Mapping Verification

Target checks:

```bash
# Example command shape.
./gradlew test --tests "*RdfMapping*"
```

Acceptance:

- Sample/source records convert directly to RDF.
- Raw facts load into `urn:dcai:graph:source`.
- Canonical facts are promoted only after validation.
- Every promoted fact has provenance.
- Re-running load/reset produces deterministic graph counts.
- Failed validation leaves canonical, inferred, and operations graphs unchanged.
- Withdrawn source facts produce explicit superseded or tombstone evidence.

Required assertions:

- Incident source record becomes an incident resource.
- Asset source record becomes an asset resource.
- Dependency source record becomes a dependency edge.
- Stage event source record becomes workflow event evidence.
- Impact snapshot source record becomes impact evidence.
- Source record identity is preserved in provenance.

## SPARQL Query Verification

Target checks:

```bash
# Example command shape.
./gradlew test --tests "*SparqlQuery*"
```

Acceptance:

- Query files load from `queries/`.
- No critical query is embedded only in service code.
- Query manifest metadata exists for graph scope, query mode, parameters,
  timeout class, result contract, and fixture coverage.
- Queue query returns deterministic ordering for fixture data.
- Detail query returns incident, asset, workflow, evidence, impact, trust, and
  dependency context.
- Provenance query traces facts back to source records or reasoning activity.
- ASK guard queries block invalid AI or update behavior.

Required query tests:

- `queries/manifest.ttl`
- `queries/operations/follow_up_queue.select.rq`
- `queries/operations/follow_up_detail.select.rq`
- `queries/operations/impact_evidence.select.rq`
- `queries/operations/trust_evidence.select.rq`
- `queries/operations/dependency_paths.select.rq`
- `queries/operations/blast_radius.select.rq`
- `queries/provenance/fact_lineage.select.rq`
- `queries/ai/context_for_question.select.rq`
- `queries/ai/validate_generated_query.ask.rq`

## Reasoning Verification

Target checks:

```bash
./gradlew test --tests "*Reasoning*"
```

Acceptance:

- Inference runs are deterministic.
- Inferred facts are written to `urn:dcai:graph:inferred`.
- Derived operational views are written to `urn:dcai:graph:operations`.
- Reasoning provenance identifies the rule or query that generated the fact.

Required reasoning cases:

- Upstream power failure infers downstream dependency exposure.
- Cooling path degradation infers thermal/capacity risk context.
- Missing validation blocks restore readiness.
- Completed repair plus passed validation supports restore readiness.
- Conflicting impact evidence infers warning or invalid trust state.
- Dependency path traversal infers blast radius.

## Semantic Service Verification

Target checks:

```bash
./gradlew test
./gradlew run
```

Acceptance:

- Service can connect to Fuseki.
- Service can load and execute named SPARQL files.
- Service can run validation and return conformance results.
- Service can refresh reasoning and operation graphs.
- Service can return UI view models from graph-backed data.
- Service cannot write to protected graphs without validation and provenance.
- Service rejects arbitrary browser-supplied SPARQL Update.
- Service enforces query metadata, graph scopes, timeout classes, and result
  size limits.
- Service preserves last known-good canonical/inferred/operations graphs when
  promotion or validation fails.

Service-level tests:

- Graph connection and health.
- Query loader.
- Validation runner.
- Reasoning runner.
- Read-only view endpoints.
- Controlled update command.
- AI query/proposal command.
- Transaction rollback and failed promotion.
- Authorization by action class.
- Query timeout and result-size guard.

## AI Governance Verification

Target checks:

```bash
./gradlew test --tests "*AiGovernance*"
```

Acceptance:

- AI-generated read queries are graph-scoped and query-type checked.
- Generated updates are blocked unless routed through proposed-triple staging.
- Proposed triples are stored in `urn:dcai:graph:ai-audit`.
- Proposed triples must pass SHACL before promotion.
- Approval/rejection is recorded.
- AI answers cite graph facts and provenance.
- Prompt-injection content in source records or graph literals cannot override
  query/write policy.
- Generated SPARQL cannot expand beyond the approved graph allowlist.

Required cases:

- Allowed read-only operational question.
- Blocked unrestricted SPARQL Update.
- Blocked generated query with disallowed graph scope.
- Blocked prompt-injection attempt from source text.
- Invalid proposed triple rejected by SHACL.
- Valid proposed triple staged but not promoted without approval.
- Approved proposed triple promoted with provenance.

## Release and Migration Verification

Target checks:

```bash
./gradlew test --tests "*ReleaseManifest*"
./gradlew test --tests "*GraphMigration*"
```

Acceptance:

- Release manifest references ontology, shapes, queries, rules, mappings,
  fixtures, and semantic service compatibility.
- Graph migrations are repeatable against fixture datasets.
- Breaking ontology changes require migration steps or explicit approval.
- Query snapshots are refreshed only with reviewed semantic changes.
- Previous graph release can be restored from backup or fixture baseline.

## UI Verification

Target checks:

```bash
cd ui
npm run build
npm run lint
```

Browser acceptance:

- Semantic operations workbench loads.
- User can find the next graph-derived follow-up.
- User can inspect why the graph produced that follow-up.
- User can inspect source evidence and provenance.
- User can inspect dependency reasoning and blast radius.
- User can inspect SHACL/trust status.
- User can use AI-governed graph question flow without direct mutation.
- User can see graph health, conformance, provenance, and AI audit status where
  those signals affect trust in an operational decision.

UI non-goals:

- The old dashboard structure does not need to survive.
- The old REST API shape does not need to survive.
- An ontology map should not become decorative center stage unless it supports
  a real operational decision.

## Old Runtime Removal Verification

Before calling the rewrite complete, check:

```bash
rg -n "fastapi|sqlalchemy|alembic|psycopg|postgres|uvicorn" .
rg -n "downtime_follow_up_queue|incident_current_status|InfrastructureIncident|Session\\(" .
```

Expected result:

- No old FastAPI/Postgres/SQLAlchemy runtime dependency remains in active
  source paths.
- Any remaining references are historical docs, archived code, or explicit
  migration notes.
- Docker Compose no longer starts Postgres as the runtime source of truth.
- Operational tests pass without SQL analytics tables.
- Any retained sample-data utilities are explicitly documented as fixture
  generation only, not runtime architecture.

## Final Completion Checklist

- [ ] Planning docs approved.
- [ ] Jena/Fuseki/TDB2 persistent runtime works.
- [ ] Ontology modules parse and load.
- [ ] SHACL fixtures pass/fail correctly.
- [ ] RDF mapping loads source graphs.
- [ ] Canonical promotion works.
- [ ] Reasoning materializes inferred facts.
- [ ] SPARQL query library backs operational views.
- [ ] Semantic service returns graph-backed UI data.
- [ ] AI governance blocks unsafe behavior and records audit facts.
- [ ] Release manifest and graph migration checks pass.
- [ ] Semantic service blocks arbitrary SPARQL Update from browser paths.
- [ ] Observability endpoints report graph health and validation status.
- [ ] UI primary workflow works.
- [ ] Old runtime is removed or archived.
- [ ] Docs describe the ontology-native platform as the primary system.

## Stopping Condition

Stop only when the final completion checklist passes with current evidence.
Partial semantic projection over SQL is not sufficient. A SQL-first runtime with
RDF export is not sufficient. The system must be graph-native in runtime data,
validation, query behavior, reasoning, provenance, AI governance, and user
workflow.
