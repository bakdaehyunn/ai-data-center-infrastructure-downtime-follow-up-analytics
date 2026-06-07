package com.dcai.semanticservice.api

import com.dcai.semanticservice.graph.FusekiReadOnlyConfig
import com.dcai.semanticservice.query.ApprovedQueryCatalog
import com.dcai.semanticservice.query.JenaFusekiReadOnlyQueryExecutor
import com.dcai.semanticservice.query.QueryResultShaper
import com.dcai.semanticservice.query.ReadOnlyQueryExecutor
import com.dcai.semanticservice.response.SemanticErrorCode
import com.dcai.semanticservice.response.SemanticResponseSerializer
import com.sun.net.httpserver.HttpExchange
import com.sun.net.httpserver.HttpServer
import java.net.InetSocketAddress
import java.net.URLDecoder
import java.nio.charset.StandardCharsets
import java.nio.file.Path

class PrivateSemanticQueryEndpoint(
    private val queryExecutor: ReadOnlyQueryExecutor,
    private val queryResultShaper: QueryResultShaper,
    private val responseSerializer: SemanticResponseSerializer = SemanticResponseSerializer(),
    private val allowedQueryIds: Set<String> = APPROVED_PRIVATE_QUERY_IDS,
) {
    fun handle(request: PrivateSemanticQueryRequest): PrivateSemanticQueryResponse {
        if (request.method != "POST") {
            return error(
                statusCode = 405,
                code = SemanticErrorCode.CONTRACT_VALIDATION_FAILED,
                message = "Private semantic query endpoint requires POST.",
            )
        }

        val queryId = request.queryId()
            ?: return error(
                statusCode = 404,
                code = SemanticErrorCode.CONTRACT_VALIDATION_FAILED,
                message = "Private semantic query route must match /semantic/query/{queryId}.",
            )

        if (request.body.containsRawSparql()) {
            return error(
                statusCode = 400,
                code = SemanticErrorCode.CONTRACT_VALIDATION_FAILED,
                message = "Private semantic query endpoint does not accept raw SPARQL.",
                queryId = queryId,
            )
        }

        if (queryId !in allowedQueryIds) {
            return error(
                statusCode = 400,
                code = SemanticErrorCode.UNAPPROVED_QUERY_ID,
                message = "Query id is not approved for the private semantic endpoint.",
                detail = "Only approved private semantic query IDs are enabled.",
                queryId = queryId,
            )
        }

        return try {
            val report = queryExecutor.execute(queryId)
            val envelope = queryResultShaper.shape(report)
            PrivateSemanticQueryResponse(
                statusCode = 200,
                payload = responseSerializer.serialize(envelope),
            )
        } catch (error: IllegalArgumentException) {
            val code = if (error.message.orEmpty().contains("Missing required binding")) {
                SemanticErrorCode.MISSING_REQUIRED_BINDING
            } else {
                SemanticErrorCode.CONTRACT_VALIDATION_FAILED
            }
            error(
                statusCode = 400,
                code = code,
                message = error.message ?: "Semantic query response failed contract validation.",
                queryId = queryId,
            )
        } catch (error: IllegalStateException) {
            val message = error.message.orEmpty()
            val code = when {
                message.contains("No result envelope contract") -> SemanticErrorCode.UNSUPPORTED_RESULT_ENVELOPE
                message.contains("Unapproved query id") -> SemanticErrorCode.UNAPPROVED_QUERY_ID
                else -> SemanticErrorCode.INTERNAL_SEMANTIC_SERVICE_ERROR
            }
            error(
                statusCode = if (code == SemanticErrorCode.UNAPPROVED_QUERY_ID) 400 else 500,
                code = code,
                message = message.ifBlank { "Semantic query execution failed." },
                queryId = queryId,
            )
        } catch (error: RuntimeException) {
            error(
                statusCode = 503,
                code = SemanticErrorCode.GRAPH_UNAVAILABLE,
                message = "Graph query endpoint is unavailable.",
                detail = error.message,
                queryId = queryId,
            )
        }
    }

    private fun error(
        statusCode: Int,
        code: SemanticErrorCode,
        message: String,
        detail: String? = null,
        queryId: String? = null,
    ): PrivateSemanticQueryResponse {
        return PrivateSemanticQueryResponse(
            statusCode = statusCode,
            payload = responseSerializer.error(
                code = code,
                message = message,
                detail = detail,
                queryId = queryId,
            ),
        )
    }

    private fun PrivateSemanticQueryRequest.queryId(): String? {
        val prefix = "/semantic/query/"
        if (!path.startsWith(prefix)) {
            return null
        }
        val encoded = path.removePrefix(prefix).substringBefore("/")
        if (encoded.isBlank()) {
            return null
        }
        return URLDecoder.decode(encoded, StandardCharsets.UTF_8)
    }

    private fun String.containsRawSparql(): Boolean {
        val normalized = lowercase()
        return normalized.contains("\"sparql\"") ||
            normalized.contains("\"query\"") ||
            RAW_SPARQL_KEYWORD.containsMatchIn(this)
    }

    companion object {
        private val RAW_SPARQL_KEYWORD = Regex(
            pattern = "\\b(select|ask|construct|describe|insert|delete|update|where)\\b",
            options = setOf(RegexOption.IGNORE_CASE),
        )
        val APPROVED_PRIVATE_QUERY_IDS = setOf(
            "fixtureNamedGraphInventory",
            "fixtureIncidentSummary",
            "fixtureProvenanceSourceRecords",
            "semanticFollowUpQueueList",
            "semanticDashboardOverview",
            "semanticFilterMetadata",
            "semanticFollowUpDetail",
            "semanticImpactSummary",
            "semanticTopologyDependencies",
            "semanticTrustFindingList",
            "semanticStageBottlenecks",
            "semanticAssetDelaySummary",
            "semanticZoneDelaySummary",
            "semanticSpareWaitSummary",
            "semanticValidationSummary",
            "semanticIncidentEvidence",
            "semanticIncidentTimeline",
            "semanticDependencyImpactByAsset",
            "semanticBlastRadiusByAsset",
        )
    }
}

