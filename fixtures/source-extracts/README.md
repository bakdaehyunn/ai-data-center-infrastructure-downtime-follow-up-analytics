# Source Extract Fixtures

Production ingestion v1 uses Kotlin DTO fixtures in
`semantic-service/src/test/kotlin/com/dcai/semanticservice/testfixtures/ProductionSourceExtractFixtures.kt`.
The internal local CLI command uses the built-in controlled extract in
`semantic-service/src/main/kotlin/com/dcai/semanticservice/ingestion/LocalControlledSourceExtract.kt`.
File-backed local ingestion v1 uses the deterministic properties fixture
`fixtures/source-extracts/local-controlled-source-v1.properties`.
Recorded source-system connector simulation v1 uses deterministic CSV exports
under `fixtures/source-extracts/recorded-source-systems/local-ops-v1/`.
Seeded recorded scenario generation v1 can generate the same connector export
shape under `fixtures/source-extracts/generated-scenarios/`.

The controlled fixture covers these source record families:

- facility
- zone
- asset
- incident
- dependency
- workflow event
- telemetry evidence
- impact

Ontology hardening v1 adds optional source fields for `hallId`, `rowId`,
`rackId`, `capacityGroupId`, and `workOrderStatus`. The recorded connector and
seeded generator use these fields to exercise AI data center facility hierarchy,
GPU pod/capacity grouping, work-order status, and controlled operational state
mapping while staying local and deterministic.

The mapper turns that source extract batch into separate source, canonical, and
provenance RDF models before promotion.

## File Format

The supported local file-backed format is `dcai-source-extract-v1`, encoded as
Java `.properties` with explicit family counts and zero-based record indexes:

```properties
format=dcai-source-extract-v1
batch.id=local-controlled-source-v1
sourceSystem.id=local-controlled-facility-ops-file
sourceSystem.label=Local controlled facility operations file extract
importedAt=2026-06-09T00:00:00Z
assets.count=1
assets.0.recordId=SRC-ASSET-001
assets.0.payloadHash=sha256:asset-001
assets.0.assetId=ASSET-001
assets.0.zoneId=ZONE-A
assets.0.assetType=GPU_RACK_ROW
assets.0.operationalStatus=DEGRADED
assets.0.hallId=HALL-A
assets.0.rowId=ROW-A
assets.0.rackId=RACK-A01
assets.0.capacityGroupId=GPU-POD-A
```

This is a controlled local fixture format only. It is not a production connector
contract and does not approve arbitrary external source ingestion.

## Recorded Connector Simulation Format

The supported recorded connector simulation format is
`dcai-recorded-connector-simulation-v1`. It is a controlled local directory with
a `manifest.properties` file and CSV exports for source-system-shaped data:

- `facilities.csv`
- `zones.csv`
- `assets.csv`
- `incidents.csv`
- `dependencies.csv`
- `workflow_events.csv`
- `work_orders.csv`
- `validation_results.csv`
- `telemetry_impacts.csv`

The semantic-service adapter maps these connector-style exports into the
existing Kotlin `SourceExtractBatch` DTOs before the normal SHACL/provenance
promotion gates run. Invalid source rows and duplicate natural keys are
quarantined in the connector load report and are not promoted. Accepted rows are
deterministic across reruns because source record IDs and payload hashes are
derived from stable local fixture content.

Promote the recorded local export through the internal CLI:

```bash
docker run --rm \
  -v "$PWD":/workspace \
  -w /workspace/semantic-service \
  -e DCAI_FUSEKI_DATASET_URL=http://host.docker.internal:3030/infrastructure \
  gradle:8.10.2-jdk17 \
  gradle --no-daemon run --args="--repo-root=/workspace --promote-source --source-release-id=recorded-local-ops-v1 --source-extract-directory=fixtures/source-extracts/recorded-source-systems/local-ops-v1"
```

This remains a local recorded simulation, not a real external connector.

## Seeded Scenario Generation

The semantic-service CLI can generate recorded source-system exports from
scenario templates. Supported profiles are:

- `demo`: four inspectable outage scenarios
- `mvp`: 48 operational scenarios
- `stress`: 600 scenarios and 10,000+ source rows

Generation is deterministic for a profile and seed: IDs, timestamps, row order,
invalid-row examples, duplicate workflow events, and batch metadata are stable.
The generated CSV files use the same recorded connector simulation format and
must still pass through the existing connector loader, SHACL/provenance gates,
managed graph URI policy, and rollback-safe promotion path.

Generated scenarios cover UPS degradation, cooling instability, telemetry
bridge failure, delayed work orders, conflicting validation evidence, repeated
blast radius, and recovery blockers. The asset exports include hall/row/rack
and GPU pod fields, and the work-order exports include explicit work-order
status values.

Generate a demo export:

```bash
docker run --rm \
  -v "$PWD":/workspace \
  -w /workspace/semantic-service \
  gradle:8.10.2-jdk17 \
  gradle --no-daemon run --args="--repo-root=/workspace --generate-source-scenarios --generated-source-profile=demo --generated-source-seed=20260610"
```

Generate and promote in one controlled local run:

```bash
docker run --rm \
  -v "$PWD":/workspace \
  -w /workspace/semantic-service \
  -e DCAI_FUSEKI_DATASET_URL=http://host.docker.internal:3030/infrastructure \
  gradle:8.10.2-jdk17 \
  gradle --no-daemon run --args="--repo-root=/workspace --generate-source-scenarios --generated-source-profile=demo --generated-source-seed=20260610 --promote-source --source-release-id=generated-demo-seed-20260610"
```

The generator is local-only. It does not connect to external systems or approve
arbitrary source ingestion.
