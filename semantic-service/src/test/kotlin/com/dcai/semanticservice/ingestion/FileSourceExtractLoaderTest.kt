package com.dcai.semanticservice.ingestion

import com.dcai.semanticservice.runtime.SemanticServiceApplication
import kotlin.io.path.createTempFile
import kotlin.io.path.writeText
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith

class FileSourceExtractLoaderTest {
    private val repoRoot = SemanticServiceApplication.locateRepoRoot()

    @Test
    fun loadsControlledPropertiesFixture() {
        val batch = FileSourceExtractLoader().load(repoRoot.resolve("fixtures/source-extracts/local-controlled-source-v1.properties"))

        assertEquals("local-controlled-source-v1", batch.batchId)
        assertEquals("local-controlled-facility-ops-file", batch.sourceSystemId)
        assertEquals(1, batch.facilities.size)
        assertEquals(1, batch.zones.size)
        assertEquals(3, batch.assets.size)
        assertEquals(1, batch.incidents.size)
        assertEquals(2, batch.dependencies.size)
        assertEquals(1, batch.workflowEvents.size)
        assertEquals(1, batch.impacts.size)
        assertEquals(1, batch.evidence.size)
    }

    @Test
    fun rejectsInvalidSourceFile() {
        val path = createTempFile(prefix = "invalid-source-extract", suffix = ".properties")
        path.writeText(
            """
            format=dcai-source-extract-v1
            batch.id=bad-source
            sourceSystem.id=bad-source-system
            sourceSystem.label=Bad Source System
            importedAt=2026-06-09T00:00:00Z
            incidents.count=1
            incidents.0.recordId=SRC-INC-001
            incidents.0.payloadHash=sha256:bad
            incidents.0.incidentId=INC-001
            incidents.0.assetId=ASSET-001
            incidents.0.currentStageId=VALIDATION
            """.trimIndent(),
        )

        assertFailsWith<IllegalStateException> {
            FileSourceExtractLoader().load(path)
        }
    }
}
