package com.dcai.semanticservice.reasoning

import com.dcai.semanticservice.ingestion.Dcai
import com.dcai.semanticservice.ingestion.Prov
import java.net.URLEncoder
import java.nio.charset.StandardCharsets
import java.time.Instant
import java.time.temporal.ChronoUnit
import org.apache.jena.rdf.model.Model
import org.apache.jena.rdf.model.ModelFactory
import org.apache.jena.rdf.model.Property
import org.apache.jena.rdf.model.Resource
import org.apache.jena.rdf.model.ResourceFactory
import org.apache.jena.vocabulary.RDF

class ReasoningModelBuilder {
    fun build(input: ReasoningInput): ReasoningOutput {
        val output = ModelFactory.createDefaultModel()
        val activity = ResourceFactory.createResource("urn:dcai:reasoning-activity:${encode(input.runId)}")
        output.add(activity, RDF.type, Dcai.ReasoningActivity)
        output.add(activity, Dcai.hasIdentifier, input.runId)
        output.add(activity, Prov.generatedAtTime, ResourceFactory.createTypedLiteral(input.generatedAt.toString(), org.apache.jena.datatypes.xsd.XSDDatatype.XSDdateTime))

        val dependencyFindings = dependencyExposureFindings(input.canonicalModel, activity, output)
        val blastRadiusFindings = blastRadiusFindings(input.canonicalModel, activity, output)
        val recoveryBlockers = recoveryBlockerFindings(input.canonicalModel, activity, output)
        val restoreReadinessFindings = restoreReadinessFindings(input.canonicalModel, input.generatedAt, activity, output)
        val trustFindings = trustFindings(input.canonicalModel, input.provenanceModel, input.generatedAt, activity, output)
        val findingCount = dependencyFindings + blastRadiusFindings + recoveryBlockers + restoreReadinessFindings + trustFindings

        return ReasoningOutput(
            auditModel = output,
            reasoningModel = ModelFactory.createDefaultModel().add(output),
            findingCount = findingCount,
        )
    }

    private fun dependencyExposureFindings(
        canonical: Model,
        activity: Resource,
        output: Model,
    ): Int {
        var count = 0
        canonical.listSubjectsWithProperty(RDF.type, Dcai.InfrastructureIncident).toList().forEach { incident ->
            canonical.listObjectsOfProperty(incident, Dcai.affectsAsset).toList()
                .filter { it.isResource }
                .map { it.asResource() }
                .forEach { asset ->
                    canonical.listSubjectsWithProperty(Dcai.hasDependentAsset, asset).toList().forEach { edge ->
                        val dependency = canonical.listObjectsOfProperty(edge, Dcai.hasDependencyAsset).toList()
                            .firstOrNull { it.isResource }
                            ?.asResource()
                            ?: return@forEach
                        pathForEdge(canonical, edge)?.let { path ->
                            val finding = ResourceFactory.createResource(
                                "urn:dcai:reasoning:dependency-exposure:${encode(incident.uri)}:${encode(edge.uri)}",
                            )
                            output.add(finding, RDF.type, Dcai.DependencyImpactFinding)
                            output.add(finding, Dcai.hasFindingSummary, "Dependency exposure from ${asset.localNameOrUri()} through ${dependency.localNameOrUri()}")
                            output.add(finding, Prov.wasDerivedFrom, incident)
                            output.add(finding, Prov.wasDerivedFrom, path)
                            output.add(finding, Prov.wasGeneratedBy, activity)
                            output.add(activity, Prov.used, incident)
                            output.add(activity, Prov.used, path)
                            output.add(activity, Prov.generated, finding)
                            count += 1
                        }
                    }
                }
        }
        return count
    }

