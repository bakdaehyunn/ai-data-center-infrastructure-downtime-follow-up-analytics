package com.dcai.semanticservice.ingestion

import com.dcai.semanticservice.testfixtures.ProductionSourceExtractFixtures
import kotlin.test.Test
import kotlin.test.assertTrue
import org.apache.jena.rdf.model.ResourceFactory
import org.apache.jena.vocabulary.RDF

class SourceExtractRdfMapperTest {
    @Test
    fun mapsProductionSourceExtractIntoSourceCanonicalAndProvenanceModels() {
        val mapping = SourceExtractRdfMapper().map(ProductionSourceExtractFixtures.validBatch())

        assertTrue(mapping.sourceModel.contains(sourceRecord("SRC-INC-001"), RDF.type, Dcai.SourceRecord))
        assertTrue(mapping.sourceModel.contains(sourceSystem("facility-ops"), RDF.type, Dcai.SourceSystem))
        assertTrue(mapping.canonicalModel.contains(asset("ASSET-GPU-RACK-ROW-A"), RDF.type, Dcai.InfrastructureAsset))
        assertTrue(mapping.canonicalModel.contains(asset("ASSET-RACK-PDU-A"), RDF.type, Dcai.PowerAsset))
        assertTrue(mapping.canonicalModel.contains(incident("INC-001"), Dcai.affectsAsset, asset("ASSET-GPU-RACK-ROW-A")))
        assertTrue(mapping.canonicalModel.contains(dependencyEdge("EDGE-RACK-PDU-A"), Dcai.hasDependencyAsset, asset("ASSET-RACK-PDU-A")))
        assertTrue(mapping.canonicalModel.contains(workflowEvent("EVT-001"), Dcai.eventForIncident, incident("INC-001")))
        assertTrue(mapping.canonicalModel.contains(impact("IMPACT-001"), Dcai.estimatedCapacityRiskKw))
        assertTrue(mapping.canonicalModel.contains(evidence("EVIDENCE-001"), Dcai.supportsFact, impact("IMPACT-001")))
        assertTrue(mapping.provenanceModel.contains(promotionActivity("release-2026-06-ingestion-v1"), RDF.type, Dcai.PromotionActivity))
    }

    @Test
    fun mapsSameBatchDeterministically() {
        val mapper = SourceExtractRdfMapper()
        val first = mapper.map(ProductionSourceExtractFixtures.validBatch()).combinedValidationModel()
        val second = mapper.map(ProductionSourceExtractFixtures.validBatch()).combinedValidationModel()

        assertTrue(first.isIsomorphicWith(second))
    }

    private fun sourceSystem(id: String) = ResourceFactory.createResource("urn:dcai:source-system:$id")

    private fun sourceRecord(id: String) = ResourceFactory.createResource("urn:dcai:source-record:facility-ops:$id")

    private fun asset(id: String) = ResourceFactory.createResource("urn:dcai:asset:$id")

    private fun incident(id: String) = ResourceFactory.createResource("urn:dcai:incident:$id")

    private fun dependencyEdge(id: String) = ResourceFactory.createResource("urn:dcai:dependency-edge:$id")

    private fun workflowEvent(id: String) = ResourceFactory.createResource("urn:dcai:workflow-event:$id")

    private fun impact(id: String) = ResourceFactory.createResource("urn:dcai:impact:$id")

    private fun evidence(id: String) = ResourceFactory.createResource("urn:dcai:evidence:$id")

    private fun promotionActivity(id: String) = ResourceFactory.createResource("urn:dcai:promotion-activity:$id")
}
