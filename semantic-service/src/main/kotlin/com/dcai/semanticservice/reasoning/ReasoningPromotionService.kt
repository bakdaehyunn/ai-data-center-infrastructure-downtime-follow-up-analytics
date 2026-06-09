package com.dcai.semanticservice.reasoning

import com.dcai.semanticservice.graph.NamedGraphSnapshot
import com.dcai.semanticservice.graph.NamedGraphStore
import java.time.Instant
import org.apache.jena.rdf.model.Model

interface ReasoningRefresher {
    fun run(plan: ReasoningPromotionPlan): ReasoningPromotionResult
}

class ReasoningPromotionService(
    private val builder: ReasoningModelBuilder,
    private val validationGate: ReasoningValidationGate,
    private val graphStore: NamedGraphStore,
) : ReasoningRefresher {
    override fun run(plan: ReasoningPromotionPlan): ReasoningPromotionResult {
        val canonicalSnapshot = graphStore.readNamedGraph(plan.inputGraphs.canonicalGraphUri)
        if (!canonicalSnapshot.exists || canonicalSnapshot.model.isEmpty) {
            return ReasoningPromotionResult(
                promoted = false,
                validation = ReasoningValidationReport(conforms = false, tripleCount = 0, errors = listOf("Canonical graph is missing or empty")),
                errors = listOf("Canonical graph is missing or empty: ${plan.inputGraphs.canonicalGraphUri}"),
            )
        }
        val provenanceSnapshot = graphStore.readNamedGraph(plan.inputGraphs.provenanceGraphUri)

        val output = builder.build(
            ReasoningInput(
                runId = plan.runId,
                generatedAt = plan.generatedAt,
                canonicalModel = canonicalSnapshot.copyModel(),
                provenanceModel = provenanceSnapshot.copyModel(),
            ),
        )
        val validation = validationGate.validate(output.auditModel)
        if (!validation.conforms) {
            return ReasoningPromotionResult(
                promoted = false,
                validation = validation,
                findingCount = output.findingCount,
                errors = validation.errors,
            )
        }

        val graphModels = plan.outputGraphs.models(output)
        val snapshots = runCatching {
            graphModels.keys.associateWith { graphUri -> graphStore.readNamedGraph(graphUri) }
        }.getOrElse { error ->
            return ReasoningPromotionResult(
                promoted = false,
                validation = validation,
                findingCount = output.findingCount,
                errors = listOf("Reasoning graph snapshot failed before promotion: ${error.message}"),
            )
        }

        val writtenGraphs = mutableListOf<String>()
        return runCatching {
            graphModels.forEach { (graphUri, model) ->
                graphStore.replaceNamedGraph(graphUri, model)
                writtenGraphs += graphUri
            }
            ReasoningPromotionResult(
                promoted = true,
                validation = validation,
                findingCount = output.findingCount,
                writtenGraphUris = writtenGraphs.toList(),
                releaseManifest = ReasoningReleaseManifest.from(plan, output.findingCount),
            )
        }.getOrElse { error ->
            val rollbackErrors = rollback(writtenGraphs.asReversed(), snapshots)
            ReasoningPromotionResult(
                promoted = false,
                validation = validation,
                findingCount = output.findingCount,
                writtenGraphUris = writtenGraphs.toList(),
                rollbackAttempted = true,
                rollbackSucceeded = rollbackErrors.isEmpty(),
                errors = listOf("Reasoning promotion write failed: ${error.message}") + rollbackErrors,
            )
        }
    }

    private fun rollback(
        writtenGraphs: List<String>,
        snapshots: Map<String, NamedGraphSnapshot>,
    ): List<String> {
        return writtenGraphs.mapNotNull { graphUri ->
            val snapshot = snapshots.getValue(graphUri)
            runCatching {
                if (snapshot.exists) {
                    graphStore.replaceNamedGraph(graphUri, snapshot.copyModel())
                } else {
                    graphStore.deleteNamedGraph(graphUri)
                }
            }.exceptionOrNull()?.let { error ->
                "Reasoning rollback failed for $graphUri: ${error.message}"
            }
        }
    }
}

