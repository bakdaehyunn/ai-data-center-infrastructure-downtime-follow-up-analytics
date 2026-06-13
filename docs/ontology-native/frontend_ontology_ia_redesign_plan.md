# Frontend Ontology IA Redesign Plan

Date: 2026-06-13

## Purpose

This plan reviews the current React frontend information architecture against
the ontology-native runtime and defines the redesign direction used for the
ontology-native frontend IA refactor.

The target is not a cosmetic redesign. The frontend should stop preserving
stale queue/filter concepts from the old operational API shape and become a
semantic operations workbench over approved graph read models.

## Implementation Status

Implemented in the local working tree after this plan was written:

- The first screen was reframed as a semantic findings workbench.
- Stale filter scopes were replaced with graph-aligned scopes such as restore
  blocked, trust review, redundancy lost, vendor/parts escalation, recovery,
  and validation.
- Frontend filtering now uses a stable semantic dashboard snapshot instead of
  refetching every approved graph query on each scope click.
- Redundancy and vendor/parts status handling is centralized in frontend
  vocabulary predicates.
- The dependency view now groups returned RDF dependency edges by graph
  `dependencyRole` and `pathId` instead of hardcoded topology IDs.
- SQL/table-oriented trust terminology was replaced with graph-scope language.

## Current Evidence

The runtime is already serving live ontology-native graph data through the
private semantic endpoint. A local MVP graph inspection on 2026-06-13 showed:

- 48 incidents in the dashboard overview.
- 124 trust findings.
- 144 dependency edges.
- 96 follow-up detail rows.
- Active workflow stage labels: `Recovery`, `Validation`.
- Active redundancy states: `N_PLUS_0`, `N_PLUS_1`.
- Active vendor states: `monitoring`, `vendor-engaged`, `parts-review`.
- Active dependency roles: `power-feed`, `cooling-loop`,
  `telemetry-source`.
- Active dependency IDs follow generated graph identifiers such as
  `DEP-GEN-SCN-20260611-POWER`, `DEP-GEN-SCN-20260611-COOLING`, and
  `DEP-GEN-SCN-20260611-BLAST`.

The target architecture already says the UI should be redesigned as a semantic
operations workbench rather than preserved as the current dashboard. It should
help operators find the next follow-up, understand why the graph inferred it,
inspect source evidence and provenance, inspect dependency and blast-radius
reasoning, and review SHACL, trust, and AI audit signals.

## Original IA Assessment

Before the refactor, the frontend was partially ontology-native:

- It reads semantic query IDs rather than old `/api/*` routes.
- It renders restore-readiness findings.
- It renders semantic trust findings.
- It renders SHACL validation status.
- It renders incident evidence, dependency impact, and blast-radius context.
- It can navigate from a queue row to a detail page.

But the IA still looked like a legacy list/detail operations dashboard with
semantic facts added into the old shape:

- The main route is still organized around a "Follow-up Queue".
- The primary table shows incident, asset, zone, blocker, time, and action,
  but it does not expose graph lineage, reasoning type, source graph, or
  provenance as first-order concepts.
- The filter buttons use stale operational tokens that do not match the
  current graph vocabulary.
- The dependency tab has graph-derived evidence available, but also keeps
  hardcoded topology path definitions that do not match the current generated
  dependency IDs.
- The adapter still maps semantic envelopes into old UI-shaped contracts such
  as `FollowUpItem`, `RequestDetail`, `DataQualityCheck`, and spare/vendor
  fields.

## Stale Or Dead Concepts Removed Or Replaced

The refactor targets these stale concepts:

| Current UI concept | Problem | Replacement |
| --- | --- | --- |
| `SPARE_VENDOR_WAITING` filter scope | Current graph emits `Recovery` and `Validation`; no active queue stage uses `SPARE_VENDOR_WAITING`. | `Recovery blockers` or graph-derived stage scopes from `semanticFilterMetadata`. |
| `Vendor ETA missed` / `ETA_MISSED` | Current graph emits `vendor-engaged`, `parts-review`, and `monitoring`. | `Vendor/parts escalation` derived from vendor status tokens or trust/recovery signals. |
| `N-1 exposure` / `N-1` | Current graph emits `N_PLUS_0` and `N_PLUS_1`. | `Redundancy exposure`, with `N_PLUS_0` treated as lost redundancy and `N_PLUS_1` as degraded/watch depending on ontology policy. |
| Hardcoded topology IDs such as `DEP-RACK-PDU`, `DEP-PDU-UPS`, `DEP-RACK-CRAH` | The MVP graph has generated dependency IDs and roles, so these paths render empty or misleading topology state. | Build dependency groups from returned RDF edge roles and path IDs. |
| `DataQualityCheck.target_table` | Table language leaks the removed SQL runtime model. | `graphScope`, `sourceFactUri`, `trustFindingUri`, and `reasoningActivityUri`. |
| `request_*` naming in UI model | The frontend is no longer reading old request rows. | `incident`, `finding`, `evidence`, and `action` domain terms. |
| Spare-centric summary types where no spare facts exist | `semanticSpareWaitSummary` can return zero while the UI still promotes spare wait as a primary scope. | Recovery blocker, work-order blocker, validation blocker, vendor/parts blocker, telemetry blocker. |

