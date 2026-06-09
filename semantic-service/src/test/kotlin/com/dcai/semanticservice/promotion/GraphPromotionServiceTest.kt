package com.dcai.semanticservice.promotion

import com.dcai.semanticservice.graph.NamedGraphSnapshot
import com.dcai.semanticservice.graph.NamedGraphStore
import com.dcai.semanticservice.graph.NamedGraphWriteResult
import com.dcai.semanticservice.ingestion.SourceExtractRdfMapper
import com.dcai.semanticservice.runtime.SemanticServiceApplication
import com.dcai.semanticservice.testfixtures.ProductionSourceExtractFixtures
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertNull
import kotlin.test.assertTrue
import org.apache.jena.rdf.model.Model
import org.apache.jena.rdf.model.ModelFactory
import org.apache.jena.rdf.model.ResourceFactory
import org.apache.jena.vocabulary.RDF

class GraphPromotionServiceTest {
    private val repoRoot = SemanticServiceApplication.locateRepoRoot()

    @Test
    fun writesSourceCanonicalAndProvenanceGraphsAfterValidation() {
        val store = InMemoryNamedGraphStore()
        val graphs = ProductionGraphUris.forRelease("release-2026-06-ingestion-v1")
        val result = service(store).promote(
            ProductionGraphPromotionPlan(
                batch = ProductionSourceExtractFixtures.validBatch(),
                graphs = graphs,
            ),
        )

        assertTrue(result.promoted, result.errors.joinToString(separator = "\n"))
        assertTrue(result.validation.conforms)
        assertEquals(
            listOf(graphs.sourceGraphUri, graphs.canonicalGraphUri, graphs.provenanceGraphUri),
            result.writtenGraphUris,
        )
        assertEquals(result.writtenGraphUris, store.writeOrder)
        assertTrue(store.graph(graphs.sourceGraphUri)!!.size() > 0)
        assertTrue(store.graph(graphs.canonicalGraphUri)!!.contains(incident("INC-001"), RDF.type))
        assertTrue(store.graph(graphs.provenanceGraphUri)!!.contains(promotionActivity("release-2026-06-ingestion-v1"), RDF.type))
        assertEquals("release-2026-06-ingestion-v1", result.releaseManifest?.releaseId)
    }

    @Test
    fun doesNotWriteGraphsWhenValidationFails() {
        val store = InMemoryNamedGraphStore()
        val result = service(store).promote(
            ProductionGraphPromotionPlan(
                batch = ProductionSourceExtractFixtures.invalidMissingZoneBatch(),
                graphs = ProductionGraphUris.forRelease("release-2026-06-ingestion-invalid"),
            ),
        )

        assertFalse(result.promoted)
        assertFalse(result.validation.conforms)
        assertEquals(emptyList(), store.writeOrder)
    }

    @Test
    fun restoresPreviousGraphsWhenPromotionWriteFails() {
        val graphs = ProductionGraphUris.forRelease("release-2026-06-ingestion-v1")
        val existingCanonical = markerModel("previous-canonical")
        val existingProvenance = markerModel("previous-provenance")
        val store = InMemoryNamedGraphStore(
            initialGraphs = mapOf(
                graphs.canonicalGraphUri to existingCanonical,
                graphs.provenanceGraphUri to existingProvenance,
            ),
            failOnReplaceGraphUri = graphs.provenanceGraphUri,
        )

        val result = service(store).promote(
            ProductionGraphPromotionPlan(
                batch = ProductionSourceExtractFixtures.validBatch(),
                graphs = graphs,
            ),
        )

        assertFalse(result.promoted)
        assertTrue(result.validation.conforms)
        assertTrue(result.rollbackAttempted)
        assertTrue(result.rollbackSucceeded, result.errors.joinToString(separator = "\n"))
        assertNull(store.graph(graphs.sourceGraphUri))
        assertTrue(store.graph(graphs.canonicalGraphUri)!!.isIsomorphicWith(existingCanonical))
        assertTrue(store.graph(graphs.provenanceGraphUri)!!.isIsomorphicWith(existingProvenance))
    }

    @Test
    fun rejectsUnmanagedGraphUris() {
        assertFailsWith<IllegalArgumentException> {
            ProductionGraphUris(
                sourceGraphUri = "urn:dcai:graph:fixture:source:not-production",
                canonicalGraphUri = "urn:dcai:graph:canonical:release-2026-06",
                provenanceGraphUri = "urn:dcai:graph:provenance:release-2026-06",
            )
        }
    }

    private fun service(store: NamedGraphStore): GraphPromotionService {
        return GraphPromotionService(
            mapper = SourceExtractRdfMapper(),
            validationGate = ProductionGraphValidationGate(repoRoot),
            graphStore = store,
        )
    }

    private fun markerModel(label: String): Model {
        return ModelFactory.createDefaultModel().apply {
            add(
                ResourceFactory.createResource("urn:dcai:test:$label"),
                ResourceFactory.createProperty("urn:dcai:test:marker"),
                label,
            )
        }
    }

    private fun incident(id: String) = ResourceFactory.createResource("urn:dcai:incident:$id")

    private fun promotionActivity(id: String) = ResourceFactory.createResource("urn:dcai:promotion-activity:$id")

    private class InMemoryNamedGraphStore(
        initialGraphs: Map<String, Model> = emptyMap(),
        private val failOnReplaceGraphUri: String? = null,
    ) : NamedGraphStore {
        private val graphs = initialGraphs.mapValuesTo(mutableMapOf()) { (_, model) ->
            ModelFactory.createDefaultModel().add(model)
        }
        val writeOrder = mutableListOf<String>()

        fun graph(graphUri: String): Model? = graphs[graphUri]

        override fun readNamedGraph(graphUri: String): NamedGraphSnapshot {
            val model = graphs[graphUri]
            return NamedGraphSnapshot(
                graphUri = graphUri,
                exists = model != null,
                model = model?.let { ModelFactory.createDefaultModel().add(it) } ?: ModelFactory.createDefaultModel(),
            )
        }

        override fun replaceNamedGraph(graphUri: String, model: Model): NamedGraphWriteResult {
            if (graphUri == failOnReplaceGraphUri) {
                error("simulated write failure for $graphUri")
            }
            writeOrder += graphUri
            graphs[graphUri] = ModelFactory.createDefaultModel().add(model)
            return NamedGraphWriteResult(
                graphUri = graphUri,
                tripleCount = model.size().toInt(),
                statusCode = 200,
            )
        }

        override fun deleteNamedGraph(graphUri: String): NamedGraphWriteResult {
            graphs.remove(graphUri)
            return NamedGraphWriteResult(
                graphUri = graphUri,
                tripleCount = 0,
                statusCode = 204,
            )
        }
    }
}
