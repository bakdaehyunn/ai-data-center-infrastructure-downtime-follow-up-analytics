package com.dcai.semanticservice.reasoning

import com.dcai.semanticservice.ingestion.Dcai
import com.dcai.semanticservice.ingestion.Prov
import com.dcai.semanticservice.ingestion.SourceExtractRdfMapper
import com.dcai.semanticservice.testfixtures.ProductionSourceExtractFixtures
import java.time.Instant
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue
import org.apache.jena.vocabulary.RDF

class ReasoningModelBuilderTest {
    @Test
    fun buildsDependencyExposureAndBlastRadiusFindingsFromCanonicalGraph() {
        val mapping = SourceExtractRdfMapper().map(ProductionSourceExtractFixtures.validBatch())

        val output = ReasoningModelBuilder().build(
            ReasoningInput(
                runId = "reasoning-2026-06-v1",
                generatedAt = Instant.parse("2026-06-09T01:00:00Z"),
                canonicalModel = mapping.canonicalModel,
                provenanceModel = mapping.provenanceModel,
            ),
        )

        assertEquals(2, output.findingCount)
        assertTrue(output.auditModel.listSubjectsWithProperty(RDF.type, Dcai.DependencyImpactFinding).hasNext())
        assertTrue(output.auditModel.listSubjectsWithProperty(RDF.type, Dcai.BlastRadiusFinding).hasNext())
        assertTrue(output.auditModel.listSubjectsWithProperty(RDF.type, Dcai.ReasoningActivity).hasNext())
        assertTrue(output.auditModel.listSubjectsWithProperty(Prov.wasGeneratedBy).hasNext())
        assertTrue(output.reasoningModel.isIsomorphicWith(output.auditModel))
    }

    @Test
    fun buildsReasoningOutputDeterministically() {
        val mapping = SourceExtractRdfMapper().map(ProductionSourceExtractFixtures.validBatch())
        val input = ReasoningInput(
            runId = "reasoning-2026-06-v1",
            generatedAt = Instant.parse("2026-06-09T01:00:00Z"),
            canonicalModel = mapping.canonicalModel,
            provenanceModel = mapping.provenanceModel,
        )
        val builder = ReasoningModelBuilder()

        val first = builder.build(input)
        val second = builder.build(input)

        assertTrue(first.auditModel.isIsomorphicWith(second.auditModel))
        assertTrue(first.reasoningModel.isIsomorphicWith(second.reasoningModel))
    }
}
