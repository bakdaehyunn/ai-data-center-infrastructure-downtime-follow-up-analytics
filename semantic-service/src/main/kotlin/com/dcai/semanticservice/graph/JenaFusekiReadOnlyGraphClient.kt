package com.dcai.semanticservice.graph

import org.apache.jena.query.QuerySolution
import org.apache.jena.sparql.exec.http.QueryExecutionHTTP

class JenaFusekiReadOnlyGraphClient(
    private val config: FusekiReadOnlyConfig = FusekiReadOnlyConfig.fromEnvironment(),
) : ReadOnlyGraphClient {
    override fun checkConnectivity(): GraphConnectionCheck {
        return try {
            val namedGraphCount = countNamedGraphs()
            GraphConnectionCheck(
                reachable = true,
                datasetUrl = config.datasetUrl,
                queryEndpointUrl = config.queryEndpointUrl,
                namedGraphCount = namedGraphCount,
                message = "Read-only Fuseki query endpoint is reachable.",
            )
        } catch (error: RuntimeException) {
            GraphConnectionCheck(
                reachable = false,
                datasetUrl = config.datasetUrl,
                queryEndpointUrl = config.queryEndpointUrl,
                message = error.message ?: error.javaClass.simpleName,
            )
        }
    }

    private fun countNamedGraphs(): Int {
        QueryExecutionHTTP
            .service(config.queryEndpointUrl)
            .query(NAMED_GRAPH_COUNT_QUERY)
            .build()
            .use { execution ->
                val results = execution.execSelect()
                return if (results.hasNext()) {
                    results.next().intValue("graphCount")
                } else {
                    0
                }
            }
    }

    private fun QuerySolution.intValue(name: String): Int {
        return getLiteral(name).int
    }

    private companion object {
        private const val NAMED_GRAPH_COUNT_QUERY = """
            SELECT (COUNT(DISTINCT ?graph) AS ?graphCount)
            WHERE {
              GRAPH ?graph { ?s ?p ?o }
            }
        """
    }
}
