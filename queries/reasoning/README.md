# Reasoning Query Scaffold

This directory contains parseable placeholder SPARQL query files for the
ontology-native reasoning boundary. The queries are syntax-checked scaffolds
only. They are not wired into a service, reasoning orchestrator, graph promotion
step, or UI surface.

Query files:

- `dependency_exposure.construct.rq`
- `recovery_blocker.construct.rq`
- `restore_readiness.construct.rq`
- `impact_trust.construct.rq`
- `blast_radius.construct.rq`
- `reasoning_finding_lineage.select.rq`

Run the non-runtime syntax check from the repository root:

```bash
backend/.venv/bin/python queries/validate_sparql.py
```

The files must remain aligned with `reasoning/manifest.ttl` and
`queries/manifest.ttl`. A later implementation phase can replace placeholder
patterns with production graph logic after the reasoning runtime contract is
approved.
