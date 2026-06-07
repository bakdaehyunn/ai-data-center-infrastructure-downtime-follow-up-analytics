from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from pyshacl import validate
from rdflib import Graph, Literal, Namespace, RDF, RDFS, SH, URIRef
from rdflib.namespace import OWL, XSD
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.infrastructure import (
    InfrastructureAsset,
    InfrastructureDependency,
    InfrastructureImpactSnapshot,
    InfrastructureIncident,
    InfrastructureZone,
)
from app.models.ops import InfrastructureReconciliationIssue, PipelineRun


DCAI = Namespace("https://example.local/ai-data-center-infrastructure#")
ONTOLOGY_DIR = Path(__file__).resolve().parents[3] / "ontology"
ONTOLOGY_FILES = (
    "infrastructure-core.ttl",
    "workflow.ttl",
    "topology.ttl",
)
SHAPES_FILE = "shapes.ttl"
_SPARQL_QUERY_LOCK = Lock()


@dataclass(frozen=True)
class SemanticValidationIssue:
    focus_node: str
    result_path: str
    message: str
    severity: str


@dataclass(frozen=True)
class SemanticValidationResult:
    conforms: bool
    issue_count: int
    issues: list[SemanticValidationIssue]


@dataclass(frozen=True)
class SemanticGraphSyncResult:
    configured: bool
    status: str
    triple_count: int
    target_url: str | None
    message: str


def build_semantic_graph(session: Session, *, include_ontology: bool = True) -> Graph:
    graph = _base_graph()
    if include_ontology:
        graph += load_ontology_graph()
        graph += load_shapes_graph()

    zones = session.scalars(select(InfrastructureZone).order_by(InfrastructureZone.zone_id)).all()
    assets = session.scalars(select(InfrastructureAsset).order_by(InfrastructureAsset.asset_id)).all()
    dependencies = session.scalars(
        select(InfrastructureDependency).order_by(InfrastructureDependency.dependency_id)
    ).all()
    incidents = session.scalars(select(InfrastructureIncident).order_by(InfrastructureIncident.incident_id)).all()
    impacts = _latest_impact_by_incident(session)
    latest_pipeline_run_id = _latest_pipeline_run_id(session)
    trust_issues = []
    if latest_pipeline_run_id:
        trust_issues = session.scalars(
            select(InfrastructureReconciliationIssue)
            .where(InfrastructureReconciliationIssue.pipeline_run_id == latest_pipeline_run_id)
            .order_by(InfrastructureReconciliationIssue.issue_id)
        ).all()

    for zone in zones:
        zone_ref = _ref(zone.zone_id)
        graph.add((zone_ref, RDF.type, DCAI.Zone))
        graph.add((zone_ref, RDFS.label, Literal(zone.zone_name)))
        graph.add((zone_ref, DCAI.zonePriority, Literal(zone.zone_priority)))
        graph.add((zone_ref, DCAI.hasCurrentStatus, Literal(zone.current_status)))

    for asset in assets:
        asset_ref = _ref(asset.asset_id)
        graph.add((asset_ref, RDF.type, DCAI.Asset))
        graph.add((asset_ref, RDFS.label, Literal(asset.asset_name)))
        graph.add((asset_ref, DCAI.assetType, Literal(asset.asset_type)))
        graph.add((asset_ref, DCAI.criticalityLevel, Literal(asset.criticality_level)))
        graph.add((asset_ref, DCAI.hasCurrentStatus, Literal(asset.current_status)))
        graph.add((asset_ref, DCAI.locatedIn, _ref(asset.zone_id)))

    for dependency in dependencies:
        dependency_ref = _ref(dependency.dependency_id)
        graph.add((dependency_ref, RDF.type, DCAI.Dependency))
        graph.add((dependency_ref, RDFS.label, Literal(_dependency_label(dependency))))
        graph.add((dependency_ref, DCAI.dependentAsset, _ref(dependency.dependent_asset_id)))
        graph.add((dependency_ref, DCAI.dependsOn, _ref(dependency.dependency_asset_id)))
        graph.add((dependency_ref, DCAI.downstreamAsset, _ref(dependency.dependent_asset_id)))
        graph.add((dependency_ref, DCAI.upstreamAsset, _ref(dependency.dependency_asset_id)))
        graph.add((dependency_ref, DCAI.hasDependencyType, Literal(dependency.dependency_type)))
        graph.add((dependency_ref, DCAI.dependencyRole, Literal(dependency.dependency_role)))
        graph.add((dependency_ref, DCAI.impactScope, Literal(dependency.impact_scope)))

    for incident in incidents:
        incident_ref = _ref(incident.incident_id)
        graph.add((incident_ref, RDF.type, DCAI.Incident))
        graph.add((incident_ref, RDFS.label, Literal(incident.request_title)))
        graph.add((incident_ref, DCAI.affectsAsset, _ref(incident.asset_id)))
        graph.add((incident_ref, DCAI.hasCurrentStatus, Literal(incident.current_status)))
        graph.add((incident_ref, DCAI.workflowStage, Literal(incident.current_stage)))
        graph.add((incident_ref, DCAI.priorityLevel, Literal(incident.priority_level)))
        graph.add((incident_ref, DCAI.businessImpact, Literal(incident.business_impact)))

        impact = impacts.get(incident.incident_id)
        if impact:
            impact_ref = _ref(impact.impact_snapshot_id)
            graph.add((impact_ref, RDF.type, DCAI.ImpactSnapshot))
            graph.add((impact_ref, DCAI.estimatedCapacityRiskKw, Literal(float(impact.estimated_capacity_risk_kw), datatype=XSD.decimal)))
            graph.add((impact_ref, DCAI.affectedGpuCount, Literal(impact.affected_gpu_count, datatype=XSD.integer)))
            graph.add((impact_ref, DCAI.redundancyState, Literal(impact.redundancy_state)))
            graph.add((impact_ref, DCAI.mitigationStatus, Literal(impact.mitigation_status)))
            graph.add((impact_ref, DCAI.vendorStatus, Literal(impact.vendor_status)))
            graph.add((incident_ref, DCAI.hasImpactSnapshot, impact_ref))

    for issue in trust_issues:
        issue_ref = _ref(issue.issue_id)
        graph.add((issue_ref, RDF.type, DCAI.TrustIssue))
        graph.add((issue_ref, RDFS.label, Literal(issue.message)))
        graph.add((issue_ref, DCAI.confidenceStatus, Literal(issue.severity)))
        if issue.incident_id:
            graph.add((_ref(issue.incident_id), DCAI.hasTrustIssue, issue_ref))

    return graph


