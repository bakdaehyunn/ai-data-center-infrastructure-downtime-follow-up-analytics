package com.dcai.semanticservice.query

import kotlin.test.Test
import kotlin.test.assertFailsWith

class JenaFusekiReadOnlyQueryExecutorTest {
    @Test
    fun rejectsUnapprovedQueryIdBeforeNetworkExecution() {
        val executor = JenaFusekiReadOnlyQueryExecutor(
            manifest = ApprovedQueryManifest(
                entries = mapOf(
                    "fixtureNamedGraphInventory" to ApprovedQueryDefinition(
                        id = "fixtureNamedGraphInventory",
                        path = java.nio.file.Path.of("queries/inspection/fixture_named_graph_inventory.select.rq"),
                        mode = QueryMode.SELECT,
                        graphScope = "fixture graphs",
                        sparql = "SELECT * WHERE { ?s ?p ?o } LIMIT 1",
                    ),
                ),
            ),
        )

        assertFailsWith<IllegalStateException> {
            executor.execute("dependencyExposureReasoning")
        }
    }
}
