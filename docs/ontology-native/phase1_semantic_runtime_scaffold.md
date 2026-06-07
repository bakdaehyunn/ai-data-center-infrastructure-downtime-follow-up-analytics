# Phase 1 Semantic Runtime Scaffold

This document records the Phase 1 scaffold for the ontology-native rewrite.
It does not implement the Java/Kotlin semantic service, real ontology modules,
SHACL rules, SPARQL query logic, UI redesign, or old-runtime removal.

## Scope

Phase 1 creates the first graph-native project boundaries:

- persistent Jena/Fuseki/TDB2 storage in Docker Compose
- ontology module directory boundary
- SHACL shape directory boundary
- query manifest placeholder
- graph release manifest placeholder
- verification commands for the scaffold

The existing FastAPI/Postgres/SQLAlchemy runtime remains intact during this
phase. It is not the target architecture, but it is not removed yet.

## Runtime Scaffold

Docker Compose now represents Fuseki as a persistent graph service:

```yaml
fuseki:
  command:
    - --update
    - --loc
    - /fuseki/databases/infrastructure-tdb2
    - /infrastructure
  volumes:
    - fuseki_data:/fuseki/databases
```

This follows the Apache Jena Fuseki model where Fuseki exposes SPARQL protocols
and TDB2 supplies persistent RDF storage. The running service path remains:

```text
http://localhost:3030/infrastructure
```

The current `postgres` service remains in Compose only because Phase 1 is a
scaffold step. It must not be treated as the future ontology-native source of
truth.

## Scaffolded Artifacts

- `ontology/modules/README.md`
- `ontology/releases/2026-06-phase1-scaffold.ttl`
- `shapes/README.md`
- `queries/manifest.ttl`
- `docs/ontology-native/phase1_semantic_runtime_scaffold.md`

## Verification Commands

Run from the repository root:

```bash
docker compose config
```

Confirm Fuseki persistence is represented:

```bash
docker compose config | rg -n "fuseki|/fuseki/databases|infrastructure-tdb2|fuseki_data|--loc|--update"
```

Confirm Phase 1 scaffold files exist:

```bash
test -f ontology/modules/README.md
test -f ontology/releases/2026-06-phase1-scaffold.ttl
test -f shapes/README.md
test -f queries/manifest.ttl
test -f docs/ontology-native/phase1_semantic_runtime_scaffold.md
```

Confirm the scaffold references the approved target boundaries:

```bash
rg -n "Jena|Fuseki|TDB2|ontology/modules|shapes|queries/manifest|release manifest|old-runtime|FastAPI|Postgres|SQLAlchemy" docker-compose.yml ontology/modules shapes queries docs/ontology-native docs/12_ontology_native_rewrite_execplan.md docs/13_ontology_native_target_architecture.md docs/14_ontology_native_verification_plan.md
```

Check formatting:

```bash
git diff --check
```

## Phase 1 Stop Condition

Phase 1 is complete when:

- Docker Compose validates.
- Fuseki is configured with persistent storage.
- The ontology module, SHACL, query manifest, and release manifest boundaries
  exist.
- Verification commands are documented.
- No old runtime code has been removed.
- No Java/Kotlin semantic service, real ontology logic, SHACL rules, SPARQL
  queries, or UI redesign has been implemented.

## Next Phase

Phase 2 should define the ontology and SHACL contract. It should create
versioned OWL/RDFS module skeletons and SHACL shape skeletons with parseable
Turtle, fixture expectations, and validation commands, without removing the old
runtime until graph-backed equivalents exist.
