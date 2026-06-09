package com.dcai.semanticservice.graph

import java.net.HttpURLConnection
import java.net.URI
import java.net.URLEncoder
import java.nio.charset.StandardCharsets
import org.apache.jena.rdf.model.Model
import org.apache.jena.rdf.model.ModelFactory
import org.apache.jena.riot.Lang
import org.apache.jena.riot.RDFDataMgr

class FusekiNamedGraphWriter(
    private val config: FusekiGraphStoreConfig = FusekiGraphStoreConfig.fromEnvironment(),
) : NamedGraphStore {
    override fun replaceNamedGraph(graphUri: String, model: Model): NamedGraphWriteResult {
        requireControlledGraphUri(graphUri)

        val encodedGraphUri = URLEncoder.encode(graphUri, StandardCharsets.UTF_8)
        val url = URI("${config.graphStoreUrl}?graph=$encodedGraphUri").toURL()
        val connection = (url.openConnection() as HttpURLConnection).apply {
            requestMethod = "PUT"
            doOutput = true
            connectTimeout = TIMEOUT_MILLIS
            readTimeout = TIMEOUT_MILLIS
            setRequestProperty("Content-Type", "text/turtle; charset=utf-8")
        }

        return try {
            connection.outputStream.use { output ->
                RDFDataMgr.write(output, model, Lang.TURTLE)
            }

            val statusCode = connection.responseCode
            if (statusCode !in 200..299) {
                val body = connection.errorStream?.bufferedReader()?.use { it.readText() }.orEmpty()
                error("Fuseki graph-store write failed with HTTP $statusCode: $body")
            }

            NamedGraphWriteResult(
                graphUri = graphUri,
                tripleCount = model.size().toInt(),
                statusCode = statusCode,
            )
        } finally {
            connection.disconnect()
        }
    }

    override fun readNamedGraph(graphUri: String): NamedGraphSnapshot {
        requireControlledGraphUri(graphUri)

        val encodedGraphUri = URLEncoder.encode(graphUri, StandardCharsets.UTF_8)
        val url = URI("${config.graphStoreUrl}?graph=$encodedGraphUri").toURL()
        val connection = (url.openConnection() as HttpURLConnection).apply {
            requestMethod = "GET"
            connectTimeout = TIMEOUT_MILLIS
            readTimeout = TIMEOUT_MILLIS
            setRequestProperty("Accept", "text/turtle")
        }

        return try {
            val statusCode = connection.responseCode
            if (statusCode == 404) {
                return NamedGraphSnapshot(
                    graphUri = graphUri,
                    exists = false,
                    model = ModelFactory.createDefaultModel(),
                )
            }
            if (statusCode !in 200..299) {
                val body = connection.errorStream?.bufferedReader()?.use { it.readText() }.orEmpty()
                error("Fuseki graph-store read failed with HTTP $statusCode: $body")
            }

            val model = ModelFactory.createDefaultModel()
            connection.inputStream.use { input -> RDFDataMgr.read(model, input, Lang.TURTLE) }
            NamedGraphSnapshot(
                graphUri = graphUri,
                exists = true,
                model = model,
            )
        } finally {
            connection.disconnect()
        }
    }

    override fun deleteNamedGraph(graphUri: String): NamedGraphWriteResult {
        requireControlledGraphUri(graphUri)

        val encodedGraphUri = URLEncoder.encode(graphUri, StandardCharsets.UTF_8)
        val url = URI("${config.graphStoreUrl}?graph=$encodedGraphUri").toURL()
        val connection = (url.openConnection() as HttpURLConnection).apply {
            requestMethod = "DELETE"
            connectTimeout = TIMEOUT_MILLIS
            readTimeout = TIMEOUT_MILLIS
        }

        return try {
            val statusCode = connection.responseCode
            if (statusCode !in setOf(200, 202, 204, 404)) {
                val body = connection.errorStream?.bufferedReader()?.use { it.readText() }.orEmpty()
                error("Fuseki graph-store delete failed with HTTP $statusCode: $body")
            }

            NamedGraphWriteResult(
                graphUri = graphUri,
                tripleCount = 0,
                statusCode = statusCode,
            )
        } finally {
            connection.disconnect()
        }
    }

    private fun requireControlledGraphUri(graphUri: String) {
        require(CONTROLLED_GRAPH_PREFIXES.any { prefix -> graphUri.startsWith(prefix) && graphUri.length > prefix.length }) {
            "Only controlled DCAI graph URIs can be written"
        }
    }

    private companion object {
        private const val TIMEOUT_MILLIS = 10_000
        private val CONTROLLED_GRAPH_PREFIXES = setOf(
            "urn:dcai:graph:fixture:",
            "urn:dcai:graph:source:",
            "urn:dcai:graph:canonical:",
            "urn:dcai:graph:provenance:",
            "urn:dcai:graph:reasoning-audit:",
            "urn:dcai:graph:reasoning:",
        )
    }
}
