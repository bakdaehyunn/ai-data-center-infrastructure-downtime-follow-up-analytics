package com.dcai.semanticservice.lifecycle

import com.dcai.semanticservice.connectors.RecordedSourceConnectorSimulationLoader
import com.dcai.semanticservice.ingestion.FileSourceExtractLoader
import com.dcai.semanticservice.ingestion.SourceExtractRdfMapper
import com.dcai.semanticservice.promotion.ProductionGraphUris
import com.dcai.semanticservice.reasoning.ReasoningInput
import com.dcai.semanticservice.reasoning.ReasoningModelBuilder
import com.dcai.semanticservice.reasoning.ReasoningOutputGraphUris
import com.dcai.semanticservice.runtime.SemanticServiceApplication
import com.dcai.semanticservice.testfixtures.InMemoryNamedGraphStore
import java.time.Instant
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class GraphLifecycleInspectorTest {
    private val repoRoot = SemanticServiceApplication.locateRepoRoot()

    @Test
    fun reportsPromotionAndReasoningLifecycleStatus() {
        val releaseId = "local-controlled-source-v1"
        val runId = "local-controlled-reasoning-v1"
        val productionGraphs = ProductionGraphUris.forRelease(releaseId)
        val reasoningGraphs = ReasoningOutputGraphUris.forRun(runId)
        val mapping = SourceExtractRdfMapper().map(
            FileSourceExtractLoader().load(repoRoot.resolve("fixtures/source-extracts/local-controlled-source-v1.properties")),
        )
        val reasoning = ReasoningModelBuilder().build(
            ReasoningInput(
                runId = runId,
                generatedAt = Instant.parse("2026-06-09T01:00:00Z"),
                canonicalModel = mapping.canonicalModel,
                provenanceModel = mapping.provenanceModel,
            ),
        )
        val store = InMemoryNamedGraphStore(
            mapOf(
                productionGraphs.sourceGraphUri to mapping.sourceModel,
                productionGraphs.canonicalGraphUri to mapping.canonicalModel,
                productionGraphs.provenanceGraphUri to mapping.provenanceModel,
                reasoningGraphs.auditGraphUri to reasoning.auditModel,
                reasoningGraphs.reasoningGraphUri to reasoning.reasoningModel,
            ),
        )

        val result = GraphLifecycleInspector(store).inspect(
            GraphLifecycleInspectionPlan(
                releaseId = releaseId,
                reasoningRunId = runId,
            ),
        )

        assertTrue(result.inspected, result.errors.joinToString(separator = "\n"))
        assertEquals("promoted", result.lifecycleStatus)
        assertEquals("refreshed", result.reasoningStatus)
        assertEquals(1, result.canonicalGraph?.incidentCount)
        assertEquals(3, result.canonicalGraph?.assetCount)
        assertEquals(2, result.canonicalGraph?.dependencyEdgeCount)
        assertEquals(11, result.provenanceGraph?.sourceRecordCount)
        assertEquals(1, result.provenanceGraph?.promotionActivityCount)
        assertEquals(2, result.reasoningGraph?.findingCount)
    }

    @Test
    fun reportsRecordedConnectorPromotionLifecycleStatus() {
        val releaseId = "recorded-local-ops-v1"
        val productionGraphs = ProductionGraphUris.forRelease(releaseId)
        val mapping = SourceExtractRdfMapper().map(
            RecordedSourceConnectorSimulationLoader()
                .load(repoRoot.resolve("fixtures/source-extracts/recorded-source-systems/local-ops-v1"))
                .batch,
        )
        val store = InMemoryNamedGraphStore(
            mapOf(
                productionGraphs.sourceGraphUri to mapping.sourceModel,
                productionGraphs.canonicalGraphUri to mapping.canonicalModel,
                productionGraphs.provenanceGraphUri to mapping.provenanceModel,
            ),
        )

        val result = GraphLifecycleInspector(store).inspect(
            GraphLifecycleInspectionPlan(
                releaseId = releaseId,
                reasoningRunId = "missing-reasoning",
            ),
        )

        assertTrue(result.inspected, result.errors.joinToString(separator = "\n"))
        assertEquals("promoted", result.lifecycleStatus)
        assertEquals("missing-reasoning", result.reasoningStatus)
        assertEquals(2, result.canonicalGraph?.incidentCount)
        assertEquals(4, result.canonicalGraph?.assetCount)
        assertEquals(3, result.canonicalGraph?.dependencyEdgeCount)
        assertEquals(23, result.provenanceGraph?.sourceRecordCount)
        assertEquals(1, result.provenanceGraph?.promotionActivityCount)
    }

    @Test
    fun reportsMissingLifecycleGraphsWithoutFailingInspection() {
        val result = GraphLifecycleInspector(InMemoryNamedGraphStore()).inspect(
            GraphLifecycleInspectionPlan(
                releaseId = "missing-release",
                reasoningRunId = "missing-reasoning",
            ),
        )

        assertTrue(result.inspected, result.errors.joinToString(separator = "\n"))
        assertEquals("missing-promotion", result.lifecycleStatus)
        assertEquals("missing-reasoning", result.reasoningStatus)
        assertEquals(false, result.sourceGraph?.exists)
        assertEquals(false, result.reasoningGraph?.exists)
    }
}
