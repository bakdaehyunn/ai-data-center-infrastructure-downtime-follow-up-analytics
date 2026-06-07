package com.dcai.semanticservice.graph

import org.apache.jena.rdf.model.Model

interface NamedGraphWriter {
    fun replaceNamedGraph(graphUri: String, model: Model): NamedGraphWriteResult
}

data class NamedGraphWriteResult(
    val graphUri: String,
    val tripleCount: Int,
    val statusCode: Int? = null,
)
