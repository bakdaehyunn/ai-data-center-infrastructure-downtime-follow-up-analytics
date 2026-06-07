# Reasoning Pipeline Scaffold

This directory records the Phase 4 reasoning pipeline scaffold for the
ontology-native rewrite. It defines target reasoning outputs, graph boundaries,
fixture expectations, and placeholder rule/query paths only.

This scaffold does not implement executable reasoning, production SPARQL rules,
Java/Kotlin service behavior, graph promotion, UI changes, or old-runtime
removal.

## Target Graph Boundaries

- `urn:dcai:graph:canonical`: validated source-to-canonical operational facts.
- `urn:dcai:graph:provenance`: source lineage, promotion activity, and future
  reasoning activity records.
- `urn:dcai:graph:reasoning`: approved derived findings produced from canonical
  facts.
- `urn:dcai:graph:reasoning-audit`: candidate findings, rule versions, and
  explanation traces before approval.

## Reasoning Outputs

| Output | Target class | Target purpose |
| --- | --- | --- |
| Dependency exposure | `dcai:DependencyImpactFinding` | Explain which power, cooling, telemetry, or redundancy paths expose an incident to operational impact. |
| Recovery blocker | `dcai:RecoveryBlocker` and `dcai:FollowUpDecision` | Identify the active blocker and recommended next operational action. |
| Restore readiness | `dcai:RestoreReadinessFinding` | Decide whether evidence supports return-to-service readiness. |
| Impact trust | `dcai:TrustFinding` | Flag impact claims that are unsupported, stale, contradictory, or low confidence. |
| Blast radius | `dcai:BlastRadiusFinding` | Identify downstream assets, zones, GPU capacity, and dependency paths affected by an incident. |

## Placeholder Structure

- `reasoning/manifest.ttl`: parseable Phase 4 reasoning manifest metadata.
- `reasoning/execution-contract.ttl`: parseable Phase 6 non-runtime execution
  contract metadata.
- `reasoning/rules/README.md`: placeholder rule boundary and future file names.
- `queries/reasoning/README.md`: placeholder SPARQL query boundary and future
  query file names.
- `queries/manifest.ttl`: query-manifest references for future reasoning
  queries.

Future executable rule or query files should be added only when a later phase
implements the reasoning runtime and validates each output against fixtures.

Phase 6 adds the future execution contract for graph inputs, graph outputs,
promotion gates, provenance requirements, failure modes, and service boundaries.
It does not add an executor or promote graph data.
