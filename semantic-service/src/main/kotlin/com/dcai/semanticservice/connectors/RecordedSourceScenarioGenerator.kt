package com.dcai.semanticservice.connectors

import java.nio.file.Files
import java.nio.file.Path
import java.time.Instant
import kotlin.io.path.writeText

class RecordedSourceScenarioGenerator {
    fun generate(request: RecordedSourceScenarioGenerationRequest): RecordedSourceScenarioGenerationReport {
        Files.createDirectories(request.outputDirectory)
        val profile = request.profile
        val context = GenerationContext(request)

        val facilities = listOf(listOf("FAC-GEN-1", "Generated Operations Facility"))
        val zones = listOf(
            listOf("ZONE-GEN-COMPUTE", "FAC-GEN-1", "Generated Compute Hall"),
            listOf("ZONE-GEN-POWER", "FAC-GEN-1", "Generated Power Gallery"),
            listOf("ZONE-GEN-COOLING", "FAC-GEN-1", "Generated Cooling Plant"),
        )

        val assets = mutableListOf<List<String>>()
        val incidents = mutableListOf<List<String>>()
        val dependencies = mutableListOf<List<String>>()
        val workflowEvents = mutableListOf<List<String>>()
        val workOrders = mutableListOf<List<String>>()
        val validations = mutableListOf<List<String>>()
        val telemetryImpacts = mutableListOf<List<String>>()

        repeat(profile.scenarioCount) { index ->
            val scenario = context.scenario(index)
            assets += scenario.assetRows()
            incidents += scenario.incidentRows()
            dependencies += scenario.dependencyRows()
            workflowEvents += scenario.workflowRows()
            workOrders += scenario.workOrderRows()
            validations += scenario.validationRows()
            telemetryImpacts += scenario.telemetryImpactRows()
        }

        repeat(profile.invalidIncidentRows) { index ->
            val badId = context.indexed("BAD", index)
            incidents += listOf("INC-GEN-$badId", "", "STAGE-VALIDATION", "Validation")
        }
        repeat(profile.duplicateWorkflowRows) { index ->
            val scenarioId = context.indexed("SCN", index)
            workflowEvents += listOf(
                "WF-GEN-$scenarioId-VALIDATION",
                "INC-GEN-$scenarioId",
                "STAGE-VALIDATION",
                "Validation",
                "duplicate",
                context.time(index, minutesOffset = 9).toString(),
                "",
                "1.2",
                "0.4",
            )
        }

        val files = listOf(
            GeneratedCsv("facilities.csv", listOf("facilityId", "label"), facilities),
            GeneratedCsv("zones.csv", listOf("zoneId", "facilityId", "label"), zones),
            GeneratedCsv(
                "assets.csv",
                listOf(
                    "assetId",
                    "zoneId",
                    "assetType",
                    "criticalityLevel",
                    "operationalStatus",
                    "hallId",
                    "rowId",
                    "rackId",
                    "capacityGroupId",
                    "assetClass",
                ),
                assets,
            ),
            GeneratedCsv(
                "incidents.csv",
                listOf("incidentId", "assetId", "currentStageId", "currentStageLabel"),
                incidents,
            ),
            GeneratedCsv(
                "dependencies.csv",
                listOf("edgeId", "dependentAssetId", "dependencyAssetId", "dependencyRole", "impactScope", "pathId", "pathClass"),
                dependencies,
            ),
            GeneratedCsv(
                "workflow_events.csv",
                listOf("eventId", "incidentId", "enteredStageId", "enteredStageLabel", "status", "enteredAt", "exitedAt", "durationHours", "delayHours"),
                workflowEvents,
            ),
            GeneratedCsv(
                "work_orders.csv",
                listOf("workOrderId", "incidentId", "workOrderStatus", "assignedTeam", "timestamp", "confidenceState"),
                workOrders,
            ),
            GeneratedCsv(
                "validation_results.csv",
                listOf("validationId", "incidentId", "validationStatus", "timestamp", "confidenceState"),
                validations,
            ),
            GeneratedCsv(
                "telemetry_impacts.csv",
                listOf(
                    "impactId",
                    "evidenceId",
                    "incidentId",
                    "timestamp",
                    "estimatedCapacityRiskKw",
                    "affectedGpuCount",
                    "affectedRackCount",
                    "redundancyState",
                    "mitigationState",
                    "vendorState",
                    "vendorEtaAt",
                    "metricName",
                    "metricValue",
                    "metricUnit",
                    "telemetryStatus",
                    "confidenceState",
                ),
                telemetryImpacts,
            ),
        )

        request.outputDirectory.resolve("manifest.properties").writeText(
            """
            format=dcai-recorded-connector-simulation-v1
            batch.id=${request.batchId}
            sourceSystem.id=generated-recorded-source-${profile.value}
            sourceSystem.label=Generated Recorded Source Scenario ${profile.value}
            importedAt=${request.importedAt}
            """.trimIndent() + "\n",
        )
        files.forEach { file ->
            request.outputDirectory.resolve(file.name).writeText(file.render())
        }

        return RecordedSourceScenarioGenerationReport(
            profile = profile,
            seed = request.seed,
            batchId = request.batchId,
            outputDirectory = request.outputDirectory,
            scenarioCount = profile.scenarioCount,
            totalRows = files.sumOf { it.rows.size },
            invalidIncidentRows = profile.invalidIncidentRows,
            duplicateWorkflowRows = profile.duplicateWorkflowRows,
            csvFiles = files.map { it.name },
        )
    }

