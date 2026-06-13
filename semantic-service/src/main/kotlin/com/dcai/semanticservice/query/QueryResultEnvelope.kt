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
    FOLLOW_UP_QUEUE("follow-up-queue"),
    DASHBOARD_OVERVIEW("dashboard-overview"),
    FILTER_METADATA("filter-metadata"),
    FOLLOW_UP_DETAIL("follow-up-detail"),
    IMPACT_SUMMARY("impact-summary"),
    TOPOLOGY_DEPENDENCIES("topology-dependencies"),
    TRUST_FINDINGS("trust-findings"),
    STAGE_BOTTLENECKS("stage-bottlenecks"),
    ASSET_DELAY_SUMMARY("asset-delay-summary"),
    ZONE_DELAY_SUMMARY("zone-delay-summary"),
    SPARE_WAIT_SUMMARY("spare-wait-summary"),
    VALIDATION_SUMMARY("validation-summary"),
    INCIDENT_EVIDENCE("incident-evidence"),
    INCIDENT_TIMELINE("incident-timeline"),
    DEPENDENCY_IMPACT("dependency-impact"),
    BLAST_RADIUS("blast-radius"),
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

data class FollowUpQueueEnvelope(
    override val queryId: String,
    val records: List<FollowUpQueueRecord>,
    override val provenance: QueryResultEnvelopeProvenance,
) : QueryResultEnvelope {
    override val resultType: QueryResultType = QueryResultType.FOLLOW_UP_QUEUE
    override val recordCount: Int = records.size
}

data class FollowUpQueueRecord(
    val graphUri: String,
    val incidentUri: String,
    val incidentId: String,
    val assetUri: String,
    val assetId: String,
    val zoneUri: String,
    val zoneId: String,
    val stageUri: String,
    val stageLabel: String? = null,
    val sourceRecordUri: String,
    val priorityRank: Int? = null,
    val requestTitle: String? = null,
    val currentStatus: String? = null,
    val hoursInCurrentStage: Double? = null,
    val neededByAt: String? = null,
    val priorityLevel: String? = null,
    val businessImpact: String? = null,
    val assetCriticalityScore: Double? = null,
    val downtimeScore: Double? = null,
    val stageDelayScore: Double? = null,
    val infrastructureZoneImpactScore: Double? = null,
    val neededByUrgencyScore: Double? = null,
    val repeatFailureScore: Double? = null,
    val spareRiskScore: Double? = null,
    val capacityRiskScore: Double? = null,
    val redundancyRiskScore: Double? = null,
    val thermalRiskScore: Double? = null,
    val vendorEtaRiskScore: Double? = null,
    val mitigationCreditScore: Double? = null,
    val totalPriorityScore: Double? = null,
)

data class DashboardOverviewEnvelope(
    override val queryId: String,
    val records: List<DashboardOverviewRecord>,
    override val provenance: QueryResultEnvelopeProvenance,
) : QueryResultEnvelope {
    override val resultType: QueryResultType = QueryResultType.DASHBOARD_OVERVIEW
    override val recordCount: Int = records.size
}

data class DashboardOverviewRecord(
    val graphUri: String,
    val totalIncidents: Int,
    val assetCount: Int,
    val zoneCount: Int,
    val impactObservationCount: Int,
    val capacityRiskKw: Double,
    val affectedGpuCount: Int,
    val dependencyEdgeCount: Int,
    val trustFindingCount: Int,
    val avgDurationHours: Double? = null,
    val totalDurationHours: Double? = null,
    val totalDelayHours: Double? = null,
    val mitigatedIncidentCount: Int? = null,
    val affectedRackCount: Int? = null,
    val thermalBreachMinutes: Int? = null,
    val redundancyLostIncidentCount: Int? = null,
    val vendorEtaMissedCount: Int? = null,
    val repeatFailureAssetCount: Int? = null,
    val engineerAssignmentDelayHours: Double? = null,
)

data class FilterMetadataEnvelope(
    override val queryId: String,
    val records: List<FilterMetadataRecord>,
    override val provenance: QueryResultEnvelopeProvenance,
) : QueryResultEnvelope {
    override val resultType: QueryResultType = QueryResultType.FILTER_METADATA
    override val recordCount: Int = records.size
}

