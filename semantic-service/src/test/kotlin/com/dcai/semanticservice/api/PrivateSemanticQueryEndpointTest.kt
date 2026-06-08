package com.dcai.semanticservice.api

import com.dcai.semanticservice.query.ApprovedQueryDefinition
import com.dcai.semanticservice.query.ApprovedQueryManifest
import com.dcai.semanticservice.query.QueryExecutionReport
import com.dcai.semanticservice.query.QueryMode
import com.dcai.semanticservice.query.QueryResultShaper
import com.dcai.semanticservice.query.ReadOnlyQueryExecutor
import java.net.URI
import java.net.http.HttpClient
import java.net.http.HttpRequest
import java.net.http.HttpResponse
import java.nio.file.Path
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue

class PrivateSemanticQueryEndpointTest {
    @Test
    fun returnsSerializedPayloadForApprovedQueryId() {
        val endpoint = endpointWith(
            QueryExecutionReport(
                queryId = "fixtureNamedGraphInventory",
                mode = QueryMode.SELECT,
                rows = listOf(
                    mapOf(
                        "graph" to "urn:dcai:graph:fixture:canonical:minimal-incident",
                        "subjectCount" to "8",
                    ),
                ),
            ),
        )

        val response = endpoint.handle(post("/semantic/query/fixtureNamedGraphInventory"))

        assertEquals(200, response.statusCode)
        assertEquals("fixtureNamedGraphInventory", response.payload["queryId"])
        assertEquals("named-graph-inventory", response.payload["resultType"])
        assertEquals(1, response.payload["recordCount"])
        assertTrue(response.jsonBody().contains("\"provenance\""))
    }

    @Test
    fun returnsSerializedFollowUpQueuePayloadForApprovedProductReadModel() {
        val endpoint = endpointWith(
            QueryExecutionReport(
                queryId = "semanticFollowUpQueueList",
                mode = QueryMode.SELECT,
                rows = listOf(
                    mapOf(
                        "graph" to "urn:dcai:graph:fixture:canonical:minimal-incident",
                        "incident" to "urn:dcai:fixture:valid:minimal-incident:inc-0001",
                        "incidentId" to "INC-0001",
                        "asset" to "urn:dcai:fixture:valid:minimal-incident:gpu-rack-row-a",
                        "assetId" to "ASSET-GPU-RACK-ROW-A",
                        "zone" to "urn:dcai:fixture:valid:minimal-incident:zone-a",
                        "zoneId" to "ZONE-A",
                        "stage" to "urn:dcai:fixture:valid:minimal-incident:stage-validation",
                        "stageLabel" to "Validation",
                        "sourceRecord" to "urn:dcai:fixture:valid:minimal-incident:source-record-inc-0001",
                    ),
                ),
            ),
        )

        val response = endpoint.handle(post("/semantic/query/semanticFollowUpQueueList"))

        assertEquals(200, response.statusCode)
        assertEquals("semanticFollowUpQueueList", response.payload["queryId"])
        assertEquals("follow-up-queue", response.payload["resultType"])
        assertEquals(1, response.payload["recordCount"])
        assertTrue(response.jsonBody().contains("\"sourceRecordUri\""))
    }

    @Test
    fun returnsSerializedDashboardOverviewPayloadForApprovedProductReadModel() {
        val endpoint = endpointWith(
            QueryExecutionReport(
                queryId = "semanticDashboardOverview",
                mode = QueryMode.SELECT,
                rows = listOf(
                    mapOf(
                        "graph" to "urn:dcai:graph:fixture:canonical:reasoning-output",
                        "totalIncidents" to "2",
                        "assetCount" to "3",
                        "zoneCount" to "1",
                        "impactObservationCount" to "1",
                        "capacityRiskKw" to "900.0",
                        "affectedGpuCount" to "320",
                        "dependencyEdgeCount" to "1",
                        "trustFindingCount" to "1",
                    ),
                ),
            ),
        )

        val response = endpoint.handle(post("/semantic/query/semanticDashboardOverview"))

        assertEquals(200, response.statusCode)
        assertEquals("semanticDashboardOverview", response.payload["queryId"])
        assertEquals("dashboard-overview", response.payload["resultType"])
        assertTrue(response.jsonBody().contains("\"capacityRiskKw\":900.0"))
    }

