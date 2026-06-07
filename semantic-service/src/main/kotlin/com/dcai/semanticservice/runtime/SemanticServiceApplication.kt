package com.dcai.semanticservice.runtime

import com.dcai.semanticservice.contracts.ContractValidationReport
import com.dcai.semanticservice.contracts.StaticContractValidator
import java.nio.file.Files
import java.nio.file.Path
import kotlin.io.path.exists
import kotlin.system.exitProcess

object SemanticServiceApplication {
    @JvmStatic
    fun main(args: Array<String>) {
        val repoRoot = args.firstOrNull()?.let { Path.of(it).toAbsolutePath().normalize() }
            ?: locateRepoRoot()
        val report = run(repoRoot)

        println("DCAI Semantic Service")
        println("mode=${report.mode}")
        println("repoRoot=${report.repoRoot}")
        println("status=${report.status}")
        println("checkedContracts=${report.contractValidation.checkedArtifacts.size}")
        println("graphExecutionEnabled=${report.graphExecutionEnabled}")
        println("httpEndpointsEnabled=${report.httpEndpointsEnabled}")

        if (!report.isReady) {
            report.contractValidation.errors.forEach { error -> println("error=$error") }
            exitProcess(1)
        }
    }

    fun run(repoRoot: Path = locateRepoRoot()): SemanticServiceRuntimeReport {
        val validation = StaticContractValidator().validate(repoRoot)
        return SemanticServiceRuntimeReport(
            repoRoot = repoRoot,
            contractValidation = validation,
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
) {
    val mode: String = "contract-validation-runtime"
    val status: String = if (contractValidation.isValid) "ready" else "blocked"
    val isReady: Boolean = contractValidation.isValid
    val graphExecutionEnabled: Boolean = false
    val httpEndpointsEnabled: Boolean = false
}
