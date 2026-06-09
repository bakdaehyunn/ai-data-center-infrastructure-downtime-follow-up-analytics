package com.dcai.semanticservice.graph

import org.apache.jena.rdf.model.Model
import org.apache.jena.rdf.model.ModelFactory

interface NamedGraphWriter {
    fun replaceNamedGraph(graphUri: String, model: Model): NamedGraphWriteResult
}

interface NamedGraphStore : NamedGraphWriter {
    fun readNamedGraph(graphUri: String): NamedGraphSnapshot

    fun deleteNamedGraph(graphUri: String): NamedGraphWriteResult
}

data class NamedGraphWriteResult(
    val graphUri: String,
    val tripleCount: Int,
    val statusCode: Int? = null,
)

data class NamedGraphSnapshot(
    val graphUri: String,
    val exists: Boolean,
    val model: Model,
) {
    fun copyModel(): Model = ModelFactory.createDefaultModel().add(model)
}
