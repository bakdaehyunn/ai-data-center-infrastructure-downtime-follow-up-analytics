package com.dcai.semanticservice.runtime

import com.dcai.semanticservice.graph.GraphConnectionCheck
import com.dcai.semanticservice.graph.ReadOnlyGraphClient
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
    fun canRunReadOnlyGraphConnectivityBoundary() {
        val report = SemanticServiceApplication.run(
            graphClient = StaticReadOnlyGraphClient(
                GraphConnectionCheck(
                    reachable = true,
                    datasetUrl = "http://localhost:3030/infrastructure",
                    queryEndpointUrl = "http://localhost:3030/infrastructure/query",
                    namedGraphCount = 0,
                    message = "ok",
                ),
            ),
        )

        assertTrue(report.isReady, report.contractValidation.errors.joinToString(separator = "\n"))
        assertEquals(true, report.graphConnectionCheck?.reachable)
        assertEquals(0, report.graphConnectionCheck?.namedGraphCount)
        assertFalse(report.graphExecutionEnabled)
        assertFalse(report.httpEndpointsEnabled)
    }

    @Test
    fun locatesRepositoryRootFromSemanticServiceDirectory() {
        val repoRoot = SemanticServiceApplication.locateRepoRoot()

        assertTrue(repoRoot.resolve("semantic-service/openapi.semantic-service.yaml").exists())
        assertTrue(repoRoot.resolve("ontology/modules").exists())
    }

    private class StaticReadOnlyGraphClient(
        private val check: GraphConnectionCheck,
    ) : ReadOnlyGraphClient {
        override fun checkConnectivity(): GraphConnectionCheck = check
    }
}
