# Semantic Service Boundary

This directory contains the Kotlin/JVM semantic service transition runtime and
its boundary contracts. It started as non-runtime scaffolding in Phases 8-12;
post-Phase-20 it now includes an internal-only private semantic query endpoint
for the existing approved fixture inspection queries.

Phase 8 defines the semantic service as a controlled facade over the
Fuseki/TDB2 RDF dataset. The service may later expose use cases for query
execution, reasoning validation, provenance lookup, promotion review, and AI
governance handoff, but the RDF named graphs remain the source of truth.

Tracked contract:

- `semantic-service/boundary-contract.ttl`
- `semantic-service/openapi.semantic-service.yaml`
- `semantic-service/api-dtos.md`
- `semantic-service/src/main/resources/contracts/semantic-service-contracts.ttl`

Phase 9 adds OpenAPI-style endpoint shape and DTO documentation. It remains
non-runtime scaffold only: no service implementation, route handlers, DTO
classes, clients, or code generation are added.

Phase 10 adds minimal Gradle/Kotlin project metadata and package-layout
placeholders. It remains non-running scaffold only: no framework plugin,
application entry point, Kotlin source files, graph clients, controllers, DTO
classes, executable tests, or service runtime are added.

Phase 11 adds the first implementation slice: Kotlin contract loading and
static validation for the Phase 8-10 contract artifacts. It still does not add
HTTP endpoints, controllers, runtime DTO classes, graph execution, Fuseki/TDB2
clients, reasoning orchestration, or service runtime.

Phase 12 adds the cutover and implementation-readiness checkpoint. It recorded
the old FastAPI/Postgres/SQLAlchemy runtime as reference-only at that point and
defined the gates that had to pass before real semantic service endpoints or
graph execution could begin.

Tracked readiness checkpoint:

- `semantic-service/cutover-readiness.ttl`
- `docs/ontology-native/phase12_cutover_implementation_readiness.md`

Phase 13 adds the first runnable JVM baseline. The service can start as a
command-line contract-validation runtime, validate the Phase 8-12 contract
artifacts, print readiness state, and exit non-zero if validation fails. It
still does not expose HTTP endpoints, connect to Fuseki/TDB2, execute SPARQL,
write graphs, or orchestrate reasoning.

Run with local Java and Gradle:

```bash
cd semantic-service
gradle test
gradle run --args="$(pwd)/.."
```

Run with Docker if local Java or Gradle is unavailable:

```bash
docker run --rm \
  -v "$PWD":/workspace \
  -w /workspace/semantic-service \
  gradle:8.10.2-jdk17 \
  gradle --no-daemon test run --args=/workspace
```

Phase 14 adds a read-only Fuseki/TDB2 graph access boundary. It introduces
Apache Jena dependencies, read-only graph configuration, and a connectivity
client that can check the Fuseki query endpoint without exposing public HTTP
routes, writing RDF graphs, executing approved application queries, or running
reasoning.

Run the service baseline with a read-only graph connectivity check:

```bash
cd semantic-service
DCAI_FUSEKI_DATASET_URL=http://localhost:3030/infrastructure \
  gradle run --args="--repo-root=$(pwd)/.. --check-graph"
```

Docker equivalent:

```bash
docker run --rm \
  -v "$PWD":/workspace \
  -w /workspace/semantic-service \
  -e DCAI_FUSEKI_DATASET_URL=http://host.docker.internal:3030/infrastructure \
  gradle:8.10.2-jdk17 \
  gradle --no-daemon run --args="--repo-root=/workspace --check-graph"
```

Phase 15 adds controlled RDF fixture loading into Fuseki named graphs. The
runtime still has no public endpoints and does not run reasoning. Fixture
loading is only available through the local CLI boundary, validates the fixture
with SHACL and provenance gates, and then writes the controlled source and
canonical fixture named graphs.

Run the baseline without writes:

