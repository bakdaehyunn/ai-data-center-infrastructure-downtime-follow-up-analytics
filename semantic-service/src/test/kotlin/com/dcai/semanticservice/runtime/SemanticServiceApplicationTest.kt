package com.dcai.semanticservice.runtime

import com.dcai.semanticservice.fixtures.FixtureGraphLoadPlan
import com.dcai.semanticservice.fixtures.FixtureGraphLoader
import com.dcai.semanticservice.fixtures.FixtureGraphTarget
import com.dcai.semanticservice.fixtures.FixtureLoadResult
import com.dcai.semanticservice.fixtures.FixtureLoadSummary
import com.dcai.semanticservice.fixtures.FixtureValidationReport
import com.dcai.semanticservice.graph.GraphConnectionCheck
import com.dcai.semanticservice.graph.ReadOnlyGraphClient
import com.dcai.semanticservice.query.QueryExecutionReport
import com.dcai.semanticservice.query.QueryMode
import com.dcai.semanticservice.query.QueryResultEnvelopeProvenance
import com.dcai.semanticservice.query.QueryResultShaper
import com.dcai.semanticservice.query.ReadOnlyQueryExecutor
import java.nio.file.Path
import kotlin.io.path.exists
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class SemanticServiceApplicationTest {
    @Test
    fun startsRunnableContractValidationBaseline() {
        val report = SemanticServiceApplication.run()

        assertTrue(report.isReady, report.contractValidation.errors.joinToString(separator = "\n"))
        assertEquals("contract-validation-runtime", report.mode)
        assertEquals("ready", report.status)
        assertFalse(report.graphExecutionEnabled)
        assertFalse(report.httpEndpointsEnabled)
    }

    @Test
    fun canRunReadOnlyGraphConnectivityBoundary() {
        val report = SemanticServiceApplication.run(
            graphClient = StaticReadOnlyGraphClient(
                GraphConnectionCheck(
                    reachable = true,
                    datasetUrl = "http://localhost:3030/infrastructure",
                    queryEndpointUrl = "http://localhost:3030/infrastructure/query",
                    namedGraphCount = 0,
                    message = "ok",
                ),
            ),
        )

        assertTrue(report.isReady, report.contractValidation.errors.joinToString(separator = "\n"))
        assertEquals(true, report.graphConnectionCheck?.reachable)
        assertEquals(0, report.graphConnectionCheck?.namedGraphCount)
        assertFalse(report.graphExecutionEnabled)
        assertFalse(report.httpEndpointsEnabled)
    }

    @Test
    fun canRunControlledFixtureLoadingBoundary() {
        val report = SemanticServiceApplication.run(
            fixtureLoader = StaticFixtureGraphLoader(
                FixtureLoadSummary(
                    listOf(
                        FixtureLoadResult(
                            target = FixtureGraphTarget(
                                path = Path.of("fixtures/rdf/valid/minimal-incident.ttl"),
                                sourceGraphUri = "urn:dcai:graph:fixture:source:minimal-incident",
                                canonicalGraphUri = "urn:dcai:graph:fixture:canonical:minimal-incident",
                            ),
                            validation = FixtureValidationReport(conforms = true, tripleCount = 1),
                            sourceGraphWritten = true,
                            canonicalGraphWritten = true,
                        ),
                    ),
                ),
            ),
        )

        assertTrue(report.isReady, report.contractValidation.errors.joinToString(separator = "\n"))
        assertTrue(report.fixtureLoadingEnabled)
        assertEquals(1, report.fixtureLoadSummary?.promotedCount)
        assertFalse(report.graphExecutionEnabled)
        assertFalse(report.httpEndpointsEnabled)
    }

    @Test
    fun canRunControlledReadOnlyQueryExecutionBoundary() {
        val manifest = com.dcai.semanticservice.query.ApprovedQueryManifest(
            entries = mapOf(
                "fixtureNamedGraphInventory" to com.dcai.semanticservice.query.ApprovedQueryDefinition(
                    id = "fixtureNamedGraphInventory",
                    path = Path.of("queries/inspection/fixture_named_graph_inventory.select.rq"),
                    mode = QueryMode.SELECT,
                    graphScope = "fixture source graph, fixture canonical graph",
                    sparql = "SELECT * WHERE { ?s ?p ?o }",
                ),
            ),
        )
        val report = SemanticServiceApplication.run(
            queryExecutor = StaticReadOnlyQueryExecutor(
                QueryExecutionReport(
                    queryId = "fixtureNamedGraphInventory",
                    mode = QueryMode.SELECT,
                    rowCount = 2,
                    rows = listOf(
                        mapOf(
                            "graph" to "urn:dcai:graph:fixture:canonical:minimal-incident",
                            "subjectCount" to "8",
                        ),
                        mapOf(
                            "graph" to "urn:dcai:graph:fixture:source:minimal-incident",
                            "subjectCount" to "8",
                        ),
                    ),
                ),
            ),
            queryId = "fixtureNamedGraphInventory",
            queryResultShaper = QueryResultShaper(manifest),
        )

        assertTrue(report.isReady, report.contractValidation.errors.joinToString(separator = "\n"))
        assertTrue(report.queryExecutionEnabled)
        assertEquals(2, report.queryExecutionReport?.rowCount)
        assertEquals("named-graph-inventory", report.queryResultEnvelope?.resultType?.value)
        assertEquals(QueryResultEnvelopeProvenance.CONTRACT_VERSION, report.queryResultEnvelope?.provenance?.contractVersion)
        assertFalse(report.graphExecutionEnabled)
        assertFalse(report.httpEndpointsEnabled)
    }

    @Test
    fun rejectsBlankQueryIdArgument() {
        assertFailsWith<IllegalArgumentException> {
            SemanticServiceRuntimeOptions.fromArgs(arrayOf("--run-query="))
        }
    }

    @Test
    fun locatesRepositoryRootFromSemanticServiceDirectory() {
        val repoRoot = SemanticServiceApplication.locateRepoRoot()

        assertTrue(repoRoot.resolve("semantic-service/openapi.semantic-service.yaml").exists())
        assertTrue(repoRoot.resolve("ontology/modules").exists())
    }

    private class StaticReadOnlyGraphClient(
        private val check: GraphConnectionCheck,
    ) : ReadOnlyGraphClient {
        override fun checkConnectivity(): GraphConnectionCheck = check
    }

    private class StaticFixtureGraphLoader(
        private val summary: FixtureLoadSummary,
    ) : FixtureGraphLoader {
        override fun load(plan: FixtureGraphLoadPlan): FixtureLoadSummary = summary
    }

    private class StaticReadOnlyQueryExecutor(
        private val report: QueryExecutionReport,
    ) : ReadOnlyQueryExecutor {
        override fun execute(queryId: String): QueryExecutionReport = report
    }
}