data class FilterMetadataRecord(
    val graphUri: String,
    val filterType: String,
    val resourceUri: String,
    val id: String,
    val label: String? = null,
    val sourceRecordUri: String? = null,
)

data class FollowUpDetailEnvelope(
    override val queryId: String,
    val records: List<FollowUpDetailRecord>,
    override val provenance: QueryResultEnvelopeProvenance,
) : QueryResultEnvelope {
    override val resultType: QueryResultType = QueryResultType.FOLLOW_UP_DETAIL
    override val recordCount: Int = records.size
}

data class FollowUpDetailRecord(
    val graphUri: String,
    val incidentUri: String,
    val incidentId: String,
    val assetUri: String,
    val assetId: String,
    val zoneUri: String,
    val zoneId: String,
    val stageUri: String,
    val stageLabel: String? = null,
    val sourceRecordUri: String,
    val impactUri: String? = null,
    val capacityRiskKw: Double? = null,
    val affectedGpuCount: Int? = null,
    val followUpDecisionUri: String? = null,
    val recommendedAction: String? = null,
    val recoveryBlockerUri: String? = null,
    val blockerSummary: String? = null,
    val restoreReadinessUri: String? = null,
    val restoreReadinessSummary: String? = null,
    val trustFindingUri: String? = null,
    val trustSummary: String? = null,
    val priorityRank: Int? = null,
    val requestTitle: String? = null,
    val currentStatus: String? = null,
    val hoursInCurrentStage: Double? = null,
    val neededByAt: String? = null,
    val priorityLevel: String? = null,
    val businessImpact: String? = null,
    val assetCriticalityScore: Double? = null,
    val downtimeScore: Double? = null,
    val stageDelayScore: Double? = null,
    val infrastructureZoneImpactScore: Double? = null,
    val neededByUrgencyScore: Double? = null,
    val repeatFailureScore: Double? = null,
    val repeatFailureAssetCount: Int? = null,
    val engineerAssignmentDelayHours: Double? = null,
    val spareRiskScore: Double? = null,
    val capacityRiskScore: Double? = null,
    val redundancyRiskScore: Double? = null,
    val thermalRiskScore: Double? = null,
    val vendorEtaRiskScore: Double? = null,
    val mitigationCreditScore: Double? = null,
    val totalPriorityScore: Double? = null,
    val redundancyState: String? = null,
    val affectedRackCount: Int? = null,
    val estimatedGpuCapacityRiskPct: Double? = null,
    val thermalBreachMinutes: Int? = null,
    val powerRedundancyLost: Boolean? = null,
    val coolingRedundancyLost: Boolean? = null,
    val mitigationStatus: String? = null,
    val vendorEtaAt: String? = null,
    val vendorStatus: String? = null,
)

data class ImpactSummaryEnvelope(
    override val queryId: String,
    val records: List<ImpactSummaryRecord>,
    override val provenance: QueryResultEnvelopeProvenance,
) : QueryResultEnvelope {
    override val resultType: QueryResultType = QueryResultType.IMPACT_SUMMARY
    override val recordCount: Int = records.size
}

data class ImpactSummaryRecord(
    val graphUri: String,
    val impactObservationCount: Int,
    val incidentCount: Int,
    val capacityRiskKw: Double,
    val affectedGpuCount: Int,
    val trustFindingCount: Int,
    val affectedRackCount: Int? = null,
    val thermalBreachMinutes: Int? = null,
    val redundancyLostIncidentCount: Int? = null,
    val vendorEtaMissedCount: Int? = null,
    val mitigatedIncidentCount: Int? = null,
)

data class TopologyDependenciesEnvelope(
    override val queryId: String,
    val records: List<TopologyDependencyRecord>,
    override val provenance: QueryResultEnvelopeProvenance,
) : QueryResultEnvelope {
    override val resultType: QueryResultType = QueryResultType.TOPOLOGY_DEPENDENCIES
    override val recordCount: Int = records.size
}

data class TopologyDependencyRecord(
    val graphUri: String,
    val dependencyEdgeUri: String,
    val dependencyId: String,
    val dependentAssetUri: String,
    val dependentAssetId: String,
    val dependencyAssetUri: String,
    val dependencyAssetId: String,
    val dependencyRole: String,
    val impactScope: String? = null,
    val dependencyPathUri: String? = null,
    val pathId: String? = null,
    val sourceRecordUri: String,
)

