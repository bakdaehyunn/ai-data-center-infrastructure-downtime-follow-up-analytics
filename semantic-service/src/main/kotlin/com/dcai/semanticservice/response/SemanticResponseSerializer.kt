package com.dcai.semanticservice.response

import com.dcai.semanticservice.query.AssetDelaySummaryEnvelope
import com.dcai.semanticservice.query.BlastRadiusEnvelope
import com.dcai.semanticservice.query.DashboardOverviewEnvelope
import com.dcai.semanticservice.query.DependencyImpactEnvelope
import com.dcai.semanticservice.query.FilterMetadataEnvelope
import com.dcai.semanticservice.query.FollowUpDetailEnvelope
import com.dcai.semanticservice.query.IncidentSummaryEnvelope
import com.dcai.semanticservice.query.FollowUpQueueEnvelope
import com.dcai.semanticservice.query.ImpactSummaryEnvelope
import com.dcai.semanticservice.query.IncidentEvidenceEnvelope
import com.dcai.semanticservice.query.IncidentTimelineEnvelope
import com.dcai.semanticservice.query.NamedGraphInventoryEnvelope
import com.dcai.semanticservice.query.ProvenanceSourceRecordsEnvelope
import com.dcai.semanticservice.query.QueryResultEnvelope
import com.dcai.semanticservice.query.QueryResultEnvelopeProvenance
import com.dcai.semanticservice.query.SpareWaitSummaryEnvelope
import com.dcai.semanticservice.query.StageBottlenecksEnvelope
import com.dcai.semanticservice.query.TopologyDependenciesEnvelope
import com.dcai.semanticservice.query.TrustFindingsEnvelope
import com.dcai.semanticservice.query.ValidationSummaryEnvelope
import com.dcai.semanticservice.query.ZoneDelaySummaryEnvelope

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
                    record.priorityRank?.let { put("priorityRank", it) }
                    record.requestTitle?.let { put("requestTitle", it) }
                    record.currentStatus?.let { put("currentStatus", it) }
                    record.hoursInCurrentStage?.let { put("hoursInCurrentStage", it) }
                    record.neededByAt?.let { put("neededByAt", it) }
                    record.priorityLevel?.let { put("priorityLevel", it) }
                    record.businessImpact?.let { put("businessImpact", it) }
                    record.assetCriticalityScore?.let { put("assetCriticalityScore", it) }
                    record.downtimeScore?.let { put("downtimeScore", it) }
                    record.stageDelayScore?.let { put("stageDelayScore", it) }
                    record.infrastructureZoneImpactScore?.let { put("infrastructureZoneImpactScore", it) }
                    record.neededByUrgencyScore?.let { put("neededByUrgencyScore", it) }
                    record.repeatFailureScore?.let { put("repeatFailureScore", it) }
                    record.spareRiskScore?.let { put("spareRiskScore", it) }
                    record.capacityRiskScore?.let { put("capacityRiskScore", it) }
                    record.redundancyRiskScore?.let { put("redundancyRiskScore", it) }
                    record.thermalRiskScore?.let { put("thermalRiskScore", it) }
                    record.vendorEtaRiskScore?.let { put("vendorEtaRiskScore", it) }
                    record.mitigationCreditScore?.let { put("mitigationCreditScore", it) }
                    record.totalPriorityScore?.let { put("totalPriorityScore", it) }
                }
            }
            is DashboardOverviewEnvelope -> envelope.records.map { record ->
                buildMap {
                    put("graphUri", record.graphUri)
                    put("totalIncidents", record.totalIncidents)
                    put("assetCount", record.assetCount)
                    put("zoneCount", record.zoneCount)
                    put("impactObservationCount", record.impactObservationCount)
                    put("capacityRiskKw", record.capacityRiskKw)
                    put("affectedGpuCount", record.affectedGpuCount)
                    put("dependencyEdgeCount", record.dependencyEdgeCount)
                    put("trustFindingCount", record.trustFindingCount)
                    record.avgDurationHours?.let { put("avgDurationHours", it) }
                    record.totalDurationHours?.let { put("totalDurationHours", it) }
                    record.totalDelayHours?.let { put("totalDelayHours", it) }
                    record.mitigatedIncidentCount?.let { put("mitigatedIncidentCount", it) }
                    record.affectedRackCount?.let { put("affectedRackCount", it) }
                    record.thermalBreachMinutes?.let { put("thermalBreachMinutes", it) }
                    record.redundancyLostIncidentCount?.let { put("redundancyLostIncidentCount", it) }
                    record.vendorEtaMissedCount?.let { put("vendorEtaMissedCount", it) }
                    record.repeatFailureAssetCount?.let { put("repeatFailureAssetCount", it) }
                    record.engineerAssignmentDelayHours?.let { put("engineerAssignmentDelayHours", it) }
                }
            }
            is FilterMetadataEnvelope -> envelope.records.map { record ->
                buildMap {
                    put("graphUri", record.graphUri)
                    put("filterType", record.filterType)
                    put("resourceUri", record.resourceUri)
                    put("id", record.id)
                    record.label?.let { put("label", it) }
                    record.sourceRecordUri?.let { put("sourceRecordUri", it) }
                }
            }
            is FollowUpDetailEnvelope -> envelope.records.map { record ->
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
                    record.impactUri?.let { put("impactUri", it) }
                    record.capacityRiskKw?.let { put("capacityRiskKw", it) }
                    record.affectedGpuCount?.let { put("affectedGpuCount", it) }
                    record.followUpDecisionUri?.let { put("followUpDecisionUri", it) }
                    record.recommendedAction?.let { put("recommendedAction", it) }
                    record.recoveryBlockerUri?.let { put("recoveryBlockerUri", it) }
                    record.blockerSummary?.let { put("blockerSummary", it) }
                    record.trustFindingUri?.let { put("trustFindingUri", it) }
                    record.trustSummary?.let { put("trustSummary", it) }
                    record.priorityRank?.let { put("priorityRank", it) }
                    record.requestTitle?.let { put("requestTitle", it) }
                    record.currentStatus?.let { put("currentStatus", it) }
                    record.hoursInCurrentStage?.let { put("hoursInCurrentStage", it) }
                    record.neededByAt?.let { put("neededByAt", it) }
                    record.priorityLevel?.let { put("priorityLevel", it) }
                    record.businessImpact?.let { put("businessImpact", it) }
                    record.assetCriticalityScore?.let { put("assetCriticalityScore", it) }
                    record.downtimeScore?.let { put("downtimeScore", it) }
                    record.stageDelayScore?.let { put("stageDelayScore", it) }
                    record.infrastructureZoneImpactScore?.let { put("infrastructureZoneImpactScore", it) }
                    record.neededByUrgencyScore?.let { put("neededByUrgencyScore", it) }
                    record.repeatFailureScore?.let { put("repeatFailureScore", it) }
                    record.repeatFailureAssetCount?.let { put("repeatFailureAssetCount", it) }
                    record.engineerAssignmentDelayHours?.let { put("engineerAssignmentDelayHours", it) }
                    record.spareRiskScore?.let { put("spareRiskScore", it) }
                    record.capacityRiskScore?.let { put("capacityRiskScore", it) }
                    record.redundancyRiskScore?.let { put("redundancyRiskScore", it) }
                    record.thermalRiskScore?.let { put("thermalRiskScore", it) }
                    record.vendorEtaRiskScore?.let { put("vendorEtaRiskScore", it) }
                    record.mitigationCreditScore?.let { put("mitigationCreditScore", it) }
                    record.totalPriorityScore?.let { put("totalPriorityScore", it) }
                    record.redundancyState?.let { put("redundancyState", it) }
                    record.affectedRackCount?.let { put("affectedRackCount", it) }
                    record.estimatedGpuCapacityRiskPct?.let { put("estimatedGpuCapacityRiskPct", it) }
                    record.thermalBreachMinutes?.let { put("thermalBreachMinutes", it) }
                    record.powerRedundancyLost?.let { put("powerRedundancyLost", it) }
                    record.coolingRedundancyLost?.let { put("coolingRedundancyLost", it) }
                    record.mitigationStatus?.let { put("mitigationStatus", it) }
                    record.vendorEtaAt?.let { put("vendorEtaAt", it) }
                    record.vendorStatus?.let { put("vendorStatus", it) }
                }
            }
            is ImpactSummaryEnvelope -> envelope.records.map { record ->
                buildMap {
                    put("graphUri", record.graphUri)
                    put("impactObservationCount", record.impactObservationCount)
                    put("incidentCount", record.incidentCount)
                    put("capacityRiskKw", record.capacityRiskKw)
                    put("affectedGpuCount", record.affectedGpuCount)
                    put("trustFindingCount", record.trustFindingCount)
                    record.affectedRackCount?.let { put("affectedRackCount", it) }
                    record.thermalBreachMinutes?.let { put("thermalBreachMinutes", it) }
                    record.redundancyLostIncidentCount?.let { put("redundancyLostIncidentCount", it) }
                    record.vendorEtaMissedCount?.let { put("vendorEtaMissedCount", it) }
                    record.mitigatedIncidentCount?.let { put("mitigatedIncidentCount", it) }
                }
            }
            is TopologyDependenciesEnvelope -> envelope.records.map { record ->
                buildMap {
                    put("graphUri", record.graphUri)
                    put("dependencyEdgeUri", record.dependencyEdgeUri)
                    put("dependencyId", record.dependencyId)
                    put("dependentAssetUri", record.dependentAssetUri)
                    put("dependentAssetId", record.dependentAssetId)
                    put("dependencyAssetUri", record.dependencyAssetUri)
                    put("dependencyAssetId", record.dependencyAssetId)
                    put("dependencyRole", record.dependencyRole)
                    record.impactScope?.let { put("impactScope", it) }
                    record.dependencyPathUri?.let { put("dependencyPathUri", it) }
                    record.pathId?.let { put("pathId", it) }
                    put("sourceRecordUri", record.sourceRecordUri)
                }
            }
            is TrustFindingsEnvelope -> envelope.records.map { record ->
                buildMap {
                    put("graphUri", record.graphUri)
                    put("trustFindingUri", record.trustFindingUri)
                    record.trustFindingId?.let { put("trustFindingId", it) }
                    put("summary", record.summary)
                    put("sourceFactUri", record.sourceFactUri)
                    record.activityUri?.let { put("activityUri", it) }
                    record.severity?.let { put("severity", it) }
                    record.status?.let { put("status", it) }
                    record.createdAt?.let { put("createdAt", it) }
                }
            }
            is StageBottlenecksEnvelope -> envelope.records.map { record ->
                buildMap {
                    put("graphUri", record.graphUri)
                    put("stageUri", record.stageUri)
                    record.stageLabel?.let { put("stageLabel", it) }
                    put("incidentCount", record.incidentCount)
                    record.delayedCount?.let { put("delayedCount", it) }
                    record.avgDurationHours?.let { put("avgDurationHours", it) }
                    record.p90DurationHours?.let { put("p90DurationHours", it) }
                    record.totalDelayHours?.let { put("totalDelayHours", it) }
                    put("sourceRecordUri", record.sourceRecordUri)
                }
            }
            is AssetDelaySummaryEnvelope -> envelope.records.map { record ->
                buildMap {
                    put("graphUri", record.graphUri)
                    put("assetUri", record.assetUri)
                    put("assetId", record.assetId)
                    put("zoneUri", record.zoneUri)
                    put("zoneId", record.zoneId)
                    put("incidentCount", record.incidentCount)
                    put("impactObservationCount", record.impactObservationCount)
                    put("capacityRiskKw", record.capacityRiskKw)
                    put("affectedGpuCount", record.affectedGpuCount)
                    record.delayedIncidentCount?.let { put("delayedIncidentCount", it) }
                    record.repeatFailureCount?.let { put("repeatFailureCount", it) }
                    record.totalDurationHours?.let { put("totalDurationHours", it) }
                    record.avgDurationHours?.let { put("avgDurationHours", it) }
                    record.topFailureMode?.let { put("topFailureMode", it) }
                    put("sourceRecordUri", record.sourceRecordUri)
                }
            }
            is ZoneDelaySummaryEnvelope -> envelope.records.map { record ->
                buildMap {
                    put("graphUri", record.graphUri)
                    put("zoneUri", record.zoneUri)
                    put("zoneId", record.zoneId)
                    put("assetCount", record.assetCount)
                    put("incidentCount", record.incidentCount)
                    put("impactObservationCount", record.impactObservationCount)
                    put("capacityRiskKw", record.capacityRiskKw)
                    put("affectedGpuCount", record.affectedGpuCount)
                    record.delayedIncidentCount?.let { put("delayedIncidentCount", it) }
                    record.criticalIncidentCount?.let { put("criticalIncidentCount", it) }
                    record.totalDurationHours?.let { put("totalDurationHours", it) }
                    record.topBottleneckStage?.let { put("topBottleneckStage", it) }
                    put("sourceRecordUri", record.sourceRecordUri)
                }
            }
            is SpareWaitSummaryEnvelope -> envelope.records.map { record ->
                buildMap {
                    put("graphUri", record.graphUri)
                    put("stageUri", record.stageUri)
                    record.stageLabel?.let { put("stageLabel", it) }
                    put("incidentCount", record.incidentCount)
                    put("recoveryBlockerCount", record.recoveryBlockerCount)
                    record.totalWaitHours?.let { put("totalWaitHours", it) }
                    record.avgWaitHours?.let { put("avgWaitHours", it) }
                    record.stockStatus?.let { put("stockStatus", it) }
                    put("sourceRecordUri", record.sourceRecordUri)
                }
            }
            is ValidationSummaryEnvelope -> envelope.records.map { record ->
                mapOf(
                    "graphUri" to record.graphUri,
                    "sourceRecordCount" to record.sourceRecordCount,
                    "incidentCount" to record.incidentCount,
                    "incidentWithProvenanceCount" to record.incidentWithProvenanceCount,
                    "assetCount" to record.assetCount,
                    "assetWithProvenanceCount" to record.assetWithProvenanceCount,
                )
            }
            is IncidentEvidenceEnvelope -> envelope.records.map { record ->
                buildMap {
                    put("graphUri", record.graphUri)
                    put("incidentUri", record.incidentUri)
                    put("incidentId", record.incidentId)
                    put("stageUri", record.stageUri)
                    record.stageLabel?.let { put("stageLabel", it) }
                    put("sourceRecordUri", record.sourceRecordUri)
                    record.impactUri?.let { put("impactUri", it) }
                    record.evidenceUri?.let { put("evidenceUri", it) }
                    record.evidenceClassUri?.let { put("evidenceClassUri", it) }
                    record.evidenceTimestamp?.let { put("evidenceTimestamp", it) }
                    record.confidenceState?.let { put("confidenceState", it) }
                    record.metricName?.let { put("metricName", it) }
                    record.metricValue?.let { put("metricValue", it) }
                    record.metricUnit?.let { put("metricUnit", it) }
                    record.telemetryStatus?.let { put("telemetryStatus", it) }
                    record.telemetryAlertId?.let { put("telemetryAlertId", it) }
                    record.alertType?.let { put("alertType", it) }
                    record.alertSeverity?.let { put("alertSeverity", it) }
                    record.alertTriggeredAt?.let { put("alertTriggeredAt", it) }
                    record.alertResolvedAt?.let { put("alertResolvedAt", it) }
                    record.validationId?.let { put("validationId", it) }
                    record.validationStatus?.let { put("validationStatus", it) }
                    record.validatorId?.let { put("validatorId", it) }
                    record.validationStartedAt?.let { put("validationStartedAt", it) }
                    record.validationCompletedAt?.let { put("validationCompletedAt", it) }
                    record.failureReason?.let { put("failureReason", it) }
                    record.workOrderId?.let { put("workOrderId", it) }
                    record.assignedTeam?.let { put("assignedTeam", it) }
                    record.assignedEngineerId?.let { put("assignedEngineerId", it) }
                    record.workOrderStatus?.let { put("workOrderStatus", it) }
                    record.plannedStartAt?.let { put("plannedStartAt", it) }
                    record.actualStartAt?.let { put("actualStartAt", it) }
                    record.actualCompletedAt?.let { put("actualCompletedAt", it) }
                    record.requiredSpareId?.let { put("requiredSpareId", it) }
                    record.requiredSpareName?.let { put("requiredSpareName", it) }
                    record.stockStatus?.let { put("stockStatus", it) }
                    record.trustFindingUri?.let { put("trustFindingUri", it) }
                    record.trustSummary?.let { put("trustSummary", it) }
                }
            }
            is IncidentTimelineEnvelope -> envelope.records.map { record ->
                buildMap {
                    put("graphUri", record.graphUri)
                    put("incidentUri", record.incidentUri)
                    put("incidentId", record.incidentId)
                    put("eventUri", record.eventUri)
                    record.eventId?.let { put("eventId", it) }
                    put("stageUri", record.stageUri)
                    record.stageLabel?.let { put("stageLabel", it) }
                    record.eventStatus?.let { put("eventStatus", it) }
                    record.enteredAt?.let { put("enteredAt", it) }
                    record.exitedAt?.let { put("exitedAt", it) }
                    record.durationHours?.let { put("durationHours", it) }
                    record.thresholdHours?.let { put("thresholdHours", it) }
                    record.delayHours?.let { put("delayHours", it) }
                    put("sourceRecordUri", record.sourceRecordUri)
                }
            }
            is DependencyImpactEnvelope -> envelope.records.map { record ->
                buildMap {
                    put("graphUri", record.graphUri)
                    put("assetUri", record.assetUri)
                    put("assetId", record.assetId)
                    record.dependencyEdgeUri?.let { put("dependencyEdgeUri", it) }
                    record.dependencyId?.let { put("dependencyId", it) }
                    record.dependencyAssetUri?.let { put("dependencyAssetUri", it) }
                    record.dependencyAssetId?.let { put("dependencyAssetId", it) }
                    record.dependencyRole?.let { put("dependencyRole", it) }
                    record.impactScope?.let { put("impactScope", it) }
                    record.findingUri?.let { put("findingUri", it) }
                    record.findingSummary?.let { put("findingSummary", it) }
                    record.sourceRecordUri?.let { put("sourceRecordUri", it) }
                }
            }
            is BlastRadiusEnvelope -> envelope.records.map { record ->
                buildMap {
                    put("graphUri", record.graphUri)
                    put("assetUri", record.assetUri)
                    put("assetId", record.assetId)
                    record.downstreamAssetUri?.let { put("downstreamAssetUri", it) }
                    record.downstreamAssetId?.let { put("downstreamAssetId", it) }
                    record.incidentUri?.let { put("incidentUri", it) }
                    record.incidentId?.let { put("incidentId", it) }
                    record.findingUri?.let { put("findingUri", it) }
                    record.findingSummary?.let { put("findingSummary", it) }
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
