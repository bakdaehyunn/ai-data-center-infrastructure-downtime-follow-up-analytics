package com.dcai.semanticservice.connectors

import com.dcai.semanticservice.ingestion.Dcai
import com.dcai.semanticservice.ingestion.Prov
import com.dcai.semanticservice.ingestion.SourceExtractRdfMapper
import com.dcai.semanticservice.reasoning.ReasoningInput
import com.dcai.semanticservice.reasoning.ReasoningModelBuilder
import java.nio.file.Files
import java.time.Instant
import kotlin.test.Test
import kotlin.test.assertTrue
import org.apache.jena.rdf.model.ResourceFactory
import org.apache.jena.vocabulary.RDF

class OntologyHardeningCompetencyTest {
    @Test
    fun generatedRecordedScenariosAnswerDowntimeFollowUpCompetencyQuestions() {
        val directory = Files.createTempDirectory("ontology-hardening-competency")
        RecordedSourceScenarioGenerator().generate(
            RecordedSourceScenarioGenerationRequest(
                profile = RecordedSourceScenarioProfile.DEMO,
                seed = 2,
                outputDirectory = directory,
            ),
        )
        val simulation = RecordedSourceConnectorSimulationLoader().load(directory)
        val mapping = SourceExtractRdfMapper().map(simulation.batch)
        val reasoning = ReasoningModelBuilder().build(
            ReasoningInput(
                runId = "ontology-hardening-competency",
                generatedAt = Instant.parse("2026-06-10T01:00:00Z"),
                canonicalModel = mapping.canonicalModel,
                provenanceModel = mapping.provenanceModel,
            ),
        )

        val incidentRecord = simulation.batch.incidents.first()
        val incident = incident(incidentRecord.incidentId)
        val sourceRecord = sourceRecord(simulation.batch.sourceSystemId, incidentRecord.recordId)

        assertTrue(mapping.canonicalModel.contains(incident, Dcai.affectsAsset))
        assertTrue(mapping.canonicalModel.contains(null, RDF.type, Dcai.PowerPath))
        assertTrue(mapping.canonicalModel.contains(null, RDF.type, Dcai.CoolingPath))
        assertTrue(mapping.canonicalModel.contains(null, RDF.type, Dcai.TelemetryPath))
        assertTrue(mapping.canonicalModel.contains(null, Dcai.hasDependencyRoleConcept, state("dependency-role", "power-feed")))
        assertTrue(mapping.canonicalModel.contains(null, Dcai.hasDependencyRoleConcept, state("dependency-role", "cooling-loop")))
        assertTrue(mapping.canonicalModel.contains(null, Dcai.hasDependencyRoleConcept, state("dependency-role", "telemetry-source")))
        assertTrue(mapping.canonicalModel.contains(null, Dcai.hasEvidenceConfidence, state("evidence-confidence", "review-required")))
        assertTrue(mapping.canonicalModel.contains(null, Dcai.hasValidationState, state("validation-status", "secondary-validation-conflict")))
        assertTrue(reasoning.auditModel.contains(null, RDF.type, Dcai.RecoveryBlocker))
        assertTrue(reasoning.auditModel.contains(null, RDF.type, Dcai.BlastRadiusFinding))
        assertTrue(mapping.canonicalModel.contains(incident, Prov.wasDerivedFrom, sourceRecord))
        assertTrue(mapping.provenanceModel.contains(sourceRecord, Dcai.hasSourcePayloadHash))
    }

    private fun incident(id: String) = ResourceFactory.createResource("urn:dcai:incident:$id")

    private fun sourceRecord(sourceSystemId: String, recordId: String) = ResourceFactory.createResource("urn:dcai:source-record:$sourceSystemId:$recordId")

    private fun state(category: String, value: String) = ResourceFactory.createResource("urn:dcai:state:$category:$value")
}
