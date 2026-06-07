package com.dcai.semanticservice.fixtures

import com.dcai.semanticservice.graph.NamedGraphWriter

class ControlledFixtureGraphLoader(
    private val validationGate: FixtureValidationGate,
    private val writer: NamedGraphWriter,
) : FixtureGraphLoader {
    override fun load(plan: FixtureGraphLoadPlan): FixtureLoadSummary {
        val validatedGraphs = plan.fixtures.map { target -> validationGate.validate(target) }
        if (validatedGraphs.any { !it.validation.conforms }) {
            return FixtureLoadSummary(
                results = validatedGraphs.map { validated ->
                    FixtureLoadResult(
                        target = validated.target,
                        validation = validated.validation,
                    )
                },
            )
        }

        return FixtureLoadSummary(results = validatedGraphs.map { loadValidated(it) })
    }

    private fun loadValidated(validated: ValidatedFixtureGraph): FixtureLoadResult {
        val target = validated.target
        val writeErrors = mutableListOf<String>()
        val sourceWritten = runCatching {
            writer.replaceNamedGraph(target.sourceGraphUri, validated.model)
        }.fold(
            onSuccess = { true },
            onFailure = { error ->
                writeErrors += "Source graph write failed for ${target.sourceGraphUri}: ${error.message}"
                false
            },
        )

        val canonicalWritten = if (sourceWritten) {
            runCatching {
                writer.replaceNamedGraph(target.canonicalGraphUri, validated.model)
            }.fold(
                onSuccess = { true },
                onFailure = { error ->
                    writeErrors += "Canonical graph promotion failed for ${target.canonicalGraphUri}: ${error.message}"
                    false
                },
            )
        } else {
            false
        }

        return FixtureLoadResult(
            target = target,
            validation = validated.validation,
            sourceGraphWritten = sourceWritten,
            canonicalGraphWritten = canonicalWritten,
            writeErrors = writeErrors,
        )
    }
}
