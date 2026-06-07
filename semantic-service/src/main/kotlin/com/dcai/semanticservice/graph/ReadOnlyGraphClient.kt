package com.dcai.semanticservice.graph

interface ReadOnlyGraphClient {
    fun checkConnectivity(): GraphConnectionCheck
}

data class GraphConnectionCheck(
    val reachable: Boolean,
    val datasetUrl: String,
    val queryEndpointUrl: String,
    val namedGraphCount: Int? = null,
    val message: String,
)
