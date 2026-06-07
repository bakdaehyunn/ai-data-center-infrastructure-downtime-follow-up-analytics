# Semantic Service Boundary

This directory records non-runtime service boundary contracts for the future
Java/Kotlin semantic service. It does not contain service implementation code,
controllers, clients, build files, route handlers, or executable orchestration.

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

Phase 12 adds the cutover and implementation-readiness checkpoint. It records
that the old FastAPI/Postgres/SQLAlchemy/React runtime remains reference-only
for now, lists later-removal triggers, and defines the gates that must pass
before real semantic service endpoints or graph execution can begin.

Tracked readiness checkpoint:

- `semantic-service/cutover-readiness.ttl`
- `docs/ontology-native/phase12_cutover_implementation_readiness.md`
