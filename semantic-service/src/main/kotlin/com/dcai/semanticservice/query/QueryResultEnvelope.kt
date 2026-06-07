package com.dcai.semanticservice.query

sealed interface QueryResultEnvelope {
    val queryId: String
    val resultType: QueryResultType
    val recordCount: Int
    val provenance: QueryResultEnvelopeProvenance
}

data class QueryResultEnvelopeProvenance(
    val queryId: String,
    val graphScope: String,
    val contractVersion: String = CONTRACT_VERSION,
) {
    companion object {
        const val CONTRACT_VERSION = "2026.06.phase17-result-envelope"
    }
}

enum class QueryResultType(
    val value: String,
) {
    NAMED_GRAPH_INVENTORY("named-graph-inventory"),
    INCIDENT_SUMMARY("incident-summary"),
    PROVENANCE_SOURCE_RECORDS("provenance-source-records"),
}

data class NamedGraphInventoryEnvelope(
    override val queryId: String,
    val records: List<NamedGraphInventoryRecord>,
    override val provenance: QueryResultEnvelopeProvenance,
) : QueryResultEnvelope {
    override val resultType: QueryResultType = QueryResultType.NAMED_GRAPH_INVENTORY
    override val recordCount: Int = records.size
}

data class NamedGraphInventoryRecord(
    val graphUri: String,
    val subjectCount: Int,
)

data class IncidentSummaryEnvelope(
    override val queryId: String,
    val records: List<IncidentSummaryRecord>,
    override val provenance: QueryResultEnvelopeProvenance,
) : QueryResultEnvelope {
    override val resultType: QueryResultType = QueryResultType.INCIDENT_SUMMARY
    override val recordCount: Int = records.size
}

data class IncidentSummaryRecord(
    val graphUri: String,
    val incidentUri: String,
    val incidentId: String,
    val assetUri: String,
    val stageUri: String,
    val sourceRecordUri: String? = null,
)

data class ProvenanceSourceRecordsEnvelope(
    override val queryId: String,
    val records: List<ProvenanceSourceRecord>,
    override val provenance: QueryResultEnvelopeProvenance,
) : QueryResultEnvelope {
    override val resultType: QueryResultType = QueryResultType.PROVENANCE_SOURCE_RECORDS
    override val recordCount: Int = records.size
}

data class ProvenanceSourceRecord(
    val graphUri: String,
    val sourceRecordUri: String,
    val sourceRecordId: String,
    val sourceSystemUri: String,
    val payloadHash: String,
    val activityUri: String,
)
