# Reasoning Rule Placeholders

This directory reserves the future rule boundary for ontology-native reasoning.
It intentionally contains documentation only.

Future executable rule files should not be added until the reasoning runtime is
implemented and verified. The expected future rule names are:

- `dependency-exposure.rules`
- `recovery-blocker.rules`
- `restore-readiness.rules`
- `impact-trust.rules`
- `blast-radius.rules`

Each future rule must:

- read only from validated canonical graph facts unless explicitly marked as an
  audit-only candidate rule
- write candidate derived facts to a reasoning audit graph first
- emit provenance through `dcai:ReasoningActivity`
- declare the ontology class it constructs
- include fixture expectations before promotion to the approved reasoning graph
