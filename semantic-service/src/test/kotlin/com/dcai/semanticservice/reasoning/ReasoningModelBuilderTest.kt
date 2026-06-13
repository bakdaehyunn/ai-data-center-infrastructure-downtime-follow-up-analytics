package com.dcai.semanticservice.reasoning

import com.dcai.semanticservice.ingestion.Dcai
import com.dcai.semanticservice.ingestion.EvidenceClass
import com.dcai.semanticservice.ingestion.EvidenceSourceRecord
import com.dcai.semanticservice.ingestion.Prov
import com.dcai.semanticservice.ingestion.SourceExtractRdfMapper
import com.dcai.semanticservice.testfixtures.ProductionSourceExtractFixtures
import java.math.BigDecimal
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

        assertEquals(3, output.findingCount)
        assertTrue(output.auditModel.listSubjectsWithProperty(RDF.type, Dcai.DependencyImpactFinding).hasNext())
        assertTrue(output.auditModel.listSubjectsWithProperty(RDF.type, Dcai.BlastRadiusFinding).hasNext())
        assertTrue(output.auditModel.listSubjectsWithProperty(RDF.type, Dcai.RestoreReadinessFinding).hasNext())
        assertTrue(output.auditModel.listSubjectsWithProperty(RDF.type, Dcai.ReasoningActivity).hasNext())
        assertTrue(output.auditModel.listSubjectsWithProperty(Prov.wasGeneratedBy).hasNext())
        assertTrue(output.reasoningModel.isIsomorphicWith(output.auditModel))
    }

    @Test
    fun buildsRestoreReadinessAndTrustFindingsWithProvenance() {
        val mapping = SourceExtractRdfMapper().map(batchWithReadinessAndTrustSignals())

        val output = ReasoningModelBuilder().build(
            ReasoningInput(
                runId = "reasoning-2026-06-v1",
                generatedAt = Instant.parse("2026-06-09T01:00:00Z"),
                canonicalModel = mapping.canonicalModel,
                provenanceModel = mapping.provenanceModel,
            ),
        )

        assertTrue(output.auditModel.listSubjectsWithProperty(RDF.type, Dcai.RecoveryBlocker).hasNext())
        assertTrue(output.auditModel.listSubjectsWithProperty(RDF.type, Dcai.RestoreReadinessFinding).hasNext())
        assertTrue(output.auditModel.listSubjectsWithProperty(RDF.type, Dcai.TrustFinding).hasNext())
        output.auditModel.listSubjectsWithProperty(RDF.type, Dcai.TrustFinding).toList().forEach { finding ->
            assertTrue(output.auditModel.contains(finding, Dcai.hasIdentifier))
            assertTrue(output.auditModel.contains(finding, Dcai.hasEvidenceSeverity))
            assertTrue(output.auditModel.contains(finding, Dcai.createdAt))
            assertTrue(output.auditModel.contains(finding, Prov.wasDerivedFrom))
            assertTrue(output.auditModel.contains(finding, Prov.wasGeneratedBy))
        }
    }

    @Test
    fun marksIncidentReadyWhenEvidenceAndMitigationAreClear() {
        val mapping = SourceExtractRdfMapper().map(readyForReviewBatch())

        val output = ReasoningModelBuilder().build(
            ReasoningInput(
                runId = "reasoning-2026-06-v1",
                generatedAt = Instant.parse("2026-06-09T01:00:00Z"),
                canonicalModel = mapping.canonicalModel,
                provenanceModel = mapping.provenanceModel,
            ),
        )

        val readiness = output.auditModel
            .listSubjectsWithProperty(RDF.type, Dcai.RestoreReadinessFinding)
            .toList()
            .single()
        val summary = output.auditModel
            .listObjectsOfProperty(readiness, Dcai.hasFindingSummary)
            .toList()
            .single()
            .asLiteral()
            .string

        assertEquals(1, output.findingCount)
        assertTrue(summary.contains("ready for review"))
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

    private fun batchWithReadinessAndTrustSignals() =
        ProductionSourceExtractFixtures.validBatch().let { batch ->
            batch.copy(
                evidence = batch.evidence + listOf(
                    EvidenceSourceRecord(
                        recordId = "SRC-EVIDENCE-WO-001",
                        payloadHash = "sha256:evidence-work-order-001",
                        evidenceId = "EVIDENCE-WO-001",
                        evidenceClass = EvidenceClass.WORK_ORDER,
                        supportsId = "INC-001",
                        confidenceState = "TRUSTED",
                        timestamp = Instant.parse("2026-06-09T00:30:00Z"),
                        workOrderId = "WO-001",
                        workOrderStatus = "BLOCKED",
                        assignedTeam = "critical-power",
                    ),
                    EvidenceSourceRecord(
                        recordId = "SRC-EVIDENCE-VALIDATION-PASS-001",
                        payloadHash = "sha256:evidence-validation-pass-001",
                        evidenceId = "EVIDENCE-VALIDATION-PASS-001",
                        evidenceClass = EvidenceClass.VALIDATION,
                        supportsId = "IMPACT-001",
                        confidenceState = "TRUSTED",
                        timestamp = Instant.parse("2026-06-09T00:35:00Z"),
                        validationId = "VAL-001",
                        validationStatus = "PASSED",
                    ),
                    EvidenceSourceRecord(
                        recordId = "SRC-EVIDENCE-VALIDATION-FAIL-001",
                        payloadHash = "sha256:evidence-validation-fail-001",
                        evidenceId = "EVIDENCE-VALIDATION-FAIL-001",
                        evidenceClass = EvidenceClass.VALIDATION,
                        supportsId = "IMPACT-001",
                        confidenceState = "LOW_CONFIDENCE",
                        timestamp = Instant.parse("2026-06-07T00:00:00Z"),
                        metricValue = BigDecimal("0"),
                        validationId = "VAL-002",
                        validationStatus = "FAILED",
                    ),
                    EvidenceSourceRecord(
                        recordId = "SRC-EVIDENCE-TELEMETRY-GAP-001",
                        payloadHash = "sha256:evidence-telemetry-gap-001",
                        evidenceId = "EVIDENCE-TELEMETRY-GAP-001",
                        evidenceClass = EvidenceClass.TELEMETRY,
                        supportsId = "IMPACT-001",
                        confidenceState = "TRUSTED",
                        timestamp = Instant.parse("2026-06-09T00:40:00Z"),
                        metricName = "dcim_bridge_state",
                        metricUnit = "state",
                        telemetryStatus = "MISSING_GAP",
                    ),
                ),
            )
        }

    private fun readyForReviewBatch() =
        ProductionSourceExtractFixtures.validBatch().let { batch ->
            batch.copy(
                dependencies = emptyList(),
                workflowEvents = batch.workflowEvents.map { event ->
                    event.copy(status = "COMPLETE", delayHours = BigDecimal("0.0"))
                },
                impacts = batch.impacts.map { impact ->
                    impact.copy(
                        redundancyState = "N_PLUS_1",
                        mitigationState = "MITIGATED",
                        vendorState = "RESOLVED",
                    )
                },
                evidence = listOf(
                    EvidenceSourceRecord(
                        recordId = "SRC-EVIDENCE-READY-TELEMETRY-001",
                        payloadHash = "sha256:evidence-ready-telemetry-001",
                        evidenceId = "EVIDENCE-READY-TELEMETRY-001",
                        evidenceClass = EvidenceClass.TELEMETRY,
                        supportsId = "IMPACT-001",
                        confidenceState = "TRUSTED",
                        timestamp = Instant.parse("2026-06-09T00:40:00Z"),
                        metricName = "power_kw_at_risk",
                        metricValue = BigDecimal("0.0"),
                        metricUnit = "kW",
                        telemetryStatus = "NORMAL",
                    ),
                    EvidenceSourceRecord(
                        recordId = "SRC-EVIDENCE-READY-VALIDATION-001",
                        payloadHash = "sha256:evidence-ready-validation-001",
                        evidenceId = "EVIDENCE-READY-VALIDATION-001",
                        evidenceClass = EvidenceClass.VALIDATION,
                        supportsId = "IMPACT-001",
                        confidenceState = "TRUSTED",
                        timestamp = Instant.parse("2026-06-09T00:42:00Z"),
                        validationId = "VAL-READY-001",
                        validationStatus = "PASSED",
                    ),
                    EvidenceSourceRecord(
                        recordId = "SRC-EVIDENCE-READY-WORK-ORDER-001",
                        payloadHash = "sha256:evidence-ready-work-order-001",
                        evidenceId = "EVIDENCE-READY-WORK-ORDER-001",
                        evidenceClass = EvidenceClass.WORK_ORDER,
                        supportsId = "INC-001",
                        confidenceState = "TRUSTED",
                        timestamp = Instant.parse("2026-06-09T00:45:00Z"),
                        workOrderId = "WO-READY-001",
                        workOrderStatus = "COMPLETED",
                        assignedTeam = "critical-power",
                    ),
                ),
            )
        }
}
