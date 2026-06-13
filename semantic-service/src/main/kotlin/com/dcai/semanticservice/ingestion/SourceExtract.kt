package com.dcai.semanticservice.ingestion

import java.math.BigDecimal
import java.time.Instant

data class SourceExtractBatch(
    val batchId: String,
    val sourceSystemId: String,
    val sourceSystemLabel: String,
    val importedAt: Instant,
    val facilities: List<FacilitySourceRecord> = emptyList(),
    val zones: List<ZoneSourceRecord> = emptyList(),
    val assets: List<AssetSourceRecord> = emptyList(),
    val incidents: List<IncidentSourceRecord> = emptyList(),
    val dependencies: List<DependencySourceRecord> = emptyList(),
    val workflowEvents: List<WorkflowEventSourceRecord> = emptyList(),
    val evidence: List<EvidenceSourceRecord> = emptyList(),
    val impacts: List<ImpactSourceRecord> = emptyList(),
) {
    val allSourceRecords: List<SourceRecordIdentity> =
        facilities + zones + assets + incidents + dependencies + workflowEvents + evidence + impacts

    init {
        require(batchId.isNotBlank()) { "batchId must not be blank" }
        require(sourceSystemId.isNotBlank()) { "sourceSystemId must not be blank" }
        require(sourceSystemLabel.isNotBlank()) { "sourceSystemLabel must not be blank" }
        require(allSourceRecords.isNotEmpty()) { "source extract batch must contain at least one record" }
    }
}

interface SourceRecordIdentity {
    val recordId: String
    val payloadHash: String
}

data class FacilitySourceRecord(
    override val recordId: String,
    override val payloadHash: String,
    val facilityId: String,
    val label: String? = null,
) : SourceRecordIdentity

data class ZoneSourceRecord(
    override val recordId: String,
    override val payloadHash: String,
    val zoneId: String,
    val facilityId: String,
    val label: String? = null,
) : SourceRecordIdentity

data class AssetSourceRecord(
    override val recordId: String,
    override val payloadHash: String,
    val assetId: String,
    val zoneId: String,
    val assetType: String,
    val criticalityLevel: String? = null,
    val operationalStatus: String? = null,
    val hallId: String? = null,
    val rowId: String? = null,
    val rackId: String? = null,
    val capacityGroupId: String? = null,
    val assetClass: AssetClass = AssetClass.INFRASTRUCTURE,
) : SourceRecordIdentity

enum class AssetClass {
    INFRASTRUCTURE,
    POWER,
    COOLING,
    CONTROL_TELEMETRY,
}

data class IncidentSourceRecord(
    override val recordId: String,
    override val payloadHash: String,
    val incidentId: String,
    val assetId: String,
    val currentStageId: String,
    val currentStageLabel: String,
) : SourceRecordIdentity

data class DependencySourceRecord(
    override val recordId: String,
    override val payloadHash: String,
    val edgeId: String,
    val dependentAssetId: String,
    val dependencyAssetId: String,
    val dependencyRole: String,
    val impactScope: String,
    val pathId: String? = null,
    val pathClass: DependencyPathClass = DependencyPathClass.DEPENDENCY,
) : SourceRecordIdentity

enum class DependencyPathClass {
    DEPENDENCY,
    POWER,
    COOLING,
    TELEMETRY,
    REDUNDANCY,
}

data class WorkflowEventSourceRecord(
    override val recordId: String,
    override val payloadHash: String,
    val eventId: String,
    val incidentId: String,
    val enteredStageId: String,
    val enteredStageLabel: String,
    val status: String,
    val enteredAt: Instant,
    val exitedAt: Instant? = null,
    val durationHours: BigDecimal? = null,
    val delayHours: BigDecimal? = null,
) : SourceRecordIdentity

data class EvidenceSourceRecord(
    override val recordId: String,
    override val payloadHash: String,
    val evidenceId: String,
    val evidenceClass: EvidenceClass,
    val supportsId: String,
    val confidenceState: String,
    val timestamp: Instant,
    val metricName: String? = null,
    val metricValue: BigDecimal? = null,
    val metricUnit: String? = null,
    val telemetryStatus: String? = null,
    val validationId: String? = null,
    val validationStatus: String? = null,
    val workOrderId: String? = null,
    val workOrderStatus: String? = null,
    val assignedTeam: String? = null,
) : SourceRecordIdentity

enum class EvidenceClass {
    TELEMETRY,
    VALIDATION,
    WORK_ORDER,
}

data class ImpactSourceRecord(
    override val recordId: String,
    override val payloadHash: String,
    val impactId: String,
    val incidentId: String,
    val estimatedCapacityRiskKw: BigDecimal? = null,
    val affectedGpuCount: Int? = null,
    val affectedRackCount: Int? = null,
    val redundancyState: String? = null,
    val mitigationState: String? = null,
    val vendorState: String? = null,
    val vendorEtaAt: Instant? = null,
) : SourceRecordIdentity
