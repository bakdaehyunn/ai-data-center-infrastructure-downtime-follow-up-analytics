# Source Extract Fixtures

Production ingestion v1 uses Kotlin DTO fixtures in
`semantic-service/src/test/kotlin/com/dcai/semanticservice/testfixtures/ProductionSourceExtractFixtures.kt`.
The internal local CLI command uses the built-in controlled extract in
`semantic-service/src/main/kotlin/com/dcai/semanticservice/ingestion/LocalControlledSourceExtract.kt`.

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
provenance RDF models before promotion. This directory is reserved for future
file-backed source extracts once a connector/parser boundary is approved.
