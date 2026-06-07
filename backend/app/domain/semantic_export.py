from __future__ import annotations

from sqlalchemy.orm import Session

from app.domain.semantic_graph import serialize_semantic_graph


def build_infrastructure_semantic_turtle(session: Session) -> str:
    return serialize_semantic_graph(session, include_ontology=True)
