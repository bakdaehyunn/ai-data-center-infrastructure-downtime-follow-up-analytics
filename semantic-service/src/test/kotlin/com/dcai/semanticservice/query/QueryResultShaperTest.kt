package com.dcai.semanticservice.query

import java.nio.file.Path
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertIs

class QueryResultShaperTest {
    private val manifest = ApprovedQueryManifest(
        entries = mapOf(
            "fixtureNamedGraphInventory" to definition("fixtureNamedGraphInventory", "fixture source graph, fixture canonical graph"),
            "fixtureIncidentSummary" to definition("fixtureIncidentSummary", "fixture canonical graph"),
            "fixtureProvenanceSourceRecords" to definition("fixtureProvenanceSourceRecords", "fixture source graph, fixture canonical graph"),
            "semanticFollowUpQueueList" to definition("semanticFollowUpQueueList", "fixture canonical graph"),
        ),
    )
    private val shaper = QueryResultShaper(manifest)

    @Test
    fun shapesNamedGraphInventoryRows() {
        val envelope = shaper.shape(
            QueryExecutionReport(
                queryId = "fixtureNamedGraphInventory",
                mode = QueryMode.SELECT,
                rowCount = 1,
                rows = listOf(
                    mapOf(
                        "graph" to "urn:dcai:graph:fixture:canonical:minimal-incident",
                        "subjectCount" to "8",
                    ),
                ),
            ),
        )

        val typed = assertIs<NamedGraphInventoryEnvelope>(envelope)
        assertEquals(QueryResultType.NAMED_GRAPH_INVENTORY, typed.resultType)
        assertEquals(1, typed.recordCount)
        assertEquals(8, typed.records.single().subjectCount)
        assertEquals(QueryResultEnvelopeProvenance.CONTRACT_VERSION, typed.provenance.contractVersion)
    }

    @Test
    fun shapesIncidentSummaryRows() {
        val envelope = shaper.shape(
            QueryExecutionReport(
                queryId = "fixtureIncidentSummary",
                mode = QueryMode.SELECT,
                rowCount = 1,
                rows = listOf(
                    mapOf(
                        "graph" to "urn:dcai:graph:fixture:canonical:minimal-incident",
                        "incident" to "urn:dcai:fixture:valid:minimal-incident:inc-0001",
                        "incidentId" to "INC-0001",
                        "asset" to "urn:dcai:fixture:valid:minimal-incident:gpu-rack-row-a",
                        "stage" to "urn:dcai:fixture:valid:minimal-incident:stage-validation",
                        "sourceRecord" to "urn:dcai:fixture:valid:minimal-incident:source-record-inc-0001",
                    ),
                ),
            ),
        )

        val typed = assertIs<IncidentSummaryEnvelope>(envelope)
        assertEquals(QueryResultType.INCIDENT_SUMMARY, typed.resultType)
        assertEquals("INC-0001", typed.records.single().incidentId)
        assertEquals("fixture canonical graph", typed.provenance.graphScope)
    }

    @Test
    fun shapesProvenanceSourceRecordRows() {
        val envelope = shaper.shape(
            QueryExecutionReport(
                queryId = "fixtureProvenanceSourceRecords",
                mode = QueryMode.SELECT,
                rowCount = 1,
                rows = listOf(
                    mapOf(
                        "graph" to "urn:dcai:graph:fixture:source:minimal-incident",
                        "sourceRecord" to "urn:dcai:fixture:valid:minimal-incident:source-record-inc-0001",
                        "sourceRecordId" to "SRC-INC-0001",
                        "sourceSystem" to "urn:dcai:fixture:valid:minimal-incident:facility-ops",
                        "payloadHash" to "sha256:phase3-minimal-incident",
                        "activity" to "urn:dcai:fixture:valid:minimal-incident:import-activity-0001",
                    ),
                ),
            ),
        )

        val typed = assertIs<ProvenanceSourceRecordsEnvelope>(envelope)
        assertEquals(QueryResultType.PROVENANCE_SOURCE_RECORDS, typed.resultType)
        assertEquals("SRC-INC-0001", typed.records.single().sourceRecordId)
    }

