package com.dcai.semanticservice.fixtures

import com.dcai.semanticservice.graph.NamedGraphWriteResult
import com.dcai.semanticservice.graph.NamedGraphWriter
import com.dcai.semanticservice.runtime.SemanticServiceApplication
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFalse
import kotlin.test.assertTrue
import org.apache.jena.rdf.model.Model

class ControlledFixtureGraphLoaderTest {
    private val repoRoot = SemanticServiceApplication.locateRepoRoot()

    @Test
    fun writesSourceAndCanonicalGraphsOnlyAfterValidation() {
        val writer = RecordingNamedGraphWriter()
        val target = FixtureGraphTarget(
            path = repoRoot.resolve("fixtures/rdf/valid/minimal-incident.ttl"),
            sourceGraphUri = "urn:dcai:graph:fixture:source:minimal-incident",
            canonicalGraphUri = "urn:dcai:graph:fixture:canonical:minimal-incident",
        )

        val summary = ControlledFixtureGraphLoader(
            validationGate = FixtureValidationGate(repoRoot),
            writer = writer,
        ).load(FixtureGraphLoadPlan(listOf(target)))

        assertTrue(summary.succeeded, summary.errors.joinToString(separator = "\n"))
        assertEquals(1, summary.promotedCount)
        assertEquals(
            listOf(target.sourceGraphUri, target.canonicalGraphUri),
            writer.writes.map { it.graphUri },
        )
    }

    @Test
    fun doesNotWriteAnyGraphWhenValidationFails() {
        val writer = RecordingNamedGraphWriter()
        val target = FixtureGraphTarget(
            path = repoRoot.resolve("fixtures/rdf/invalid/missing-asset-link.ttl"),
            sourceGraphUri = "urn:dcai:graph:fixture:source:invalid",
            canonicalGraphUri = "urn:dcai:graph:fixture:canonical:invalid",
        )

        val summary = ControlledFixtureGraphLoader(
            validationGate = FixtureValidationGate(repoRoot),
            writer = writer,
        ).load(FixtureGraphLoadPlan(listOf(target)))

        assertFalse(summary.succeeded)
        assertTrue(summary.errors.isNotEmpty())
        assertEquals(emptyList(), writer.writes)
    }

    @Test
    fun doesNotWritePartialPlanWhenAnyFixtureFails() {
        val writer = RecordingNamedGraphWriter()
        val validTarget = FixtureGraphTarget(
            path = repoRoot.resolve("fixtures/rdf/valid/minimal-incident.ttl"),
            sourceGraphUri = "urn:dcai:graph:fixture:source:minimal-incident",
            canonicalGraphUri = "urn:dcai:graph:fixture:canonical:minimal-incident",
        )
        val invalidTarget = FixtureGraphTarget(
            path = repoRoot.resolve("fixtures/rdf/invalid/missing-asset-link.ttl"),
            sourceGraphUri = "urn:dcai:graph:fixture:source:invalid",
            canonicalGraphUri = "urn:dcai:graph:fixture:canonical:invalid",
        )

        val summary = ControlledFixtureGraphLoader(
            validationGate = FixtureValidationGate(repoRoot),
            writer = writer,
        ).load(FixtureGraphLoadPlan(listOf(validTarget, invalidTarget)))

        assertFalse(summary.succeeded)
        assertTrue(summary.errors.isNotEmpty())
        assertEquals(emptyList(), writer.writes)
    }

    private class RecordingNamedGraphWriter : NamedGraphWriter {
        val writes = mutableListOf<NamedGraphWriteResult>()

        override fun replaceNamedGraph(graphUri: String, model: Model): NamedGraphWriteResult {
            val result = NamedGraphWriteResult(
                graphUri = graphUri,
                tripleCount = model.size().toInt(),
                statusCode = 200,
            )
            writes += result
            return result
        }
    }
}
