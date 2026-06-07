package com.dcai.semanticservice.fixtures

import java.nio.file.Path
import kotlin.io.path.nameWithoutExtension

data class FixtureGraphLoadPlan(
    val fixtures: List<FixtureGraphTarget>,
) {
    init {
        require(fixtures.isNotEmpty()) { "fixtures must not be empty" }
    }

    companion object {
        fun default(repoRoot: Path): FixtureGraphLoadPlan {
            val validFixtureRoot = repoRoot.resolve("fixtures/rdf/valid").normalize()
            val fixtureFiles = listOf(
                "minimal-incident.ttl",
                "dependency-path.ttl",
                "evidence-provenance.ttl",
            )

            return FixtureGraphLoadPlan(
                fixtures = fixtureFiles.map { fileName ->
                    val path = validFixtureRoot.resolve(fileName)
                    FixtureGraphTarget(
                        path = path,
                        sourceGraphUri = "urn:dcai:graph:fixture:source:${path.nameWithoutExtension}",
                        canonicalGraphUri = "urn:dcai:graph:fixture:canonical:${path.nameWithoutExtension}",
                    )
                },
            )
        }
    }
}

data class FixtureGraphTarget(
    val path: Path,
    val sourceGraphUri: String,
    val canonicalGraphUri: String,
) {
    init {
        require(sourceGraphUri.startsWith("urn:dcai:graph:fixture:source:")) {
            "sourceGraphUri must use the controlled fixture source namespace"
        }
        require(canonicalGraphUri.startsWith("urn:dcai:graph:fixture:canonical:")) {
            "canonicalGraphUri must use the controlled fixture canonical namespace"
        }
    }
}
