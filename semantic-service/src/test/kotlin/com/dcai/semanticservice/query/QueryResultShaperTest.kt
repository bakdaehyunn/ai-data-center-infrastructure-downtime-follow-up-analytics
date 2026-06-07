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
            "semanticDashboardOverview" to definition("semanticDashboardOverview", "fixture canonical graph"),
            "semanticFilterMetadata" to definition("semanticFilterMetadata", "fixture canonical graph"),
            "semanticFollowUpDetail" to definition("semanticFollowUpDetail", "fixture canonical graph"),
            "semanticImpactSummary" to definition("semanticImpactSummary", "fixture canonical graph"),
            "semanticTopologyDependencies" to definition("semanticTopologyDependencies", "fixture canonical graph"),
            "semanticTrustFindingList" to definition("semanticTrustFindingList", "fixture canonical graph"),
            "semanticStageBottlenecks" to definition("semanticStageBottlenecks", "fixture canonical graph"),
            "semanticAssetDelaySummary" to definition("semanticAssetDelaySummary", "fixture canonical graph"),
            "semanticZoneDelaySummary" to definition("semanticZoneDelaySummary", "fixture canonical graph"),
            "semanticSpareWaitSummary" to definition("semanticSpareWaitSummary", "fixture canonical graph"),
            "semanticValidationSummary" to definition("semanticValidationSummary", "fixture canonical graph"),
            "semanticIncidentEvidence" to definition("semanticIncidentEvidence", "fixture canonical graph"),
            "semanticIncidentTimeline" to definition("semanticIncidentTimeline", "fixture canonical graph"),
            "semanticDependencyImpactByAsset" to definition("semanticDependencyImpactByAsset", "fixture canonical graph"),
            "semanticBlastRadiusByAsset" to definition("semanticBlastRadiusByAsset", "fixture canonical graph"),
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
        assertEquals(1, record.priorityRank)
        assertEquals(63.0, record.hoursInCurrentStage)
        assertEquals("CRITICAL", record.priorityLevel)
        assertEquals(169.0, record.totalPriorityScore)
        assertEquals("fixture canonical graph", typed.provenance.graphScope)
    }

    @Test
    fun shapesDashboardOverviewRows() {
        val envelope = shaper.shape(
            QueryExecutionReport(
                queryId = "semanticDashboardOverview",
                mode = QueryMode.SELECT,
                rows = listOf(
                    mapOf(
                        "graph" to "urn:dcai:graph:fixture:canonical:minimal-incident",
                        "totalIncidents" to "2",
                        "assetCount" to "3",
                        "zoneCount" to "1",
                        "impactObservationCount" to "1",
                        "capacityRiskKw" to "900.0",
                        "affectedGpuCount" to "320",
                        "dependencyEdgeCount" to "1",
                        "trustFindingCount" to "1",
                    ),
                ),
            ),
        )

        val typed = assertIs<DashboardOverviewEnvelope>(envelope)
        assertEquals(QueryResultType.DASHBOARD_OVERVIEW, typed.resultType)
        assertEquals(900.0, typed.records.single().capacityRiskKw)
        assertEquals(320, typed.records.single().affectedGpuCount)
    }

    @Test
    fun shapesFilterMetadataRows() {
        val envelope = shaper.shape(
            QueryExecutionReport(
                queryId = "semanticFilterMetadata",
                mode = QueryMode.SELECT,
                rows = listOf(
                    mapOf(
                        "graph" to "urn:dcai:graph:fixture:canonical:minimal-incident",
                        "filterType" to "asset",
                        "resource" to "urn:dcai:fixture:valid:minimal-incident:gpu-rack-row-a",
                        "id" to "ASSET-GPU-RACK-ROW-A",
                        "label" to "GPU Rack Sensor Row A",
                        "sourceRecord" to "urn:dcai:fixture:valid:minimal-incident:source-record-inc-0001",
                    ),
                ),
            ),
        )

        val typed = assertIs<FilterMetadataEnvelope>(envelope)
        assertEquals(QueryResultType.FILTER_METADATA, typed.resultType)
        assertEquals("asset", typed.records.single().filterType)
    }

    @Test
    fun shapesFollowUpDetailRows() {
        val envelope = shaper.shape(
            QueryExecutionReport(
                queryId = "semanticFollowUpDetail",
                mode = QueryMode.SELECT,
                rows = listOf(followUpDetailRow()),
            ),
        )

        val typed = assertIs<FollowUpDetailEnvelope>(envelope)
        val record = typed.records.single()
        assertEquals(QueryResultType.FOLLOW_UP_DETAIL, typed.resultType)
        assertEquals("INC-0001", record.incidentId)
        assertEquals(900.0, record.capacityRiskKw)
        assertEquals("Escalate vendor ETA.", record.recommendedAction)
        assertEquals("N-1", record.redundancyState)
        assertEquals(40, record.affectedRackCount)
        assertEquals(true, record.powerRedundancyLost)
        assertEquals("ETA_MISSED", record.vendorStatus)
    }

    @Test
    fun shapesImpactSummaryRows() {
        val envelope = shaper.shape(
            QueryExecutionReport(
                queryId = "semanticImpactSummary",
                mode = QueryMode.SELECT,
                rows = listOf(
                    mapOf(
                        "graph" to "urn:dcai:graph:fixture:canonical:reasoning-output",
                        "impactObservationCount" to "1",
                        "incidentCount" to "1",
                        "capacityRiskKw" to "900.0",
                        "affectedGpuCount" to "320",
                        "trustFindingCount" to "1",
                    ),
                ),
            ),
        )

        val typed = assertIs<ImpactSummaryEnvelope>(envelope)
        assertEquals(QueryResultType.IMPACT_SUMMARY, typed.resultType)
        assertEquals(1, typed.records.single().trustFindingCount)
    }

    @Test
    fun shapesTopologyDependencyRows() {
        val envelope = shaper.shape(
            QueryExecutionReport(
                queryId = "semanticTopologyDependencies",
                mode = QueryMode.SELECT,
                rows = listOf(topologyDependencyRow()),
            ),
        )

        val typed = assertIs<TopologyDependenciesEnvelope>(envelope)
        val record = typed.records.single()
        assertEquals(QueryResultType.TOPOLOGY_DEPENDENCIES, typed.resultType)
        assertEquals("POWER_SUPPLY", record.dependencyRole)
        assertEquals("SRC-TOPO", record.sourceRecordUri.substringAfterLast(":"))
    }

    @Test
    fun shapesTrustFindingRows() {
        val envelope = shaper.shape(
            QueryExecutionReport(
                queryId = "semanticTrustFindingList",
                mode = QueryMode.SELECT,
                rows = listOf(
                    mapOf(
                        "graph" to "urn:dcai:graph:fixture:canonical:reasoning-output",
                        "trustFinding" to "urn:dcai:fixture:valid:reasoning-output:trust-finding-0001",
                        "summary" to "Impact evidence is supported by telemetry.",
                        "sourceFact" to "urn:dcai:fixture:valid:reasoning-output:impact-0001",
                        "activity" to "urn:dcai:fixture:valid:reasoning-output:reasoning-activity-0001",
                    ),
                ),
            ),
        )

        val typed = assertIs<TrustFindingsEnvelope>(envelope)
        assertEquals(QueryResultType.TRUST_FINDINGS, typed.resultType)
        assertEquals("Impact evidence is supported by telemetry.", typed.records.single().summary)
    }

    @Test
    fun shapesIncidentEvidenceDetailRows() {
        val envelope = shaper.shape(
            QueryExecutionReport(
                queryId = "semanticIncidentEvidence",
                mode = QueryMode.SELECT,
                rows = listOf(
                    mapOf(
                        "graph" to "urn:dcai:graph:fixture:canonical:reasoning-output",
                        "incident" to "urn:dcai:fixture:valid:reasoning-output:incident-0001",
                        "incidentId" to "INC-REASONING-0001",
                        "stage" to "urn:dcai:fixture:valid:reasoning-output:stage-waiting",
                        "stageLabel" to "Spare/vendor waiting",
                        "sourceRecord" to "urn:dcai:fixture:valid:reasoning-output:source-record-0001",
                        "impact" to "urn:dcai:fixture:valid:reasoning-output:impact-0001",
                        "evidence" to "urn:dcai:fixture:valid:reasoning-output:evidence-0001",
                        "evidenceClass" to "urn:dcai:ontology:TelemetryEvidence",
                        "evidenceTimestamp" to "2026-01-08T02:15:00Z",
                        "confidenceState" to "TRUSTED",
                        "metricName" to "fuel_pressure_psi",
                        "metricValue" to "18.0",
                        "metricUnit" to "psi",
                        "telemetryStatus" to "CRITICAL",
                        "trustFinding" to "urn:dcai:fixture:valid:reasoning-output:trust-finding-0001",
                        "trustSummary" to "Impact evidence is supported by telemetry.",
                    ),
                ),
            ),
        )

        val typed = assertIs<IncidentEvidenceEnvelope>(envelope)
        val record = typed.records.single()
        assertEquals(QueryResultType.INCIDENT_EVIDENCE, typed.resultType)
        assertEquals("urn:dcai:ontology:TelemetryEvidence", record.evidenceClassUri)
        assertEquals("2026-01-08T02:15:00Z", record.evidenceTimestamp)
        assertEquals("fuel_pressure_psi", record.metricName)
        assertEquals(18.0, record.metricValue)
        assertEquals("CRITICAL", record.telemetryStatus)
    }

    @Test
    fun shapesIncidentTimelineRows() {
        val envelope = shaper.shape(
            QueryExecutionReport(
                queryId = "semanticIncidentTimeline",
                mode = QueryMode.SELECT,
                rows = listOf(
                    mapOf(
                        "graph" to "urn:dcai:graph:fixture:canonical:reasoning-output",
                        "incident" to "urn:dcai:fixture:valid:reasoning-output:incident-0001",
                        "incidentId" to "INC-REASONING-0001",
                        "event" to "urn:dcai:fixture:valid:reasoning-output:workflow-event-0004",
                        "eventId" to "EVT-0004",
                        "stage" to "urn:dcai:fixture:valid:reasoning-output:stage-waiting",
                        "stageLabel" to "Spare/vendor waiting",
                        "eventStatus" to "ACTIVE",
                        "enteredAt" to "2026-01-06T08:00:00Z",
                        "durationHours" to "63.0",
                        "thresholdHours" to "18.0",
                        "delayHours" to "45.0",
                        "sourceRecord" to "urn:dcai:fixture:valid:reasoning-output:source-record-0001",
                    ),
                ),
            ),
        )

        val typed = assertIs<IncidentTimelineEnvelope>(envelope)
        val record = typed.records.single()
        assertEquals(QueryResultType.INCIDENT_TIMELINE, typed.resultType)
        assertEquals("EVT-0004", record.eventId)
        assertEquals(63.0, record.durationHours)
        assertEquals(18.0, record.thresholdHours)
        assertEquals(45.0, record.delayHours)
    }

    @Test
    fun shapesRemainingDashboardReadModelRows() {
        val cases = listOf(
            "semanticStageBottlenecks" to mapOf(
                "graph" to "urn:dcai:graph:fixture:canonical:reasoning-output",
                "stage" to "urn:dcai:fixture:valid:reasoning-output:stage-waiting",
                "stageLabel" to "Spare/vendor waiting",
                "incidentCount" to "2",
                "delayedCount" to "1",
                "avgDurationHours" to "63.0",
                "p90DurationHours" to "63.0",
                "totalDelayHours" to "45.0",
                "sourceRecord" to "urn:dcai:fixture:valid:reasoning-output:source-record-0001",
            ),
            "semanticAssetDelaySummary" to mapOf(
                "graph" to "urn:dcai:graph:fixture:canonical:reasoning-output",
                "asset" to "urn:dcai:fixture:valid:reasoning-output:asset-a",
                "assetId" to "ASSET-A",
                "zone" to "urn:dcai:fixture:valid:reasoning-output:zone-a",
                "zoneId" to "ZONE-A",
                "incidentCount" to "1",
                "impactObservationCount" to "1",
                "capacityRiskKw" to "900.0",
                "affectedGpuCount" to "320",
                "delayedIncidentCount" to "1",
                "totalDurationHours" to "63.0",
                "avgDurationHours" to "63.0",
                "topFailureMode" to "Spare/vendor waiting",
                "sourceRecord" to "urn:dcai:fixture:valid:reasoning-output:source-record-0001",
            ),
            "semanticZoneDelaySummary" to mapOf(
                "graph" to "urn:dcai:graph:fixture:canonical:reasoning-output",
                "zone" to "urn:dcai:fixture:valid:reasoning-output:zone-a",
                "zoneId" to "ZONE-A",
                "assetCount" to "1",
                "incidentCount" to "1",
                "impactObservationCount" to "1",
                "capacityRiskKw" to "900.0",
                "affectedGpuCount" to "320",
                "delayedIncidentCount" to "1",
                "criticalIncidentCount" to "1",
                "totalDurationHours" to "63.0",
                "topBottleneckStage" to "Spare/vendor waiting",
                "sourceRecord" to "urn:dcai:fixture:valid:reasoning-output:source-record-0001",
            ),
            "semanticSpareWaitSummary" to mapOf(
                "graph" to "urn:dcai:graph:fixture:canonical:reasoning-output",
                "stage" to "urn:dcai:fixture:valid:reasoning-output:stage-waiting",
                "stageLabel" to "Spare/vendor waiting",
                "incidentCount" to "1",
                "recoveryBlockerCount" to "1",
                "totalWaitHours" to "63.0",
                "avgWaitHours" to "63.0",
                "stockStatus" to "OUT_OF_STOCK",
                "sourceRecord" to "urn:dcai:fixture:valid:reasoning-output:source-record-0001",
            ),
            "semanticValidationSummary" to mapOf(
                "graph" to "urn:dcai:graph:fixture:canonical:reasoning-output",
                "sourceRecordCount" to "1",
                "incidentCount" to "1",
                "incidentWithProvenanceCount" to "1",
                "assetCount" to "1",
                "assetWithProvenanceCount" to "1",
            ),
            "semanticIncidentEvidence" to mapOf(
                "graph" to "urn:dcai:graph:fixture:canonical:reasoning-output",
                "incident" to "urn:dcai:fixture:valid:reasoning-output:incident-0001",
                "incidentId" to "INC-REASONING-0001",
                "stage" to "urn:dcai:fixture:valid:reasoning-output:stage-waiting",
                "stageLabel" to "Spare/vendor waiting",
                "sourceRecord" to "urn:dcai:fixture:valid:reasoning-output:source-record-0001",
                "impact" to "urn:dcai:fixture:valid:reasoning-output:impact-0001",
                "evidence" to "urn:dcai:fixture:valid:reasoning-output:evidence-0001",
                "evidenceClass" to "urn:dcai:ontology:TelemetryEvidence",
                "evidenceTimestamp" to "2026-01-08T02:15:00Z",
                "confidenceState" to "TRUSTED",
                "metricName" to "fuel_pressure_psi",
                "metricValue" to "18.0",
                "metricUnit" to "psi",
                "telemetryStatus" to "CRITICAL",
                "trustFinding" to "urn:dcai:fixture:valid:reasoning-output:trust-finding-0001",
                "trustSummary" to "Impact evidence is supported by telemetry.",
            ),
            "semanticDependencyImpactByAsset" to mapOf(
                "graph" to "urn:dcai:graph:fixture:canonical:dependency-path",
                "asset" to "urn:dcai:fixture:valid:dependency-path:gpu-rack-row-a",
                "assetId" to "ASSET-GPU-RACK-ROW-A",
                "dependencyEdge" to "urn:dcai:fixture:valid:dependency-path:edge-rack-to-pdu",
                "dependencyId" to "EDGE-RACK-PDU-A",
                "dependencyAsset" to "urn:dcai:fixture:valid:dependency-path:rack-pdu-a",
                "dependencyAssetId" to "ASSET-RACK-PDU-A",
                "dependencyRole" to "POWER_SUPPLY",
                "impactScope" to "RACK_ROW",
                "sourceRecord" to "urn:dcai:fixture:valid:dependency-path:source-record-topology-0001",
            ),
            "semanticBlastRadiusByAsset" to mapOf(
                "graph" to "urn:dcai:graph:fixture:canonical:dependency-path",
                "asset" to "urn:dcai:fixture:valid:dependency-path:rack-pdu-a",
                "assetId" to "ASSET-RACK-PDU-A",
                "downstreamAsset" to "urn:dcai:fixture:valid:dependency-path:gpu-rack-row-a",
                "downstreamAssetId" to "ASSET-GPU-RACK-ROW-A",
            ),
        )

        val resultTypes = cases.map { (queryId, row) ->
            shaper.shape(
                QueryExecutionReport(
                    queryId = queryId,
                    mode = QueryMode.SELECT,
                    rows = listOf(row),
                ),
            ).resultType
        }

        assertEquals(
            listOf(
                QueryResultType.STAGE_BOTTLENECKS,
                QueryResultType.ASSET_DELAY_SUMMARY,
                QueryResultType.ZONE_DELAY_SUMMARY,
                QueryResultType.SPARE_WAIT_SUMMARY,
                QueryResultType.VALIDATION_SUMMARY,
                QueryResultType.INCIDENT_EVIDENCE,
                QueryResultType.DEPENDENCY_IMPACT,
                QueryResultType.BLAST_RADIUS,
            ),
            resultTypes,
        )
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

    @Test
    fun rejectsFollowUpDetailRowsMissingSourceRecordProvenance() {
        assertFailsWith<IllegalArgumentException> {
            shaper.shape(
                QueryExecutionReport(
                    queryId = "semanticFollowUpDetail",
                    mode = QueryMode.SELECT,
                    rows = listOf(
                        followUpDetailRow() - "sourceRecord",
                    ),
                ),
            )
        }
    }

    @Test
    fun rejectsTopologyRowsMissingSourceRecordProvenance() {
        assertFailsWith<IllegalArgumentException> {
            shaper.shape(
                QueryExecutionReport(
                    queryId = "semanticTopologyDependencies",
                    mode = QueryMode.SELECT,
                    rows = listOf(
                        topologyDependencyRow() - "sourceRecord",
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
            "priorityRank" to "1",
            "requestTitle" to "Backup generator fuel system vendor wait",
            "currentStatus" to "BLOCKED",
            "hoursInCurrentStage" to "63.0",
            "neededByAt" to "2026-01-08T18:00:00Z",
            "priorityLevel" to "CRITICAL",
            "businessImpact" to "320 GPUs and 900 kW at risk",
            "assetCriticalityScore" to "20.0",
            "downtimeScore" to "30.0",
            "stageDelayScore" to "15.0",
            "infrastructureZoneImpactScore" to "20.0",
            "neededByUrgencyScore" to "10.0",
            "repeatFailureScore" to "0.0",
            "spareRiskScore" to "22.0",
            "capacityRiskScore" to "30.0",
            "redundancyRiskScore" to "24.0",
            "thermalRiskScore" to "0.0",
            "vendorEtaRiskScore" to "22.0",
            "mitigationCreditScore" to "4.0",
            "totalPriorityScore" to "169.0",
        )
    }

    private fun followUpDetailRow(): Map<String, String> {
        return followUpQueueRow() + mapOf(
            "impact" to "urn:dcai:fixture:valid:reasoning-output:impact-0001",
            "capacityRiskKw" to "900.0",
            "affectedGpuCount" to "320",
            "followUpDecision" to "urn:dcai:fixture:valid:reasoning-output:follow-up-decision-0001",
            "recommendedAction" to "Escalate vendor ETA.",
            "recoveryBlocker" to "urn:dcai:fixture:valid:reasoning-output:recovery-blocker-0001",
            "blockerSummary" to "Current blocker is spare/vendor waiting.",
            "trustFinding" to "urn:dcai:fixture:valid:reasoning-output:trust-finding-0001",
            "trustSummary" to "Impact evidence is supported by telemetry.",
            "redundancyState" to "N-1",
            "affectedRackCount" to "40",
            "estimatedGpuCapacityRiskPct" to "40.0",
            "thermalBreachMinutes" to "0",
            "powerRedundancyLost" to "true",
            "coolingRedundancyLost" to "false",
            "mitigationStatus" to "RUNNING_DEGRADED",
            "vendorEtaAt" to "2026-01-08T01:00:00Z",
            "vendorStatus" to "ETA_MISSED",
        )
    }

    private fun topologyDependencyRow(): Map<String, String> {
        return mapOf(
            "graph" to "urn:dcai:graph:fixture:canonical:dependency-path",
            "dependencyEdge" to "urn:dcai:fixture:valid:dependency-path:edge-rack-to-pdu",
            "dependencyId" to "EDGE-RACK-PDU-A",
            "dependentAsset" to "urn:dcai:fixture:valid:dependency-path:gpu-rack-row-a",
            "dependentAssetId" to "ASSET-GPU-RACK-ROW-A",
            "dependencyAsset" to "urn:dcai:fixture:valid:dependency-path:rack-pdu-a",
            "dependencyAssetId" to "ASSET-RACK-PDU-A",
            "dependencyRole" to "POWER_SUPPLY",
            "impactScope" to "RACK_ROW",
            "dependencyPath" to "urn:dcai:fixture:valid:dependency-path:power-path-a",
            "pathId" to "PATH-POWER-A",
            "sourceRecord" to "urn:dcai:fixture:valid:dependency-path:SRC-TOPO",
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
