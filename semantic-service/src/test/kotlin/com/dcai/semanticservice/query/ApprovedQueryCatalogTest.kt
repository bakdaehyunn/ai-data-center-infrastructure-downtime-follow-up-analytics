package com.dcai.semanticservice.query

import com.dcai.semanticservice.runtime.SemanticServiceApplication
import java.nio.file.Files
import kotlin.test.Test
import kotlin.test.assertEquals
import kotlin.test.assertFailsWith
import kotlin.test.assertTrue

class ApprovedQueryCatalogTest {
    private val repoRoot = SemanticServiceApplication.locateRepoRoot()

    @Test
    fun loadsOnlyPhaseSixteenApprovedReadOnlyQueries() {
        val manifest = ApprovedQueryCatalog(repoRoot).load()

        assertEquals(
            setOf(
                "fixtureNamedGraphInventory",
                "fixtureIncidentSummary",
                "fixtureProvenanceSourceRecords",
                "semanticFollowUpQueueList",
                "semanticDashboardOverview",
                "semanticFilterMetadata",
                "semanticFollowUpDetail",
                "semanticImpactSummary",
                "semanticTopologyDependencies",
                "semanticTrustFindingList",
                "semanticStageBottlenecks",
                "semanticAssetDelaySummary",
                "semanticZoneDelaySummary",
                "semanticSpareWaitSummary",
                "semanticValidationSummary",
                "semanticIncidentEvidence",
                "semanticIncidentTimeline",
                "semanticDependencyImpactByAsset",
                "semanticBlastRadiusByAsset",
            ),
            manifest.entries.keys,
        )
        assertTrue(manifest.entries.values.all { it.mode == QueryMode.SELECT })
        assertEquals(
            "fixture or promoted canonical graph, reasoning graph",
            manifest.requireQuery("semanticFollowUpDetail").graphScope,
        )
        assertTrue(manifest.requireQuery("semanticFollowUpDetail").sparql.contains("urn:dcai:graph:canonical:"))
        assertTrue(manifest.requireQuery("semanticFollowUpDetail").sparql.contains("urn:dcai:graph:reasoning:"))
        assertEquals(
            "fixture canonical graph or reasoning graph",
            manifest.requireQuery("semanticTrustFindingList").graphScope,
        )
        assertTrue(manifest.requireQuery("semanticTrustFindingList").sparql.contains("urn:dcai:graph:reasoning:"))
    }

    @Test
    fun rejectsUnapprovedPlaceholderQueryIds() {
        val manifest = ApprovedQueryCatalog(repoRoot).load()

        assertFailsWith<IllegalStateException> {
            manifest.requireQuery("dependencyExposureReasoning")
        }
    }

    @Test
    fun rejectsApprovedNonReadOnlyQueryModes() {
        val tempRepo = Files.createTempDirectory("phase16-query-catalog-test")
        tempRepo.resolve("queries/inspection").toFile().mkdirs()
        tempRepo.resolve("queries/inspection/bad.construct.rq").toFile().writeText(
            """
            CONSTRUCT { ?s ?p ?o }
            WHERE { ?s ?p ?o }
            """.trimIndent(),
        )
        tempRepo.resolve("queries/manifest.ttl").toFile().writeText(
            """
            @prefix dcai-query: <urn:dcai:query:> .
            @prefix dcterms: <http://purl.org/dc/terms/> .
            @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .

            dcai-query:badRuntimeConstruct
              rdf:type dcai-query:QueryEntry ;
              dcterms:title "Bad runtime construct" ;
              dcai-query:queryPath "queries/inspection/bad.construct.rq" ;
              dcai-query:queryMode "CONSTRUCT" ;
              dcai-query:graphScope "fixture graph" ;
              dcai-query:implementationStatus "phase16-approved" .
            """.trimIndent(),
        )

        assertFailsWith<IllegalArgumentException> {
            ApprovedQueryCatalog(tempRepo).load()
        }
    }
}
