from collections.abc import Generator
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.domain.semantic_graph import DCAI, build_semantic_graph, validate_graph, validate_semantic_graph
from app.models import Base
from app.pipeline.runner import run_ingestion_pipeline
from app.sample_data.generator import generate_sample_dataset, write_sample_dataset


@pytest.fixture()
def semantic_session(tmp_path: Path) -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    sample_dir = tmp_path / "sample_data"
    write_sample_dataset(generate_sample_dataset(), sample_dir)
    with session_factory() as session:
        run_ingestion_pipeline(session=session, sample_dir=sample_dir)
        yield session


def test_semantic_graph_conforms_to_shacl_shapes(semantic_session: Session) -> None:
    result = validate_semantic_graph(semantic_session)

    assert result.conforms is True
    assert result.issue_count == 0
    assert result.issues == []


def test_semantic_graph_shacl_validation_reports_missing_required_incident_asset(
    semantic_session: Session,
) -> None:
    graph = build_semantic_graph(semantic_session, include_ontology=True)
    graph.remove((DCAI["INC-0007"], DCAI.affectsAsset, None))

    result = validate_graph(graph)

    assert result.conforms is False
    assert result.issue_count >= 1
    assert any(
        issue.focus_node == "INC-0007" and issue.result_path == "affectsAsset"
        for issue in result.issues
    )
