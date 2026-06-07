package com.dcai.semanticservice.query

interface ReadOnlyQueryExecutor {
    fun execute(queryId: String): QueryExecutionReport
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