data class TrustFindingsEnvelope(
    override val queryId: String,
    val records: List<TrustFindingRecord>,
    override val provenance: QueryResultEnvelopeProvenance,
) : QueryResultEnvelope {
    override val resultType: QueryResultType = QueryResultType.TRUST_FINDINGS
    override val recordCount: Int = records.size
}

data class TrustFindingRecord(
    val graphUri: String,
    val trustFindingUri: String,
    val trustFindingId: String? = null,
    val summary: String,
    val sourceFactUri: String,
    val activityUri: String? = null,
    val severity: String? = null,
    val status: String? = null,
    val createdAt: String? = null,
)

data class StageBottlenecksEnvelope(
    override val queryId: String,
    val records: List<StageBottleneckRecord>,
    override val provenance: QueryResultEnvelopeProvenance,
) : QueryResultEnvelope {
    override val resultType: QueryResultType = QueryResultType.STAGE_BOTTLENECKS
    override val recordCount: Int = records.size
}

data class StageBottleneckRecord(
    val graphUri: String,
    val stageUri: String,
    val stageLabel: String? = null,
    val incidentCount: Int,
    val delayedCount: Int? = null,
    val avgDurationHours: Double? = null,
    val p90DurationHours: Double? = null,
    val totalDelayHours: Double? = null,
    val sourceRecordUri: String,
)

data class AssetDelaySummaryEnvelope(
    override val queryId: String,
    val records: List<AssetDelaySummaryRecord>,
    override val provenance: QueryResultEnvelopeProvenance,
) : QueryResultEnvelope {
    override val resultType: QueryResultType = QueryResultType.ASSET_DELAY_SUMMARY
    override val recordCount: Int = records.size
}

data class AssetDelaySummaryRecord(
    val graphUri: String,
    val assetUri: String,
    val assetId: String,
    val zoneUri: String,
    val zoneId: String,
    val incidentCount: Int,
    val impactObservationCount: Int,
    val capacityRiskKw: Double,
    val affectedGpuCount: Int,
    val delayedIncidentCount: Int? = null,
    val repeatFailureCount: Int? = null,
    val totalDurationHours: Double? = null,
    val avgDurationHours: Double? = null,
    val topFailureMode: String? = null,
    val sourceRecordUri: String,
)

data class ZoneDelaySummaryEnvelope(
    override val queryId: String,
    val records: List<ZoneDelaySummaryRecord>,
    override val provenance: QueryResultEnvelopeProvenance,
) : QueryResultEnvelope {
    override val resultType: QueryResultType = QueryResultType.ZONE_DELAY_SUMMARY
    override val recordCount: Int = records.size
}

data class ZoneDelaySummaryRecord(
    val graphUri: String,
    val zoneUri: String,
    val zoneId: String,
    val assetCount: Int,
    val incidentCount: Int,
    val impactObservationCount: Int,
    val capacityRiskKw: Double,
    val affectedGpuCount: Int,
    val delayedIncidentCount: Int? = null,
    val criticalIncidentCount: Int? = null,
    val totalDurationHours: Double? = null,
    val topBottleneckStage: String? = null,
    val sourceRecordUri: String,
)

data class SpareWaitSummaryEnvelope(
    override val queryId: String,
    val records: List<SpareWaitSummaryRecord>,
    override val provenance: QueryResultEnvelopeProvenance,
) : QueryResultEnvelope {
    override val resultType: QueryResultType = QueryResultType.SPARE_WAIT_SUMMARY
    override val recordCount: Int = records.size
}

data class SpareWaitSummaryRecord(
    val graphUri: String,
    val stageUri: String,
    val stageLabel: String? = null,
    val incidentCount: Int,
    val recoveryBlockerCount: Int,
    val totalWaitHours: Double? = null,
    val avgWaitHours: Double? = null,
    val stockStatus: String? = null,
    val sourceRecordUri: String,
)

data class ValidationSummaryEnvelope(
    override val queryId: String,
    val records: List<ValidationSummaryRecord>,
    override val provenance: QueryResultEnvelopeProvenance,
) : QueryResultEnvelope {
    override val resultType: QueryResultType = QueryResultType.VALIDATION_SUMMARY
    override val recordCount: Int = records.size
}

