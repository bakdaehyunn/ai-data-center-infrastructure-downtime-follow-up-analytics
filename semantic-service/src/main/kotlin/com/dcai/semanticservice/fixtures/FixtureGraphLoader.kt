package com.dcai.semanticservice.fixtures

interface FixtureGraphLoader {
    fun load(plan: FixtureGraphLoadPlan): FixtureLoadSummary
}

data class FixtureLoadSummary(
    val results: List<FixtureLoadResult>,
) {
    val attemptedCount: Int = results.size
    val promotedCount: Int = results.count { it.promoted }
    val succeeded: Boolean = results.all { it.promoted }
    val errors: List<String> = results.flatMap { result ->
        result.validation.errors + result.writeErrors
    }
}

data class FixtureLoadResult(
    val target: FixtureGraphTarget,
    val validation: FixtureValidationReport,
    val sourceGraphWritten: Boolean = false,
    val canonicalGraphWritten: Boolean = false,
    val writeErrors: List<String> = emptyList(),
) {
    val promoted: Boolean = validation.conforms && sourceGraphWritten && canonicalGraphWritten && writeErrors.isEmpty()
}