    private data class GeneratedCsv(
        val name: String,
        val headers: List<String>,
        val rows: List<List<String>>,
    ) {
        fun render(): String {
            return (listOf(headers) + rows)
                .joinToString(separator = "\n") { row -> row.joinToString(separator = ",") }
                .plus("\n")
        }
    }

    private class GenerationContext(
        private val request: RecordedSourceScenarioGenerationRequest,
    ) {
        private val scenarioTypes = ScenarioType.values()

        fun scenario(index: Int): Scenario {
            val scenarioOrdinal = index + 1
            val scenarioId = indexed("SCN", index)
            return Scenario(
                id = scenarioId,
                ordinal = scenarioOrdinal,
                type = scenarioTypes[(request.seed + index).floorMod(scenarioTypes.size)],
                baseTime = time(index, minutesOffset = 0),
            )
        }

        fun indexed(prefix: String, index: Int): String {
            return "$prefix-${(request.seed + index + 1).toString().padStart(6, '0')}"
        }

        fun time(index: Int, minutesOffset: Long): Instant {
            return request.importedAt.plusSeconds(index.toLong() * 600L + minutesOffset * 60L)
        }

        private fun Int.floorMod(divisor: Int): Int = Math.floorMod(this, divisor)
    }

    private data class Scenario(
        val id: String,
        val ordinal: Int,
        val type: ScenarioType,
        val baseTime: Instant,
    ) {
        private val gpu = "ASSET-GEN-GPU-$id"
        private val ups = "ASSET-GEN-UPS-$id"
        private val cooling = "ASSET-GEN-CHW-$id"
        private val telemetry = "ASSET-GEN-DCIM-$id"
        private val incident = "INC-GEN-$id"
        private val hall = "HALL-GEN-${ordinal.toString().padStart(3, '0')}"
        private val row = "ROW-GEN-${ordinal.toString().padStart(3, '0')}"
        private val rack = "RACK-GEN-${ordinal.toString().padStart(3, '0')}"
        private val capacityGroup = "GPU-POD-GEN-${ordinal.toString().padStart(3, '0')}"

        fun assetRows(): List<List<String>> {
            return listOf(
                listOf(gpu, "ZONE-GEN-COMPUTE", "GPU Pod", "critical", type.gpuStatus, hall, row, rack, capacityGroup, "INFRASTRUCTURE"),
                listOf(ups, "ZONE-GEN-POWER", "UPS Feed", "critical", type.powerStatus, hall, row, "POWER-$rack", "", "POWER"),
                listOf(cooling, "ZONE-GEN-COOLING", "Chilled Water Loop", "high", type.coolingStatus, hall, "", "", "", "COOLING"),
                listOf(telemetry, "ZONE-GEN-COMPUTE", "DCIM Telemetry Bridge", "high", type.telemetryStatus, hall, row, rack, capacityGroup, "CONTROL_TELEMETRY"),
            )
        }

        fun incidentRows(): List<List<String>> {
            return listOf(listOf(incident, gpu, type.stageId, type.stageLabel))
        }

        fun dependencyRows(): List<List<String>> {
            return listOf(
                listOf("DEP-GEN-$id-POWER", gpu, ups, "power-feed", "pod", "PATH-GEN-$id-POWER", "POWER"),
                listOf("DEP-GEN-$id-COOLING", gpu, cooling, "cooling-loop", "row", "PATH-GEN-$id-COOLING", "COOLING"),
                listOf("DEP-GEN-$id-BLAST", telemetry, gpu, "telemetry-source", "pod", "PATH-GEN-$id-BLAST", "TELEMETRY"),
            )
        }

        fun workflowRows(): List<List<String>> {
            return listOf(
                listOf("WF-GEN-$id-DETECTED", incident, "STAGE-DETECTED", "Detected", "complete", baseTime.toString(), baseTime.plusSeconds(600).toString(), "0.2", "0.0"),
                listOf("WF-GEN-$id-VALIDATION", incident, "STAGE-VALIDATION", "Validation", type.validationWorkflowStatus, baseTime.plusSeconds(600).toString(), "", "1.0", type.validationDelayHours),
                listOf("WF-GEN-$id-CURRENT", incident, type.stageId, type.stageLabel, "open", baseTime.plusSeconds(1800).toString(), "", type.durationHours, type.delayHours),
            )
        }

        fun workOrderRows(): List<List<String>> {
            return listOf(
                listOf("WO-GEN-$id-FAC", incident, type.workOrderStatus, type.assignedTeam, baseTime.plusSeconds(2100).toString(), "TRUSTED"),
                listOf("WO-GEN-$id-SRE", incident, type.secondaryWorkOrderStatus, "Site Reliability", baseTime.plusSeconds(2400).toString(), type.workOrderConfidence),
            )
        }

        fun validationRows(): List<List<String>> {
            return listOf(
                listOf("VAL-GEN-$id-PRIMARY", incident, type.primaryValidationStatus, baseTime.plusSeconds(2700).toString(), "TRUSTED"),
                listOf("VAL-GEN-$id-SECONDARY", incident, type.secondaryValidationStatus, baseTime.plusSeconds(3000).toString(), type.validationConfidence),
            )
        }

        fun telemetryImpactRows(): List<List<String>> {
            return listOf(
                listOf(
                    "IMPACT-GEN-$id-CAPACITY",
                    "TEL-GEN-$id-CAPACITY",
                    incident,
                    baseTime.plusSeconds(900).toString(),
                    type.capacityRiskKw,
                    type.gpuCount,
                    type.rackCount,
                    type.redundancyState,
                    type.mitigationState,
                    type.vendorState,
                    baseTime.plusSeconds(7200).toString(),
                    type.primaryMetric,
                    type.primaryMetricValue,
                    type.primaryMetricUnit,
                    type.primaryTelemetryStatus,
                    type.telemetryConfidence,
                ),
                listOf(
                    "IMPACT-GEN-$id-WORKFLOW",
                    "TEL-GEN-$id-WORKFLOW",
                    incident,
                    baseTime.plusSeconds(1500).toString(),
                    type.secondaryCapacityRiskKw,
                    type.secondaryGpuCount,
                    type.secondaryRackCount,
                    type.secondaryRedundancyState,
                    type.secondaryMitigationState,
                    type.secondaryVendorState,
                    "",
                    type.secondaryMetric,
                    type.secondaryMetricValue,
                    type.secondaryMetricUnit,
                    type.secondaryTelemetryStatus,
                    type.secondaryTelemetryConfidence,
                ),
            )
        }
    }

