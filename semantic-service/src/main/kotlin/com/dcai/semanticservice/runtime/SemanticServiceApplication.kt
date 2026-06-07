package com.dcai.semanticservice.runtime

import com.dcai.semanticservice.contracts.ContractValidationReport
import com.dcai.semanticservice.contracts.StaticContractValidator
import com.dcai.semanticservice.graph.FusekiReadOnlyConfig
import com.dcai.semanticservice.graph.GraphConnectionCheck
import com.dcai.semanticservice.graph.JenaFusekiReadOnlyGraphClient
import com.dcai.semanticservice.graph.ReadOnlyGraphClient
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
        val report = run(repoRoot, graphClient)

        println("DCAI Semantic Service")
        println("mode=${report.mode}")
        println("repoRoot=${report.repoRoot}")
        println("status=${report.status}")
        println("checkedContracts=${report.contractValidation.checkedArtifacts.size}")
        println("graphExecutionEnabled=${report.graphExecutionEnabled}")
        println("httpEndpointsEnabled=${report.httpEndpointsEnabled}")
        report.graphConnectionCheck?.let { check ->
            println("graphReachable=${check.reachable}")
            println("graphDatasetUrl=${check.datasetUrl}")
            println("graphQueryEndpointUrl=${check.queryEndpointUrl}")
            println("namedGraphCount=${check.namedGraphCount ?: "unknown"}")
            println("graphMessage=${check.message}")
        }

        if (!report.isReady) {
            report.contractValidation.errors.forEach { error -> println("error=$error") }
            report.graphConnectionCheck
                ?.takeUnless { it.reachable }
                ?.let { println("error=${it.message}") }
            exitProcess(1)
        }
    }

    fun run(
        repoRoot: Path = locateRepoRoot(),
        graphClient: ReadOnlyGraphClient? = null,
    ): SemanticServiceRuntimeReport {
        val validation = StaticContractValidator().validate(repoRoot)
        val graphConnectionCheck = graphClient?.checkConnectivity()
        return SemanticServiceRuntimeReport(
            repoRoot = repoRoot,
            contractValidation = validation,
            graphConnectionCheck = graphConnectionCheck,
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
) {
    val mode: String = "contract-validation-runtime"
    val isReady: Boolean = contractValidation.isValid &&
        (graphConnectionCheck == null || graphConnectionCheck.reachable)
    val status: String = if (isReady) "ready" else "blocked"
    val graphExecutionEnabled: Boolean = false
    val httpEndpointsEnabled: Boolean = false
}

data class SemanticServiceRuntimeOptions(
    val repoRoot: String? = null,
    val checkGraph: Boolean = false,
) {
    companion object {
        fun fromArgs(args: Array<String>): SemanticServiceRuntimeOptions {
            var repoRoot: String? = null
            var checkGraph = false

            for (arg in args) {
                when {
                    arg == "--check-graph" -> checkGraph = true
                    arg.startsWith("--repo-root=") -> repoRoot = arg.substringAfter("=")
                    repoRoot == null -> repoRoot = arg
                    else -> error("Unknown argument: $arg")
                }
            }

            return SemanticServiceRuntimeOptions(
                repoRoot = repoRoot,
                checkGraph = checkGraph,
            )
        }
    }
}
