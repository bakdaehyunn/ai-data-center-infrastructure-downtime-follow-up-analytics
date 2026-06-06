# Phase Two: Topology, Semantic Export, and Connector Contracts

## Purpose

Phase two makes the infrastructure model stronger without turning the application into a graph database project. It adds a real topology graph, exposes a small RDF/OWL-lite projection, and documents production connector contracts.

## Infrastructure Topology Graph

The core model now includes `infrastructure_dependencies`. Each row means:

```text
dependent asset -> dependency asset
```

This supports paths such as:

- rack -> PDU -> UPS -> switchgear -> generator
- rack -> CRAH -> chiller
- rack -> CDU -> chiller

The endpoint `GET /api/topology/dependencies` returns each edge with asset names, asset types, current statuses, dependency type, role, impact scope, and active incident counts on both sides.

This is intentionally relational. The project can answer topology questions without adding a graph database or changing the analytics persistence layer.

## RDF/OWL-Lite Semantic Export

The endpoint `GET /api/semantic/infrastructure.ttl` returns Turtle generated from the current relational model. It includes:

- assets
- zones
- incidents
- dependency edges
- basic OWL classes and properties
- a small SHACL-style dependency shape

This is an additive semantic projection. It helps explain the project as semantic infrastructure analytics, but it is not a SPARQL service, graph storage layer, or replacement for SQLAlchemy/PostgreSQL.

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
- The project can be marketed honestly as workflow-ontology-backed analytics with an RDF/OWL-lite semantic export.
- Production readiness is clearer because source contracts are explicit before live connector work begins.

## What Remains Future Work

- Transitive blast-radius scoring across topology paths.
- Operator-facing topology path drilldowns inside incident detail.
- Real authenticated connectors for DCIM, CMMS, ticketing, inventory, telemetry, and vendor systems.
- Optional SHACL validation with a dedicated RDF library if production semantic validation becomes a requirement.
