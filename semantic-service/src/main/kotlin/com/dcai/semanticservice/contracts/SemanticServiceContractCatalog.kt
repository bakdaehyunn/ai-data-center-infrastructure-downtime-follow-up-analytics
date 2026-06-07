package com.dcai.semanticservice.contracts

object SemanticServiceContractCatalog {
    val requiredArtifacts: List<ContractArtifact> = listOf(
        ContractArtifact(
            path = "semantic-service/boundary-contract.ttl",
            requiredMarkers = setOf(
                "dcai-service:semanticServiceBoundary",
                "queryExecution",
                "reasoningValidation",
                "provenanceLookup",
                "promotionReview",
                "aiGovernanceHandoff",
            ),
        ),
        ContractArtifact(
            path = "semantic-service/openapi.semantic-service.yaml",
            requiredMarkers = setOf(
                "openapi: 3.1.0",
                "/semantic/query/{queryId}",
                "/semantic/reasoning/validate",
                "/semantic/provenance/{resourceId}",
                "/semantic/promotion/review",
                "/semantic/ai-governance/handoff",
            ),
        ),
        ContractArtifact(
            path = "semantic-service/api-dtos.md",
            requiredMarkers = setOf(
                "Query Execution",
                "Reasoning Validation",
                "Provenance Lookup",
                "Promotion Review",
                "AI Governance Handoff",
            ),
        ),
        ContractArtifact(
            path = "semantic-service/src/main/resources/contracts/semantic-service-contracts.ttl",
            requiredMarkers = setOf(
                "dcai-service:phase10ServiceScaffold",
                "semantic-service/boundary-contract.ttl",
                "semantic-service/openapi.semantic-service.yaml",
                "semantic-service/api-dtos.md",
            ),
        ),
    )

    val forbiddenMainSourceMarkers: Set<String> = setOf(
        "@RestController",
        "@Controller",
        "@SpringBootApplication",
        "HttpClient",
        "SPARQLRepository",
        "RDFConnection",
        "SPARQLUpdate",
    )
}
