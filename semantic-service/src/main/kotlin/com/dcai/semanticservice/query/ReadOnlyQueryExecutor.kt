package com.dcai.semanticservice.query

interface ReadOnlyQueryExecutor {
    fun execute(queryId: String): QueryExecutionReport
    fun execute(
        queryId: String,
        parameters: Map<String, String>,
    ): QueryExecutionReport = execute(queryId)
}

data class QueryExecutionReport(
    val queryId: String,
    val mode: QueryMode,
    val rowCount: Int = 0,
    val askResult: Boolean? = null,
    val rows: List<Map<String, String>> = emptyList(),
) {
    val succeeded: Boolean = true
}
