package com.dcai.semanticservice.contracts

import java.nio.file.Path
import kotlin.io.path.exists
import kotlin.test.Test
import kotlin.test.assertTrue

class EndpointReadinessCheckpointTest {
    private val repoRoot: Path = locateRepoRoot()
    private val checkpoint = repoRoot.resolve("semantic-service/endpoint-readiness.ttl").toFile().readText()

    @Test
    fun phaseTwentyKeepsRuntimeInternalOnly() {
        assertTrue(checkpoint.contains("dcai-service:phase20EndpointReadinessCheckpoint"))
        assertTrue(checkpoint.contains("dcai-service:currentRuntimeMode \"cli-only\""))
        assertTrue(checkpoint.contains("dcai-service:phase20Decision \"remain-internal-only-for-this-phase\""))
        assertTrue(checkpoint.contains("dcai-service:publicEndpointImplementationAllowed \"false\""))
        assertTrue(checkpoint.contains("dcai-service:privateEndpointImplementationAllowedInPhase20 \"false\""))
        assertTrue(checkpoint.contains("dcai-service:oldRuntimeRemovalAllowed \"false\""))
    }

    @Test
    fun futureEndpointMustUsePhaseNineteenSerializer() {
        assertTrue(checkpoint.contains("SemanticResponseSerializer.kt"))
        assertTrue(checkpoint.contains("dcai-service:futureEndpointMustNotReturn \"raw SPARQL bindings\""))
        assertTrue(checkpoint.contains("dcai-service:futureEndpointMustNotAccept \"arbitrary browser-supplied SPARQL\""))
        assertTrue(checkpoint.contains("dcai-service:futureEndpointMustNotRun \"SPARQL Update\""))
        assertTrue(checkpoint.contains("dcai-service:futureEndpointMustNotBypass \"approved query manifest\""))
    }

    @Test
    fun publicEndpointGatesAreExplicit() {
        assertTrue(checkpoint.contains("dcai-service:authPolicyAccepted"))
        assertTrue(checkpoint.contains("dcai-service:graphScopePolicyAccepted"))
        assertTrue(checkpoint.contains("dcai-service:timeoutResultLimitPolicyAccepted"))
        assertTrue(checkpoint.contains("dcai-service:auditPolicyAccepted"))
        assertTrue(checkpoint.contains("dcai-service:privateEndpointScaffoldReviewed"))
    }

    private fun locateRepoRoot(): Path {
        var current = Path.of("").toAbsolutePath().normalize()
        while (current.parent != null) {
            if (
                current.resolve("semantic-service/endpoint-readiness.ttl").exists() &&
                current.resolve("ontology/modules").exists()
            ) {
                return current
            }
            current = current.parent
        }
        error("Unable to locate repository root from ${Path.of("").toAbsolutePath()}")
    }
}
