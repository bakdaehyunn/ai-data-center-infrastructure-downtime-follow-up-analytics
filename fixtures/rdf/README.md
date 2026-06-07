# RDF Fixture Expectations

Phase 3 adds scaffold RDF fixtures for ontology and SHACL contract validation.
It does not add executable RDF ingestion, graph promotion, or service logic.

Future fixture groups:

- `valid/minimal-incident.ttl`: valid minimal incident graph with an incident,
  affected asset, zone, current workflow stage, source record, and provenance.
- `valid/dependency-path.ttl`: valid dependency path graph with assets,
  dependency edges, path membership, and topology provenance.
- `valid/evidence-provenance.ttl`: valid evidence/provenance graph linking
  telemetry, validation, or work-order evidence to operational facts.
- `valid/reasoning-output.ttl`: valid reasoning output graph covering
  dependency impact, recovery blocker, follow-up decision, restore readiness,
  trust, blast radius, and reasoning activity provenance.
- `invalid/missing-asset-link.ttl`: invalid incident graph missing the required
  `dcai:affectsAsset` relationship.
- `invalid/unknown-workflow-stage.ttl`: invalid workflow graph using a stage
  that is not represented as `dcai:WorkflowStage`.
- `invalid/ai-proposed-write.ttl`: invalid AI proposed triple set missing
  required provenance, validation shape, or proposed triple content.
- `invalid/reasoning-output-missing-provenance.ttl`: invalid reasoning output
  graph missing required source-fact and reasoning-activity provenance.

These fixtures are intentionally small. They prove the current skeleton
contracts can distinguish conforming fixture graphs from invalid source or
canonical graph shapes before executable source-to-canonical mapping exists.
