package com.dcai.semanticservice.query

import com.dcai.semanticservice.graph.FusekiReadOnlyConfig
import org.apache.jena.query.QuerySolution
import org.apache.jena.rdf.model.RDFNode
import org.apache.jena.sparql.exec.http.QueryExecutionHTTP

class JenaFusekiReadOnlyQueryExecutor(
    private val manifest: ApprovedQueryManifest,
    private val config: FusekiReadOnlyConfig = FusekiReadOnlyConfig.fromEnvironment(),
) : ReadOnlyQueryExecutor {
    override fun execute(queryId: String): QueryExecutionReport {
        val definition = manifest.requireQuery(queryId)
        return when (definition.mode) {
            QueryMode.SELECT -> executeSelect(definition)
            QueryMode.ASK -> executeAsk(definition)
            QueryMode.CONSTRUCT,
            QueryMode.UPDATE,
            -> error("Query ${definition.id} is not approved for runtime read-only execution")
        }
    }

    private fun executeSelect(definition: ApprovedQueryDefinition): QueryExecutionReport {
        QueryExecutionHTTP
            .service(config.queryEndpointUrl)
            .query(definition.sparql)
            .build()
            .use { execution ->
                val results = execution.execSelect()
                val variables = results.resultVars
                val rows = mutableListOf<Map<String, String>>()
                while (results.hasNext()) {
                    val solution = results.next()
                    rows += variables.associateWith { variable ->
                        solution.stringValue(variable)
                    }
                }

                return QueryExecutionReport(
                    queryId = definition.id,
                    mode = definition.mode,
                    rowCount = rows.size,
                    rows = rows,
                )
            }
    }

    private fun executeAsk(definition: ApprovedQueryDefinition): QueryExecutionReport {
        QueryExecutionHTTP
            .service(config.queryEndpointUrl)
            .query(definition.sparql)
            .build()
            .use { execution ->
                val result = execution.execAsk()
                return QueryExecutionReport(
                    queryId = definition.id,
                    mode = definition.mode,
                    rowCount = 1,
                    askResult = result,
                )
            }
    }

    private fun QuerySolution.stringValue(variable: String): String {
        return get(variable)?.displayString().orEmpty()
    }

    private fun RDFNode.displayString(): String {
        return when {
            isLiteral -> asLiteral().lexicalForm
            isURIResource -> asResource().uri
            else -> toString()
        }
    }
}
