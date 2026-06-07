package com.dcai.semanticservice.contracts

import java.nio.file.Files
import java.nio.file.Path
import kotlin.io.path.extension

class StaticContractValidator(
    private val loader: ContractFileLoader = ContractFileLoader(),
) {
    fun validate(repoRoot: Path): ContractValidationReport {
        val errors = mutableListOf<String>()
        val loadedContracts = SemanticServiceContractCatalog.requiredArtifacts.map { artifact ->
            loader.load(repoRoot, artifact)
        }

        for (loaded in loadedContracts) {
            if (!loaded.exists) {
                errors += "Missing contract artifact: ${loaded.artifact.path}"
                continue
            }
            if (!loaded.isNotBlank) {
                errors += "Blank contract artifact: ${loaded.artifact.path}"
                continue
            }
            val content = loaded.content.orEmpty()
            for (marker in loaded.artifact.requiredMarkers) {
                if (!content.contains(marker)) {
                    errors += "Missing marker '$marker' in ${loaded.artifact.path}"
                }
            }
        }

        errors += findForbiddenRuntimeMarkers(repoRoot)

        return ContractValidationReport(
            checkedArtifacts = loadedContracts.map { it.artifact.path },
            errors = errors,
        )
    }

    private fun findForbiddenRuntimeMarkers(repoRoot: Path): List<String> {
        val sourceRoot = repoRoot.resolve("semantic-service/src/main/kotlin").normalize()
        if (!Files.exists(sourceRoot)) {
            return listOf("Missing Kotlin source root: semantic-service/src/main/kotlin")
        }

        return Files.walk(sourceRoot).use { stream ->
            stream
                .filter {
                    Files.isRegularFile(it) &&
                        it.extension == "kt" &&
                        it.fileName.toString() != "SemanticServiceContractCatalog.kt"
                }
                .flatMap { path ->
                    val relative = repoRoot.relativize(path).toString()
                    val content = Files.readString(path)
                    SemanticServiceContractCatalog.forbiddenMainSourceMarkers
                        .filter { marker ->
                            content.contains(marker) &&
                                relative !in SemanticServiceContractCatalog.allowedForbiddenMarkerPaths
                                    .getOrDefault(marker, emptySet())
                        }
                        .map { marker -> "Forbidden runtime marker '$marker' in $relative" }
                        .stream()
                }
                .toList()
        }
    }
}

data class ContractValidationReport(
    val checkedArtifacts: List<String>,
    val errors: List<String>,
) {
    val isValid: Boolean = errors.isEmpty()
}
