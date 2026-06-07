package com.dcai.semanticservice.graph

import java.net.HttpURLConnection
import java.net.URI
import java.net.URLEncoder
import java.nio.charset.StandardCharsets
import org.apache.jena.rdf.model.Model
import org.apache.jena.riot.Lang
import org.apache.jena.riot.RDFDataMgr

class FusekiNamedGraphWriter(
    private val config: FusekiGraphStoreConfig = FusekiGraphStoreConfig.fromEnvironment(),
) : NamedGraphWriter {
    override fun replaceNamedGraph(graphUri: String, model: Model): NamedGraphWriteResult {
        require(graphUri.startsWith("urn:dcai:graph:fixture:")) {
            "Only controlled fixture graph URIs can be written"
        }

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

    private companion object {
        private const val TIMEOUT_MILLIS = 10_000
    }
}
