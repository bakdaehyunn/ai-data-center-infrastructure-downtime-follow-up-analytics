package com.dcai.semanticservice.lifecycle

import com.dcai.semanticservice.graph.NamedGraphStore
import com.dcai.semanticservice.ingestion.Dcai
import com.dcai.semanticservice.ingestion.Prov
import com.dcai.semanticservice.promotion.ProductionGraphUris
import com.dcai.semanticservice.reasoning.ReasoningOutputGraphUris
import org.apache.jena.rdf.model.Model
import org.apache.jena.rdf.model.Resource
import org.apache.jena.vocabulary.RDF

class GraphLifecycleInspector(
    private val graphStore: NamedGraphStore,
) {
    fun inspect(plan: GraphLifecycleInspectionPlan): GraphLifecycleInspectionResult {
        return runCatching {
            val productionGraphs = ProductionGraphUris.forRelease(plan.releaseId)
            val source = graphStore.readNamedGraph(productionGraphs.sourceGraphUri)
            val canonical = graphStore.readNamedGraph(productionGraphs.canonicalGraphUri)
            val provenance = graphStore.readNamedGraph(productionGraphs.provenanceGraphUri)
            val reasoningGraphs = plan.reasoningRunId?.let(ReasoningOutputGraphUris::forRun)
            val reasoningAudit = reasoningGraphs?.let { graphStore.readNamedGraph(it.auditGraphUri) }
            val reasoning = reasoningGraphs?.let { graphStore.readNamedGraph(it.reasoningGraphUri) }

            GraphLifecycleInspectionResult(
                releaseId = plan.releaseId,
                sourceGraph = GraphInspectionSummary.from(productionGraphs.sourceGraphUri, source.exists, source.model),
                canonicalGraph = CanonicalGraphInspectionSummary.from(productionGraphs.canonicalGraphUri, canonical.exists, canonical.model),
                provenanceGraph = ProvenanceGraphInspectionSummary.from(productionGraphs.provenanceGraphUri, provenance.exists, provenance.model),
                reasoningRunId = plan.reasoningRunId,
                reasoningAuditGraph = reasoningAudit?.let {
                    ReasoningGraphInspectionSummary.from(reasoningGraphs!!.auditGraphUri, it.exists, it.model)
                },
                reasoningGraph = reasoning?.let {
                    ReasoningGraphInspectionSummary.from(reasoningGraphs!!.reasoningGraphUri, it.exists, it.model)
                },
            )
        }.getOrElse { error ->
            GraphLifecycleInspectionResult(
                releaseId = plan.releaseId,
                reasoningRunId = plan.reasoningRunId,
                errors = listOf("Graph lifecycle inspection failed: ${error.message}"),
            )
        }
    }
}

data class GraphLifecycleInspectionPlan(
    val releaseId: String,
    val reasoningRunId: String? = null,
)

data class GraphLifecycleInspectionResult(
    val releaseId: String,
    val sourceGraph: GraphInspectionSummary? = null,
    val canonicalGraph: CanonicalGraphInspectionSummary? = null,
    val provenanceGraph: ProvenanceGraphInspectionSummary? = null,
    val reasoningRunId: String? = null,
    val reasoningAuditGraph: ReasoningGraphInspectionSummary? = null,
    val reasoningGraph: ReasoningGraphInspectionSummary? = null,
    val errors: List<String> = emptyList(),
) {
    val inspected: Boolean = errors.isEmpty()
    val lifecycleStatus: String = when {
        errors.isNotEmpty() -> "blocked"
        sourceGraph?.exists == true && canonicalGraph?.exists == true && provenanceGraph?.exists == true -> "promoted"
        else -> "missing-promotion"
    }
    val reasoningStatus: String = when {
        reasoningRunId == null -> "not-requested"
        errors.isNotEmpty() -> "blocked"
        reasoningAuditGraph?.exists == true && reasoningGraph?.exists == true -> "refreshed"
        else -> "missing-reasoning"
    }
}

open class GraphInspectionSummary(
    val graphUri: String,
    val exists: Boolean,
    val tripleCount: Int,
) {
    companion object {
        fun from(graphUri: String, exists: Boolean, model: Model): GraphInspectionSummary {
            return GraphInspectionSummary(
                graphUri = graphUri,
                exists = exists,
                tripleCount = model.size().toInt(),
            )
        }
    }
}

class CanonicalGraphInspectionSummary(
    graphUri: String,
    exists: Boolean,
    tripleCount: Int,
    val incidentCount: Int,
    val assetCount: Int,
    val dependencyEdgeCount: Int,
    val impactObservationCount: Int,
) : GraphInspectionSummary(graphUri, exists, tripleCount) {
    companion object {
        fun from(graphUri: String, exists: Boolean, model: Model): CanonicalGraphInspectionSummary {
            return CanonicalGraphInspectionSummary(
                graphUri = graphUri,
                exists = exists,
                tripleCount = model.size().toInt(),
                incidentCount = model.countType(Dcai.InfrastructureIncident),
                assetCount = listOf(Dcai.InfrastructureAsset, Dcai.PowerAsset, Dcai.CoolingAsset, Dcai.ControlTelemetryAsset)
                    .sumOf(model::countType),
                dependencyEdgeCount = model.countType(Dcai.DependencyEdge),
                impactObservationCount = model.countType(Dcai.ImpactObservation),
            )
        }
    }
}

class ProvenanceGraphInspectionSummary(
    graphUri: String,
    exists: Boolean,
    tripleCount: Int,
    val sourceRecordCount: Int,
    val importActivityCount: Int,
    val promotionActivityCount: Int,
    val generatedFactCount: Int,
) : GraphInspectionSummary(graphUri, exists, tripleCount) {
    companion object {
        fun from(graphUri: String, exists: Boolean, model: Model): ProvenanceGraphInspectionSummary {
            return ProvenanceGraphInspectionSummary(
                graphUri = graphUri,
                exists = exists,
                tripleCount = model.size().toInt(),
                sourceRecordCount = model.countType(Dcai.SourceRecord),
                importActivityCount = model.countType(Dcai.ImportActivity),
                promotionActivityCount = model.countType(Dcai.PromotionActivity),
                generatedFactCount = model.listObjectsOfProperty(Prov.generated).toList().distinct().size,
            )
        }
    }
}

class ReasoningGraphInspectionSummary(
    graphUri: String,
    exists: Boolean,
    tripleCount: Int,
    val reasoningActivityCount: Int,
    val dependencyImpactFindingCount: Int,
    val blastRadiusFindingCount: Int,
    val recoveryBlockerCount: Int,
) : GraphInspectionSummary(graphUri, exists, tripleCount) {
    val findingCount: Int = dependencyImpactFindingCount + blastRadiusFindingCount + recoveryBlockerCount

    companion object {
        fun from(graphUri: String, exists: Boolean, model: Model): ReasoningGraphInspectionSummary {
            return ReasoningGraphInspectionSummary(
                graphUri = graphUri,
                exists = exists,
                tripleCount = model.size().toInt(),
                reasoningActivityCount = model.countType(Dcai.ReasoningActivity),
                dependencyImpactFindingCount = model.countType(Dcai.DependencyImpactFinding),
                blastRadiusFindingCount = model.countType(Dcai.BlastRadiusFinding),
                recoveryBlockerCount = model.countType(Dcai.RecoveryBlocker),
            )
        }
    }
}

private fun Model.countType(type: Resource): Int {
    return listSubjectsWithProperty(RDF.type, type).toList().distinct().size
}
