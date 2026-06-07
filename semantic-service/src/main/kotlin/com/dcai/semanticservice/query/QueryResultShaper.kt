package com.dcai.semanticservice.query

class QueryResultShaper(
    private val manifest: ApprovedQueryManifest,
) {
    fun shape(report: QueryExecutionReport): QueryResultEnvelope {
        val definition = manifest.requireQuery(report.queryId)
        require(report.mode == definition.mode) {
            "Query result mode mismatch for ${report.queryId}: report=${report.mode.value}, manifest=${definition.mode.value}"
        }
        require(report.mode == QueryMode.SELECT) {
            "Query result envelopes are only defined for SELECT results: ${report.queryId}"
        }
        return when (report.queryId) {
            "fixtureNamedGraphInventory" -> shapeNamedGraphInventory(report, definition)
            "fixtureIncidentSummary" -> shapeIncidentSummary(report, definition)
            "fixtureProvenanceSourceRecords" -> shapeProvenanceSourceRecords(report, definition)
            "semanticFollowUpQueueList" -> shapeFollowUpQueue(report, definition)
            else -> error("No result envelope contract for query id: ${report.queryId}")
        }
    }

    private fun shapeNamedGraphInventory(
        report: QueryExecutionReport,
        definition: ApprovedQueryDefinition,
    ): NamedGraphInventoryEnvelope {
        return NamedGraphInventoryEnvelope(
            queryId = report.queryId,
            records = report.rows.map { row ->
                NamedGraphInventoryRecord(
                    graphUri = row.required("graph"),
                    subjectCount = row.required("subjectCount").toInt(),
                )
            },
            provenance = provenance(definition),
        )
    }

    private fun shapeIncidentSummary(
        report: QueryExecutionReport,
        definition: ApprovedQueryDefinition,
    ): IncidentSummaryEnvelope {
        return IncidentSummaryEnvelope(
            queryId = report.queryId,
            records = report.rows.map { row ->
                IncidentSummaryRecord(
                    graphUri = row.required("graph"),
                    incidentUri = row.required("incident"),
                    incidentId = row.required("incidentId"),
                    assetUri = row.required("asset"),
                    stageUri = row.required("stage"),
                    sourceRecordUri = row.optional("sourceRecord"),
                )
            },
            provenance = provenance(definition),
        )
    }

    private fun shapeProvenanceSourceRecords(
        report: QueryExecutionReport,
        definition: ApprovedQueryDefinition,
    ): ProvenanceSourceRecordsEnvelope {
        return ProvenanceSourceRecordsEnvelope(
            queryId = report.queryId,
            records = report.rows.map { row ->
                ProvenanceSourceRecord(
                    graphUri = row.required("graph"),
                    sourceRecordUri = row.required("sourceRecord"),
                    sourceRecordId = row.required("sourceRecordId"),
                    sourceSystemUri = row.required("sourceSystem"),
                    payloadHash = row.required("payloadHash"),
                    activityUri = row.required("activity"),
                )
            },
            provenance = provenance(definition),
        )
    }

    private fun shapeFollowUpQueue(
        report: QueryExecutionReport,
        definition: ApprovedQueryDefinition,
    ): FollowUpQueueEnvelope {
        return FollowUpQueueEnvelope(
            queryId = report.queryId,
            records = report.rows.map { row ->
                FollowUpQueueRecord(
                    graphUri = row.required("graph"),
                    incidentUri = row.required("incident"),
                    incidentId = row.required("incidentId"),
                    assetUri = row.required("asset"),
                    assetId = row.required("assetId"),
                    zoneUri = row.required("zone"),
                    zoneId = row.required("zoneId"),
                    stageUri = row.required("stage"),
                    stageLabel = row.optional("stageLabel"),
                    sourceRecordUri = row.required("sourceRecord"),
                )
            },
            provenance = provenance(definition),
        )
    }

    private fun provenance(definition: ApprovedQueryDefinition): QueryResultEnvelopeProvenance {
        return QueryResultEnvelopeProvenance(
            queryId = definition.id,
            graphScope = definition.graphScope,
        )
    }

    private fun Map<String, String>.required(key: String): String {
        val value = this[key]
        require(!value.isNullOrBlank()) { "Missing required binding '$key'" }
        return value
    }

    private fun Map<String, String>.optional(key: String): String? {
        return this[key]?.takeIf { it.isNotBlank() }
    }
}
