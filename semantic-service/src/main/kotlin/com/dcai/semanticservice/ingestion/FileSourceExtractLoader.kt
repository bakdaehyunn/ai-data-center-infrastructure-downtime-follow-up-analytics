package com.dcai.semanticservice.ingestion

import java.math.BigDecimal
import java.nio.file.Path
import java.time.Instant
import java.util.Properties
import kotlin.io.path.inputStream

class FileSourceExtractLoader {
    fun load(path: Path): SourceExtractBatch {
        val properties = Properties()
        path.inputStream().use { input -> properties.load(input) }
        require(properties.required("format") == FORMAT) {
            "source extract file must declare format=$FORMAT"
        }

        val importedAt = Instant.parse(properties.required("importedAt"))
        return SourceExtractBatch(
            batchId = properties.required("batch.id"),
            sourceSystemId = properties.required("sourceSystem.id"),
            sourceSystemLabel = properties.required("sourceSystem.label"),
            importedAt = importedAt,
            facilities = properties.records("facilities") { prefix ->
                FacilitySourceRecord(
                    recordId = required("$prefix.recordId"),
                    payloadHash = required("$prefix.payloadHash"),
                    facilityId = required("$prefix.facilityId"),
                    label = optional("$prefix.label"),
                )
            },
            zones = properties.records("zones") { prefix ->
                ZoneSourceRecord(
                    recordId = required("$prefix.recordId"),
                    payloadHash = required("$prefix.payloadHash"),
                    zoneId = required("$prefix.zoneId"),
                    facilityId = required("$prefix.facilityId"),
                    label = optional("$prefix.label"),
                )
            },
            assets = properties.records("assets") { prefix ->
                AssetSourceRecord(
                    recordId = required("$prefix.recordId"),
                    payloadHash = required("$prefix.payloadHash"),
                    assetId = required("$prefix.assetId"),
                    zoneId = required("$prefix.zoneId"),
                    assetType = required("$prefix.assetType"),
                    criticalityLevel = optional("$prefix.criticalityLevel"),
                    operationalStatus = optional("$prefix.operationalStatus"),
                    hallId = optional("$prefix.hallId"),
                    rowId = optional("$prefix.rowId"),
                    rackId = optional("$prefix.rackId"),
                    capacityGroupId = optional("$prefix.capacityGroupId"),
                    assetClass = enumOptional<AssetClass>("$prefix.assetClass") ?: AssetClass.INFRASTRUCTURE,
                )
            },
            incidents = properties.records("incidents") { prefix ->
                IncidentSourceRecord(
                    recordId = required("$prefix.recordId"),
                    payloadHash = required("$prefix.payloadHash"),
                    incidentId = required("$prefix.incidentId"),
                    assetId = required("$prefix.assetId"),
                    currentStageId = required("$prefix.currentStageId"),
                    currentStageLabel = required("$prefix.currentStageLabel"),
                )
            },
            dependencies = properties.records("dependencies") { prefix ->
                DependencySourceRecord(
                    recordId = required("$prefix.recordId"),
                    payloadHash = required("$prefix.payloadHash"),
                    edgeId = required("$prefix.edgeId"),
                    dependentAssetId = required("$prefix.dependentAssetId"),
                    dependencyAssetId = required("$prefix.dependencyAssetId"),
                    dependencyRole = required("$prefix.dependencyRole"),
                    impactScope = required("$prefix.impactScope"),
                    pathId = optional("$prefix.pathId"),
                    pathClass = enumOptional<DependencyPathClass>("$prefix.pathClass") ?: DependencyPathClass.DEPENDENCY,
                )
            },
            workflowEvents = properties.records("workflowEvents") { prefix ->
                WorkflowEventSourceRecord(
                    recordId = required("$prefix.recordId"),
                    payloadHash = required("$prefix.payloadHash"),
                    eventId = required("$prefix.eventId"),
                    incidentId = required("$prefix.incidentId"),
                    enteredStageId = required("$prefix.enteredStageId"),
                    enteredStageLabel = required("$prefix.enteredStageLabel"),
                    status = required("$prefix.status"),
                    enteredAt = Instant.parse(required("$prefix.enteredAt")),
                    exitedAt = optional("$prefix.exitedAt")?.let(Instant::parse),
                    durationHours = optional("$prefix.durationHours")?.let(::BigDecimal),
                    delayHours = optional("$prefix.delayHours")?.let(::BigDecimal),
                )
            },
            evidence = properties.records("evidence") { prefix ->
                EvidenceSourceRecord(
                    recordId = required("$prefix.recordId"),
                    payloadHash = required("$prefix.payloadHash"),
                    evidenceId = required("$prefix.evidenceId"),
                    evidenceClass = enumRequired("$prefix.evidenceClass"),
                    supportsId = required("$prefix.supportsId"),
                    confidenceState = required("$prefix.confidenceState"),
                    timestamp = Instant.parse(required("$prefix.timestamp")),
                    metricName = optional("$prefix.metricName"),
                    metricValue = optional("$prefix.metricValue")?.let(::BigDecimal),
                    metricUnit = optional("$prefix.metricUnit"),
                    telemetryStatus = optional("$prefix.telemetryStatus"),
                    validationId = optional("$prefix.validationId"),
                    validationStatus = optional("$prefix.validationStatus"),
                    workOrderId = optional("$prefix.workOrderId"),
                    workOrderStatus = optional("$prefix.workOrderStatus"),
                    assignedTeam = optional("$prefix.assignedTeam"),
                )
            },
            impacts = properties.records("impacts") { prefix ->
                ImpactSourceRecord(
                    recordId = required("$prefix.recordId"),
                    payloadHash = required("$prefix.payloadHash"),
                    impactId = required("$prefix.impactId"),
                    incidentId = required("$prefix.incidentId"),
                    estimatedCapacityRiskKw = optional("$prefix.estimatedCapacityRiskKw")?.let(::BigDecimal),
                    affectedGpuCount = optional("$prefix.affectedGpuCount")?.toInt(),
                    affectedRackCount = optional("$prefix.affectedRackCount")?.toInt(),
                    redundancyState = optional("$prefix.redundancyState"),
                    mitigationState = optional("$prefix.mitigationState"),
                    vendorState = optional("$prefix.vendorState"),
                    vendorEtaAt = optional("$prefix.vendorEtaAt")?.let(Instant::parse),
                )
            },
        )
    }

    private fun <T : SourceRecordIdentity> Properties.records(
        family: String,
        build: Properties.(String) -> T,
    ): List<T> {
        val count = optional("$family.count")?.toInt() ?: 0
        require(count >= 0) { "$family.count must be zero or greater" }
        return (0 until count).map { index -> build("$family.$index") }
    }

    private fun Properties.required(key: String): String {
        return optional(key) ?: error("Missing required source extract field: $key")
    }

    private fun Properties.optional(key: String): String? {
        return getProperty(key)?.trim()?.takeIf { it.isNotEmpty() }
    }

    private inline fun <reified T : Enum<T>> Properties.enumRequired(key: String): T {
        return enumValueOf(required(key))
    }

    private inline fun <reified T : Enum<T>> Properties.enumOptional(key: String): T? {
        return optional(key)?.let { enumValueOf<T>(it) }
    }

    private companion object {
        const val FORMAT = "dcai-source-extract-v1"
    }
}
