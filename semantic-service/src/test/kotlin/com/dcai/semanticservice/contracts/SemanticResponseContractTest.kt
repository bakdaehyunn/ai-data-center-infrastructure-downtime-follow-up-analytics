package com.dcai.semanticservice.contracts

import com.dcai.semanticservice.query.QueryResultEnvelopeProvenance
import com.dcai.semanticservice.query.QueryResultType
import java.nio.file.Path
import kotlin.io.path.exists
import kotlin.test.Test
import kotlin.test.assertTrue

class SemanticResponseContractTest {
    private val repoRoot: Path = locateRepoRoot()
    private val openApi = repoRoot.resolve("semantic-service/openapi.semantic-service.yaml").toFile().readText()
    private val dtoDocs = repoRoot.resolve("semantic-service/api-dtos.md").toFile().readText()

    @Test
    fun openApiPinsPhaseEighteenResponseContractSchemas() {
        assertTrue(openApi.contains("version: 2026-06-phase18-response-contract-checkpoint"))
        assertTrue(openApi.contains("QueryExecutionResponse:"))
        assertTrue(openApi.contains("NamedGraphInventoryResponse:"))
        assertTrue(openApi.contains("IncidentSummaryResponse:"))
        assertTrue(openApi.contains("ProvenanceSourceRecordsResponse:"))
        assertTrue(openApi.contains("SemanticErrorResponse:"))
        assertTrue(openApi.contains("SemanticResponseProvenance:"))
    }

    @Test
    fun openApiResultTypesMatchKotlinEnvelopeTypes() {
        for (type in QueryResultType.entries) {
            assertTrue(openApi.contains(type.value), "Missing OpenAPI result type: ${type.value}")
            assertTrue(dtoDocs.contains(type.value), "Missing DTO doc result type: ${type.value}")
        }
    }

    @Test
    fun responseContractDocumentsVersionAndErrorRules() {
        assertTrue(dtoDocs.contains("Phase 18 Response Contract Checkpoint"))
        assertTrue(dtoDocs.contains(QueryResultEnvelopeProvenance.CONTRACT_VERSION))
        assertTrue(dtoDocs.contains("2026.06.phase18-error-envelope"))
        assertTrue(openApi.contains("unapproved-query-id"))
        assertTrue(openApi.contains("unsupported-result-envelope"))
        assertTrue(openApi.contains("missing-required-binding"))
        assertTrue(openApi.contains("graph-unavailable"))
        assertTrue(openApi.contains("contract-validation-failed"))
        assertTrue(openApi.contains("internal-semantic-service-error"))
    }

    private fun locateRepoRoot(): Path {
        var current = Path.of("").toAbsolutePath().normalize()
        while (current.parent != null) {
            if (
                current.resolve("semantic-service/openapi.semantic-service.yaml").exists() &&
                current.resolve("ontology/modules").exists()
            ) {
                return current
            }
            current = current.parent
        }
        error("Unable to locate repository root from ${Path.of("").toAbsolutePath()}")
    }
}
