package com.dcai.semanticservice.response

import com.dcai.semanticservice.query.IncidentSummaryEnvelope
import com.dcai.semanticservice.query.IncidentSummaryRecord
import com.dcai.semanticservice.query.NamedGraphInventoryEnvelope
import com.dcai.semanticservice.query.NamedGraphInventoryRecord
import com.dcai.semanticservice.query.ProvenanceSourceRecord
import com.dcai.semanticservice.query.ProvenanceSourceRecordsEnvelope
import com.dcai.semanticservice.query.QueryResultEnvelopeProvenance
import kotlin.test.Test
import kotlin.test.assertEquals

class SemanticResponseSerializerTest {
    private val serializer = SemanticResponseSerializer()

    @Test
    fun serializesNamedGraphInventoryEnvelope() {
        val payload = serializer.serialize(
            NamedGraphInventoryEnvelope(
                queryId = "fixtureNamedGraphInventory",
                records = listOf(
                    NamedGraphInventoryRecord(
                        graphUri = "urn:dcai:graph:fixture:canonical:minimal-incident",
                        subjectCount = 8,
                    ),
                ),
                provenance = provenance("fixtureNamedGraphInventory"),
            ),
        )

        assertEquals(setOf("queryId", "resultType", "recordCount", "records", "provenance"), payload.keys)
        assertEquals("fixtureNamedGraphInventory", payload["queryId"])
        assertEquals("named-graph-inventory", payload["resultType"])
        assertEquals(1, payload["recordCount"])
        assertEquals(
            listOf(
                mapOf(
                    "graphUri" to "urn:dcai:graph:fixture:canonical:minimal-incident",
                    "subjectCount" to 8,
                ),
            ),
            payload["records"],
        )
        assertEquals(provenancePayload("fixtureNamedGraphInventory"), payload["provenance"])
    }

    @Test
    fun serializesIncidentSummaryEnvelopeWithoutNullOptionalFields() {
        val payload = serializer.serialize(
            IncidentSummaryEnvelope(
                queryId = "fixtureIncidentSummary",
                records = listOf(
                    IncidentSummaryRecord(
                        graphUri = "urn:dcai:graph:fixture:canonical:minimal-incident",
                        incidentUri = "urn:dcai:fixture:valid:minimal-incident:inc-0001",
                        incidentId = "INC-0001",
                        assetUri = "urn:dcai:fixture:valid:minimal-incident:gpu-rack-row-a",
                        stageUri = "urn:dcai:fixture:valid:minimal-incident:stage-validation",
                        sourceRecordUri = null,
                    ),
                ),
                provenance = provenance("fixtureIncidentSummary"),
            ),
        )

        assertEquals("incident-summary", payload["resultType"])
        assertEquals(1, payload["recordCount"])
        assertEquals(
            listOf(
                mapOf(
                    "graphUri" to "urn:dcai:graph:fixture:canonical:minimal-incident",
                    "incidentUri" to "urn:dcai:fixture:valid:minimal-incident:inc-0001",
                    "incidentId" to "INC-0001",
                    "assetUri" to "urn:dcai:fixture:valid:minimal-incident:gpu-rack-row-a",
                    "stageUri" to "urn:dcai:fixture:valid:minimal-incident:stage-validation",
                ),
            ),
            payload["records"],
        )
    }

    @Test
    fun serializesProvenanceSourceRecordsEnvelope() {
        val payload = serializer.serialize(
            ProvenanceSourceRecordsEnvelope(
                queryId = "fixtureProvenanceSourceRecords",
                records = listOf(
                    ProvenanceSourceRecord(
                        graphUri = "urn:dcai:graph:fixture:source:minimal-incident",
                        sourceRecordUri = "urn:dcai:fixture:valid:minimal-incident:source-record-inc-0001",
                        sourceRecordId = "SRC-INC-0001",
                        sourceSystemUri = "urn:dcai:fixture:valid:minimal-incident:facility-ops",
                        payloadHash = "sha256:phase3-minimal-incident",
                        activityUri = "urn:dcai:fixture:valid:minimal-incident:import-activity-0001",
                    ),
                ),
                provenance = provenance("fixtureProvenanceSourceRecords"),
            ),
        )

        assertEquals("provenance-source-records", payload["resultType"])
        assertEquals(
            listOf(
                mapOf(
                    "graphUri" to "urn:dcai:graph:fixture:source:minimal-incident",
                    "sourceRecordUri" to "urn:dcai:fixture:valid:minimal-incident:source-record-inc-0001",
                    "sourceRecordId" to "SRC-INC-0001",
                    "sourceSystemUri" to "urn:dcai:fixture:valid:minimal-incident:facility-ops",
                    "payloadHash" to "sha256:phase3-minimal-incident",
                    "activityUri" to "urn:dcai:fixture:valid:minimal-incident:import-activity-0001",
                ),
            ),
            payload["records"],
        )
    }

    @Test
    fun serializesSemanticErrorEnvelope() {
        val payload = serializer.error(
            code = SemanticErrorCode.UNAPPROVED_QUERY_ID,
            message = "Query id is not approved.",
            detail = "queries/manifest.ttl has no matching entry.",
            queryId = "unknownQuery",
        )

        assertEquals(setOf("error"), payload.keys)
        assertEquals(
            mapOf(
                "code" to "unapproved-query-id",
                "message" to "Query id is not approved.",
                "detail" to "queries/manifest.ttl has no matching entry.",
                "queryId" to "unknownQuery",
                "contractVersion" to SemanticErrorContract.VERSION,
            ),
            payload["error"],
        )
    }

    @Test
    fun semanticErrorCodesMatchPhaseEighteenContractNames() {
        assertEquals(
            setOf(
                "unapproved-query-id",
                "unsupported-result-envelope",
                "missing-required-binding",
                "graph-unavailable",
                "contract-validation-failed",
                "internal-semantic-service-error",
            ),
            SemanticErrorCode.entries.map { it.value }.toSet(),
        )
    }

    private fun provenance(queryId: String): QueryResultEnvelopeProvenance {
        return QueryResultEnvelopeProvenance(
            queryId = queryId,
            graphScope = "fixture canonical graph",
        )
    }

    private fun provenancePayload(queryId: String): Map<String, String> {
        return mapOf(
            "queryId" to queryId,
            "graphScope" to "fixture canonical graph",
            "contractVersion" to QueryResultEnvelopeProvenance.CONTRACT_VERSION,
        )
    }
}
