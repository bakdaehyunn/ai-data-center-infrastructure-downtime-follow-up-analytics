package com.dcai.semanticservice.fixtures

import java.nio.file.Path
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertTrue

class FixtureGraphLoadPlanTest {
    @Test
    fun buildsDefaultPlanForValidFixturesOnly() {
        val plan = FixtureGraphLoadPlan.default(Path.of("/repo"))

        assertEquals(3, plan.fixtures.size)
        assertEquals("/repo/fixtures/rdf/valid/minimal-incident.ttl", plan.fixtures.first().path.toString())
        assertTrue(plan.fixtures.all { it.sourceGraphUri.startsWith("urn:dcai:graph:fixture:source:") })
        assertTrue(plan.fixtures.all { it.canonicalGraphUri.startsWith("urn:dcai:graph:fixture:canonical:") })
    }
}
