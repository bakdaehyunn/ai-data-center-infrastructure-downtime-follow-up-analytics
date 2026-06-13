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
        assertTrue(mapping.canonicalModel.contains(asset("ASSET-GPU-RACK-ROW-A"), RDF.type, Dcai.GpuPod))
        assertTrue(mapping.canonicalModel.contains(asset("ASSET-GPU-RACK-ROW-A"), Dcai.assetInRack, rack("RACK-A01")))
        assertTrue(mapping.canonicalModel.contains(asset("ASSET-GPU-RACK-ROW-A"), Dcai.assetInCapacityGroup, capacityGroup("GPU-POD-A")))
        assertTrue(mapping.canonicalModel.contains(rack("RACK-A01"), Dcai.rackInRow, infrastructureRow("ROW-A")))
        assertTrue(mapping.canonicalModel.contains(capacityGroup("GPU-POD-A"), RDF.type, Dcai.ComputeCapacityGroup))
        assertTrue(mapping.canonicalModel.contains(asset("ASSET-GPU-RACK-ROW-A"), Dcai.hasCriticality, state("criticality", "critical")))
        assertTrue(mapping.canonicalModel.contains(asset("ASSET-GPU-RACK-ROW-A"), Dcai.hasOperationalState, state("operational-status", "degraded")))
        assertTrue(mapping.canonicalModel.contains(asset("ASSET-RACK-PDU-A"), RDF.type, Dcai.PowerAsset))
        assertTrue(mapping.canonicalModel.contains(asset("ASSET-RACK-PDU-A"), RDF.type, Dcai.PowerDistributionUnit))
        assertTrue(mapping.canonicalModel.contains(incident("INC-001"), Dcai.affectsAsset, asset("ASSET-GPU-RACK-ROW-A")))
        assertTrue(mapping.canonicalModel.contains(incident("INC-001"), Dcai.hasIncidentStageState, state("incident-stage", "validation")))
        assertTrue(mapping.canonicalModel.contains(dependencyEdge("EDGE-RACK-PDU-A"), Dcai.hasDependencyAsset, asset("ASSET-RACK-PDU-A")))
        assertTrue(mapping.canonicalModel.contains(dependencyEdge("EDGE-RACK-PDU-A"), Dcai.hasDependencyRoleConcept, state("dependency-role", "power-supply")))
        assertTrue(mapping.canonicalModel.contains(dependencyEdge("EDGE-RACK-PDU-A"), Dcai.hasImpactScopeConcept, state("impact-scope", "rack-row")))
        assertTrue(mapping.canonicalModel.contains(workflowEvent("EVT-001"), Dcai.eventForIncident, incident("INC-001")))
        assertTrue(mapping.canonicalModel.contains(workflowEvent("EVT-001"), Dcai.hasWorkflowEventStatus, state("workflow-event-status", "open")))
        assertTrue(mapping.canonicalModel.contains(impact("IMPACT-001"), Dcai.estimatedCapacityRiskKw))
        assertTrue(mapping.canonicalModel.contains(impact("IMPACT-001"), Dcai.hasRedundancyStateConcept, state("redundancy-state", "n-1")))
        assertTrue(mapping.canonicalModel.contains(impact("IMPACT-001"), Dcai.hasMitigationStateConcept, state("mitigation-state", "running-degraded")))
        assertTrue(mapping.canonicalModel.contains(impact("IMPACT-001"), Dcai.hasVendorStateConcept, state("vendor-state", "eta-missed")))
        assertTrue(mapping.canonicalModel.contains(evidence("EVIDENCE-001"), Dcai.supportsFact, impact("IMPACT-001")))
        assertTrue(mapping.canonicalModel.contains(evidence("EVIDENCE-001"), Dcai.hasEvidenceConfidence, state("evidence-confidence", "trusted")))
        assertTrue(mapping.canonicalModel.contains(evidence("EVIDENCE-001"), Dcai.hasTelemetryState, state("telemetry-status", "alerting")))
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

    private fun infrastructureRow(id: String) = ResourceFactory.createResource("urn:dcai:row:$id")

    private fun rack(id: String) = ResourceFactory.createResource("urn:dcai:rack:$id")

    private fun capacityGroup(id: String) = ResourceFactory.createResource("urn:dcai:capacity-group:$id")

    private fun incident(id: String) = ResourceFactory.createResource("urn:dcai:incident:$id")

    private fun dependencyEdge(id: String) = ResourceFactory.createResource("urn:dcai:dependency-edge:$id")

    private fun workflowEvent(id: String) = ResourceFactory.createResource("urn:dcai:workflow-event:$id")

    private fun impact(id: String) = ResourceFactory.createResource("urn:dcai:impact:$id")

    private fun evidence(id: String) = ResourceFactory.createResource("urn:dcai:evidence:$id")

    private fun promotionActivity(id: String) = ResourceFactory.createResource("urn:dcai:promotion-activity:$id")

    private fun state(category: String, value: String) = ResourceFactory.createResource("urn:dcai:state:$category:$value")
}