data class ValidationSummaryRecord(
    val graphUri: String,
    val sourceRecordCount: Int,
    val incidentCount: Int,
    val incidentWithProvenanceCount: Int,
    val assetCount: Int,
    val assetWithProvenanceCount: Int,
)

data class IncidentEvidenceEnvelope(
    override val queryId: String,
    val records: List<IncidentEvidenceRecord>,
    override val provenance: QueryResultEnvelopeProvenance,
) : QueryResultEnvelope {
    override val resultType: QueryResultType = QueryResultType.INCIDENT_EVIDENCE
    override val recordCount: Int = records.size
}

data class IncidentEvidenceRecord(
    val graphUri: String,
    val incidentUri: String,
    val incidentId: String,
    val stageUri: String,
    val stageLabel: String? = null,
    val sourceRecordUri: String,
    val impactUri: String? = null,
    val evidenceUri: String? = null,
    val evidenceClassUri: String? = null,
    val evidenceTimestamp: String? = null,
    val confidenceState: String? = null,
    val metricName: String? = null,
    val metricValue: Double? = null,
    val metricUnit: String? = null,
    val telemetryStatus: String? = null,
    val telemetryAlertId: String? = null,
    val alertType: String? = null,
    val alertSeverity: String? = null,
    val alertTriggeredAt: String? = null,
    val alertResolvedAt: String? = null,
    val validationId: String? = null,
    val validationStatus: String? = null,
    val validatorId: String? = null,
    val validationStartedAt: String? = null,
    val validationCompletedAt: String? = null,
    val failureReason: String? = null,
    val workOrderId: String? = null,
    val assignedTeam: String? = null,
    val assignedEngineerId: String? = null,
    val workOrderStatus: String? = null,
    val plannedStartAt: String? = null,
    val actualStartAt: String? = null,
    val actualCompletedAt: String? = null,
    val requiredSpareId: String? = null,
    val requiredSpareName: String? = null,
    val stockStatus: String? = null,
    val trustFindingUri: String? = null,
    val trustSummary: String? = null,
)

data class IncidentTimelineEnvelope(
    override val queryId: String,
    val records: List<IncidentTimelineRecord>,
    override val provenance: QueryResultEnvelopeProvenance,
) : QueryResultEnvelope {
    override val resultType: QueryResultType = QueryResultType.INCIDENT_TIMELINE
    override val recordCount: Int = records.size
}

data class IncidentTimelineRecord(
    val graphUri: String,
    val incidentUri: String,
    val incidentId: String,
    val eventUri: String,
    val eventId: String? = null,
    val stageUri: String,
    val stageLabel: String? = null,
    val eventStatus: String? = null,
    val enteredAt: String? = null,
    val exitedAt: String? = null,
    val durationHours: Double? = null,
    val thresholdHours: Double? = null,
    val delayHours: Double? = null,
    val sourceRecordUri: String,
)

data class DependencyImpactEnvelope(
    override val queryId: String,
    val records: List<DependencyImpactRecord>,
    override val provenance: QueryResultEnvelopeProvenance,
) : QueryResultEnvelope {
    override val resultType: QueryResultType = QueryResultType.DEPENDENCY_IMPACT
    override val recordCount: Int = records.size
}

data class DependencyImpactRecord(
    val graphUri: String,
    val assetUri: String,
    val assetId: String,
    val dependencyEdgeUri: String? = null,
    val dependencyId: String? = null,
    val dependencyAssetUri: String? = null,
    val dependencyAssetId: String? = null,
    val dependencyRole: String? = null,
    val impactScope: String? = null,
    val findingUri: String? = null,
    val findingSummary: String? = null,
    val sourceRecordUri: String? = null,
)

data class BlastRadiusEnvelope(
    override val queryId: String,
    val records: List<BlastRadiusRecord>,
    override val provenance: QueryResultEnvelopeProvenance,
) : QueryResultEnvelope {
    override val resultType: QueryResultType = QueryResultType.BLAST_RADIUS
    override val recordCount: Int = records.size
}

data class BlastRadiusRecord(
    val graphUri: String,
    val assetUri: String,
    val assetId: String,
    val downstreamAssetUri: String? = null,
    val downstreamAssetId: String? = null,
    val incidentUri: String? = null,
    val incidentId: String? = null,
    val findingUri: String? = null,
    val findingSummary: String? = null,
)
