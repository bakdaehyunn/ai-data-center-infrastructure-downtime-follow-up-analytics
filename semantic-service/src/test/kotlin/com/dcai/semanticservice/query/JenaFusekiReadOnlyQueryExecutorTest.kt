package com.dcai.semanticservice.query

import com.dcai.semanticservice.runtime.SemanticServiceApplication
import org.apache.jena.query.ParameterizedSparqlString
import org.apache.jena.query.QueryFactory
import kotlin.test.Test
import kotlin.test.assertFailsWith

class JenaFusekiReadOnlyQueryExecutorTest {
    private val repoRoot = SemanticServiceApplication.locateRepoRoot()

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

    @Test
    fun parameterizedReadModelQueriesRemainParseableAfterLiteralBinding() {
        val manifest = ApprovedQueryCatalog(repoRoot).load()
        val parameterizedQueries = mapOf(
            "semanticFollowUpDetail" to "incidentIdParam",
            "semanticIncidentEvidence" to "incidentIdParam",
            "semanticIncidentTimeline" to "incidentIdParam",
            "semanticDependencyImpactByAsset" to "assetIdParam",
            "semanticBlastRadiusByAsset" to "assetIdParam",
            "semanticTrustFindingList" to "trustFindingIdParam",
        )

        parameterizedQueries.forEach { (queryId, parameterName) ->
            val query = ParameterizedSparqlString(manifest.requireQuery(queryId).sparql)
            query.setLiteral(parameterName, "INC-REASONING-0001")

            QueryFactory.create(query.toString())
        }
    }
}
