# Topology, Semantic Ontology, and Connector Contracts

## Purpose

This layer makes the infrastructure model semantic enough to validate and query as an ontology-backed operational system. It keeps source ingestion and analytics materialization in SQL, but projects canonical records into RDF/OWL, validates them with SHACL, exposes SPARQL-backed semantic APIs, and can sync the graph to a Fuseki-compatible triple store.

## Infrastructure Topology Graph

The core model now includes `infrastructure_dependencies`. Each row means:

```text
dependent asset -> dependency asset
```

This supports paths such as:

- rack -> PDU -> UPS -> switchgear -> generator
- rack -> CRAH -> chiller
- rack -> CDU -> chiller

The endpoint `GET /api/topology/dependencies` returns each edge with asset names, asset types, current statuses, dependency type, role, impact scope, and active incident counts on both sides. The same edges are projected into RDF as `dcai:Dependency` resources so semantic services can infer downstream blast radius.

## Semantic Ontology Runtime

The endpoint `GET /api/semantic/infrastructure.ttl` returns Turtle generated from the current relational model. It includes:

- assets
- zones
- incidents
- dependency edges
- OWL classes and properties for infrastructure, workflow, impact, trust, and topology
- SHACL shapes for asset, incident, and dependency validation

Semantic platform endpoints:

```text
GET /api/semantic/validation
GET /api/semantic/query/dependency-impact/{asset_id}
GET /api/semantic/query/incident-evidence/{incident_id}
GET /api/semantic/query/blast-radius/{asset_id}
POST /api/semantic/graph/sync
```

Validation uses SHACL to report whether the generated graph conforms to the ontology contract. Query endpoints use SPARQL over the generated RDF graph to answer evidence and dependency questions. Graph sync sends Turtle to a configured graph-store endpoint such as `http://localhost:3030/infrastructure/data`.

The Compose file includes a Fuseki-compatible service for local semantic graph storage:

```bash
docker compose up -d fuseki
SEMANTIC_TRIPLE_STORE_GRAPH_URL=http://localhost:3030/infrastructure/data
```

## Production Connector Contracts

The endpoint `GET /api/connectors/contracts` lists expected extract contracts for incident, stage-event, work-order, validation, telemetry, and topology feeds.

Each contract identifies:

- source name
- extract file
- target table
- expected cadence
- required payload fields
- optional payload fields
- operational notes

The contracts do not contain credentials, secrets, tokens, live source-system calls, or private production data. Real connectors still require approved source schemas, authentication, scheduling, secret management, network access, and privacy review.

## What This Enables

- Operators can see which upstream power or cooling assets affect a delayed rack or infrastructure component.
- The project can be marketed honestly as a semantic ontology platform with SQL-backed ingestion and analytics.
- SHACL validation makes ontology contract failures explicit instead of buried inside UI logic.
- SPARQL-backed semantic APIs make dependency impact, incident evidence, and blast radius explainable.
- Production readiness is clearer because source contracts are explicit before live connector work begins.

## What Remains Future Work

- Persisting graph sync on every pipeline run.
- Adding authenticated, protected SPARQL read access for trusted internal users.
- Expanding SHACL shapes beyond required fields into stronger controlled-vocabulary and topology consistency rules.
- Transitive blast-radius scoring across topology paths.
- Real authenticated connectors for DCIM, CMMS, ticketing, inventory, telemetry, and vendor systems.
