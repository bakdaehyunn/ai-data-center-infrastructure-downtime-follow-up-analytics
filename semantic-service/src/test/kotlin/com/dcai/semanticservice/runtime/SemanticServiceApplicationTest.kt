package com.dcai.semanticservice.runtime

import kotlin.io.path.exists
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class SemanticServiceApplicationTest {
    @Test
    fun startsRunnableContractValidationBaseline() {
        val report = SemanticServiceApplication.run()

        assertTrue(report.isReady, report.contractValidation.errors.joinToString(separator = "\n"))
        assertEquals("contract-validation-runtime", report.mode)
        assertEquals("ready", report.status)
        assertFalse(report.graphExecutionEnabled)
        assertFalse(report.httpEndpointsEnabled)
    }

    @Test
    fun locatesRepositoryRootFromSemanticServiceDirectory() {
        val repoRoot = SemanticServiceApplication.locateRepoRoot()

        assertTrue(repoRoot.resolve("semantic-service/openapi.semantic-service.yaml").exists())
        assertTrue(repoRoot.resolve("ontology/modules").exists())
    }
}