    private enum class ScenarioType(
        val stageId: String,
        val stageLabel: String,
        val gpuStatus: String,
        val powerStatus: String,
        val coolingStatus: String,
        val telemetryStatus: String,
        val validationWorkflowStatus: String,
        val validationDelayHours: String,
        val durationHours: String,
        val delayHours: String,
        val assignedTeam: String,
        val workOrderStatus: String,
        val secondaryWorkOrderStatus: String,
        val workOrderConfidence: String,
        val primaryValidationStatus: String,
        val secondaryValidationStatus: String,
        val validationConfidence: String,
        val capacityRiskKw: String,
        val gpuCount: String,
        val rackCount: String,
        val redundancyState: String,
        val mitigationState: String,
        val vendorState: String,
        val primaryMetric: String,
        val primaryMetricValue: String,
        val primaryMetricUnit: String,
        val primaryTelemetryStatus: String,
        val telemetryConfidence: String,
        val secondaryCapacityRiskKw: String,
        val secondaryGpuCount: String,
        val secondaryRackCount: String,
        val secondaryRedundancyState: String,
        val secondaryMitigationState: String,
        val secondaryVendorState: String,
        val secondaryMetric: String,
        val secondaryMetricValue: String,
        val secondaryMetricUnit: String,
        val secondaryTelemetryStatus: String,
        val secondaryTelemetryConfidence: String,
    ) {
        UPS_DEGRADATION(
            "STAGE-VALIDATION",
            "Validation",
            "degraded",
            "monitor",
            "stable",
            "stable",
            "open",
            "0.5",
            "2.0",
            "1.0",
            "Facilities Electrical",
            "dispatched",
            "in-progress",
            "TRUSTED",
            "power-path-confirmed",
            "awaiting-transfer-test",
            "TRUSTED",
            "390.0",
            "96",
            "4",
            "N_PLUS_0",
            "load-shed-active",
            "vendor-engaged",
            "ups-output-kw",
            "390.0",
            "kW",
            "alerting",
            "TRUSTED",
            "120.0",
            "24",
            "1",
            "N_PLUS_1",
            "capacity-watch",
            "monitoring",
            "battery-runtime-min",
            "12.0",
            "minute",
            "warning",
            "TRUSTED",
        ),
        COOLING_INSTABILITY(
            "STAGE-RECOVERY",
            "Recovery",
            "degraded",
            "stable",
            "degraded",
            "stable",
            "open",
            "0.7",
            "3.0",
            "1.5",
            "Mechanical Cooling",
            "in-progress",
            "pending-verification",
            "TRUSTED",
            "cooling-loop-confirmed",
            "awaiting-temperature-stabilization",
            "TRUSTED",
            "280.0",
            "72",
            "3",
            "N_PLUS_0",
            "thermal-throttle-active",
            "vendor-engaged",
            "chw-supply-temp-c",
            "19.5",
            "celsius",
            "alerting",
            "TRUSTED",
            "95.0",
            "18",
            "1",
            "N_PLUS_1",
            "fan-curve-adjusted",
            "monitoring",
            "return-temp-c",
            "28.0",
            "celsius",
            "warning",
            "TRUSTED",
        ),
        TELEMETRY_BRIDGE_FAILURE(
            "STAGE-VALIDATION",
            "Validation",
            "monitor",
            "stable",
            "stable",
            "degraded",
            "blocked",
            "1.0",
            "2.5",
            "1.5",
            "Controls Engineering",
            "blocked",
            "manual-review",
            "REVIEW_REQUIRED",
            "telemetry-gap-detected",
            "manual-confirmation-required",
            "REVIEW_REQUIRED",
            "160.0",
            "48",
            "2",
            "N_PLUS_1",
            "manual-sampling-active",
            "monitoring",
            "dcim-signal-loss",
            "9.0",
            "count",
            "degraded",
            "REVIEW_REQUIRED",
            "60.0",
            "12",
            "1",
            "N_PLUS_1",
            "telemetry-replay-pending",
            "monitoring",
            "missing-sample-window-min",
            "18.0",
            "minute",
            "degraded",
            "REVIEW_REQUIRED",
        ),
        DELAYED_WORK_ORDER(
            "STAGE-RECOVERY",
            "Recovery",
            "degraded",
            "stable",
            "stable",
            "stable",
            "delayed",
            "2.0",
            "4.0",
            "2.5",
            "Field Operations",
            "delayed",
            "awaiting-assignment",
            "REVIEW_REQUIRED",
            "field-dispatch-needed",
            "repair-window-delayed",
            "REVIEW_REQUIRED",
            "210.0",
            "64",
            "2",
            "N_PLUS_1",
            "dispatch-pending",
            "parts-review",
            "work-order-age-hours",
            "6.0",
            "hour",
            "warning",
            "TRUSTED",
            "80.0",
            "16",
            "1",
            "N_PLUS_1",
            "manual-mitigation-active",
            "monitoring",
            "engineer-assignment-delay-hours",
            "3.5",
            "hour",
            "warning",
            "REVIEW_REQUIRED",
        ),
        CONFLICTING_VALIDATION(
            "STAGE-VALIDATION",
            "Validation",
            "monitor",
            "monitor",
            "stable",
            "stable",
            "open",
            "1.3",
            "2.5",
            "1.2",
            "Site Reliability",
            "manual-review",
            "conflict-review",
            "REVIEW_REQUIRED",
            "primary-validation-pass",
            "secondary-validation-conflict",
            "REVIEW_REQUIRED",
            "175.0",
            "40",
            "2",
            "N_PLUS_1",
            "validation-hold",
            "monitoring",
            "transfer-test-pass",
            "1.0",
            "boolean",
            "normal",
            "TRUSTED",
            "140.0",
            "32",
            "2",
            "N_PLUS_1",
            "evidence-review",
            "monitoring",
            "manual-check-disagree",
            "1.0",
            "boolean",
            "conflict",
            "REVIEW_REQUIRED",
        ),
        REPEATED_BLAST_RADIUS(
            "STAGE-RECOVERY",
            "Recovery",
            "degraded",
            "monitor",
            "monitor",
            "stable",
            "open",
            "0.8",
            "3.5",
            "1.7",
            "Capacity Engineering",
            "in-progress",
            "capacity-review",
            "TRUSTED",
            "repeat-failure-observed",
            "blast-radius-review-required",
            "TRUSTED",
            "430.0",
            "128",
            "5",
            "N_PLUS_0",
            "workload-evacuation-active",
            "vendor-engaged",
            "affected-gpu-count",
            "128.0",
            "count",
            "alerting",
            "TRUSTED",
            "190.0",
            "48",
            "2",
            "N_PLUS_1",
            "capacity-buffer-reduced",
            "monitoring",
            "repeat-failure-window-days",
            "14.0",
            "day",
            "warning",
            "TRUSTED",
        ),
        RECOVERY_BLOCKER(
            "STAGE-RECOVERY",
            "Recovery",
            "degraded",
            "degraded",
            "stable",
            "degraded",
            "blocked",
            "1.5",
            "5.0",
            "3.0",
            "Incident Command",
            "blocked",
            "awaiting-signoff",
            "REVIEW_REQUIRED",
            "restore-readiness-blocked",
            "missing-final-validation",
            "REVIEW_REQUIRED",
            "260.0",
            "80",
            "3",
            "N_PLUS_0",
            "restore-blocked",
            "vendor-engaged",
            "restore-readiness-score",
            "0.4",
            "ratio",
            "alerting",
            "REVIEW_REQUIRED",
            "110.0",
            "24",
            "1",
            "N_PLUS_1",
            "awaiting-signoff",
            "monitoring",
            "open-blocker-count",
            "3.0",
            "count",
            "warning",
            "REVIEW_REQUIRED",
        ),
    }
}

