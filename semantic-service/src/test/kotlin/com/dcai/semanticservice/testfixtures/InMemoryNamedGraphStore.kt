package com.dcai.semanticservice.testfixtures

import com.dcai.semanticservice.graph.NamedGraphSnapshot
import com.dcai.semanticservice.graph.NamedGraphStore
import com.dcai.semanticservice.graph.NamedGraphWriteResult
import org.apache.jena.rdf.model.Model
import org.apache.jena.rdf.model.ModelFactory

class InMemoryNamedGraphStore(
    initialGraphs: Map<String, Model> = emptyMap(),
    private val failOnReplaceGraphUri: String? = null,
) : NamedGraphStore {
    private val graphs = initialGraphs.mapValuesTo(mutableMapOf()) { (_, model) ->
        ModelFactory.createDefaultModel().add(model)
    }
    val writeOrder = mutableListOf<String>()

    fun graph(graphUri: String): Model? = graphs[graphUri]

    override fun readNamedGraph(graphUri: String): NamedGraphSnapshot {
        val model = graphs[graphUri]
        return NamedGraphSnapshot(
            graphUri = graphUri,
            exists = model != null,
            model = model?.let { ModelFactory.createDefaultModel().add(it) } ?: ModelFactory.createDefaultModel(),
        )
    }

    override fun replaceNamedGraph(graphUri: String, model: Model): NamedGraphWriteResult {
        if (graphUri == failOnReplaceGraphUri) {
            error("simulated write failure for $graphUri")
        }
        writeOrder += graphUri
        graphs[graphUri] = ModelFactory.createDefaultModel().add(model)
        return NamedGraphWriteResult(
            graphUri = graphUri,
            tripleCount = model.size().toInt(),
            statusCode = 200,
        )
    }

    override fun deleteNamedGraph(graphUri: String): NamedGraphWriteResult {
        graphs.remove(graphUri)
        return NamedGraphWriteResult(
            graphUri = graphUri,
            tripleCount = 0,
            statusCode = 204,
        )
    }
}