    private fun blastRadiusFindings(
        canonical: Model,
        activity: Resource,
        output: Model,
    ): Int {
        var count = 0
        canonical.listSubjectsWithProperty(RDF.type, Dcai.InfrastructureIncident).toList().forEach { incident ->
            canonical.listObjectsOfProperty(incident, Dcai.affectsAsset).toList()
                .filter { it.isResource }
                .map { it.asResource() }
                .forEach { asset ->
                    canonical.listSubjectsWithProperty(Dcai.hasDependencyAsset, asset).toList().forEach { edge ->
                        val downstream = canonical.listObjectsOfProperty(edge, Dcai.hasDependentAsset).toList()
                            .firstOrNull { it.isResource }
                            ?.asResource()
                            ?: return@forEach
                        pathForEdge(canonical, edge)?.let { path ->
                            val finding = ResourceFactory.createResource(
                                "urn:dcai:reasoning:blast-radius:${encode(incident.uri)}:${encode(edge.uri)}",
                            )
                            output.add(finding, RDF.type, Dcai.BlastRadiusFinding)
                            output.add(finding, Dcai.hasFindingSummary, "Blast radius from ${asset.localNameOrUri()} to ${downstream.localNameOrUri()}")
                            output.add(finding, Prov.wasDerivedFrom, incident)
                            output.add(finding, Prov.wasDerivedFrom, path)
                            output.add(finding, Prov.wasGeneratedBy, activity)
                            output.add(activity, Prov.used, incident)
                            output.add(activity, Prov.used, path)
                            output.add(activity, Prov.generated, finding)
                            count += 1
                        }
                    }
                }
        }
        return count
    }

    private fun recoveryBlockerFindings(
        canonical: Model,
        activity: Resource,
        output: Model,
    ): Int {
        var count = 0
        canonical.listSubjectsWithProperty(RDF.type, Dcai.InfrastructureIncident).toList().forEach { incident ->
            val signals = recoveryBlockerSignals(canonical, incident)
            if (signals.isEmpty()) {
                return@forEach
            }

            val finding = ResourceFactory.createResource(
                "urn:dcai:reasoning:recovery-blocker:${encode(incident.uri)}",
            )
            output.add(finding, RDF.type, Dcai.RecoveryBlocker)
            output.add(finding, Dcai.hasFindingSummary, "Recovery blocker for ${incident.localNameOrUri()}: ${signals.joinToString(separator = "; ") { it.summary }}")
            output.add(finding, Prov.wasDerivedFrom, incident)
            output.add(finding, Prov.wasGeneratedBy, activity)
            output.add(activity, Prov.used, incident)
            output.add(activity, Prov.generated, finding)
            signals.forEach { signal ->
                output.add(finding, Prov.wasDerivedFrom, signal.source)
                output.add(activity, Prov.used, signal.source)
            }
            count += 1
        }
        return count
    }

    private fun restoreReadinessFindings(
        canonical: Model,
        generatedAt: Instant,
        activity: Resource,
        output: Model,
    ): Int {
        var count = 0
        canonical.listSubjectsWithProperty(RDF.type, Dcai.InfrastructureIncident).toList()
            .sortedBy { it.uri }
            .forEach { incident ->
                val signals = restoreReadinessSignals(canonical, incident, generatedAt)
                val finding = ResourceFactory.createResource(
                    "urn:dcai:reasoning:restore-readiness:${encode(incident.uri)}",
                )
                val summary = if (signals.isEmpty()) {
                    "Restore readiness for ${incident.localNameOrUri()}: ready for review; no active blocker, stale evidence, telemetry alert, or unsupported impact claim detected."
                } else {
                    "Restore readiness for ${incident.localNameOrUri()}: not ready; ${signals.joinToString(separator = "; ") { it.summary }}"
                }
                output.add(finding, RDF.type, Dcai.RestoreReadinessFinding)
                output.add(finding, Dcai.hasFindingSummary, summary)
                output.add(finding, Prov.wasDerivedFrom, incident)
                output.add(finding, Prov.wasGeneratedBy, activity)
                output.add(activity, Prov.used, incident)
                output.add(activity, Prov.generated, finding)
                signals.forEach { signal ->
                    output.add(finding, Prov.wasDerivedFrom, signal.source)
                    output.add(activity, Prov.used, signal.source)
                }
                count += 1
            }
        return count
    }

