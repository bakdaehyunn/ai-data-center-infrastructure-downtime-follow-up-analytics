# Reasoning Query Scaffold

This directory contains parseable SPARQL reference files for the ontology-native
reasoning boundary. The queries are syntax-checked scaffolds only. Executable
reasoning v1 is implemented in Kotlin inside semantic-service; these query files
are not wired into a service, graph promotion step, or UI surface.

Query files:

- `dependency_exposure.construct.rq`
- `recovery_blocker.construct.rq`
- `restore_readiness.construct.rq`
- `impact_trust.construct.rq`
- `blast_radius.construct.rq`
- `reasoning_finding_lineage.select.rq`

Run the non-runtime syntax check from the repository root:

```bash
PYTHONPATH=/tmp/dcai-rdf-tools python3 queries/validate_sparql.py
```

The files must remain aligned with `reasoning/manifest.ttl` and
`queries/manifest.ttl`. A later implementation phase can either replace these
placeholder patterns with production graph logic or keep Kotlin as the
service-owned reasoning runtime.
