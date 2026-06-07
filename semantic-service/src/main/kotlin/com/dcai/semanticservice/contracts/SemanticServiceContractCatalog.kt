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
                "2026-06-phase18-response-contract-checkpoint",
                "/semantic/query/{queryId}",
                "/semantic/reasoning/validate",
                "/semantic/provenance/{resourceId}",
                "/semantic/promotion/review",
                "/semantic/ai-governance/handoff",
                "NamedGraphInventoryResponse",
                "IncidentSummaryResponse",
                "ProvenanceSourceRecordsResponse",
                "SemanticErrorResponse",
                "SemanticResponseProvenance",
            ),
        ),
        ContractArtifact(
            path = "semantic-service/api-dtos.md",
            requiredMarkers = setOf(
                "Phase 18 Response Contract Checkpoint",
                "2026.06.phase17-result-envelope",
                "2026.06.phase18-error-envelope",
                "named-graph-inventory",
                "incident-summary",
                "provenance-source-records",
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
        "HttpURLConnection",
        "openConnection(",
        "SPARQLRepository",
        "RDFConnection",
        "SPARQLUpdate",
        "UpdateFactory",
        "UpdateExecutionFactory",
        "DatasetAccessor",
    )

    val allowedForbiddenMarkerPaths: Map<String, Set<String>> = mapOf(
        "HttpURLConnection" to setOf(
            "semantic-service/src/main/kotlin/com/dcai/semanticservice/graph/FusekiNamedGraphWriter.kt",
        ),
        "openConnection(" to setOf(
            "semantic-service/src/main/kotlin/com/dcai/semanticservice/graph/FusekiNamedGraphWriter.kt",
        ),
    )
}