    private fun trustFindings(
        canonical: Model,
        provenance: Model,
        generatedAt: Instant,
        activity: Resource,
        output: Model,
    ): Int {
        var count = 0
        val emitted = mutableSetOf<String>()
        fun emit(issue: TrustIssue) {
            if (!emitted.add(issue.uriSuffix)) {
                return
            }
            val finding = ResourceFactory.createResource("urn:dcai:reasoning:trust:${issue.uriSuffix}")
            output.add(finding, RDF.type, Dcai.TrustFinding)
            output.add(finding, Dcai.hasIdentifier, issue.identifier)
            output.add(finding, Dcai.createdAt, ResourceFactory.createTypedLiteral(generatedAt.toString(), org.apache.jena.datatypes.xsd.XSDDatatype.XSDdateTime))
            output.add(finding, Dcai.hasEvidenceSeverity, issue.severity)
            output.add(finding, Dcai.hasConfidenceState, issue.status)
            output.add(finding, Dcai.hasFindingSummary, issue.summary)
            issue.sources.distinctBy { it.uri }.sortedBy { it.uri }.forEach { source ->
                output.add(finding, Prov.wasDerivedFrom, source)
                output.add(activity, Prov.used, source)
            }
            output.add(finding, Prov.wasGeneratedBy, activity)
            output.add(activity, Prov.generated, finding)
            count += 1
        }

        evidenceRecords(canonical).forEach { evidence ->
            val confidence = canonical.literalValue(evidence, Dcai.hasConfidenceState)
            if (confidence.isLowConfidenceToken()) {
                emit(
                    TrustIssue(
                        uriSuffix = "low-confidence:${encode(evidence.uri)}",
                        identifier = "low-confidence:${evidence.localNameOrUri()}",
                        severity = "warning",
                        status = "low-confidence",
                        summary = "Low-confidence evidence ${evidence.localNameOrUri()} reports confidence state $confidence.",
                        sources = listOf(evidence),
                    ),
                )
            }

            val telemetryStatus = canonical.literalValue(evidence, Dcai.hasTelemetryStatus)
            if (telemetryStatus.isTelemetryGapToken()) {
                emit(
                    TrustIssue(
                        uriSuffix = "telemetry-gap:${encode(evidence.uri)}",
                        identifier = "telemetry-gap:${evidence.localNameOrUri()}",
                        severity = "critical",
                        status = "telemetry-gap",
                        summary = "Telemetry evidence ${evidence.localNameOrUri()} has gap status $telemetryStatus.",
                        sources = listOf(evidence),
                    ),
                )
            }

            val validationStatus = canonical.literalValue(evidence, Dcai.hasValidationStatus)
            if (validationStatus.isConflictingValidationToken()) {
                emit(
                    TrustIssue(
                        uriSuffix = "validation-conflict:${encode(evidence.uri)}",
                        identifier = "validation-conflict:${evidence.localNameOrUri()}",
                        severity = "critical",
                        status = "conflicting-validation",
                        summary = "Validation evidence ${evidence.localNameOrUri()} requires review because status is $validationStatus.",
                        sources = listOf(evidence),
                    ),
                )
            }

            val timestamp = canonical.instantValue(evidence, Dcai.hasEvidenceTimestamp)
            if (timestamp != null && timestamp.isBefore(generatedAt.minus(24, ChronoUnit.HOURS))) {
                emit(
                    TrustIssue(
                        uriSuffix = "stale-evidence:${encode(evidence.uri)}",
                        identifier = "stale-evidence:${evidence.localNameOrUri()}",
                        severity = "warning",
                        status = "stale-evidence",
                        summary = "Evidence ${evidence.localNameOrUri()} is stale relative to reasoning run ${generatedAt}.",
                        sources = listOf(evidence),
                    ),
                )
            }

            canonical.listObjectsOfProperty(evidence, Dcai.supportsFact).toList()
                .filter { it.isResource }
                .map { it.asResource() }
                .filterNot { canonical.contains(it, RDF.type) }
                .forEach { unsupported ->
                    emit(
                        TrustIssue(
                            uriSuffix = "unsupported-target:${encode(evidence.uri)}:${encode(unsupported.uri)}",
                            identifier = "unsupported-target:${evidence.localNameOrUri()}",
                            severity = "critical",
                            status = "source-quality",
                            summary = "Evidence ${evidence.localNameOrUri()} supports ${unsupported.localNameOrUri()}, but that target is not present as a canonical fact.",
                            sources = listOf(evidence, unsupported),
                        ),
                    )
                }
        }

        canonical.listSubjectsWithProperty(RDF.type, Dcai.ImpactObservation).toList()
            .sortedBy { it.uri }
            .forEach { impact ->
                val supportingEvidence = canonical.listSubjectsWithProperty(Dcai.supportsFact, impact).toList()
                if (supportingEvidence.isEmpty()) {
                    emit(
                        TrustIssue(
                            uriSuffix = "unsupported-impact:${encode(impact.uri)}",
                            identifier = "unsupported-impact:${impact.localNameOrUri()}",
                            severity = "critical",
                            status = "unsupported-impact",
                            summary = "Impact claim ${impact.localNameOrUri()} has no supporting telemetry, validation, or work-order evidence.",
                            sources = listOf(impact),
                        ),
                    )
                }
            }

        validationEvidenceBySupportedFact(canonical).forEach { (fact, evidence) ->
            val statuses = evidence.mapNotNull { canonical.literalValue(it, Dcai.hasValidationStatus) }
            if (statuses.any { it.isPassingValidationToken() } && statuses.any { it.isFailingValidationToken() }) {
                emit(
                    TrustIssue(
                        uriSuffix = "validation-status-conflict:${encode(fact.uri)}",
                        identifier = "validation-status-conflict:${fact.localNameOrUri()}",
                        severity = "critical",
                        status = "conflicting-validation",
                        summary = "Validation evidence for ${fact.localNameOrUri()} contains both passing and failing statuses: ${statuses.sorted().joinToString()}",
                        sources = listOf(fact) + evidence,
                    ),
                )
            }
        }

        canonical.listSubjectsWithProperty(Prov.wasDerivedFrom).toList()
            .filter { it.isURIResource }
            .sortedBy { it.uri }
            .forEach { resource ->
                canonical.listObjectsOfProperty(resource, Prov.wasDerivedFrom).toList()
                    .filter { it.isResource }
                    .map { it.asResource() }
                    .filter { sourceRecord ->
                        !provenance.contains(sourceRecord, Dcai.hasSourcePayloadHash) &&
                            sourceRecord.uri.startsWith("urn:dcai:source-record:")
                    }
                    .forEach { sourceRecord ->
                        emit(
                            TrustIssue(
                                uriSuffix = "missing-source-hash:${encode(resource.uri)}:${encode(sourceRecord.uri)}",
                                identifier = "missing-source-hash:${resource.localNameOrUri()}",
                                severity = "warning",
                                status = "source-quality",
                                summary = "Canonical fact ${resource.localNameOrUri()} is derived from source record ${sourceRecord.localNameOrUri()} without a payload hash in provenance.",
                                sources = listOf(resource, sourceRecord),
                            ),
                        )
                    }
            }

        return count
    }

