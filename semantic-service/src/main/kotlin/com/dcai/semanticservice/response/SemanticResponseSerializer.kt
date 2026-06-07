package com.dcai.semanticservice.response

import com.dcai.semanticservice.query.IncidentSummaryEnvelope
import com.dcai.semanticservice.query.FollowUpQueueEnvelope
import com.dcai.semanticservice.query.NamedGraphInventoryEnvelope
import com.dcai.semanticservice.query.ProvenanceSourceRecordsEnvelope
import com.dcai.semanticservice.query.QueryResultEnvelope
import com.dcai.semanticservice.query.QueryResultEnvelopeProvenance

class SemanticResponseSerializer {
    fun serialize(envelope: QueryResultEnvelope): Map<String, Any> {
        val records = when (envelope) {
            is NamedGraphInventoryEnvelope -> envelope.records.map { record ->
                mapOf(
                    "graphUri" to record.graphUri,
                    "subjectCount" to record.subjectCount,
                )
            }
            is IncidentSummaryEnvelope -> envelope.records.map { record ->
                buildMap {
                    put("graphUri", record.graphUri)
                    put("incidentUri", record.incidentUri)
                    put("incidentId", record.incidentId)
                    put("assetUri", record.assetUri)
                    put("stageUri", record.stageUri)
                    record.sourceRecordUri?.let { put("sourceRecordUri", it) }
                }
            }
            is ProvenanceSourceRecordsEnvelope -> envelope.records.map { record ->
                mapOf(
                    "graphUri" to record.graphUri,
                    "sourceRecordUri" to record.sourceRecordUri,
                    "sourceRecordId" to record.sourceRecordId,
                    "sourceSystemUri" to record.sourceSystemUri,
                    "payloadHash" to record.payloadHash,
                    "activityUri" to record.activityUri,
                )
            }
            is FollowUpQueueEnvelope -> envelope.records.map { record ->
                buildMap {
                    put("graphUri", record.graphUri)
                    put("incidentUri", record.incidentUri)
                    put("incidentId", record.incidentId)
                    put("assetUri", record.assetUri)
                    put("assetId", record.assetId)
                    put("zoneUri", record.zoneUri)
                    put("zoneId", record.zoneId)
                    put("stageUri", record.stageUri)
                    record.stageLabel?.let { put("stageLabel", it) }
                    put("sourceRecordUri", record.sourceRecordUri)
                }
            }
        }

        return mapOf(
            "queryId" to envelope.queryId,
            "resultType" to envelope.resultType.value,
            "recordCount" to envelope.recordCount,
            "records" to records,
            "provenance" to envelope.provenance.toPayload(),
        )
    }

    fun error(
        code: SemanticErrorCode,
        message: String,
        detail: String? = null,
        queryId: String? = null,
    ): Map<String, Any> {
        val error = buildMap {
            put("code", code.value)
            put("message", message)
            detail?.let { put("detail", it) }
            queryId?.let { put("queryId", it) }
            put("contractVersion", SemanticErrorContract.VERSION)
        }

        return mapOf("error" to error)
    }

    private fun QueryResultEnvelopeProvenance.toPayload(): Map<String, String> {
        return mapOf(
            "queryId" to queryId,
            "graphScope" to graphScope,
            "contractVersion" to contractVersion,
        )
    }
}

enum class SemanticErrorCode(
    val value: String,
) {
    UNAPPROVED_QUERY_ID("unapproved-query-id"),
    UNSUPPORTED_RESULT_ENVELOPE("unsupported-result-envelope"),
    MISSING_REQUIRED_BINDING("missing-required-binding"),
    GRAPH_UNAVAILABLE("graph-unavailable"),
    CONTRACT_VALIDATION_FAILED("contract-validation-failed"),
    INTERNAL_SEMANTIC_SERVICE_ERROR("internal-semantic-service-error"),
}

object SemanticErrorContract {
    const val VERSION = "2026.06.phase18-error-envelope"
}