```bash
docker run --rm \
  -v "$PWD":/workspace \
  -w /workspace/semantic-service \
  gradle:8.10.2-jdk17 \
  gradle --no-daemon test run --args=/workspace
```

Run controlled fixture loading against a local Fuseki graph-store endpoint:

```bash
docker run --rm \
  -v "$PWD":/workspace \
  -w /workspace/semantic-service \
  -e DCAI_FUSEKI_DATASET_URL=http://host.docker.internal:3030/infrastructure \
  gradle:8.10.2-jdk17 \
  gradle --no-daemon run --args="--repo-root=/workspace --load-fixtures"
```

Phase 16 adds controlled read-only query execution. Queries must be listed in
`queries/manifest.ttl` with `implementationStatus "phase16-approved"` and must
parse as SELECT or ASK. Placeholder reasoning queries and update queries are not
executable in this phase.

Run an approved read-only query against fixture-loaded named graphs:

```bash
docker run --rm \
  -v "$PWD":/workspace \
  -w /workspace/semantic-service \
  -e DCAI_FUSEKI_DATASET_URL=http://host.docker.internal:3030/infrastructure \
  gradle:8.10.2-jdk17 \
  gradle --no-daemon run --args="--repo-root=/workspace --run-query=fixtureNamedGraphInventory"
```

Phase 17 adds stable result-envelope shaping for future semantic service
responses. The runtime remains CLI-only, but approved query results now map
into typed contracts for named graph inventory, incident summary, and
provenance source-record inspection.

Phase 18 adds a semantic response contract checkpoint. The runtime remains
CLI-only, but `openapi.semantic-service.yaml` and `api-dtos.md` now define
future typed query response shapes, semantic error envelopes, and versioning
rules aligned to the Phase 17 result envelopes.

Phase 19 adds internal-only response serialization. The runtime remains
CLI-only, but query-result envelopes and semantic errors can now be converted
into deterministic in-memory payload maps aligned to the Phase 18 contract.

Phase 20 adds the endpoint readiness decision checkpoint. The runtime remains
CLI-only; private endpoint scaffolding is deferred to a later approved phase
and any future endpoint must use the Phase 19 serializer instead of raw SPARQL
bindings.

Post-Phase-20 adds the first private endpoint slice:

- internal `POST /semantic/query/{queryId}`
- loopback-only bind host, defaulting to `127.0.0.1`
- approved query IDs only:
  - `fixtureNamedGraphInventory`
  - `fixtureIncidentSummary`
  - `fixtureProvenanceSourceRecords`
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
- all success payloads go through `SemanticResponseSerializer`
- all errors use the Phase 18 semantic error envelope
- approved lookup queries accept string-valued `parameters`
- raw SPARQL request bodies, arbitrary query IDs, graph writes, reasoning
  execution, and public exposure remain blocked

Post-Phase-20 semantic queue read-model implementation adds
`semanticFollowUpQueueList` as the first product read model. It returns
canonical graph incident, asset, zone, stage, and source-record provenance
fields.

The runtime cutover batches add additional private product read-model queries
for dashboard overview, filter metadata, follow-up detail, impact summary,
topology dependencies, trust findings, stage bottlenecks, asset/zone delay
summaries, spare/vendor wait summaries, validation summaries, incident
evidence, dependency impact, and blast radius. The React dashboard now reads
these graph-backed semantic-service contracts through its API adapter.
Telemetry alerts, repeat-failure counters, engineer-assignment counters,
semantic data-quality detail lookup, and parameterized incident/asset lookup
are backed by RDF fixture facts, approved SPARQL bindings, typed envelopes,
result shaping, and serializer output.

Run the private endpoint against a fixture-loaded Fuseki dataset:

```bash
docker run --rm \
  -v "$PWD":/workspace \
  -w /workspace/semantic-service \
  -e DCAI_FUSEKI_DATASET_URL=http://host.docker.internal:3030/infrastructure \
  gradle:8.10.2-jdk17 \
  gradle --no-daemon run --args="--repo-root=/workspace --serve-private-query-endpoint"
```