    private fun restoreReadinessSignals(canonical: Model, incident: Resource, generatedAt: Instant): List<ReasoningSignal> {
        val signals = mutableListOf<ReasoningSignal>()
        signals += recoveryBlockerSignals(canonical, incident)
            .map { ReasoningSignal(it.source, "active recovery blocker: ${it.summary}") }

        val impacts = canonical.listSubjectsWithProperty(Dcai.impactForIncident, incident).toList()
            .sortedBy { it.uri }
        if (impacts.isEmpty()) {
            signals += ReasoningSignal(incident, "missing impact observation")
        }

        impacts.forEach { impact ->
            val mitigationState = canonical.literalValue(impact, Dcai.hasMitigationState)
            if (mitigationState.isMitigationNotReadyToken()) {
                signals += ReasoningSignal(impact, "mitigation state $mitigationState")
            }
            val redundancyState = canonical.literalValue(impact, Dcai.hasRedundancyState)
            if (redundancyState.isRedundancyNotReadyToken()) {
                signals += ReasoningSignal(impact, "redundancy state $redundancyState")
            }
            val vendorState = canonical.literalValue(impact, Dcai.hasVendorState)
            if (vendorState.isVendorNotReadyToken()) {
                signals += ReasoningSignal(impact, "vendor state $vendorState")
            }
        }

        val evidence = (canonical.listSubjectsWithProperty(Dcai.supportsFact, incident).toList() +
            impacts.flatMap { impact -> canonical.listSubjectsWithProperty(Dcai.supportsFact, impact).toList() })
            .distinctBy { it.uri }
            .sortedBy { it.uri }
        if (evidence.none { canonical.contains(it, RDF.type, Dcai.ValidationEvidence) }) {
            signals += ReasoningSignal(incident, "missing validation evidence")
        }
        if (evidence.none { canonical.contains(it, RDF.type, Dcai.WorkOrderEvidence) }) {
            signals += ReasoningSignal(incident, "missing work-order evidence")
        }

        evidence.forEach { item ->
            val confidence = canonical.literalValue(item, Dcai.hasConfidenceState)
            if (confidence.isLowConfidenceToken()) {
                signals += ReasoningSignal(item, "evidence confidence $confidence")
            }
            val telemetryStatus = canonical.literalValue(item, Dcai.hasTelemetryStatus)
            if (telemetryStatus.isTelemetryNotReadyToken()) {
                signals += ReasoningSignal(item, "telemetry status $telemetryStatus")
            }
            val validationStatus = canonical.literalValue(item, Dcai.hasValidationStatus)
            if (validationStatus.isValidationNotReadyToken()) {
                signals += ReasoningSignal(item, "validation status $validationStatus")
            }
            val workOrderStatus = canonical.literalValue(item, Dcai.hasWorkOrderStatus)
            if (workOrderStatus.isWorkOrderNotReadyToken()) {
                signals += ReasoningSignal(item, "work-order status $workOrderStatus")
            }
            val timestamp = canonical.instantValue(item, Dcai.hasEvidenceTimestamp)
            if (timestamp != null && timestamp.isBefore(generatedAt.minus(24, ChronoUnit.HOURS))) {
                signals += ReasoningSignal(item, "stale evidence timestamp $timestamp")
            }
        }

        val affectedAssets = canonical.listObjectsOfProperty(incident, Dcai.affectsAsset).toList()
            .filter { it.isResource }
            .map { it.asResource() }
        affectedAssets.forEach { asset ->
            canonical.listSubjectsWithProperty(Dcai.hasDependencyAsset, asset).toList()
                .sortedBy { it.uri }
                .forEach { edge ->
                    signals += ReasoningSignal(edge, "downstream dependency remains exposed via ${edge.localNameOrUri()}")
                }
        }

        return signals.distinctBy { "${it.source.uri}|${it.summary}" }.sortedWith(compareBy({ it.source.uri }, { it.summary }))
    }

