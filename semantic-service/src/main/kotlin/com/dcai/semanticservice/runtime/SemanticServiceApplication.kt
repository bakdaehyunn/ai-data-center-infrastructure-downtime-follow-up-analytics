package com.dcai.semanticservice.runtime

import com.dcai.semanticservice.contracts.ContractValidationReport
import com.dcai.semanticservice.contracts.StaticContractValidator
import com.dcai.semanticservice.fixtures.ControlledFixtureGraphLoader
import com.dcai.semanticservice.fixtures.FixtureGraphLoadPlan
import com.dcai.semanticservice.fixtures.FixtureGraphLoader
import com.dcai.semanticservice.fixtures.FixtureLoadSummary
import com.dcai.semanticservice.fixtures.FixtureValidationGate
import com.dcai.semanticservice.graph.FusekiGraphStoreConfig
import com.dcai.semanticservice.graph.FusekiReadOnlyConfig
import com.dcai.semanticservice.graph.FusekiNamedGraphWriter
import com.dcai.semanticservice.graph.GraphConnectionCheck
import com.dcai.semanticservice.graph.JenaFusekiReadOnlyGraphClient
import com.dcai.semanticservice.graph.ReadOnlyGraphClient
import com.dcai.semanticservice.query.ApprovedQueryCatalog
import com.dcai.semanticservice.query.JenaFusekiReadOnlyQueryExecutor
import com.dcai.semanticservice.query.QueryExecutionReport
import com.dcai.semanticservice.query.QueryResultEnvelope
import com.dcai.semanticservice.query.QueryResultShaper
import com.dcai.semanticservice.query.ReadOnlyQueryExecutor
import java.nio.file.Files
import java.nio.file.Path
import kotlin.io.path.exists
import kotlin.system.exitProcess

object SemanticServiceApplication {
    @JvmStatic
    fun main(args: Array<String>) {
        val options = SemanticServiceRuntimeOptions.fromArgs(args)
        val repoRoot = options.repoRoot?.let { Path.of(it).toAbsolutePath().normalize() }
            ?: locateRepoRoot()
        val graphClient = if (options.checkGraph) {
            JenaFusekiReadOnlyGraphClient(FusekiReadOnlyConfig.fromEnvironment())
        } else {
            null
        }
        val fixtureLoader = if (options.loadFixtures) {
            ControlledFixtureGraphLoader(
                validationGate = FixtureValidationGate(repoRoot),
                writer = FusekiNamedGraphWriter(FusekiGraphStoreConfig.fromEnvironment()),
            )
        } else {
            null
        }
        val approvedQueryManifest = options.queryId?.let {
            ApprovedQueryCatalog(repoRoot).load()
        }
        val queryExecutor = approvedQueryManifest?.let { manifest ->
            JenaFusekiReadOnlyQueryExecutor(
                manifest = manifest,
                config = FusekiReadOnlyConfig.fromEnvironment(),
            )
        }
        val queryResultShaper = approvedQueryManifest?.let { manifest ->
            QueryResultShaper(manifest)
        }
        val report = run(
            repoRoot = repoRoot,
            graphClient = graphClient,
            fixtureLoader = fixtureLoader,
            queryExecutor = queryExecutor,
            queryId = options.queryId,
            queryResultShaper = queryResultShaper,
        )

        println("DCAI Semantic Service")
        println("mode=${report.mode}")
        println("repoRoot=${report.repoRoot}")
        println("status=${report.status}")
        println("checkedContracts=${report.contractValidation.checkedArtifacts.size}")
        println("graphExecutionEnabled=${report.graphExecutionEnabled}")
        println("httpEndpointsEnabled=${report.httpEndpointsEnabled}")
        println("fixtureLoadingEnabled=${report.fixtureLoadingEnabled}")
        println("queryExecutionEnabled=${report.queryExecutionEnabled}")
        report.graphConnectionCheck?.let { check ->
            println("graphReachable=${check.reachable}")
            println("graphDatasetUrl=${check.datasetUrl}")
            println("graphQueryEndpointUrl=${check.queryEndpointUrl}")
            println("namedGraphCount=${check.namedGraphCount ?: "unknown"}")
            println("graphMessage=${check.message}")
        }
        report.fixtureLoadSummary?.let { summary ->
            println("fixtureLoadSucceeded=${summary.succeeded}")
            println("fixtureLoadAttempted=${summary.attemptedCount}")
            println("fixtureGraphsPromoted=${summary.promotedCount}")
        }
        report.queryExecutionReport?.let { queryReport ->
            println("queryId=${queryReport.queryId}")
            println("queryMode=${queryReport.mode.value}")
            println("queryRows=${queryReport.rowCount}")
            queryReport.askResult?.let { result -> println("queryAskResult=$result") }
        }
        report.queryResultEnvelope?.let { envelope ->
            println("queryResultType=${envelope.resultType.value}")
            println("queryResultRecords=${envelope.recordCount}")
            println("queryResultContract=${envelope.provenance.contractVersion}")
        }

        if (!report.isReady) {
            report.contractValidation.errors.forEach { error -> println("error=$error") }
            report.graphConnectionCheck
                ?.takeUnless { it.reachable }
                ?.let { println("error=${it.message}") }
            report.fixtureLoadSummary?.errors?.forEach { error -> println("error=$error") }
            exitProcess(1)
        }
    }

