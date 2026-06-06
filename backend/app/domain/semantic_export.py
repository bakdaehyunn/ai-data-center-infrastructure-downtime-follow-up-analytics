from __future__ import annotations

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.infrastructure import (
    InfrastructureAsset,
    InfrastructureDependency,
    InfrastructureIncident,
    InfrastructureZone,
)


BASE_IRI = "https://example.local/ai-data-center-infrastructure#"


def build_infrastructure_semantic_turtle(session: Session) -> str:
    zones = session.scalars(select(InfrastructureZone).order_by(InfrastructureZone.zone_id)).all()
    assets = session.scalars(select(InfrastructureAsset).order_by(InfrastructureAsset.asset_id)).all()
    dependencies = session.scalars(
        select(InfrastructureDependency).order_by(InfrastructureDependency.dependency_id)
    ).all()
    incidents = session.scalars(select(InfrastructureIncident).order_by(InfrastructureIncident.incident_id)).all()

    lines = [
        "@prefix dcai: <https://example.local/ai-data-center-infrastructure#> .",
        "@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .",
        "@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .",
        "@prefix owl: <http://www.w3.org/2002/07/owl#> .",
        "@prefix sh: <http://www.w3.org/ns/shacl#> .",
        "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .",
        "",
        "dcai:InfrastructureOntology a owl:Ontology ;",
        '  rdfs:label "AI data center infrastructure workflow and topology ontology" .',
        "",
        "dcai:Asset a owl:Class .",
        "dcai:Zone a owl:Class .",
        "dcai:Dependency a owl:Class .",
        "dcai:Incident a owl:Class .",
        "dcai:dependsOn a owl:ObjectProperty .",
        "dcai:locatedIn a owl:ObjectProperty .",
        "dcai:dependentAsset a owl:ObjectProperty .",
        "dcai:affectsAsset a owl:ObjectProperty .",
        "dcai:assetType a owl:DatatypeProperty .",
        "dcai:hasDependencyType a owl:DatatypeProperty .",
        "dcai:dependencyRole a owl:DatatypeProperty .",
        "dcai:impactScope a owl:DatatypeProperty .",
        "dcai:hasCurrentStatus a owl:DatatypeProperty .",
        "dcai:workflowStage a owl:DatatypeProperty .",
        "",
        "dcai:DependencyShape a sh:NodeShape ;",
        "  sh:targetClass dcai:Dependency ;",
        "  sh:property [ sh:path dcai:dependsOn ; sh:minCount 1 ] ;",
        "  sh:property [ sh:path dcai:hasDependencyType ; sh:minCount 1 ] .",
        "",
    ]

    for zone in zones:
        lines.extend(
            [
                f"dcai:{_iri_id(zone.zone_id)} a dcai:Zone ;",
                f'  rdfs:label "{_literal(zone.zone_name)}" ;',
                f'  dcai:hasCurrentStatus "{_literal(zone.current_status)}" .',
                "",
            ]
        )

    for asset in assets:
        lines.extend(
            [
                f"dcai:{_iri_id(asset.asset_id)} a dcai:Asset ;",
                f'  rdfs:label "{_literal(asset.asset_name)}" ;',
                f'  dcai:assetType "{_literal(asset.asset_type)}" ;',
                f'  dcai:hasCurrentStatus "{_literal(asset.current_status)}" ;',
                f"  dcai:locatedIn dcai:{_iri_id(asset.zone_id)} .",
                "",
            ]
        )

    for dependency in dependencies:
        lines.extend(
            [
                f"dcai:{_iri_id(dependency.dependency_id)} a dcai:Dependency ;",
                f'  rdfs:label "{_literal(_dependency_label(dependency))}" ;',
                f"  dcai:dependentAsset dcai:{_iri_id(dependency.dependent_asset_id)} ;",
                f"  dcai:dependsOn dcai:{_iri_id(dependency.dependency_asset_id)} ;",
                f'  dcai:hasDependencyType "{_literal(dependency.dependency_type)}" ;',
                f'  dcai:dependencyRole "{_literal(dependency.dependency_role)}" ;',
                f'  dcai:impactScope "{_literal(dependency.impact_scope)}" .',
                "",
            ]
        )

    for incident in incidents:
        lines.extend(
            [
                f"dcai:{_iri_id(incident.incident_id)} a dcai:Incident ;",
                f'  rdfs:label "{_literal(incident.request_title)}" ;',
                f"  dcai:affectsAsset dcai:{_iri_id(incident.asset_id)} ;",
                f'  dcai:hasCurrentStatus "{_literal(incident.current_status)}" ;',
                f'  dcai:workflowStage "{_literal(incident.current_stage)}" .',
                "",
            ]
        )

    return "\n".join(lines).rstrip() + "\n"


def _dependency_label(dependency: InfrastructureDependency) -> str:
    return (
        f"{dependency.dependent_asset_id} depends on "
        f"{dependency.dependency_asset_id} via {dependency.dependency_type}"
    )


def _iri_id(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "-", value.strip())
    return cleaned or "unknown"


def _literal(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')