    private fun recoveryBlockerSignals(canonical: Model, incident: Resource): List<RecoveryBlockerSignal> {
        val signals = mutableListOf<RecoveryBlockerSignal>()

        canonical.listSubjectsWithProperty(Dcai.eventForIncident, incident).toList().sortedBy { it.uri }.forEach { event ->
            val status = canonical.literalValue(event, Dcai.hasEventStatus)
            if (status.isBlockerToken()) {
                signals += RecoveryBlockerSignal(event, "workflow status $status")
            }
        }

        canonical.listSubjectsWithProperty(Dcai.supportsFact, incident).toList().sortedBy { it.uri }.forEach { evidence ->
            val workOrderStatus = canonical.literalValue(evidence, Dcai.hasWorkOrderStatus)
            if (workOrderStatus.isBlockerToken()) {
                signals += RecoveryBlockerSignal(evidence, "work order status $workOrderStatus")
            }
            val validationStatus = canonical.literalValue(evidence, Dcai.hasValidationStatus)
            if (validationStatus.isBlockerToken()) {
                signals += RecoveryBlockerSignal(evidence, "validation status $validationStatus")
            }
            val telemetryStatus = canonical.literalValue(evidence, Dcai.hasTelemetryStatus)
            if (telemetryStatus.isBlockerToken()) {
                signals += RecoveryBlockerSignal(evidence, "telemetry status $telemetryStatus")
            }
        }

        return signals
    }

    private fun pathForEdge(canonical: Model, edge: Resource): Resource? {
        return canonical.listSubjectsWithProperty(Dcai.hasPathStep, edge).toList().firstOrNull()
    }

    private fun evidenceRecords(canonical: Model): List<Resource> {
        return listOf(Dcai.TelemetryEvidence, Dcai.ValidationEvidence, Dcai.WorkOrderEvidence)
            .flatMap { type -> canonical.listSubjectsWithProperty(RDF.type, type).toList() }
            .distinctBy { it.uri }
            .sortedBy { it.uri }
    }

    private fun validationEvidenceBySupportedFact(canonical: Model): Map<Resource, List<Resource>> {
        return canonical.listSubjectsWithProperty(RDF.type, Dcai.ValidationEvidence).toList()
            .flatMap { evidence ->
                canonical.listObjectsOfProperty(evidence, Dcai.supportsFact).toList()
                    .filter { it.isResource }
                    .map { it.asResource() to evidence }
            }
            .groupBy(keySelector = { it.first }, valueTransform = { it.second })
    }

    private data class RecoveryBlockerSignal(
        val source: Resource,
        val summary: String,
    )

    private data class ReasoningSignal(
        val source: Resource,
        val summary: String,
    )

    private data class TrustIssue(
        val uriSuffix: String,
        val identifier: String,
        val severity: String,
        val status: String,
        val summary: String,
        val sources: List<Resource>,
    )