    fun run(
        repoRoot: Path = locateRepoRoot(),
        graphClient: ReadOnlyGraphClient? = null,
        fixtureLoader: FixtureGraphLoader? = null,
        fixtureLoadPlan: FixtureGraphLoadPlan? = null,
        queryExecutor: ReadOnlyQueryExecutor? = null,
        queryId: String? = null,
        queryResultShaper: QueryResultShaper? = null,
    ): SemanticServiceRuntimeReport {
        val validation = StaticContractValidator().validate(repoRoot)
        val graphConnectionCheck = graphClient?.checkConnectivity()
        val fixtureLoadSummary = fixtureLoader?.load(
            fixtureLoadPlan ?: FixtureGraphLoadPlan.default(repoRoot),
        )
        val queryExecutionReport = queryId?.let { id ->
            requireNotNull(queryExecutor) { "queryExecutor is required when queryId is provided" }
                .execute(id)
        }
        val queryResultEnvelope = queryExecutionReport?.let { report ->
            requireNotNull(queryResultShaper) { "queryResultShaper is required when query execution is enabled" }
                .shape(report)
        }
        return SemanticServiceRuntimeReport(
            repoRoot = repoRoot,
            contractValidation = validation,
            graphConnectionCheck = graphConnectionCheck,
            fixtureLoadSummary = fixtureLoadSummary,
            queryExecutionReport = queryExecutionReport,
            queryResultEnvelope = queryResultEnvelope,
        )
    }

    fun locateRepoRoot(start: Path = Path.of("").toAbsolutePath().normalize()): Path {
        var current = start
        while (current.parent != null) {
            if (
                current.resolve("semantic-service/openapi.semantic-service.yaml").exists() &&
                current.resolve("ontology/modules").exists() &&
                Files.isDirectory(current.resolve("semantic-service/src/main/kotlin"))
            ) {
                return current
            }
            current = current.parent
        }
        error("Unable to locate repository root from $start")
    }
}

data class SemanticServiceRuntimeReport(
    val repoRoot: Path,
    val contractValidation: ContractValidationReport,
    val graphConnectionCheck: GraphConnectionCheck? = null,
    val fixtureLoadSummary: FixtureLoadSummary? = null,
    val queryExecutionReport: QueryExecutionReport? = null,
    val queryResultEnvelope: QueryResultEnvelope? = null,
) {
    val mode: String = "contract-validation-runtime"
    val isReady: Boolean = contractValidation.isValid &&
        (graphConnectionCheck == null || graphConnectionCheck.reachable) &&
        (fixtureLoadSummary == null || fixtureLoadSummary.succeeded)
    val status: String = if (isReady) "ready" else "blocked"
    val graphExecutionEnabled: Boolean = false
    val httpEndpointsEnabled: Boolean = false
    val fixtureLoadingEnabled: Boolean = fixtureLoadSummary != null
    val queryExecutionEnabled: Boolean = queryExecutionReport != null
}

data class SemanticServiceRuntimeOptions(
    val repoRoot: String? = null,
    val checkGraph: Boolean = false,
    val loadFixtures: Boolean = false,
    val queryId: String? = null,
) {
    companion object {
        fun fromArgs(args: Array<String>): SemanticServiceRuntimeOptions {
            var repoRoot: String? = null
            var checkGraph = false
            var loadFixtures = false
            var queryId: String? = null

            for (arg in args) {
                when {
                    arg == "--check-graph" -> checkGraph = true
                    arg == "--load-fixtures" -> loadFixtures = true
                    arg.startsWith("--run-query=") -> {
                        queryId = arg.substringAfter("=")
                        require(queryId.isNotBlank()) { "--run-query requires a query id" }
                    }
                    arg.startsWith("--repo-root=") -> repoRoot = arg.substringAfter("=")
                    repoRoot == null -> repoRoot = arg
                    else -> error("Unknown argument: $arg")
                }
            }

            return SemanticServiceRuntimeOptions(
                repoRoot = repoRoot,
                checkGraph = checkGraph,
                loadFixtures = loadFixtures,
                queryId = queryId,
            )
        }
    }
}
