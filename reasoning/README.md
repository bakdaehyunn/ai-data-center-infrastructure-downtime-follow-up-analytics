# Reasoning Pipeline

This directory records the reasoning pipeline for the ontology-native rewrite.
Phase 4 started as a scaffold. Executable reasoning v1 now adds internal Kotlin
reasoning for dependency exposure, recovery blockers, restore readiness, impact
trust, and blast radius over promoted canonical graphs.

Executable reasoning v1 does not add public endpoints, browser-supplied raw
SPARQL, UI changes, authentication, AI governance workflows, connector jobs, or
old-runtime restoration.

## Target Graph Boundaries

- `urn:dcai:graph:canonical`: validated source-to-canonical operational facts.
- `urn:dcai:graph:provenance`: source lineage, promotion activity, and
  reasoning activity input context.
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

Implemented v1 outputs:

- dependency exposure findings from an incident's affected asset to upstream
  dependency assets through canonical dependency paths
- blast-radius findings from an incident's affected asset to downstream assets
  that depend on it through canonical dependency paths
- recovery-blocker findings from blocked, delayed, awaiting, missing,
  conflicting, or manual-review workflow, work-order, validation, or telemetry
  states supporting an incident
- restore-readiness findings for each incident from recovery blockers,
  work-order state, validation state, mitigation state, telemetry state,
  evidence confidence, stale evidence, unsupported impacts, and downstream
  dependency exposure
- trust findings for low-confidence evidence, conflicting validation, telemetry
  gaps, stale evidence, unsupported impact claims, unsupported evidence targets,
  and source records missing payload-hash provenance
- `dcai:ReasoningActivity` provenance with `prov:used`, `prov:generated`, and
  `prov:generatedAtTime`
- reasoning-audit and approved reasoning graph promotion with rollback

## Placeholder Structure

- `reasoning/manifest.ttl`: parseable Phase 4 reasoning manifest metadata.
- `reasoning/execution-contract.ttl`: parseable Phase 6 non-runtime execution
  contract metadata.
- `reasoning/rules/README.md`: placeholder rule boundary and future file names.
- `queries/reasoning/README.md`: placeholder SPARQL query boundary and future
  query file names.
- `queries/manifest.ttl`: query-manifest references for future reasoning
  queries.

The existing `queries/reasoning/*.rq` files remain parseable SPARQL reference
scaffolds and are not exposed to browsers or the private query endpoint.
Executable v1 uses internal Kotlin model rules so graph mutation remains
service-owned.

Remaining future work:

- richer path traversal, conflict handling, and policy approval gates
- production connector scheduling and operator-facing promotion controls
