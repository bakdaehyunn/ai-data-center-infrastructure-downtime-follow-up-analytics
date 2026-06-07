package com.dcai.semanticservice.graph

import kotlin.test.Test
import kotlin.test.assertFailsWith
import org.apache.jena.rdf.model.ModelFactory

class FusekiNamedGraphWriterTest {
    @Test
    fun rejectsNonFixtureGraphUriBeforeNetworkWrite() {
        val writer = FusekiNamedGraphWriter(
            FusekiGraphStoreConfig(
                datasetUrl = "http://127.0.0.1:1/infrastructure",
                graphStoreUrl = "http://127.0.0.1:1/infrastructure/data",
            ),
        )

        assertFailsWith<IllegalArgumentException> {
            writer.replaceNamedGraph("urn:dcai:graph:canonical", ModelFactory.createDefaultModel())
        }
    }
}
