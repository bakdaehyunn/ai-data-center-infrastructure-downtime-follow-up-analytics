package com.dcai.semanticservice.fixtures

import com.dcai.semanticservice.runtime.SemanticServiceApplication
import kotlin.test.Test
import kotlin.test.assertFalse
import kotlin.test.assertTrue

class FixtureValidationGateTest {
    private val repoRoot = SemanticServiceApplication.locateRepoRoot()
    private val gate = FixtureValidationGate(repoRoot)

    @Test
    fun acceptsValidFixtureWithShaclAndProvenance() {
        val target = FixtureGraphTarget(
            path = repoRoot.resolve("fixtures/rdf/valid/minimal-incident.ttl"),
            sourceGraphUri = "urn:dcai:graph:fixture:source:minimal-incident",
            canonicalGraphUri = "urn:dcai:graph:fixture:canonical:minimal-incident",
        )

        val validated = gate.validate(target)

        assertTrue(validated.validation.conforms, validated.validation.errors.joinToString(separator = "\n"))
        assertTrue(validated.validation.tripleCount > 0)
    }

    @Test
    fun acceptsDefaultPhaseThreeFixturePlan() {
        val failures = FixtureGraphLoadPlan.default(repoRoot).fixtures
            .map { target -> gate.validate(target) }
            .filterNot { validated -> validated.validation.conforms }

        assertTrue(
            failures.isEmpty(),
            failures.joinToString(separator = "\n") { failure ->
                "${failure.target.path}: ${failure.validation.errors.joinToString()}"
            },
        )
    }

    @Test
    fun rejectsInvalidFixtureBeforePromotion() {
        val target = FixtureGraphTarget(
            path = repoRoot.resolve("fixtures/rdf/invalid/reasoning-output-missing-provenance.ttl"),
            sourceGraphUri = "urn:dcai:graph:fixture:source:invalid-reasoning-output",
            canonicalGraphUri = "urn:dcai:graph:fixture:canonical:invalid-reasoning-output",
        )

        val validated = gate.validate(target)

        assertFalse(validated.validation.conforms)
        assertTrue(validated.validation.errors.isNotEmpty())
    }
}