def serialize_semantic_graph(session: Session, *, include_ontology: bool = True) -> str:
    graph = build_semantic_graph(session, include_ontology=include_ontology)
    return graph.serialize(format="turtle")


def load_ontology_graph() -> Graph:
    graph = _base_graph()
    for filename in ONTOLOGY_FILES:
        graph.parse(ONTOLOGY_DIR / filename, format="turtle")
    return graph


def load_shapes_graph() -> Graph:
    graph = _base_graph()
    graph.parse(ONTOLOGY_DIR / SHAPES_FILE, format="turtle")
    return graph


def validate_graph(data_graph: Graph) -> SemanticValidationResult:
    conforms, results_graph, _ = validate(
        data_graph,
        shacl_graph=load_shapes_graph(),
        ont_graph=load_ontology_graph(),
        inference="rdfs",
        abort_on_first=False,
        allow_infos=True,
        allow_warnings=True,
    )
    issues = [
        SemanticValidationIssue(
            focus_node=_local_name(str(focus_node)),
            result_path=_local_name(str(result_path)),
            message=str(message),
            severity=_local_name(str(severity)),
        )
        for result in results_graph.subjects(RDF.type, SH.ValidationResult)
        for focus_node in results_graph.objects(result, SH.focusNode)
        for result_path in results_graph.objects(result, SH.resultPath)
        for message in results_graph.objects(result, SH.resultMessage)
        for severity in results_graph.objects(result, SH.resultSeverity)
    ]
    return SemanticValidationResult(
        conforms=bool(conforms),
        issue_count=len(issues),
        issues=issues,
    )


