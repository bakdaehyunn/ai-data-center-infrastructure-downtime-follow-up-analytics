package com.dcai.semanticservice.promotion

import com.dcai.semanticservice.ingestion.SourceExtractRdfMapper
import com.dcai.semanticservice.runtime.SemanticServiceApplication
import com.dcai.semanticservice.testfixtures.ProductionSourceExtractFixtures
import kotlin.test.Test
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class ProductionGraphValidationGateTest {
    private val repoRoot = SemanticServiceApplication.locateRepoRoot()
    private val gate = ProductionGraphValidationGate(repoRoot)

    @Test
    fun acceptsMappedSourceCanonicalAndProvenanceGraph() {
        val mapping = SourceExtractRdfMapper().map(ProductionSourceExtractFixtures.validBatch())

        val report = gate.validate(mapping.combinedValidationModel())

        assertTrue(report.conforms, report.errors.joinToString(separator = "\n"))
        assertTrue(report.tripleCount > 0)
    }

    @Test
    fun rejectsCanonicalPromotionWhenRequiredZoneFactIsMissing() {
        val mapping = SourceExtractRdfMapper().map(ProductionSourceExtractFixtures.invalidMissingZoneBatch())

        val report = gate.validate(mapping.combinedValidationModel())

        assertFalse(report.conforms)
        assertTrue(report.errors.any { it.contains("SHACL validation failed") })
    }
}
