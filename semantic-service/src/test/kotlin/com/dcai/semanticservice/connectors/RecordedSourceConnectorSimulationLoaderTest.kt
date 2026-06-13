package com.dcai.semanticservice.connectors

import com.dcai.semanticservice.runtime.SemanticServiceApplication
import java.nio.file.Files
import java.nio.file.Path
import kotlin.io.path.writeText
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue

class RecordedSourceConnectorSimulationLoaderTest {
    private val repoRoot = SemanticServiceApplication.locateRepoRoot()
    private val fixtureDirectory = repoRoot.resolve("fixtures/source-extracts/recorded-source-systems/local-ops-v1")
    private val loader = RecordedSourceConnectorSimulationLoader()

    @Test
    fun mapsRecordedSourceExportsIntoSourceExtractDtoBatch() {
        val simulation = loader.load(fixtureDirectory)
        val batch = simulation.batch
        val report = simulation.report

        assertEquals("recorded-local-ops-v1", batch.batchId)
        assertEquals("recorded-facility-ops", batch.sourceSystemId)
        assertEquals(1, batch.facilities.size)
        assertEquals(3, batch.zones.size)
        assertEquals(4, batch.assets.size)
        assertEquals(2, batch.incidents.size)
        assertEquals(3, batch.dependencies.size)
        assertEquals(2, batch.workflowEvents.size)
        assertEquals(6, batch.evidence.size)
        assertEquals(2, batch.impacts.size)

        assertEquals(23, batch.allSourceRecords.size)
        assertEquals(23, report.totalRows)
        assertEquals(21, report.acceptedRows)
        assertEquals(2, report.rejectedRowCount)
        assertTrue(report.batchHistoryEntry.contains("accepted=21"))
        assertTrue(report.batchHistoryEntry.contains("rejected=2"))
    }

    @Test
    fun quarantinesInvalidRowsAndDuplicateEventsWithoutRejectingWholeBatch() {
        val report = loader.load(fixtureDirectory).report

        assertTrue(
            report.rejectedRows.any {
                it.sourceFile == "incidents.csv" &&
                    it.rowNumber == 4 &&
                    it.reason == "missing required field assetId"
            },
            report.rejectedRows.joinToString(separator = "\n"),
        )
        assertTrue(
            report.rejectedRows.any {
                it.sourceFile == "workflow_events.csv" &&
                    it.reason == "duplicate eventId=WF-OPS-1001-VALIDATION"
            },
            report.rejectedRows.joinToString(separator = "\n"),
        )
    }

    @Test
    fun loadsRecordedExportsDeterministicallyAcrossReruns() {
        val first = loader.load(fixtureDirectory)
        val second = loader.load(fixtureDirectory)

        assertEquals(first.report.batchHistoryEntry, second.report.batchHistoryEntry)
        assertEquals(
            first.batch.allSourceRecords.map { it.recordId to it.payloadHash },
            second.batch.allSourceRecords.map { it.recordId to it.payloadHash },
        )
    }

    @Test
    fun rejectsUnsupportedFixtureFormat() {
        val directory = Files.createTempDirectory("recorded-connector-invalid")
        directory.resolve("manifest.properties").writeText(
            """
            format=unsupported
            batch.id=bad
            sourceSystem.id=bad-source
            sourceSystem.label=Bad Source
            importedAt=2026-06-10T00:00:00Z
            """.trimIndent(),
        )

        assertFailsWith<IllegalArgumentException> {
            loader.load(directory)
        }
    }

    @Test
    fun rejectsMalformedCsvRows() {
        val directory = Files.createTempDirectory("recorded-connector-malformed")
        writeMinimalManifest(directory)
        directory.resolve("facilities.csv").writeText(
            """
            facilityId,label
            FAC-1,Facility One,extra-value
            """.trimIndent(),
        )

        assertFailsWith<IllegalArgumentException> {
            loader.load(directory)
        }
    }

    private fun writeMinimalManifest(directory: Path) {
        directory.resolve("manifest.properties").writeText(
            """
            format=dcai-recorded-connector-simulation-v1
            batch.id=malformed
            sourceSystem.id=malformed-source
            sourceSystem.label=Malformed Source
            importedAt=2026-06-10T00:00:00Z
            """.trimIndent(),
        )
    }
}