def validate_semantic_graph(session: Session) -> SemanticValidationResult:
    return validate_graph(build_semantic_graph(session, include_ontology=True))


def semantic_dependency_impact(session: Session, asset_id: str) -> dict[str, Any]:
    graph = build_semantic_graph(session)
    asset_ref = _ref(asset_id)
    direct_rows = [
        {
            "dependency_id": _local_name(str(row.dependency)),
            "dependent_asset_id": _local_name(str(row.dependentAsset)),
            "dependency_asset_id": _local_name(str(row.dependsOn)),
            "dependency_type": str(row.dependencyType),
            "dependency_role": str(row.dependencyRole),
        }
        for row in _query_graph(
            graph,
            """
            PREFIX dcai: <https://example.local/ai-data-center-infrastructure#>
            SELECT ?dependency ?dependentAsset ?dependsOn ?dependencyType ?dependencyRole
            WHERE {
              ?dependency a dcai:Dependency ;
                dcai:dependentAsset ?dependentAsset ;
                dcai:dependsOn ?dependsOn ;
                dcai:hasDependencyType ?dependencyType ;
                dcai:dependencyRole ?dependencyRole .
              FILTER (?dependentAsset = ?asset || ?dependsOn = ?asset)
            }
            ORDER BY ?dependency
            """,
            initBindings={"asset": asset_ref},
        )
    ]
    return {
        "asset_id": asset_id,
        "direct_dependency_count": len(direct_rows),
        "direct_dependencies": direct_rows,
        "inferred_downstream_assets": _blast_radius_assets(graph, asset_ref),
    }


def semantic_incident_evidence(session: Session, incident_id: str) -> dict[str, Any]:
    graph = build_semantic_graph(session)
    rows = list(
        _query_graph(
            graph,
            """
            PREFIX dcai: <https://example.local/ai-data-center-infrastructure#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT ?label ?asset ?stage ?status ?priority ?trustIssue
            WHERE {
              ?incident a dcai:Incident ;
                rdfs:label ?label ;
                dcai:affectsAsset ?asset ;
                dcai:workflowStage ?stage ;
                dcai:hasCurrentStatus ?status ;
                dcai:priorityLevel ?priority .
              OPTIONAL { ?incident dcai:hasTrustIssue ?trustIssue . }
            }
            """,
            initBindings={"incident": _ref(incident_id)},
        )
    )
    if not rows:
        return {
            "incident_id": incident_id,
            "found": False,
            "semantic_evidence": [],
        }
    first = rows[0]
    trust_issues = sorted({_local_name(str(row.trustIssue)) for row in rows if row.trustIssue})
    return {
        "incident_id": incident_id,
        "found": True,
        "request_title": str(first.label),
        "asset_id": _local_name(str(first.asset)),
        "workflow_stage": str(first.stage),
        "current_status": str(first.status),
        "priority_level": str(first.priority),
        "trust_issue_ids": trust_issues,
    }


def semantic_blast_radius(session: Session, asset_id: str) -> dict[str, Any]:
    graph = build_semantic_graph(session)
    downstream_assets = _blast_radius_assets(graph, _ref(asset_id))
    incident_rows = [
        {
            "incident_id": _local_name(str(row.incident)),
            "asset_id": _local_name(str(row.asset)),
            "title": str(row.label),
            "stage": str(row.stage),
        }
        for row in _query_graph(
            graph,
            """
            PREFIX dcai: <https://example.local/ai-data-center-infrastructure#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            SELECT ?incident ?asset ?label ?stage
            WHERE {
              ?incident a dcai:Incident ;
                rdfs:label ?label ;
                dcai:affectsAsset ?asset ;
                dcai:workflowStage ?stage .
            }
            ORDER BY ?incident
            """
        )
        if _local_name(str(row.asset)) in {asset_id, *downstream_assets}
    ]
    return {
        "asset_id": asset_id,
        "inferred_downstream_assets": downstream_assets,
        "affected_incident_count": len(incident_rows),
        "affected_incidents": incident_rows,
    }


