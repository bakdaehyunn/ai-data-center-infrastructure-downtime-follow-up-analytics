package com.dcai.semanticservice.connectors

import com.dcai.semanticservice.ingestion.SourceExtractRdfMapper
import com.dcai.semanticservice.lifecycle.GraphLifecycleInspectionPlan
import com.dcai.semanticservice.lifecycle.GraphLifecycleInspector
import com.dcai.semanticservice.promotion.GraphPromotionService
import com.dcai.semanticservice.promotion.ProductionGraphPromotionPlan
import com.dcai.semanticservice.promotion.ProductionGraphUris
import com.dcai.semanticservice.promotion.ProductionGraphValidationGate
import com.dcai.semanticservice.reasoning.ReasoningInputGraphUris
import com.dcai.semanticservice.reasoning.ReasoningModelBuilder
import com.dcai.semanticservice.reasoning.ReasoningOutputGraphUris
import com.dcai.semanticservice.reasoning.ReasoningPromotionPlan
import com.dcai.semanticservice.reasoning.ReasoningPromotionService
import com.dcai.semanticservice.reasoning.ReasoningValidationGate
import com.dcai.semanticservice.runtime.SemanticServiceApplication
import com.dcai.semanticservice.testfixtures.InMemoryNamedGraphStore
import java.nio.file.Files
import java.nio.file.Path
import java.time.Instant
import kotlin.io.path.readText
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class RecordedSourceScenarioGeneratorTest {
    private val repoRoot = SemanticServiceApplication.locateRepoRoot()
    private val generator = RecordedSourceScenarioGenerator()
    private val loader = RecordedSourceConnectorSimulationLoader()

    @Test
    fun generatesDeterministicDemoExportsCompatibleWithConnectorLoader() {
        val firstDirectory = Files.createTempDirectory("generated-demo-first")
        val secondDirectory = Files.createTempDirectory("generated-demo-second")

        val first = generator.generate(request(RecordedSourceScenarioProfile.DEMO, 20260610, firstDirectory))
        val second = generator.generate(request(RecordedSourceScenarioProfile.DEMO, 20260610, secondDirectory))
        val firstLoaded = loader.load(firstDirectory)
        val secondLoaded = loader.load(secondDirectory)

        assertEquals(first.copy(outputDirectory = second.outputDirectory), second)
        assertEquals(renderedFiles(firstDirectory), renderedFiles(secondDirectory))
        assertEquals("generated-demo-seed-20260610", firstLoaded.batch.batchId)
        assertEquals(74, firstLoaded.report.totalRows)
        assertEquals(72, firstLoaded.report.acceptedRows)
        assertEquals(2, firstLoaded.report.rejectedRowCount)
        assertEquals(
            firstLoaded.batch.allSourceRecords.map { it.recordId to it.payloadHash },
            secondLoaded.batch.allSourceRecords.map { it.recordId to it.payloadHash },
        )
        assertTrue(firstLoaded.report.rejectedRows.any { it.reason == "missing required field assetId" })
        assertTrue(firstLoaded.report.rejectedRows.any { it.reason.startsWith("duplicate eventId=") })
    }

    @Test
    fun generatesMvpAndStressProfilesWithExpectedScale() {
        val mvpDirectory = Files.createTempDirectory("generated-mvp")
        val stressDirectory = Files.createTempDirectory("generated-stress")

        val mvp = generator.generate(request(RecordedSourceScenarioProfile.MVP, 42, mvpDirectory))
        val stress = generator.generate(request(RecordedSourceScenarioProfile.STRESS, 42, stressDirectory))
        val stressLoaded = loader.load(stressDirectory)

        assertEquals(48, mvp.scenarioCount)
        assertEquals(824, mvp.totalRows)
        assertEquals(600, stress.scenarioCount)
        assertEquals(10_228, stress.totalRows)
        assertTrue(stress.totalRows >= 10_000)
        assertEquals(10_204, stressLoaded.report.acceptedRows)
        assertEquals(24, stressLoaded.report.rejectedRowCount)
    }

    @Test
    fun promotesReasonsAndInspectsGeneratedDemoBatch() {
        val directory = Files.createTempDirectory("generated-demo-lifecycle")
        val generation = generator.generate(request(RecordedSourceScenarioProfile.DEMO, 7, directory))
        val simulation = loader.load(directory)
        val productionGraphs = ProductionGraphUris.forRelease(generation.batchId)
        val store = InMemoryNamedGraphStore()

        val promotion = GraphPromotionService(
            mapper = SourceExtractRdfMapper(),
            validationGate = ProductionGraphValidationGate(repoRoot),
            graphStore = store,
        ).promote(
            ProductionGraphPromotionPlan(
                batch = simulation.batch,
                graphs = productionGraphs,
            ),
        )

        assertTrue(promotion.promoted, promotion.errors.joinToString(separator = "\n"))

        val reasoningRunId = "${generation.batchId}-reasoning"
        val reasoningGraphs = ReasoningOutputGraphUris.forRun(reasoningRunId)
        val reasoning = ReasoningPromotionService(
            builder = ReasoningModelBuilder(),
            validationGate = ReasoningValidationGate(repoRoot),
            graphStore = store,
        ).run(
            ReasoningPromotionPlan(
                runId = reasoningRunId,
                generatedAt = Instant.parse("2026-06-10T01:00:00Z"),
                inputGraphs = ReasoningInputGraphUris.forRelease(generation.batchId),
                outputGraphs = reasoningGraphs,
            ),
        )

        assertTrue(reasoning.promoted, reasoning.errors.joinToString(separator = "\n"))
        assertEquals(16, reasoning.findingCount)

        val lifecycle = GraphLifecycleInspector(store).inspect(
            GraphLifecycleInspectionPlan(
                releaseId = generation.batchId,
                reasoningRunId = reasoningRunId,
            ),
        )

        assertTrue(lifecycle.inspected, lifecycle.errors.joinToString(separator = "\n"))
        assertEquals("promoted", lifecycle.lifecycleStatus)
        assertEquals("refreshed", lifecycle.reasoningStatus)
        assertEquals(4, lifecycle.canonicalGraph?.incidentCount)
        assertEquals(16, lifecycle.canonicalGraph?.assetCount)
        assertEquals(12, lifecycle.canonicalGraph?.dependencyEdgeCount)
        assertEquals(80, lifecycle.provenanceGraph?.sourceRecordCount)
        assertEquals(16, lifecycle.reasoningGraph?.findingCount)
        assertEquals(4, lifecycle.reasoningGraph?.recoveryBlockerCount)
    }

    private fun request(
        profile: RecordedSourceScenarioProfile,
        seed: Int,
        outputDirectory: Path,
    ): RecordedSourceScenarioGenerationRequest {
        return RecordedSourceScenarioGenerationRequest(
            profile = profile,
            seed = seed,
            outputDirectory = outputDirectory,
        )
    }

    private fun renderedFiles(directory: Path): Map<String, String> {
        return Files.list(directory).use { paths ->
            paths
                .filter { Files.isRegularFile(it) }
                .sorted { left, right -> left.fileName.toString().compareTo(right.fileName.toString()) }
                .toList()
                .associate { it.fileName.toString() to it.readText() }
        }
    }
}