data class ReasoningPromotionPlan(
    val runId: String,
    val generatedAt: Instant,
    val inputGraphs: ReasoningInputGraphUris,
    val outputGraphs: ReasoningOutputGraphUris,
) {
    init {
        require(runId.matches(Regex("[A-Za-z0-9._-]+"))) {
            "runId must contain only letters, numbers, dot, underscore, or hyphen"
        }
    }
}

data class ReasoningInputGraphUris(
    val canonicalGraphUri: String,
    val provenanceGraphUri: String,
) {
    init {
        require(canonicalGraphUri.startsWith(CANONICAL_PREFIX) && canonicalGraphUri.length > CANONICAL_PREFIX.length) {
            "canonicalGraphUri must use $CANONICAL_PREFIX with a release-specific suffix"
        }
        require(provenanceGraphUri.startsWith(PROVENANCE_PREFIX) && provenanceGraphUri.length > PROVENANCE_PREFIX.length) {
            "provenanceGraphUri must use $PROVENANCE_PREFIX with a release-specific suffix"
        }
    }

    companion object {
        const val CANONICAL_PREFIX = "urn:dcai:graph:canonical:"
        const val PROVENANCE_PREFIX = "urn:dcai:graph:provenance:"

        fun forRelease(releaseId: String): ReasoningInputGraphUris {
            require(releaseId.matches(Regex("[A-Za-z0-9._-]+"))) {
                "releaseId must contain only letters, numbers, dot, underscore, or hyphen"
            }
            return ReasoningInputGraphUris(
                canonicalGraphUri = "$CANONICAL_PREFIX$releaseId",
                provenanceGraphUri = "$PROVENANCE_PREFIX$releaseId",
            )
        }
    }
}

data class ReasoningOutputGraphUris(
    val auditGraphUri: String,
    val reasoningGraphUri: String,
) {
    init {
        require(auditGraphUri.startsWith(AUDIT_PREFIX) && auditGraphUri.length > AUDIT_PREFIX.length) {
            "auditGraphUri must use $AUDIT_PREFIX with a run-specific suffix"
        }
        require(reasoningGraphUri.startsWith(REASONING_PREFIX) && reasoningGraphUri.length > REASONING_PREFIX.length) {
            "reasoningGraphUri must use $REASONING_PREFIX with a run-specific suffix"
        }
    }

    fun models(output: ReasoningOutput): LinkedHashMap<String, Model> {
        return linkedMapOf(
            auditGraphUri to output.auditModel,
            reasoningGraphUri to output.reasoningModel,
        )
    }

    companion object {
        const val AUDIT_PREFIX = "urn:dcai:graph:reasoning-audit:"
        const val REASONING_PREFIX = "urn:dcai:graph:reasoning:"

        fun forRun(runId: String): ReasoningOutputGraphUris {
            require(runId.matches(Regex("[A-Za-z0-9._-]+"))) {
                "runId must contain only letters, numbers, dot, underscore, or hyphen"
            }
            return ReasoningOutputGraphUris(
                auditGraphUri = "$AUDIT_PREFIX$runId",
                reasoningGraphUri = "$REASONING_PREFIX$runId",
            )
        }
    }
}

data class ReasoningPromotionResult(
    val promoted: Boolean,
    val validation: ReasoningValidationReport,
    val findingCount: Int = 0,
    val writtenGraphUris: List<String> = emptyList(),
    val rollbackAttempted: Boolean = false,
    val rollbackSucceeded: Boolean = false,
    val releaseManifest: ReasoningReleaseManifest? = null,
    val errors: List<String> = emptyList(),
)

data class ReasoningReleaseManifest(
    val runId: String,
    val canonicalGraphUri: String,
    val provenanceGraphUri: String,
    val auditGraphUri: String,
    val reasoningGraphUri: String,
    val findingCount: Int,
) {
    companion object {
        fun from(plan: ReasoningPromotionPlan, findingCount: Int): ReasoningReleaseManifest {
            return ReasoningReleaseManifest(
                runId = plan.runId,
                canonicalGraphUri = plan.inputGraphs.canonicalGraphUri,
                provenanceGraphUri = plan.inputGraphs.provenanceGraphUri,
                auditGraphUri = plan.outputGraphs.auditGraphUri,
                reasoningGraphUri = plan.outputGraphs.reasoningGraphUri,
                findingCount = findingCount,
            )
        }
    }
}
