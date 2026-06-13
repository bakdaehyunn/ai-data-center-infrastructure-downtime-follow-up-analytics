package com.dcai.semanticservice.connectors

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
import java.nio.file.Path
import java.security.MessageDigest
import java.time.Instant
import java.util.Properties
import kotlin.io.path.exists
import kotlin.io.path.inputStream
import kotlin.io.path.readLines

class RecordedSourceConnectorSimulationLoader {
    fun load(directory: Path): RecordedConnectorSimulation {
        val manifest = directory.resolve("manifest.properties").loadProperties()
        require(manifest.required("format") == FORMAT) {
            "recorded connector manifest must declare format=$FORMAT"
        }

        val context = ConnectorLoadContext(
            directory = directory,
            sourceSystemId = manifest.required("sourceSystem.id"),
        )

        val facilities = context.loadRecords("facilities.csv", "facilityId") { row ->
            FacilitySourceRecord(
                recordId = row.recordId("FAC", row.required("facilityId")),
                payloadHash = row.payloadHash(),
                facilityId = row.required("facilityId"),
                label = row.optional("label"),
            )
        }
        val zones = context.loadRecords("zones.csv", "zoneId") { row ->
            ZoneSourceRecord(
                recordId = row.recordId("ZONE", row.required("zoneId")),
                payloadHash = row.payloadHash(),
                zoneId = row.required("zoneId"),
                facilityId = row.required("facilityId"),
                label = row.optional("label"),
            )
        }
        val assets = context.loadRecords("assets.csv", "assetId") { row ->
            AssetSourceRecord(
                recordId = row.recordId("ASSET", row.required("assetId")),
                payloadHash = row.payloadHash(),
                assetId = row.required("assetId"),
                zoneId = row.required("zoneId"),
                assetType = row.required("assetType"),
                criticalityLevel = row.optional("criticalityLevel"),
                operationalStatus = row.optional("operationalStatus"),
                hallId = row.optional("hallId"),
                rowId = row.optional("rowId"),
                rackId = row.optional("rackId"),
                capacityGroupId = row.optional("capacityGroupId"),
                assetClass = row.enumOptional<AssetClass>("assetClass") ?: AssetClass.INFRASTRUCTURE,
            )
        }
        val incidents = context.loadRecords("incidents.csv", "incidentId") { row ->
            IncidentSourceRecord(
                recordId = row.recordId("INC", row.required("incidentId")),
                payloadHash = row.payloadHash(),
                incidentId = row.required("incidentId"),
                assetId = row.required("assetId"),
                currentStageId = row.required("currentStageId"),
                currentStageLabel = row.required("currentStageLabel"),
            )
        }
        val dependencies = context.loadRecords("dependencies.csv", "edgeId") { row ->
            DependencySourceRecord(
                recordId = row.recordId("TOPO", row.required("edgeId")),
                payloadHash = row.payloadHash(),
                edgeId = row.required("edgeId"),
                dependentAssetId = row.required("dependentAssetId"),
                dependencyAssetId = row.required("dependencyAssetId"),
                dependencyRole = row.required("dependencyRole"),
                impactScope = row.required("impactScope"),
                pathId = row.optional("pathId"),
                pathClass = row.enumOptional<DependencyPathClass>("pathClass") ?: DependencyPathClass.DEPENDENCY,
            )
        }
        val workflowEvents = context.loadRecords("workflow_events.csv", "eventId") { row ->
            WorkflowEventSourceRecord(
                recordId = row.recordId("WF", row.required("eventId")),
                payloadHash = row.payloadHash(),
                eventId = row.required("eventId"),
                incidentId = row.required("incidentId"),
                enteredStageId = row.required("enteredStageId"),
                enteredStageLabel = row.required("enteredStageLabel"),
                status = row.required("status"),
                enteredAt = Instant.parse(row.required("enteredAt")),
                exitedAt = row.optional("exitedAt")?.let(Instant::parse),
                durationHours = row.optional("durationHours")?.let(::BigDecimal),
                delayHours = row.optional("delayHours")?.let(::BigDecimal),
            )
        }
        val workOrders = context.loadRecords("work_orders.csv", "workOrderId") { row ->
            EvidenceSourceRecord(
                recordId = row.recordId("WO", row.required("workOrderId")),
                payloadHash = row.payloadHash(),
                evidenceId = row.required("workOrderId"),
                evidenceClass = EvidenceClass.WORK_ORDER,
                supportsId = row.required("incidentId"),
                confidenceState = row.optional("confidenceState") ?: "TRUSTED",
                timestamp = Instant.parse(row.required("timestamp")),
                workOrderId = row.required("workOrderId"),
                workOrderStatus = row.optional("workOrderStatus"),
                assignedTeam = row.optional("assignedTeam"),
            )
        }
        val validationResults = context.loadRecords("validation_results.csv", "validationId") { row ->
            EvidenceSourceRecord(
                recordId = row.recordId("VAL", row.required("validationId")),
                payloadHash = row.payloadHash(),
                evidenceId = row.required("validationId"),
                evidenceClass = EvidenceClass.VALIDATION,
                supportsId = row.required("incidentId"),
                confidenceState = row.optional("confidenceState") ?: "TRUSTED",
                timestamp = Instant.parse(row.required("timestamp")),
                validationId = row.required("validationId"),
                validationStatus = row.required("validationStatus"),
            )
        }
        val telemetryImpacts = context.loadRecords("telemetry_impacts.csv", "impactId") { row ->
            TelemetryImpactRecord(
                impact = ImpactSourceRecord(
                    recordId = row.recordId("IMPACT", row.required("impactId")),
                    payloadHash = row.payloadHash(),
                    impactId = row.required("impactId"),
                    incidentId = row.required("incidentId"),
                    estimatedCapacityRiskKw = row.optional("estimatedCapacityRiskKw")?.let(::BigDecimal),
                    affectedGpuCount = row.optional("affectedGpuCount")?.toInt(),
                    affectedRackCount = row.optional("affectedRackCount")?.toInt(),
                    redundancyState = row.optional("redundancyState"),
                    mitigationState = row.optional("mitigationState"),
                    vendorState = row.optional("vendorState"),
                    vendorEtaAt = row.optional("vendorEtaAt")?.let(Instant::parse),
                ),
                evidence = EvidenceSourceRecord(
                    recordId = row.recordId("TEL", row.required("evidenceId")),
                    payloadHash = row.payloadHash(),
                    evidenceId = row.required("evidenceId"),
                    evidenceClass = EvidenceClass.TELEMETRY,
                    supportsId = row.required("impactId"),
                    confidenceState = row.optional("confidenceState") ?: "TRUSTED",
                    timestamp = Instant.parse(row.required("timestamp")),
                    metricName = row.optional("metricName"),
                    metricValue = row.optional("metricValue")?.let(::BigDecimal),
                    metricUnit = row.optional("metricUnit"),
                    telemetryStatus = row.optional("telemetryStatus"),
                ),
            )
        }

        val batch = SourceExtractBatch(
            batchId = manifest.required("batch.id"),
            sourceSystemId = manifest.required("sourceSystem.id"),
            sourceSystemLabel = manifest.required("sourceSystem.label"),
            importedAt = Instant.parse(manifest.required("importedAt")),
            facilities = facilities,
            zones = zones,
            assets = assets,
            incidents = incidents,
            dependencies = dependencies,
            workflowEvents = workflowEvents,
            evidence = workOrders + validationResults + telemetryImpacts.map { it.evidence },
            impacts = telemetryImpacts.map { it.impact },
        )

        return RecordedConnectorSimulation(
            batch = batch,
            report = RecordedConnectorSimulationReport(
                batchId = batch.batchId,
                sourceSystemId = batch.sourceSystemId,
                importedAt = batch.importedAt,
                sourceFiles = context.sourceFileReports.sortedBy { it.path },
                rejectedRows = context.rejectedRows,
            ),
        )
    }