data class PrivateSemanticQueryRequest(
    val method: String,
    val path: String,
    val body: String = "",
)

data class PrivateSemanticQueryResponse(
    val statusCode: Int,
    val payload: Map<String, Any>,
    val contentType: String = "application/json; charset=utf-8",
) {
    fun jsonBody(): String = JsonPayloadWriter.write(payload)
}

class PrivateSemanticQueryEndpointServer(
    private val endpoint: PrivateSemanticQueryEndpoint,
    private val config: PrivateSemanticQueryEndpointServerConfig = PrivateSemanticQueryEndpointServerConfig(),
) : AutoCloseable {
    private val server: HttpServer = HttpServer.create(InetSocketAddress(config.host, config.port), 0)

    val address: InetSocketAddress
        get() = server.address

    fun start(): PrivateSemanticQueryEndpointServer {
        server.createContext("/semantic/query") { exchange -> handle(exchange) }
        server.executor = null
        server.start()
        return this
    }

    override fun close() {
        server.stop(0)
    }

    private fun handle(exchange: HttpExchange) {
        exchange.responseHeaders.set("Access-Control-Allow-Origin", config.corsAllowOrigin)
        exchange.responseHeaders.set("Access-Control-Allow-Methods", "POST, OPTIONS")
        exchange.responseHeaders.set("Access-Control-Allow-Headers", "Content-Type")
        if (exchange.requestMethod == "OPTIONS") {
            exchange.sendResponseHeaders(204, -1)
            exchange.close()
            return
        }

        val response = endpoint.handle(
            PrivateSemanticQueryRequest(
                method = exchange.requestMethod,
                path = exchange.requestURI.path,
                body = exchange.requestBody.bufferedReader(StandardCharsets.UTF_8).use { it.readText() },
            ),
        )
        val bytes = response.jsonBody().toByteArray(StandardCharsets.UTF_8)
        exchange.responseHeaders.set("Content-Type", response.contentType)
        exchange.sendResponseHeaders(response.statusCode, bytes.size.toLong())
        exchange.responseBody.use { output -> output.write(bytes) }
    }

    companion object {
        fun fromRepoRoot(
            repoRoot: Path,
            config: PrivateSemanticQueryEndpointServerConfig = PrivateSemanticQueryEndpointServerConfig(),
            fusekiConfig: FusekiReadOnlyConfig = FusekiReadOnlyConfig.fromEnvironment(),
        ): PrivateSemanticQueryEndpointServer {
            val manifest = ApprovedQueryCatalog(repoRoot).load()
            val endpoint = PrivateSemanticQueryEndpoint(
                queryExecutor = JenaFusekiReadOnlyQueryExecutor(
                    manifest = manifest,
                    config = fusekiConfig,
                ),
                queryResultShaper = QueryResultShaper(manifest),
            )
            return PrivateSemanticQueryEndpointServer(endpoint, config)
        }
    }
}

data class PrivateSemanticQueryEndpointServerConfig(
    val host: String = "127.0.0.1",
    val port: Int = 18080,
    val corsAllowOrigin: String = "*",
) {
    init {
        require(host == "127.0.0.1" || host == "localhost") {
            "private semantic endpoint must bind to a loopback host"
        }
        require(port in 0..65535) { "port must be between 0 and 65535" }
    }
}

object JsonPayloadWriter {
    fun write(value: Any?): String {
        return when (value) {
            null -> "null"
            is String -> "\"${value.escapeJson()}\""
            is Number,
            is Boolean,
            -> value.toString()
            is Map<*, *> -> value.entries.joinToString(
                prefix = "{",
                postfix = "}",
            ) { (key, entryValue) ->
                "\"${key.toString().escapeJson()}\":${write(entryValue)}"
            }
            is Iterable<*> -> value.joinToString(prefix = "[", postfix = "]") { item -> write(item) }
            else -> "\"${value.toString().escapeJson()}\""
        }
    }

    private fun String.escapeJson(): String {
        return buildString {
            for (char in this@escapeJson) {
                when (char) {
                    '\\' -> append("\\\\")
                    '"' -> append("\\\"")
                    '\b' -> append("\\b")
                    '\u000C' -> append("\\f")
                    '\n' -> append("\\n")
                    '\r' -> append("\\r")
                    '\t' -> append("\\t")
                    else -> {
                        if (char.code < 0x20) {
                            append("\\u")
                            append(char.code.toString(16).padStart(4, '0'))
                        } else {
                            append(char)
                        }
                    }
                }
            }
        }
    }
}