    @Test
    fun shapesFollowUpQueueRows() {
        val envelope = shaper.shape(
            QueryExecutionReport(
                queryId = "semanticFollowUpQueueList",
                mode = QueryMode.SELECT,
                rowCount = 1,
                rows = listOf(followUpQueueRow()),
            ),
        )

        val typed = assertIs<FollowUpQueueEnvelope>(envelope)
        val record = typed.records.single()
        assertEquals(QueryResultType.FOLLOW_UP_QUEUE, typed.resultType)
        assertEquals("INC-0001", record.incidentId)
        assertEquals("ASSET-GPU-RACK-ROW-A", record.assetId)
        assertEquals("ZONE-A", record.zoneId)
        assertEquals("Validation", record.stageLabel)
        assertEquals("urn:dcai:fixture:valid:minimal-incident:source-record-inc-0001", record.sourceRecordUri)
        assertEquals("fixture canonical graph", typed.provenance.graphScope)
    }

    @Test
    fun rejectsUnsupportedEnvelopeQueryId() {
        val unsupportedManifest = ApprovedQueryManifest(
            entries = mapOf(
                "unsupported" to definition("unsupported", "fixture graph"),
            ),
        )

        assertFailsWith<IllegalStateException> {
            QueryResultShaper(unsupportedManifest).shape(
                QueryExecutionReport(
                    queryId = "unsupported",
                    mode = QueryMode.SELECT,
                ),
            )
        }
    }

    @Test
    fun rejectsModeMismatchBetweenReportAndManifest() {
        assertFailsWith<IllegalArgumentException> {
            shaper.shape(
                QueryExecutionReport(
                    queryId = "fixtureNamedGraphInventory",
                    mode = QueryMode.ASK,
                ),
            )
        }
    }

    @Test
    fun rejectsMissingRequiredBindings() {
        assertFailsWith<IllegalArgumentException> {
            shaper.shape(
                QueryExecutionReport(
                    queryId = "fixtureNamedGraphInventory",
                    mode = QueryMode.SELECT,
                    rows = listOf(mapOf("graph" to "urn:dcai:graph:fixture:source:minimal-incident")),
                ),
            )
        }
    }

    @Test
    fun rejectsFollowUpQueueRowsMissingProvenanceCarryingIdentifiers() {
        assertFailsWith<IllegalArgumentException> {
            shaper.shape(
                QueryExecutionReport(
                    queryId = "semanticFollowUpQueueList",
                    mode = QueryMode.SELECT,
                    rows = listOf(
                        followUpQueueRow() - "incidentId",
                    ),
                ),
            )
        }
    }

    @Test
    fun rejectsFollowUpQueueRowsMissingSourceRecordProvenance() {
        assertFailsWith<IllegalArgumentException> {
            shaper.shape(
                QueryExecutionReport(
                    queryId = "semanticFollowUpQueueList",
                    mode = QueryMode.SELECT,
                    rows = listOf(
                        followUpQueueRow() - "sourceRecord",
                    ),
                ),
            )
        }
    }

    private fun followUpQueueRow(): Map<String, String> {
        return mapOf(
            "graph" to "urn:dcai:graph:fixture:canonical:minimal-incident",
            "incident" to "urn:dcai:fixture:valid:minimal-incident:inc-0001",
            "incidentId" to "INC-0001",
            "asset" to "urn:dcai:fixture:valid:minimal-incident:gpu-rack-row-a",
            "assetId" to "ASSET-GPU-RACK-ROW-A",
            "zone" to "urn:dcai:fixture:valid:minimal-incident:zone-a",
            "zoneId" to "ZONE-A",
            "stage" to "urn:dcai:fixture:valid:minimal-incident:stage-validation",
            "stageLabel" to "Validation",
            "sourceRecord" to "urn:dcai:fixture:valid:minimal-incident:source-record-inc-0001",
        )
    }

    private fun definition(
        id: String,
        graphScope: String,
    ): ApprovedQueryDefinition {
        return ApprovedQueryDefinition(
            id = id,
            path = Path.of("queries/inspection/$id.select.rq"),
            mode = QueryMode.SELECT,
            graphScope = graphScope,
            sparql = "SELECT * WHERE { ?s ?p ?o }",
        )
    }
}