    @Test
    fun rejectsUnapprovedQueryIdWithSemanticErrorEnvelope() {
        val response = endpointWith(
            QueryExecutionReport(
                queryId = "fixtureNamedGraphInventory",
                mode = QueryMode.SELECT,
            ),
        ).handle(post("/semantic/query/dependencyExposureReasoning"))

        assertEquals(400, response.statusCode)
        assertErrorCode("unapproved-query-id", response)
    }

    @Test
    fun rejectsRawSparqlRequestBody() {
        val response = endpointWith(
            QueryExecutionReport(
                queryId = "fixtureNamedGraphInventory",
                mode = QueryMode.SELECT,
            ),
        ).handle(
            post(
                path = "/semantic/query/fixtureNamedGraphInventory",
                body = """{"sparql":"SELECT * WHERE { ?s ?p ?o }"}""",
            ),
        )

        assertEquals(400, response.statusCode)
        assertErrorCode("contract-validation-failed", response)
        assertTrue(response.jsonBody().contains("does not accept raw SPARQL"))
    }

    @Test
    fun passesStringParametersToApprovedQueryExecutor() {
        val executor = CapturingQueryExecutor(
            QueryExecutionReport(
                queryId = "semanticFollowUpDetail",
                mode = QueryMode.SELECT,
                rows = listOf(
                    mapOf(
                        "graph" to "urn:dcai:graph:fixture:canonical:reasoning-output",
                        "incident" to "urn:dcai:fixture:valid:reasoning-output:incident-0001",
                        "incidentId" to "INC-REASONING-0001",
                        "asset" to "urn:dcai:fixture:valid:reasoning-output:asset-a",
                        "assetId" to "ASSET-A",
                        "zone" to "urn:dcai:fixture:valid:reasoning-output:zone-a",
                        "zoneId" to "ZONE-A",
                        "stage" to "urn:dcai:fixture:valid:reasoning-output:stage-waiting",
                        "sourceRecord" to "urn:dcai:fixture:valid:reasoning-output:source-record-0001",
                    ),
                ),
            ),
        )
        val endpoint = PrivateSemanticQueryEndpoint(
            queryExecutor = executor,
            queryResultShaper = QueryResultShaper(manifestWith("semanticFollowUpDetail")),
        )

        val response = endpoint.handle(
            post(
                path = "/semantic/query/semanticFollowUpDetail",
                body = """{"parameters":{"incidentIdParam":"INC-REASONING-0001"}}""",
            ),
        )

        assertEquals(200, response.statusCode)
        assertEquals(mapOf("incidentIdParam" to "INC-REASONING-0001"), executor.lastParameters)
    }

    @Test
    fun rejectsMalformedParametersWithoutExecutingQuery() {
        val executor = CapturingQueryExecutor(
            QueryExecutionReport(
                queryId = "semanticFollowUpDetail",
                mode = QueryMode.SELECT,
            ),
        )
        val endpoint = PrivateSemanticQueryEndpoint(
            queryExecutor = executor,
            queryResultShaper = QueryResultShaper(manifestWith("semanticFollowUpDetail")),
        )

        val response = endpoint.handle(
            post(
                path = "/semantic/query/semanticFollowUpDetail",
                body = """{"parameters":{"incidentIdParam":42}}""",
            ),
        )

        assertEquals(400, response.statusCode)
        assertErrorCode("contract-validation-failed", response)
        assertEquals(emptyMap(), executor.lastParameters)
    }