def sync_graph_to_triple_store(session: Session, *, target_url: str | None) -> SemanticGraphSyncResult:
    graph = build_semantic_graph(session)
    if not target_url:
        return SemanticGraphSyncResult(
            configured=False,
            status="NOT_CONFIGURED",
            triple_count=len(graph),
            target_url=None,
            message="Semantic graph was built locally; no triple-store endpoint is configured.",
        )

    turtle = graph.serialize(format="turtle").encode("utf-8")
    request = Request(
        target_url,
        data=turtle,
        headers={"Content-Type": "text/turtle"},
        method="PUT",
    )
    try:
        with urlopen(request, timeout=10) as response:
            return SemanticGraphSyncResult(
                configured=True,
                status="SYNCED" if 200 <= response.status < 300 else "FAILED",
                triple_count=len(graph),
                target_url=target_url,
                message=f"Triple-store response status {response.status}.",
            )
    except URLError as exc:
        return SemanticGraphSyncResult(
            configured=True,
            status="FAILED",
            triple_count=len(graph),
            target_url=target_url,
            message=str(exc.reason),
        )


def _base_graph() -> Graph:
    graph = Graph()
    graph.bind("dcai", DCAI)
    graph.bind("owl", OWL)
    graph.bind("rdf", RDF)
    graph.bind("rdfs", RDFS)
    graph.bind("sh", SH)
    graph.bind("xsd", XSD)
    return graph


def _latest_impact_by_incident(session: Session) -> dict[str, InfrastructureImpactSnapshot]:
    impacts = session.scalars(
        select(InfrastructureImpactSnapshot).order_by(
            InfrastructureImpactSnapshot.incident_id,
            desc(InfrastructureImpactSnapshot.snapshot_at),
            InfrastructureImpactSnapshot.impact_snapshot_id,
        )
    ).all()
    latest: dict[str, InfrastructureImpactSnapshot] = {}
    for impact in impacts:
        latest.setdefault(impact.incident_id, impact)
    return latest


def _latest_pipeline_run_id(session: Session) -> str | None:
    return session.scalar(
        select(PipelineRun.pipeline_run_id)
        .order_by(desc(PipelineRun.started_at), PipelineRun.pipeline_run_id)
        .limit(1)
    )


def _blast_radius_assets(graph: Graph, asset_ref: URIRef) -> list[str]:
    visited: set[URIRef] = set()
    frontier = [asset_ref]
    while frontier:
        current = frontier.pop(0)
        for row in _query_graph(
            graph,
            """
            PREFIX dcai: <https://example.local/ai-data-center-infrastructure#>
            SELECT ?downstream
            WHERE {
              ?dependency a dcai:Dependency ;
                dcai:dependsOn ?upstream ;
                dcai:dependentAsset ?downstream .
            }
            """,
            initBindings={"upstream": current},
        ):
            downstream = row.downstream
            if downstream not in visited and downstream != asset_ref:
                visited.add(downstream)
                frontier.append(downstream)
    return sorted(_local_name(str(item)) for item in visited)


def _query_graph(graph: Graph, query: str, *, initBindings: dict[str, Any] | None = None) -> list[Any]:
    # rdflib's SPARQL parser stack is not safe under concurrent browser requests.
    with _SPARQL_QUERY_LOCK:
        return list(graph.query(query, initBindings=initBindings))


def _ref(value: str) -> URIRef:
    return DCAI[_iri_id(value)]


def _dependency_label(dependency: InfrastructureDependency) -> str:
    return (
        f"{dependency.dependent_asset_id} depends on "
        f"{dependency.dependency_asset_id} via {dependency.dependency_type}"
    )


def _iri_id(value: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in {"_", "-"} else "-" for char in value.strip())
    return cleaned or "unknown"


def _local_name(value: str) -> str:
    if "#" in value:
        return value.rsplit("#", 1)[1]
    if "/" in value:
        return value.rsplit("/", 1)[1]
    return value
