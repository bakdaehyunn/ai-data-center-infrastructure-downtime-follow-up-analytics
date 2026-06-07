package com.dcai.semanticservice.contracts

import kotlin.io.path.exists
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue
import java.nio.file.Path

class StaticContractValidatorTest {
    private val repoRoot: Path = locateRepoRoot()

    @Test
    fun validatesPhaseEightToTenContracts() {
        val report = StaticContractValidator().validate(repoRoot)

        assertTrue(report.isValid, report.errors.joinToString(separator = "\n"))
        assertEquals(
            SemanticServiceContractCatalog.requiredArtifacts.map { it.path },
            report.checkedArtifacts,
        )
    }

    @Test
    fun contractCatalogReferencesExpectedSemanticServiceArtifacts() {
        val paths = SemanticServiceContractCatalog.requiredArtifacts.map { it.path }.toSet()

        assertTrue("semantic-service/boundary-contract.ttl" in paths)
        assertTrue("semantic-service/openapi.semantic-service.yaml" in paths)
        assertTrue("semantic-service/api-dtos.md" in paths)
        assertTrue("semantic-service/src/main/resources/contracts/semantic-service-contracts.ttl" in paths)
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