    @Test
    fun rejectsCompactRawSparqlRequestBody() {
        val response = endpointWith(
            QueryExecutionReport(
                queryId = "fixtureNamedGraphInventory",
                mode = QueryMode.SELECT,
            ),
        ).handle(
            post(
                path = "/semantic/query/fixtureNamedGraphInventory",
                body = "PREFIX dcai:<urn:dcai:> SELECT?s WHERE{?s ?p ?o}",
            ),
        )

        assertEquals(400, response.statusCode)
        assertErrorCode("contract-validation-failed", response)
    }

    @Test
    fun mapsMissingRequiredBindingToSemanticErrorEnvelope() {
        val response = endpointWith(
            QueryExecutionReport(
                queryId = "fixtureNamedGraphInventory",
                mode = QueryMode.SELECT,
                rows = listOf(mapOf("graph" to "urn:dcai:graph:fixture:canonical:minimal-incident")),
            ),
        ).handle(post("/semantic/query/fixtureNamedGraphInventory"))

        assertEquals(400, response.statusCode)
        assertErrorCode("missing-required-binding", response)
    }

    @Test
    fun mapsUnsupportedEnvelopeToSemanticErrorEnvelope() {
        val manifest = manifestWith("unsupported")
        val endpoint = PrivateSemanticQueryEndpoint(
            queryExecutor = StaticQueryExecutor(
                QueryExecutionReport(
                    queryId = "unsupported",
                    mode = QueryMode.SELECT,
                ),
            ),
            queryResultShaper = QueryResultShaper(manifest),
            allowedQueryIds = setOf("unsupported"),
        )

        val response = endpoint.handle(post("/semantic/query/unsupported"))

        assertEquals(500, response.statusCode)
        assertErrorCode("unsupported-result-envelope", response)
    }

    @Test
    fun mapsGraphFailureToUnavailableSemanticErrorEnvelope() {
        val endpoint = PrivateSemanticQueryEndpoint(
            queryExecutor = FailingQueryExecutor(RuntimeException("Connection refused")),
            queryResultShaper = QueryResultShaper(manifestWith("fixtureNamedGraphInventory")),
        )

        val response = endpoint.handle(post("/semantic/query/fixtureNamedGraphInventory"))

        assertEquals(503, response.statusCode)
        assertErrorCode("graph-unavailable", response)
    }

    @Test
    fun rejectsNonPostMethods() {
        val response = endpointWith(
            QueryExecutionReport(
                queryId = "fixtureNamedGraphInventory",
                mode = QueryMode.SELECT,
            ),
        ).handle(
            PrivateSemanticQueryRequest(
                method = "GET",
                path = "/semantic/query/fixtureNamedGraphInventory",
            ),
        )

        assertEquals(405, response.statusCode)
        assertErrorCode("contract-validation-failed", response)
    }

    @Test
    fun servesApprovedQueryOnLoopbackHttpBoundary() {
        val endpoint = endpointWith(
            QueryExecutionReport(
                queryId = "fixtureNamedGraphInventory",
                mode = QueryMode.SELECT,
                rows = listOf(
                    mapOf(
                        "graph" to "urn:dcai:graph:fixture:source:minimal-incident",
                        "subjectCount" to "4",
                    ),
                ),
            ),
        )

        PrivateSemanticQueryEndpointServer(
            endpoint = endpoint,
            config = PrivateSemanticQueryEndpointServerConfig(port = 0),
        ).use { server ->
            server.start()
            val response = HttpClient.newHttpClient().send(
                HttpRequest
                    .newBuilder(URI.create("http://127.0.0.1:${server.address.port}/semantic/query/fixtureNamedGraphInventory"))
                    .POST(HttpRequest.BodyPublishers.noBody())
                    .build(),
                HttpResponse.BodyHandlers.ofString(),
            )

            assertEquals(200, response.statusCode())
            assertTrue(response.body().contains("\"queryId\":\"fixtureNamedGraphInventory\""))
            assertTrue(response.body().contains("\"resultType\":\"named-graph-inventory\""))
        }
    }