    private data class TelemetryImpactRecord(
        val impact: ImpactSourceRecord,
        val evidence: EvidenceSourceRecord,
    )

    private class ConnectorLoadContext(
        private val directory: Path,
        private val sourceSystemId: String,
    ) {
        val sourceFileReports = mutableListOf<RecordedConnectorSourceFileReport>()
        val rejectedRows = mutableListOf<RecordedConnectorRejectedRow>()

        fun readRows(fileName: String): List<CsvRow> {
            val path = directory.resolve(fileName)
            if (!path.exists()) {
                sourceFileReports += RecordedConnectorSourceFileReport(fileName, totalRows = 0, acceptedRows = 0, rejectedRows = 0)
                return emptyList()
            }
            return parseCsv(path, fileName)
        }

        fun <T> loadRecords(
            fileName: String,
            naturalKey: String,
            build: (CsvRow) -> T,
        ): List<T> {
            return acceptRows(fileName, readRows(fileName), naturalKey, build)
        }

        fun <T> acceptRows(
            fileName: String,
            rows: List<CsvRow>,
            naturalKey: String,
            build: (CsvRow) -> T,
        ): List<T> {
            val seenKeys = mutableSetOf<String>()
            val accepted = mutableListOf<T>()
            var rejectedCount = 0

            rows.forEach { row ->
                runCatching {
                    val key = row.required(naturalKey)
                    require(seenKeys.add(key)) { "duplicate $naturalKey=$key" }
                    build(row)
                }.onSuccess { record ->
                    accepted += record
                }.onFailure { error ->
                    rejectedCount += 1
                    rejectedRows += RecordedConnectorRejectedRow(
                        sourceFile = fileName,
                        rowNumber = row.rowNumber,
                        reason = error.message ?: "record rejected",
                    )
                }
            }

            sourceFileReports += RecordedConnectorSourceFileReport(
                path = fileName,
                totalRows = rows.size,
                acceptedRows = accepted.size,
                rejectedRows = rejectedCount,
            )
            return accepted
        }

        private fun parseCsv(path: Path, fileName: String): List<CsvRow> {
            val lines = path.readLines().filter { it.isNotBlank() && !it.trimStart().startsWith("#") }
            if (lines.isEmpty()) {
                return emptyList()
            }
            val headers = lines.first().split(",").map { it.trim() }
            require(headers.all { it.isNotBlank() }) { "$fileName has a blank header" }
            return lines.drop(1).mapIndexed { index, line ->
                val values = line.split(",").map { it.trim() }
                require(values.size == headers.size) {
                    "$fileName row ${index + 2} has ${values.size} values for ${headers.size} headers"
                }
                CsvRow(
                    sourceSystemId = sourceSystemId,
                    sourceFile = fileName,
                    rowNumber = index + 2,
                    fields = headers.zip(values).toMap(),
                )
            }
        }
    }

