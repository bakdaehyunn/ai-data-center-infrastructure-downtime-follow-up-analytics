package com.dcai.semanticservice.testfixtures

import com.dcai.semanticservice.ingestion.AssetClass
import com.dcai.semanticservice.ingestion.AssetSourceRecord
import com.dcai.semanticservice.ingestion.DependencyPathClass
import com.dcai.semanticservice.ingestion.DependencySourceRecord
import com.dcai.semanticservice.ingestion.EvidenceClass
import com.dcai.semanticservice.ingestion.EvidenceSourceRecord
import com.dcai.semanticservice.ingestion.FacilitySourceRecord
import com.dcai.semanticservice.ingestion.ImpactSourceRecord
import com.dcai.semanticservice.ingestion.IncidentSourceRecord
import com.dcai.semanticservice.ingestion.SourceExtractBatch
import com.dcai.semanticservice.ingestion.WorkflowEventSourceRecord
import com.dcai.semanticservice.ingestion.ZoneSourceRecord
import java.math.BigDecimal
import java.time.Instant

object ProductionSourceExtractFixtures {
    fun validBatch(batchId: String = "release-2026-06-ingestion-v1"): SourceExtractBatch {
        val importedAt = Instant.parse("2026-06-09T00:00:00Z")
        return SourceExtractBatch(
            batchId = batchId,
            sourceSystemId = "facility-ops",
            sourceSystemLabel = "Facility operations production extract",
            importedAt = importedAt,
            facilities = listOf(
                FacilitySourceRecord(
                    recordId = "SRC-FAC-001",
                    payloadHash = "sha256:facility-001",
                    facilityId = "FAC-GPU-A",
                    label = "GPU Hall A",
                ),
            ),
            zones = listOf(
                ZoneSourceRecord(
                    recordId = "SRC-ZONE-001",
                    payloadHash = "sha256:zone-001",
                    zoneId = "ZONE-A",
                    facilityId = "FAC-GPU-A",
                    label = "Zone A",
                ),
            ),
            assets = listOf(
                AssetSourceRecord(
                    recordId = "SRC-ASSET-GPU-001",
                    payloadHash = "sha256:asset-gpu-001",
                    assetId = "ASSET-GPU-RACK-ROW-A",
                    zoneId = "ZONE-A",
                    assetType = "GPU_RACK_ROW",
                    criticalityLevel = "CRITICAL",
                    operationalStatus = "DEGRADED",
                    hallId = "HALL-A",
                    rowId = "ROW-A",
                    rackId = "RACK-A01",
                    capacityGroupId = "GPU-POD-A",
                ),
                AssetSourceRecord(
                    recordId = "SRC-ASSET-PDU-001",
                    payloadHash = "sha256:asset-pdu-001",
                    assetId = "ASSET-RACK-PDU-A",
                    zoneId = "ZONE-A",
                    assetType = "RACK_PDU",
                    operationalStatus = "RUNNING",
                    hallId = "HALL-A",
                    rowId = "ROW-A",
                    rackId = "RACK-A01",
                    assetClass = AssetClass.POWER,
                ),
                AssetSourceRecord(
                    recordId = "SRC-ASSET-DOWNSTREAM-001",
                    payloadHash = "sha256:asset-downstream-001",
                    assetId = "ASSET-DOWNSTREAM-RACK-ROW-B",
                    zoneId = "ZONE-A",
                    assetType = "GPU_RACK_ROW",
                    criticalityLevel = "HIGH",
                    operationalStatus = "AT_RISK",
                    hallId = "HALL-A",
                    rowId = "ROW-B",
                    rackId = "RACK-B01",
                    capacityGroupId = "GPU-POD-B",
                ),
            ),
            incidents = listOf(
                IncidentSourceRecord(
                    recordId = "SRC-INC-001",
                    payloadHash = "sha256:incident-001",
                    incidentId = "INC-001",
                    assetId = "ASSET-GPU-RACK-ROW-A",
                    currentStageId = "VALIDATION",
                    currentStageLabel = "Validation",
                ),
            ),
            dependencies = listOf(
                DependencySourceRecord(
                    recordId = "SRC-TOPO-001",
                    payloadHash = "sha256:topology-001",
                    edgeId = "EDGE-RACK-PDU-A",
                    dependentAssetId = "ASSET-GPU-RACK-ROW-A",
                    dependencyAssetId = "ASSET-RACK-PDU-A",
                    dependencyRole = "POWER_SUPPLY",
                    impactScope = "RACK_ROW",
                    pathId = "PATH-POWER-A",
                    pathClass = DependencyPathClass.POWER,
                ),
                DependencySourceRecord(
                    recordId = "SRC-TOPO-002",
                    payloadHash = "sha256:topology-002",
                    edgeId = "EDGE-DOWNSTREAM-GPU-A",
                    dependentAssetId = "ASSET-DOWNSTREAM-RACK-ROW-B",
                    dependencyAssetId = "ASSET-GPU-RACK-ROW-A",
                    dependencyRole = "UPSTREAM_GPU_FABRIC",
                    impactScope = "DOWNSTREAM_RACK_ROW",
                    pathId = "PATH-DOWNSTREAM-A",
                    pathClass = DependencyPathClass.DEPENDENCY,
                ),
            ),
            workflowEvents = listOf(
                WorkflowEventSourceRecord(
                    recordId = "SRC-WF-001",
                    payloadHash = "sha256:workflow-001",
                    eventId = "EVT-001",
                    incidentId = "INC-001",
                    enteredStageId = "VALIDATION",
                    enteredStageLabel = "Validation",
                    status = "OPEN",
                    enteredAt = importedAt.minusSeconds(7200),
                    durationHours = BigDecimal("2.0"),
                    delayHours = BigDecimal("1.0"),
                ),
            ),
            impacts = listOf(
                ImpactSourceRecord(
                    recordId = "SRC-IMPACT-001",
                    payloadHash = "sha256:impact-001",
                    impactId = "IMPACT-001",
                    incidentId = "INC-001",
                    estimatedCapacityRiskKw = BigDecimal("480.0"),
                    affectedGpuCount = 128,
                    affectedRackCount = 4,
                    redundancyState = "N-1",
                    mitigationState = "RUNNING_DEGRADED",
                    vendorState = "ETA_MISSED",
                ),
            ),
            evidence = listOf(
                EvidenceSourceRecord(
                    recordId = "SRC-EVIDENCE-001",
                    payloadHash = "sha256:evidence-001",
                    evidenceId = "EVIDENCE-001",
                    evidenceClass = EvidenceClass.TELEMETRY,
                    supportsId = "IMPACT-001",
                    confidenceState = "TRUSTED",
                    timestamp = importedAt.minusSeconds(3600),
                    metricName = "power_kw_at_risk",
                    metricValue = BigDecimal("480.0"),
                    metricUnit = "kW",
                    telemetryStatus = "ALERTING",
                ),
            ),
        )
    }

    fun invalidMissingZoneBatch(): SourceExtractBatch {
        return validBatch(batchId = "release-2026-06-ingestion-invalid").copy(
            zones = emptyList(),
        )
    }
}
