# Package Layout Placeholder

This package tree reserves the future Kotlin namespace for the semantic
service. Phase 11 adds Kotlin source only under `contracts` for local contract
loading and static validation.

Reserved package areas:

- `api`: future endpoint adapters for the Phase 9 API contract
- `contracts`: future contract loading and version checks
- `query`: future approved query execution boundary
- `reasoning`: future reasoning validation and runner boundary
- `provenance`: future lineage lookup boundary
- `governance`: future AI governance handoff boundary

Do not add controllers, DTO classes, graph clients, runners, or executable
service code in this phase.
