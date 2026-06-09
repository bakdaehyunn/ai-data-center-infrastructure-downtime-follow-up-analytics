package com.dcai.semanticservice.reasoning

import com.dcai.semanticservice.ingestion.SourceExtractRdfMapper
import com.dcai.semanticservice.runtime.SemanticServiceApplication
import com.dcai.semanticservice.testfixtures.ProductionSourceExtractFixtures
import java.time.Instant
import kotlin.test.Test
import kotlin.test.assertFalse
import kotlin.test.assertTrue
import org.apache.jena.rdf.model.ModelFactory

class ReasoningValidationGateTest {
    private val repoRoot = SemanticServiceApplication.locateRepoRoot()
    private val gate = ReasoningValidationGate(repoRoot)

    @Test
    fun acceptsReasoningOutputWithActivitiesAndFindingProvenance() {
        val output = reasoningOutput()

        val report = gate.validate(output.auditModel)

        assertTrue(report.conforms, report.errors.joinToString(separator = "\n"))
        assertTrue(report.tripleCount > 0)
    }

    @Test
    fun rejectsEmptyReasoningOutput() {
        val report = gate.validate(ModelFactory.createDefaultModel())

        assertFalse(report.conforms)
        assertTrue(report.errors.any { it.contains("no dcai:ReasoningActivity") })
    }

    private fun reasoningOutput(): ReasoningOutput {
        val mapping = SourceExtractRdfMapper().map(ProductionSourceExtractFixtures.validBatch())
        return ReasoningModelBuilder().build(
            ReasoningInput(
                runId = "reasoning-2026-06-v1",
                generatedAt = Instant.parse("2026-06-09T01:00:00Z"),
                canonicalModel = mapping.canonicalModel,
                provenanceModel = mapping.provenanceModel,
            ),
        )
    }
}
