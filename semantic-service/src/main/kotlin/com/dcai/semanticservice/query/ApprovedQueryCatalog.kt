package com.dcai.semanticservice.query

import java.nio.file.Path
import kotlin.io.path.exists
import org.apache.jena.query.QueryFactory
import org.apache.jena.query.QueryParseException
import org.apache.jena.rdf.model.ModelFactory
import org.apache.jena.rdf.model.Property
import org.apache.jena.rdf.model.Resource
import org.apache.jena.rdf.model.ResourceFactory
import org.apache.jena.riot.RDFDataMgr
import org.apache.jena.vocabulary.RDF

class ApprovedQueryCatalog(
    private val repoRoot: Path,
) {
    fun load(): ApprovedQueryManifest {
        val manifestPath = repoRoot.resolve("queries/manifest.ttl").normalize()
        require(manifestPath.exists()) { "Missing query manifest: queries/manifest.ttl" }

        val model = ModelFactory.createDefaultModel()
        RDFDataMgr.read(model, manifestPath.toUri().toString())

        val entries = model
            .listResourcesWithProperty(RDF.type, QUERY_ENTRY)
            .toList()
            .mapNotNull { resource -> loadEntry(resource) }
            .associateBy { entry -> entry.id }

        return ApprovedQueryManifest(entries)
    }

    private fun loadEntry(resource: Resource): ApprovedQueryDefinition? {
        val implementationStatus = resource.stringValue(IMPLEMENTATION_STATUS)
        if (implementationStatus != APPROVED_STATUS) {
            return null
        }

        val id = resource.uri.removePrefix(QUERY_NAMESPACE)
        val mode = QueryMode.from(resource.stringValue(QUERY_MODE))
        val queryPath = repoRoot.resolve(resource.stringValue(QUERY_PATH)).normalize()
        require(queryPath.startsWith(repoRoot.resolve("queries").normalize())) {
            "Approved query $id must resolve under queries/"
        }
        require(queryPath.exists()) {
            "Approved query $id references a missing query file: ${repoRoot.relativize(queryPath)}"
        }

        val sparql = queryPath.toFile().readText()
        validateReadOnlyQuery(id, mode, sparql)

        return ApprovedQueryDefinition(
            id = id,
            path = queryPath,
            mode = mode,
            graphScope = resource.stringValue(GRAPH_SCOPE),
            sparql = sparql,
        )
    }

    private fun validateReadOnlyQuery(
        id: String,
        mode: QueryMode,
        sparql: String,
    ) {
        require(mode.isRuntimeReadOnly) {
            "Approved runtime query $id must be SELECT or ASK, not ${mode.value}"
        }

        val parsed = try {
            QueryFactory.create(sparql)
        } catch (error: QueryParseException) {
            error("Approved query $id is not parseable SPARQL: ${error.message}")
        }

        val matchesMode = when (mode) {
            QueryMode.SELECT -> parsed.isSelectType
            QueryMode.ASK -> parsed.isAskType
            QueryMode.CONSTRUCT,
            QueryMode.UPDATE,
            -> false
        }
        require(matchesMode) {
            "Approved query $id mode ${mode.value} does not match query file operation"
        }
    }

    private fun Resource.stringValue(property: Property): String {
        val statement = getProperty(property)
            ?: error("Missing ${property.localName} for query entry $uri")
        return statement.`object`.asLiteral().string
    }

    private companion object {
        private const val QUERY_NAMESPACE = "urn:dcai:query:"
        private const val APPROVED_STATUS = "phase16-approved"
        private val QUERY_ENTRY = ResourceFactory.createResource("${QUERY_NAMESPACE}QueryEntry")
        private val QUERY_PATH = ResourceFactory.createProperty("${QUERY_NAMESPACE}queryPath")
        private val QUERY_MODE = ResourceFactory.createProperty("${QUERY_NAMESPACE}queryMode")
        private val GRAPH_SCOPE = ResourceFactory.createProperty("${QUERY_NAMESPACE}graphScope")
        private val IMPLEMENTATION_STATUS = ResourceFactory.createProperty("${QUERY_NAMESPACE}implementationStatus")
    }
}

data class ApprovedQueryManifest(
    val entries: Map<String, ApprovedQueryDefinition>,
) {
    fun requireQuery(id: String): ApprovedQueryDefinition {
        return entries[id] ?: error("Unapproved query id: $id")
    }
}

data class ApprovedQueryDefinition(
    val id: String,
    val path: Path,
    val mode: QueryMode,
    val graphScope: String,
    val sparql: String,
)

enum class QueryMode(
    val value: String,
) {
    SELECT("SELECT"),
    ASK("ASK"),
    CONSTRUCT("CONSTRUCT"),
    UPDATE("UPDATE"),
    ;

    val isRuntimeReadOnly: Boolean
        get() = this == SELECT || this == ASK

    companion object {
        fun from(value: String): QueryMode {
            return entries.firstOrNull { mode -> mode.value == value }
                ?: error("Unsupported query mode: $value")
        }
    }
}
