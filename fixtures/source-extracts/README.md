# Source Extract Fixtures

Production ingestion v1 uses Kotlin DTO fixtures in
`semantic-service/src/test/kotlin/com/dcai/semanticservice/testfixtures/ProductionSourceExtractFixtures.kt`.
The internal local CLI command uses the built-in controlled extract in
`semantic-service/src/main/kotlin/com/dcai/semanticservice/ingestion/LocalControlledSourceExtract.kt`.
File-backed local ingestion v1 uses the deterministic properties fixture
`fixtures/source-extracts/local-controlled-source-v1.properties`.

The controlled fixture covers these source record families:

- facility
- zone
- asset
- incident
- dependency
- workflow event
- telemetry evidence
- impact

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
```

This is a controlled local fixture format only. It is not a production connector
contract and does not approve arbitrary external source ingestion.
