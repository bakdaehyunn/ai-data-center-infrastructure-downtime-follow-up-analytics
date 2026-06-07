package com.dcai.semanticservice.graph

import kotlin.test.Test
import kotlin.test.assertEquals

class FusekiGraphStoreConfigTest {
    @Test
    fun usesDefaultLocalGraphStoreUrl() {
        val config = FusekiGraphStoreConfig.fromEnvironment(emptyMap())

        assertEquals("http://localhost:3030/infrastructure", config.datasetUrl)
        assertEquals("http://localhost:3030/infrastructure/data", config.graphStoreUrl)
    }

    @Test
    fun acceptsExplicitGraphStoreUrl() {
        val config = FusekiGraphStoreConfig.fromEnvironment(
            mapOf(
                "DCAI_FUSEKI_DATASET_URL" to "http://fuseki:3030/infrastructure/",
                "DCAI_FUSEKI_GRAPH_STORE_URL" to "http://fuseki:3030/infrastructure/data/",
            ),
        )

        assertEquals("http://fuseki:3030/infrastructure", config.datasetUrl)
        assertEquals("http://fuseki:3030/infrastructure/data", config.graphStoreUrl)
    }
}
