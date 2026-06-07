package com.dcai.semanticservice.graph

import kotlin.test.Test
import kotlin.test.assertEquals

class FusekiReadOnlyConfigTest {
    @Test
    fun usesDefaultLocalFusekiDataset() {
        val config = FusekiReadOnlyConfig.fromEnvironment(emptyMap())

        assertEquals("http://localhost:3030/infrastructure", config.datasetUrl)
        assertEquals("http://localhost:3030/infrastructure/query", config.queryEndpointUrl)
    }

    @Test
    fun acceptsExplicitDatasetAndQueryUrls() {
        val config = FusekiReadOnlyConfig.fromEnvironment(
            mapOf(
                "DCAI_FUSEKI_DATASET_URL" to "http://fuseki:3030/infrastructure/",
                "DCAI_FUSEKI_QUERY_URL" to "http://fuseki:3030/infrastructure/sparql",
            ),
        )

        assertEquals("http://fuseki:3030/infrastructure", config.datasetUrl)
        assertEquals("http://fuseki:3030/infrastructure/sparql", config.queryEndpointUrl)
    }
}
