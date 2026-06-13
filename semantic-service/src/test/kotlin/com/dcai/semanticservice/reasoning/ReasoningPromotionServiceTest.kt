package com.dcai.semanticservice.reasoning

import com.dcai.semanticservice.ingestion.SourceExtractRdfMapper
import com.dcai.semanticservice.runtime.SemanticServiceApplication
import com.dcai.semanticservice.testfixtures.InMemoryNamedGraphStore
import com.dcai.semanticservice.testfixtures.ProductionSourceExtractFixtures
import java.time.Instant
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertNull
import kotlin.test.assertTrue
import org.apache.jena.rdf.model.Model
import org.apache.jena.rdf.model.ModelFactory
import org.apache.jena.rdf.model.ResourceFactory

class ReasoningPromotionServiceTest {
    private val repoRoot = SemanticServiceApplication.locateRepoRoot()

    @Test
    fun promotesReasoningAuditAndApprovedReasoningGraphs() {
        val canonicalReleaseId = "release-2026-06-ingestion-v1"
        val runId = "reasoning-2026-06-v1"
        val inputGraphs = ReasoningInputGraphUris.forRelease(canonicalReleaseId)
        val outputGraphs = ReasoningOutputGraphUris.forRun(runId)
        val store = InMemoryNamedGraphStore(initialGraphs = inputGraphModels(inputGraphs))

        val result = service(store).run(plan(runId, inputGraphs, outputGraphs))

        assertTrue(result.promoted, result.errors.joinToString(separator = "\n"))
        assertEquals(3, result.findingCount)
        assertEquals(listOf(outputGraphs.auditGraphUri, outputGraphs.reasoningGraphUri), result.writtenGraphUris)
        assertTrue(store.graph(outputGraphs.auditGraphUri)!!.size() > 0)
        assertTrue(store.graph(outputGraphs.reasoningGraphUri)!!.isIsomorphicWith(store.graph(outputGraphs.auditGraphUri)))
        assertEquals(runId, result.releaseManifest?.runId)
        assertEquals(3, result.releaseManifest?.findingCount)
    }

    @Test
    fun doesNotPromoteWhenCanonicalGraphIsMissing() {
        val result = service(InMemoryNamedGraphStore()).run(
            plan(
                runId = "reasoning-2026-06-v1",
                inputGraphs = ReasoningInputGraphUris.forRelease("release-2026-06-ingestion-v1"),
                outputGraphs = ReasoningOutputGraphUris.forRun("reasoning-2026-06-v1"),
            ),
        )

        assertFalse(result.promoted)
        assertTrue(result.errors.any { it.contains("Canonical graph is missing or empty") })
    }

    @Test
    fun restoresReasoningGraphsWhenApprovedGraphWriteFails() {
        val canonicalReleaseId = "release-2026-06-ingestion-v1"
        val runId = "reasoning-2026-06-v1"
        val inputGraphs = ReasoningInputGraphUris.forRelease(canonicalReleaseId)
        val outputGraphs = ReasoningOutputGraphUris.forRun(runId)
        val previousReasoning = markerModel("previous-reasoning")
        val store = InMemoryNamedGraphStore(
            initialGraphs = inputGraphModels(inputGraphs) + mapOf(
                outputGraphs.reasoningGraphUri to previousReasoning,
            ),
            failOnReplaceGraphUri = outputGraphs.reasoningGraphUri,
        )

        val result = service(store).run(plan(runId, inputGraphs, outputGraphs))

        assertFalse(result.promoted)
        assertTrue(result.rollbackAttempted)
        assertTrue(result.rollbackSucceeded, result.errors.joinToString(separator = "\n"))
        assertNull(store.graph(outputGraphs.auditGraphUri))
        assertTrue(store.graph(outputGraphs.reasoningGraphUri)!!.isIsomorphicWith(previousReasoning))
    }

    @Test
    fun rejectsUnmanagedReasoningGraphUris() {
        assertFailsWith<IllegalArgumentException> {
            ReasoningOutputGraphUris(
                auditGraphUri = "urn:dcai:graph:canonical:not-audit",
                reasoningGraphUri = "urn:dcai:graph:reasoning:reasoning-2026-06-v1",
            )
        }
    }

    private fun service(store: InMemoryNamedGraphStore): ReasoningPromotionService {
        return ReasoningPromotionService(
            builder = ReasoningModelBuilder(),
            validationGate = ReasoningValidationGate(repoRoot),
            graphStore = store,
        )
    }

    private fun plan(
        runId: String,
        inputGraphs: ReasoningInputGraphUris,
        outputGraphs: ReasoningOutputGraphUris,
    ): ReasoningPromotionPlan {
        return ReasoningPromotionPlan(
            runId = runId,
            generatedAt = Instant.parse("2026-06-09T01:00:00Z"),
            inputGraphs = inputGraphs,
            outputGraphs = outputGraphs,
        )
    }

    private fun inputGraphModels(graphs: ReasoningInputGraphUris): Map<String, Model> {
        val mapping = SourceExtractRdfMapper().map(ProductionSourceExtractFixtures.validBatch())
        return mapOf(
            graphs.canonicalGraphUri to mapping.canonicalModel,
            graphs.provenanceGraphUri to mapping.provenanceModel,
        )
    }

    private fun markerModel(label: String): Model {
        return ModelFactory.createDefaultModel().apply {
            add(
                ResourceFactory.createResource("urn:dcai:test:$label"),
                ResourceFactory.createProperty("urn:dcai:test:marker"),
                label,
            )
        }
    }
}
