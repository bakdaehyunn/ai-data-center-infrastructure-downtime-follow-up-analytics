package com.dcai.semanticservice.runtime

import com.dcai.semanticservice.fixtures.FixtureGraphLoadPlan
import com.dcai.semanticservice.fixtures.FixtureGraphLoader
import com.dcai.semanticservice.fixtures.FixtureGraphTarget
import com.dcai.semanticservice.fixtures.FixtureLoadResult
import com.dcai.semanticservice.fixtures.FixtureLoadSummary
import com.dcai.semanticservice.fixtures.FixtureValidationReport
import com.dcai.semanticservice.graph.GraphConnectionCheck
import com.dcai.semanticservice.graph.ReadOnlyGraphClient
import com.dcai.semanticservice.promotion.GraphPromotionResult
import com.dcai.semanticservice.promotion.ProductionGraphPromotionPlan
import com.dcai.semanticservice.promotion.ProductionGraphValidationReport
import com.dcai.semanticservice.promotion.PromotionReleaseManifest
import com.dcai.semanticservice.promotion.SourceGraphPromoter
import com.dcai.semanticservice.query.QueryExecutionReport
import com.dcai.semanticservice.query.QueryMode
import com.dcai.semanticservice.query.QueryResultEnvelopeProvenance
import com.dcai.semanticservice.query.QueryResultShaper
import com.dcai.semanticservice.query.ReadOnlyQueryExecutor
import com.dcai.semanticservice.reasoning.ReasoningPromotionPlan
import com.dcai.semanticservice.reasoning.ReasoningPromotionResult
import com.dcai.semanticservice.reasoning.ReasoningRefresher
import com.dcai.semanticservice.reasoning.ReasoningReleaseManifest
import com.dcai.semanticservice.reasoning.ReasoningValidationReport
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
    fun canRunControlledSourcePromotionCommandBoundary() {
        val report = SemanticServiceApplication.run(
            sourcePromoter = StaticSourceGraphPromoter(
                GraphPromotionResult(
                    promoted = true,
                    validation = ProductionGraphValidationReport(conforms = true, tripleCount = 12),
                    writtenGraphUris = listOf(
                        "urn:dcai:graph:source:local-controlled-source-v1",
                        "urn:dcai:graph:canonical:local-controlled-source-v1",
                        "urn:dcai:graph:provenance:local-controlled-source-v1",
                    ),
                    releaseManifest = PromotionReleaseManifest(
                        releaseId = "local-controlled-source-v1",
                        sourceGraphUri = "urn:dcai:graph:source:local-controlled-source-v1",
                        canonicalGraphUri = "urn:dcai:graph:canonical:local-controlled-source-v1",
                        provenanceGraphUri = "urn:dcai:graph:provenance:local-controlled-source-v1",
                    ),
                ),
            ),
            sourcePromotionPlan = com.dcai.semanticservice.promotion.ProductionGraphPromotionPlan(
                batch = com.dcai.semanticservice.ingestion.LocalControlledSourceExtract.batch(),
                graphs = com.dcai.semanticservice.promotion.ProductionGraphUris.forRelease("local-controlled-source-v1"),
            ),
        )

        assertTrue(report.isReady, report.contractValidation.errors.joinToString(separator = "\n"))
        assertTrue(report.graphExecutionEnabled)
        assertTrue(report.sourcePromotionEnabled)
        assertEquals(3, report.sourcePromotionResult?.writtenGraphUris?.size)
        assertFalse(report.httpEndpointsEnabled)
    }

    @Test
    fun canRunReasoningRefreshCommandBoundary() {
        val report = SemanticServiceApplication.run(
            reasoningRefresher = StaticReasoningRefresher(
                ReasoningPromotionResult(
                    promoted = true,
                    validation = ReasoningValidationReport(conforms = true, tripleCount = 10),
                    findingCount = 2,
                    writtenGraphUris = listOf(
                        "urn:dcai:graph:reasoning-audit:local-controlled-reasoning-v1",
                        "urn:dcai:graph:reasoning:local-controlled-reasoning-v1",
                    ),
                    releaseManifest = ReasoningReleaseManifest(
                        runId = "local-controlled-reasoning-v1",
                        canonicalGraphUri = "urn:dcai:graph:canonical:local-controlled-source-v1",
                        provenanceGraphUri = "urn:dcai:graph:provenance:local-controlled-source-v1",
                        auditGraphUri = "urn:dcai:graph:reasoning-audit:local-controlled-reasoning-v1",
                        reasoningGraphUri = "urn:dcai:graph:reasoning:local-controlled-reasoning-v1",
                        findingCount = 2,
                    ),
                ),
            ),
            reasoningPromotionPlan = ReasoningPromotionPlan(
                runId = "local-controlled-reasoning-v1",
                generatedAt = java.time.Instant.parse("2026-06-09T01:00:00Z"),
                inputGraphs = com.dcai.semanticservice.reasoning.ReasoningInputGraphUris.forRelease("local-controlled-source-v1"),
                outputGraphs = com.dcai.semanticservice.reasoning.ReasoningOutputGraphUris.forRun("local-controlled-reasoning-v1"),
            ),
        )

        assertTrue(report.isReady, report.contractValidation.errors.joinToString(separator = "\n"))
        assertTrue(report.graphExecutionEnabled)
        assertTrue(report.reasoningRefreshEnabled)
        assertEquals(2, report.reasoningPromotionResult?.findingCount)
        assertFalse(report.httpEndpointsEnabled)
    }

    @Test
    fun failedReasoningRefreshBlocksRuntimeReport() {
        val report = SemanticServiceApplication.run(
            reasoningRefresher = StaticReasoningRefresher(
                ReasoningPromotionResult(
                    promoted = false,
                    validation = ReasoningValidationReport(
                        conforms = false,
                        tripleCount = 0,
                        errors = listOf("Canonical graph is missing or empty"),
                    ),
                    errors = listOf("Canonical graph is missing or empty"),
                ),
            ),
            reasoningPromotionPlan = ReasoningPromotionPlan(
                runId = "local-controlled-reasoning-v1",
                generatedAt = java.time.Instant.parse("2026-06-09T01:00:00Z"),
                inputGraphs = com.dcai.semanticservice.reasoning.ReasoningInputGraphUris.forRelease("local-controlled-source-v1"),
                outputGraphs = com.dcai.semanticservice.reasoning.ReasoningOutputGraphUris.forRun("local-controlled-reasoning-v1"),
            ),
        )

        assertFalse(report.isReady)
        assertEquals("blocked", report.status)
        assertTrue(report.reasoningRefreshEnabled)
    }

    @Test
    fun failedSourcePromotionSkipsCombinedReasoningRefresh() {
        val report = SemanticServiceApplication.run(
            sourcePromoter = StaticSourceGraphPromoter(
                GraphPromotionResult(
                    promoted = false,
                    validation = ProductionGraphValidationReport(
                        conforms = false,
                        tripleCount = 0,
                        errors = listOf("Source validation failed"),
                    ),
                    errors = listOf("Source validation failed"),
                ),
            ),
            sourcePromotionPlan = com.dcai.semanticservice.promotion.ProductionGraphPromotionPlan(
                batch = com.dcai.semanticservice.ingestion.LocalControlledSourceExtract.batch(),
                graphs = com.dcai.semanticservice.promotion.ProductionGraphUris.forRelease("local-controlled-source-v1"),
            ),
            reasoningRefresher = FailingIfCalledReasoningRefresher,
            reasoningPromotionPlan = ReasoningPromotionPlan(
                runId = "local-controlled-reasoning-v1",
                generatedAt = java.time.Instant.parse("2026-06-09T01:00:00Z"),
                inputGraphs = com.dcai.semanticservice.reasoning.ReasoningInputGraphUris.forRelease("local-controlled-source-v1"),
                outputGraphs = com.dcai.semanticservice.reasoning.ReasoningOutputGraphUris.forRun("local-controlled-reasoning-v1"),
            ),
        )

        assertFalse(report.isReady)
        assertTrue(report.sourcePromotionEnabled)
        assertTrue(report.reasoningRefreshEnabled)
        assertEquals(false, report.reasoningPromotionResult?.promoted)
        assertTrue(report.reasoningPromotionResult?.errors.orEmpty().contains("Reasoning refresh skipped because source promotion failed."))
    }

    @Test
    fun rejectsBlankQueryIdArgument() {
        assertFailsWith<IllegalArgumentException> {
            SemanticServiceRuntimeOptions.fromArgs(arrayOf("--run-query="))
        }
    }

    @Test
    fun parsesPrivateEndpointOptionsOnlyWhenExplicitlyRequested() {
        val defaultOptions = SemanticServiceRuntimeOptions.fromArgs(emptyArray())

        assertFalse(defaultOptions.servePrivateQueryEndpoint)
        assertEquals("127.0.0.1", defaultOptions.privateEndpointHost)
        assertEquals(18080, defaultOptions.privateEndpointPort)

        val endpointOptions = SemanticServiceRuntimeOptions.fromArgs(
            arrayOf(
                "--repo-root=/workspace",
                "--serve-private-query-endpoint",
                "--private-endpoint-host=localhost",
                "--private-endpoint-port=19090",
            ),
        )

        assertTrue(endpointOptions.servePrivateQueryEndpoint)
        assertEquals("localhost", endpointOptions.privateEndpointHost)
        assertEquals(19090, endpointOptions.privateEndpointPort)
    }

    @Test
    fun parsesGraphLifecycleCommandOptions() {
        val options = SemanticServiceRuntimeOptions.fromArgs(
            arrayOf(
                "--repo-root=/workspace",
                "--promote-source",
                "--source-release-id=release-a",
                "--refresh-reasoning",
                "--reasoning-input-release-id=release-a",
                "--reasoning-run-id=reasoning-a",
            ),
        )

        assertTrue(options.promoteSource)
        assertEquals("release-a", options.sourceReleaseId)
        assertTrue(options.refreshReasoning)
        assertEquals("release-a", options.reasoningInputReleaseId)
        assertEquals("reasoning-a", options.reasoningRunId)
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

    private class StaticSourceGraphPromoter(
        private val result: GraphPromotionResult,
    ) : SourceGraphPromoter {
        override fun promote(plan: ProductionGraphPromotionPlan): GraphPromotionResult = result
    }

    private class StaticReasoningRefresher(
        private val result: ReasoningPromotionResult,
    ) : ReasoningRefresher {
        override fun run(plan: ReasoningPromotionPlan): ReasoningPromotionResult = result
    }

    private object FailingIfCalledReasoningRefresher : ReasoningRefresher {
        override fun run(plan: ReasoningPromotionPlan): ReasoningPromotionResult {
            error("Reasoning refresher should not run after failed source promotion")
        }
    }
}