data class RecordedSourceScenarioGenerationRequest(
    val profile: RecordedSourceScenarioProfile,
    val seed: Int,
    val outputDirectory: Path,
    val batchId: String = "generated-${profile.value}-seed-$seed",
    val importedAt: Instant = Instant.parse("2026-06-10T00:00:00Z"),
) {
    init {
        require(seed >= 0) { "seed must be non-negative" }
        require(batchId.matches(Regex("[A-Za-z0-9._-]+"))) {
            "batchId must contain only letters, numbers, dot, underscore, or hyphen"
        }
    }
}

enum class RecordedSourceScenarioProfile(
    val value: String,
    val scenarioCount: Int,
    val invalidIncidentRows: Int,
    val duplicateWorkflowRows: Int,
) {
    DEMO("demo", scenarioCount = 4, invalidIncidentRows = 1, duplicateWorkflowRows = 1),
    MVP("mvp", scenarioCount = 48, invalidIncidentRows = 2, duplicateWorkflowRows = 2),
    STRESS("stress", scenarioCount = 600, invalidIncidentRows = 12, duplicateWorkflowRows = 12);

    companion object {
        fun fromValue(value: String): RecordedSourceScenarioProfile {
            return entries.firstOrNull { it.value == value.lowercase() }
                ?: error("Unknown recorded source scenario profile: $value")
        }
    }
}

data class RecordedSourceScenarioGenerationReport(
    val profile: RecordedSourceScenarioProfile,
    val seed: Int,
    val batchId: String,
    val outputDirectory: Path,
    val scenarioCount: Int,
    val totalRows: Int,
    val invalidIncidentRows: Int,
    val duplicateWorkflowRows: Int,
    val csvFiles: List<String>,
)
