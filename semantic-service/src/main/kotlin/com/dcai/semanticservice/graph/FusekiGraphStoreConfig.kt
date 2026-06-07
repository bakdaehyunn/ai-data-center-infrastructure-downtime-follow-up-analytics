package com.dcai.semanticservice.graph

data class FusekiGraphStoreConfig(
    val datasetUrl: String = DEFAULT_DATASET_URL,
    val graphStoreUrl: String = "$datasetUrl/data",
) {
    init {
        require(datasetUrl.isNotBlank()) { "datasetUrl must not be blank" }
        require(graphStoreUrl.isNotBlank()) { "graphStoreUrl must not be blank" }
    }

    companion object {
        const val DEFAULT_DATASET_URL = FusekiReadOnlyConfig.DEFAULT_DATASET_URL

        fun fromEnvironment(
            env: Map<String, String> = System.getenv(),
        ): FusekiGraphStoreConfig {
            val datasetUrl = (env["DCAI_FUSEKI_DATASET_URL"] ?: DEFAULT_DATASET_URL).trimEnd('/')
            val graphStoreUrl = (env["DCAI_FUSEKI_GRAPH_STORE_URL"] ?: "$datasetUrl/data").trimEnd('/')
            return FusekiGraphStoreConfig(
                datasetUrl = datasetUrl,
                graphStoreUrl = graphStoreUrl,
            )
        }
    }
}
