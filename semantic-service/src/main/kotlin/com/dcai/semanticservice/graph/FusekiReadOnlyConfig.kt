package com.dcai.semanticservice.graph

data class FusekiReadOnlyConfig(
    val datasetUrl: String = DEFAULT_DATASET_URL,
    val queryEndpointUrl: String = "$datasetUrl/query",
) {
    init {
        require(datasetUrl.isNotBlank()) { "datasetUrl must not be blank" }
        require(queryEndpointUrl.isNotBlank()) { "queryEndpointUrl must not be blank" }
    }

    companion object {
        const val DEFAULT_DATASET_URL = "http://localhost:3030/infrastructure"

        fun fromEnvironment(
            env: Map<String, String> = System.getenv(),
        ): FusekiReadOnlyConfig {
            val datasetUrl = env["DCAI_FUSEKI_DATASET_URL"] ?: DEFAULT_DATASET_URL
            val queryEndpointUrl = env["DCAI_FUSEKI_QUERY_URL"] ?: "$datasetUrl/query"
            return FusekiReadOnlyConfig(
                datasetUrl = datasetUrl.trimEnd('/'),
                queryEndpointUrl = queryEndpointUrl,
            )
        }
    }
}