## Target User And Primary Task

Primary user: an AI data center operations lead or incident commander reviewing
semantic graph findings during recovery.

Primary task: decide what needs follow-up next, why the graph believes it is
blocked or risky, whether the evidence is trustworthy, and which dependency or
source facts support the recommendation.

The UI should answer these questions without forcing the user to infer graph
meaning from old queue labels:

- What operational finding needs attention?
- Is the finding asserted, inferred, or trust/audit related?
- Which incident, asset, zone, and dependency path are involved?
- What restore-readiness state blocks action?
- What evidence supports or contradicts the finding?
- Which source records and graph releases produced the facts?
- What blast radius is inferred downstream?
- Is the recommendation safe to act on?

## Target Object Model

The frontend should treat these as first-class objects:

- `Incident`: operational incident resource.
- `Asset`: affected or dependency asset resource.
- `Zone`: facility zone.
- `WorkflowStage`: current semantic recovery/validation stage.
- `ImpactObservation`: capacity, GPU, rack, thermal, redundancy, vendor, and
  mitigation facts.
- `DependencyEdge`: graph edge between dependent and dependency assets.
- `DependencyPath`: path or role grouping such as power, cooling, telemetry, or
  blast-radius.
- `Evidence`: telemetry, validation, work order, workflow event, or source
  record evidence.
- `RestoreReadinessFinding`: reasoning output for restore safety.
- `TrustFinding`: reasoning output for low-confidence, conflicting, stale, or
  unsupported evidence.
- `RecoveryBlocker`: reasoning output explaining why recovery is blocked.
- `BlastRadiusFinding`: reasoning output showing downstream exposure.
- `Provenance`: source record, import activity, promotion activity, and
  reasoning activity lineage.

## Proposed Page Structure

### 1. Semantic Operations Workbench

Replace the current queue-first dashboard hierarchy with a finding-first
workbench.

Primary sections:

- Graph status strip: graph release, reasoning run, SHACL state, trust load,
  endpoint/query catalog status.
- Finding scopes: all findings, restore blocked, trust review, redundancy
  exposure, dependency exposure, blast radius, validation blockers,
  vendor/parts escalation.
- Findings table: incident, finding type, restore readiness, trust state,
  dependency role, affected capacity, evidence count, provenance state, next
  action.
- Graph insight panels: top blocker, highest blast radius, trust issue load,
  dependency role distribution.

The list can remain, but it should list semantic findings/actions rather than
old follow-up rows.

### 2. Finding Detail

The detail route should be organized around the selected graph finding and its
lineage:

- Decision header: finding type, incident, asset, zone, restore-readiness state,
  trust state, recommended action.
- Why inferred: recovery blocker, dependency exposure, blast radius, and
  readiness signals.
- Evidence chain: workflow events, telemetry, validation, work orders, source
  records.
- Provenance chain: source record -> canonical fact -> reasoning activity ->
  finding.
- Dependency path: dynamic graph-derived power/cooling/telemetry/blast path.
- Trust review: trust findings grouped by cause.
- Raw graph identifiers: compact advanced section for URIs, graph scope, query
  ID, and release/run IDs.

### 3. Dependency View

Replace hardcoded topology definitions with graph-derived grouping:

- Group by `dependencyRole`.
- Use `pathId` where present.
- Render edge rows as dependent asset -> dependency asset.
- Mark incident activity on each endpoint.
- Highlight dependency edges that participate in dependency exposure or
  blast-radius findings.
- Show blast-radius downstream assets and incidents beside the direct edge
  evidence.

A full node-link visualization is optional. For the MVP, a path/edge view is
better than a force-directed graph because it is deterministic, readable, and
easier to verify.

### 4. Trust And Provenance View

Elevate trust/provenance from a secondary tab into the decision flow:

- Trust finding summary by cause.
- Evidence confidence state.
- Conflicting validation state.
- Telemetry gap/stale evidence state.
- Unsupported impact claim state.
- Source record and payload hash status.
- Reasoning activity and generated-at time.

## Filter And Vocabulary Strategy

The next implementation should not hardcode legacy tokens in React. It should:

- Build filter controls from semantic metadata where possible.
- Normalize graph vocabulary in one adapter boundary.
- Preserve raw ontology tokens for advanced inspection.
- Use user-facing labels from a semantic label map:
  - `N_PLUS_0` -> "Redundancy lost"
  - `N_PLUS_1` -> "Redundancy available / watch"
  - `vendor-engaged` -> "Vendor engaged"
  - `parts-review` -> "Parts review"
  - `monitoring` -> "Monitoring"
  - `Recovery` -> "Recovery"
  - `Validation` -> "Validation"
- Treat unknown tokens as displayable ontology values rather than filtering them
  out.

