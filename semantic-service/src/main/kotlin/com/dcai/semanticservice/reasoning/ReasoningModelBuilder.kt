package com.dcai.semanticservice.reasoning

import com.dcai.semanticservice.ingestion.Dcai
import com.dcai.semanticservice.ingestion.Prov
import java.net.URLEncoder
import java.nio.charset.StandardCharsets
import java.time.Instant
import org.apache.jena.rdf.model.Model
import org.apache.jena.rdf.model.ModelFactory
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
        val findingCount = dependencyFindings + blastRadiusFindings + recoveryBlockers

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

    private fun recoveryBlockerSignals(canonical: Model, incident: Resource): List<RecoveryBlockerSignal> {
        val signals = mutableListOf<RecoveryBlockerSignal>()

        canonical.listSubjectsWithProperty(Dcai.eventForIncident, incident).toList().forEach { event ->
            val status = canonical.literalValue(event, Dcai.hasEventStatus)
            if (status.isBlockerToken()) {
                signals += RecoveryBlockerSignal(event, "workflow status $status")
            }
        }

        canonical.listSubjectsWithProperty(Dcai.supportsFact, incident).toList().forEach { evidence ->
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

    private data class RecoveryBlockerSignal(
        val source: Resource,
        val summary: String,
    )

    private fun Resource.localNameOrUri(): String = localName ?: uri

    private fun Model.literalValue(subject: Resource, property: org.apache.jena.rdf.model.Property): String? {
        return listObjectsOfProperty(subject, property).toList()
            .firstOrNull { it.isLiteral }
            ?.asLiteral()
            ?.string
    }

    private fun String?.isBlockerToken(): Boolean {
        if (this.isNullOrBlank()) {
            return false
        }
        val normalized = trim().lowercase()
        return listOf("blocked", "delayed", "awaiting", "missing", "conflict", "manual-review", "review_required")
            .any { it in normalized }
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