    private fun Resource.localNameOrUri(): String = localName ?: uri

    private fun Model.literalValue(subject: Resource, property: Property): String? {
        return listObjectsOfProperty(subject, property).toList()
            .firstOrNull { it.isLiteral }
            ?.asLiteral()
            ?.string
    }

    private fun Model.instantValue(subject: Resource, property: Property): Instant? {
        return listObjectsOfProperty(subject, property).toList()
            .firstOrNull { it.isLiteral }
            ?.asLiteral()
            ?.string
            ?.let { runCatching { Instant.parse(it) }.getOrNull() }
    }

    private fun Model.contains(subject: Resource, property: Property): Boolean {
        return contains(subject, property, null as org.apache.jena.rdf.model.RDFNode?)
    }

    private fun String?.isBlockerToken(): Boolean {
        if (this.isNullOrBlank()) {
            return false
        }
        val normalized = trim().lowercase()
        return listOf("blocked", "delayed", "awaiting", "missing", "conflict", "manual-review", "review_required")
            .any { it in normalized }
    }

    private fun String?.isLowConfidenceToken(): Boolean = containsAny(
        "low",
        "untrusted",
        "unknown",
        "manual-review",
        "review-required",
        "review_required",
        "conflict",
    )

    private fun String?.isTelemetryGapToken(): Boolean = containsAny(
        "missing",
        "stale",
        "gap",
        "offline",
        "unavailable",
        "lost",
    )

    private fun String?.isTelemetryNotReadyToken(): Boolean = containsAny(
        "alert",
        "alarm",
        "missing",
        "stale",
        "gap",
        "offline",
        "unavailable",
        "lost",
        "degraded",
    )

    private fun String?.isValidationNotReadyToken(): Boolean = containsAny(
        "failed",
        "fail",
        "conflict",
        "pending",
        "missing",
        "manual-review",
        "review-required",
        "review_required",
        "rejected",
    )

    private fun String?.isWorkOrderNotReadyToken(): Boolean = containsAny(
        "blocked",
        "delayed",
        "awaiting",
        "pending",
        "open",
        "in-progress",
        "missing",
        "hold",
        "failed",
    )

    private fun String?.isMitigationNotReadyToken(): Boolean = containsAny(
        "degraded",
        "pending",
        "failed",
        "missing",
        "not-started",
        "unmitigated",
        "partial",
    )

    private fun String?.isRedundancyNotReadyToken(): Boolean = containsAny(
        "lost",
        "degraded",
        "n-1",
        "single",
        "none",
        "at-risk",
    )

    private fun String?.isVendorNotReadyToken(): Boolean = containsAny(
        "missed",
        "delayed",
        "blocked",
        "awaiting",
        "pending",
    )

    private fun String?.isConflictingValidationToken(): Boolean = containsAny(
        "conflict",
        "mismatch",
        "failed",
        "fail",
        "manual-review",
        "review-required",
        "rejected",
    )

    private fun String?.isPassingValidationToken(): Boolean = containsAny(
        "passed",
        "pass",
        "validated",
        "complete",
        "accepted",
        "ok",
    )

    private fun String?.isFailingValidationToken(): Boolean = containsAny(
        "failed",
        "fail",
        "conflict",
        "mismatch",
        "rejected",
    )

    private fun String?.containsAny(vararg tokens: String): Boolean {
        if (this.isNullOrBlank()) {
            return false
        }
        val normalized = trim().lowercase().replace('_', '-')
        return tokens.any { it in normalized }
    }

    private companion object {
        private fun encode(value: String): String {
            require(value.isNotBlank()) { "reasoning identifier must not be blank" }
            return URLEncoder.encode(value, StandardCharsets.UTF_8).replace("+", "%20")
        }
    }
}

data class ReasoningInput(
    val runId: String,
    val generatedAt: Instant,
    val canonicalModel: Model,
    val provenanceModel: Model = ModelFactory.createDefaultModel(),
) {
    init {
        require(runId.matches(Regex("[A-Za-z0-9._-]+"))) {
            "runId must contain only letters, numbers, dot, underscore, or hyphen"
        }
        require(!canonicalModel.isEmpty) { "canonicalModel must not be empty" }
    }
}

data class ReasoningOutput(
    val auditModel: Model,
    val reasoningModel: Model,
    val findingCount: Int,
)