Filter scopes should become:

- All findings.
- Restore blocked.
- Trust review.
- Redundancy lost.
- Vendor/parts escalation.
- Recovery stage.
- Validation stage.
- Power dependency.
- Cooling dependency.
- Telemetry dependency.
- Blast-radius exposure.

## Adapter Strategy

The frontend can still use an adapter, but the adapter should stop pretending
semantic envelopes are old REST objects.

Recommended model split:

- `SemanticFindingListItem`
- `SemanticFindingDetail`
- `SemanticEvidenceItem`
- `SemanticDependencyPath`
- `SemanticTrustIssue`
- `SemanticProvenanceTrace`
- `SemanticGraphStatus`

The adapter should:

- Merge queue, detail, trust, dependency, blast-radius, and validation query
  results into finding-centered objects.
- Provide normalized labels and scope predicates.
- Keep raw URIs and graph tokens for audit display.
- Avoid fallback values that create fake states not present in the graph.
- Avoid table-oriented names such as `target_table`.

## Query / Backend Read-Model Gaps

The current approved queries are enough for a first UI hardening pass, but a
clean semantic workbench would benefit from additional read models later:

- `semanticGraphLifecycleStatus`: latest source/canonical/provenance/reasoning
  release IDs and counts.
- `semanticFindingList`: one row per operational finding, not one row per
  incident/detail join.
- `semanticFindingLineage`: source fact -> canonical fact -> reasoning
  activity -> finding.
- `semanticDependencyPathByIncident`: graph-derived dependency paths for the
  selected incident.
- `semanticFindingScopeMetadata`: supported scopes derived from actual graph
  tokens.

These are not required to start the frontend IA refactor, but they would reduce
adapter complexity.

## Implementation Boundary For Next Coding Goal

Allowed implementation scope:

- `frontend/src/api.ts`
- `frontend/src/App.tsx`
- `frontend/src/App.css`
- focused frontend tests if the project adds them
- approved read-model SPARQL only if a missing semantic field blocks the UI
- minimal docs update for new UI terminology

Non-goals:

- No public endpoints.
- No raw SPARQL exposure.
- No auth work.
- No AI governance implementation.
- No real external connectors.
- No changes to graph promotion or reasoning logic unless a query proves a
  required fact is missing.
- No commit or push unless explicitly requested.

## Implementation Steps

1. Define semantic frontend types in `frontend/src/api.ts`.
2. Add a central vocabulary normalization layer for stage, redundancy, vendor,
   dependency role, readiness, trust, and evidence status.
3. Replace legacy queue scope controls with semantic finding scopes.
4. Change dashboard loading so filter clicks do not refetch every graph query
   unnecessarily; apply client-side filtering to a stable semantic snapshot
   where possible.
5. Replace old summary metrics with graph-native metrics: restore blocked,
   trust review, dependency exposure, blast radius, redundancy lost,
   validation blockers.
6. Replace hardcoded topology path definitions with dependency paths grouped by
   returned graph `dependencyRole` and `pathId`.
7. Reorganize detail tabs around decision, evidence, dependency, trust, and
   provenance.
8. Remove dead spare/vendor and SQL/table naming from visible UI and adapter
   types where practical.
9. Add empty states that explain graph absence precisely, such as "No
   dependency edges returned for this incident" instead of generic queue text.
10. Verify desktop and mobile rendering against the running local MVP graph.

## Verification Plan

Minimum checks after implementation:

- `npm run build`
- semantic endpoint smoke checks for:
  - `semanticDashboardOverview`
  - `semanticFollowUpQueueList`
  - `semanticFollowUpDetail`
  - `semanticFilterMetadata`
  - `semanticTopologyDependencies`
  - `semanticDependencyImpactByAsset`
  - `semanticBlastRadiusByAsset`
  - `semanticTrustFindingList`
- source scan confirms no visible stale labels:
  - `SPARE_VENDOR_WAITING`
  - `ETA_MISSED`
  - old hardcoded topology dependency IDs
  - `target_table`
- browser verification:
  - scope buttons return non-misleading counts.
  - restore blocked incidents are visible.
  - trust review findings are visible.
  - dependency path view renders current graph roles.
  - blast-radius evidence is visible for a selected incident.
  - no console warnings/errors.
  - mobile has no horizontal overflow.

## Acceptance Criteria

The frontend IA refactor is complete when:

- The first screen is a semantic operations workbench, not a legacy queue
  dashboard.
- Visible filters and scope buttons match live ontology vocabulary or derived
  semantic scopes.
- No primary UI path depends on stale `SPARE_VENDOR_WAITING`, `ETA_MISSED`,
  `N-1`, or hardcoded old topology IDs.
- The selected detail view makes reasoning, evidence, trust, dependency,
  blast-radius, and provenance relationships discoverable without reading raw
  JSON.
- The UI still uses approved semantic query IDs and does not expose raw SPARQL.
- The implementation is verified with frontend build, source scans, endpoint
  smoke checks, and browser checks.
