# Phase 2 Ontology and SHACL Contract

This document records the Phase 2 ontology-native rewrite scaffold. It defines
parseable OWL/RDFS and SHACL contract skeletons only. It does not implement RDF
ingestion, SPARQL query behavior, reasoning, a Java/Kotlin semantic service, UI
redesign, or old-runtime removal.

## Ontology Modules

- `ontology/modules/core.ttl`: shared operational entity, event, evidence,
  derived fact, source system, identifier, timestamp, and source-system terms.
- `ontology/modules/infrastructure.ttl`: facility, zone, asset, power, cooling,
  control telemetry, and compute capacity group skeleton.
- `ontology/modules/topology.ttl`: dependency edge, dependency path, power,
  cooling, telemetry, redundancy path, and dependency relationship skeleton.
- `ontology/modules/workflow.ttl`: incident, workflow stage, workflow event,
  recovery blocker, follow-up decision, and stage relationship skeleton.
- `ontology/modules/impact.ttl`: capacity, GPU, thermal, redundancy, and vendor
  exposure skeleton.
- `ontology/modules/evidence.ttl`: telemetry, validation, work-order evidence,
  source quality issue, trust finding, support, and contradiction skeleton.
- `ontology/modules/provenance.ttl`: source extract, source record, import,
  promotion, reasoning activity, and PROV-O-aligned lineage skeleton.
- `ontology/modules/ai-interaction.ttl`: AI question, generated SPARQL,
  proposed triple set, approval decision, and guardrail violation skeleton.
- `ontology/modules/operations.ttl`: follow-up queue item, priority score,
  dependency impact, restore readiness, and blast-radius finding skeleton.

## SHACL Shape Skeletons

- `shapes/source-required-fields.ttl`: source record identifier and source
  system boundary.
- `shapes/canonical-integrity.ttl`: asset and incident canonical relationship
  boundary.
- `shapes/workflow-transitions.ttl`: incident current stage and workflow event
  stage boundary.
- `shapes/topology-integrity.ttl`: dependency edge asset and role boundary.
- `shapes/impact-evidence.ttl`: impact observation and evidence support or
  contradiction boundary.
- `shapes/provenance-required.ttl`: derived fact and operational entity
  provenance boundary.
- `shapes/ai-proposed-write.ttl`: proposed triple set, validation shape, and
  provenance boundary.

## Fixture Expectations

Phase 2 names the fixture contract without implementing final data:

- Valid minimal incident graph.
- Valid dependency path graph.
- Valid evidence/provenance graph.
- Invalid graph with missing required asset link.
- Invalid graph with unknown workflow stage.
- Invalid AI proposed write graph.

The tracked fixture expectation file is `fixtures/rdf/README.md`.

## Validation Commands

Run from the repository root.

Parse ontology modules and SHACL skeletons with the current Python/RDF tooling:

```bash
backend/.venv/bin/python - <<'PY'
from pathlib import Path
from rdflib import Graph

for folder in ["ontology/modules", "shapes", "ontology/releases", "queries"]:
    for path in sorted(Path(folder).glob("*.ttl")):
        graph = Graph()
        graph.parse(path, format="turtle")
        print(f"{path}: {len(graph)} triples")
PY
```

Confirm all required Phase 2 files exist:

```bash
test -f ontology/modules/core.ttl
test -f ontology/modules/infrastructure.ttl
test -f ontology/modules/topology.ttl
test -f ontology/modules/workflow.ttl
test -f ontology/modules/impact.ttl
test -f ontology/modules/evidence.ttl
test -f ontology/modules/provenance.ttl
test -f ontology/modules/ai-interaction.ttl
test -f ontology/modules/operations.ttl
test -f shapes/source-required-fields.ttl
test -f shapes/canonical-integrity.ttl
test -f shapes/workflow-transitions.ttl
test -f shapes/topology-integrity.ttl
test -f shapes/impact-evidence.ttl
test -f shapes/provenance-required.ttl
test -f shapes/ai-proposed-write.ttl
test -f ontology/releases/2026-06-phase2-ontology-shacl-skeleton.ttl
test -f fixtures/rdf/README.md
```

Check target terms:

```bash
rg -n "OperationalEntity|InfrastructureAsset|DependencyEdge|InfrastructureIncident|ImpactObservation|EvidenceRecord|SourceRecord|AIInteraction|FollowUpQueueItem" ontology/modules
rg -n "SourceRecordRequiredFieldsShape|InfrastructureAssetCanonicalShape|WorkflowIncidentStageShape|DependencyEdgeShape|ImpactObservationShape|DerivedFactProvenanceShape|AIProposedTripleSetShape" shapes
rg -n "valid minimal incident graph|dependency path graph|evidence/provenance graph|missing required asset link|unknown workflow stage|AI proposed write" docs/ontology-native/phase2_ontology_shacl_contract.md fixtures/rdf/README.md
```

Keep the Phase 1 runtime scaffold valid:

```bash
docker compose config
```

Check formatting:

```bash
git diff --check
```

## Stop Condition

Phase 2 is complete when every ontology module and SHACL shape skeleton parses,
fixture expectations and validation commands are documented, the Phase 2
release manifest parses, Phase 1 Compose still validates, and no old
FastAPI/Postgres/SQLAlchemy runtime code has been removed or replaced.