    @Test
    fun servesCorsPreflightOnLoopbackHttpBoundary() {
        val endpoint = endpointWith(
            QueryExecutionReport(
                queryId = "fixtureNamedGraphInventory",
                mode = QueryMode.SELECT,
            ),
        )

        PrivateSemanticQueryEndpointServer(
            endpoint = endpoint,
            config = PrivateSemanticQueryEndpointServerConfig(port = 0),
        ).use { server ->
            server.start()
            val response = HttpClient.newHttpClient().send(
                HttpRequest
                    .newBuilder(URI.create("http://127.0.0.1:${server.address.port}/semantic/query/fixtureNamedGraphInventory"))
                    .method("OPTIONS", HttpRequest.BodyPublishers.noBody())
                    .build(),
                HttpResponse.BodyHandlers.ofString(),
            )

            assertEquals(204, response.statusCode())
            assertEquals("*", response.headers().firstValue("Access-Control-Allow-Origin").orElse(""))
            assertTrue(response.headers().firstValue("Access-Control-Allow-Methods").orElse("").contains("POST"))
            assertTrue(response.body().isBlank())
        }
    }

    @Test
    fun serverConfigRejectsNonLoopbackHosts() {
        assertFailsWith<IllegalArgumentException> {
            PrivateSemanticQueryEndpointServerConfig(host = "0.0.0.0")
        }
    }

    @Test
    fun jsonWriterEscapesStrings() {
        assertEquals(
            """{"message":"quote: \" and newline\n"}""",
            JsonPayloadWriter.write(mapOf("message" to "quote: \" and newline\n")),
        )
    }

    private fun endpointWith(report: QueryExecutionReport): PrivateSemanticQueryEndpoint {
        return PrivateSemanticQueryEndpoint(
            queryExecutor = StaticQueryExecutor(report),
            queryResultShaper = QueryResultShaper(manifestWith(report.queryId)),
        )
    }

    private fun post(
        path: String,
        body: String = "",
    ): PrivateSemanticQueryRequest {
        return PrivateSemanticQueryRequest(
            method = "POST",
            path = path,
            body = body,
        )
    }

    private fun manifestWith(vararg queryIds: String): ApprovedQueryManifest {
        return ApprovedQueryManifest(
            entries = queryIds.associateWith { queryId ->
                ApprovedQueryDefinition(
                    id = queryId,
                    path = Path.of("queries/inspection/$queryId.select.rq"),
                    mode = QueryMode.SELECT,
                    graphScope = "fixture graph",
                    sparql = "SELECT * WHERE { ?s ?p ?o }",
                )
            },
        )
    }

    private fun assertErrorCode(
        expected: String,
        response: PrivateSemanticQueryResponse,
    ) {
        val error = response.payload["error"] as Map<*, *>
        assertEquals(expected, error["code"])
    }

    private class StaticQueryExecutor(
        private val report: QueryExecutionReport,
    ) : ReadOnlyQueryExecutor {
        override fun execute(queryId: String): QueryExecutionReport {
            return report.copy(queryId = queryId)
        }
    }

    private class FailingQueryExecutor(
        private val error: RuntimeException,
    ) : ReadOnlyQueryExecutor {
        override fun execute(queryId: String): QueryExecutionReport {
            throw error
        }
    }

    private class CapturingQueryExecutor(
        private val report: QueryExecutionReport,
    ) : ReadOnlyQueryExecutor {
        var lastParameters: Map<String, String> = emptyMap()

        override fun execute(queryId: String): QueryExecutionReport {
            return execute(queryId, emptyMap())
        }

        override fun execute(
            queryId: String,
            parameters: Map<String, String>,
        ): QueryExecutionReport {
            lastParameters = parameters
            return report.copy(queryId = queryId)
        }
    }
}