    private data class CsvRow(
        val sourceSystemId: String,
        val sourceFile: String,
        val rowNumber: Int,
        val fields: Map<String, String>,
    ) {
        fun required(key: String): String {
            return optional(key) ?: error("missing required field $key")
        }

        fun optional(key: String): String? {
            return fields[key]?.trim()?.takeIf { it.isNotEmpty() }
        }

        fun recordId(prefix: String, naturalId: String): String {
            return optional("recordId") ?: "SRC-$prefix-$naturalId"
        }

        fun payloadHash(): String {
            val normalized = fields.toSortedMap().entries.joinToString(separator = "|") { (key, value) -> "$key=$value" }
            return "sha256:${sha256("$sourceSystemId|$sourceFile|$normalized")}"
        }

        inline fun <reified T : Enum<T>> enumOptional(key: String): T? {
            return optional(key)?.let { enumValueOf<T>(it) }
        }
    }

    private fun Path.loadProperties(): Properties {
        val properties = Properties()
        inputStream().use { input -> properties.load(input) }
        return properties
    }

    private fun Properties.required(key: String): String {
        return getProperty(key)?.trim()?.takeIf { it.isNotEmpty() }
            ?: error("Missing required recorded connector manifest field: $key")
    }

    private companion object {
        const val FORMAT = "dcai-recorded-connector-simulation-v1"

        fun sha256(value: String): String {
            val digest = MessageDigest.getInstance("SHA-256").digest(value.toByteArray(Charsets.UTF_8))
            return digest.joinToString(separator = "") { "%02x".format(it) }
        }
    }
}

data class RecordedConnectorSimulation(
    val batch: SourceExtractBatch,
    val report: RecordedConnectorSimulationReport,
)

data class RecordedConnectorSimulationReport(
    val batchId: String,
    val sourceSystemId: String,
    val importedAt: Instant,
    val sourceFiles: List<RecordedConnectorSourceFileReport>,
    val rejectedRows: List<RecordedConnectorRejectedRow>,
) {
    val totalRows: Int = sourceFiles.sumOf { it.totalRows }
    val acceptedRows: Int = sourceFiles.sumOf { it.acceptedRows }
    val rejectedRowCount: Int = sourceFiles.sumOf { it.rejectedRows }
    val batchHistoryEntry: String = "$batchId|$sourceSystemId|$importedAt|accepted=$acceptedRows|rejected=$rejectedRowCount"
}

data class RecordedConnectorSourceFileReport(
    val path: String,
    val totalRows: Int,
    val acceptedRows: Int,
    val rejectedRows: Int,
)

data class RecordedConnectorRejectedRow(
    val sourceFile: String,
    val rowNumber: Int,
    val reason: String,
)
