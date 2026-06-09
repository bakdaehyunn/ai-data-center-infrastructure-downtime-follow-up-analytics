package com.dcai.semanticservice.promotion

import java.nio.file.Path
import org.apache.jena.rdf.model.Model
import org.apache.jena.rdf.model.ModelFactory
import org.apache.jena.rdf.model.RDFNode
import org.apache.jena.rdf.model.Resource
import org.apache.jena.rdf.model.ResourceFactory
import org.apache.jena.riot.RDFDataMgr
import org.apache.jena.shacl.ShaclValidator
import org.apache.jena.shacl.Shapes
import org.apache.jena.vocabulary.RDF
import org.apache.jena.vocabulary.RDFS

class ProductionGraphValidationGate(
    private val repoRoot: Path,
) {
    fun validate(model: Model): ProductionGraphValidationReport {
        val errors = validateShacl(model) + validateProvenance(model)
        return ProductionGraphValidationReport(
            conforms = errors.isEmpty(),
            tripleCount = model.size().toInt(),
            errors = errors,
        )
    }

    private fun validateShacl(model: Model): List<String> {
        val shapesModel = ModelFactory.createDefaultModel()
        repoRoot.resolve("shapes").toFile()
            .walkTopDown()
            .filter { it.isFile && it.extension == "ttl" }
            .sortedBy { it.path }
            .forEach { RDFDataMgr.read(shapesModel, it.toURI().toString()) }

        val shapes = Shapes.parse(shapesModel.graph)
        val validationModel = withRdfsTypeClosure(model)
        val report = ShaclValidator.get().validate(shapes, validationModel.graph)
        return if (report.conforms()) {
            emptyList()
        } else {
            val details = report.getEntries().joinToString(separator = "; ") { it.toString() }
            listOf("SHACL validation failed: $details")
        }
    }

    private fun withRdfsTypeClosure(model: Model): Model {
        val validationModel = ModelFactory.createDefaultModel().add(model)
        val ontologyModel = ModelFactory.createDefaultModel()
        repoRoot.resolve("ontology/modules").toFile()
            .walkTopDown()
            .filter { it.isFile && it.extension == "ttl" }
            .sortedBy { it.path }
            .forEach { RDFDataMgr.read(ontologyModel, it.toURI().toString()) }

        val superClasses = ontologyModel
            .listStatements(null as Resource?, RDFS.subClassOf, null as RDFNode?)
            .toList()
            .filter { statement -> statement.subject.isURIResource && statement.`object`.isURIResource }
            .groupBy(
                keySelector = { statement -> statement.subject.asResource() },
                valueTransform = { statement -> statement.`object`.asResource() },
            )

        validationModel.listStatements(null as Resource?, RDF.type, null as RDFNode?).toList()
            .filter { statement -> statement.`object`.isURIResource }
            .forEach { statement ->
                ancestorsOf(statement.`object`.asResource(), superClasses).forEach { ancestor ->
                    validationModel.add(statement.subject, RDF.type, ancestor)
                }
            }

        return validationModel
    }

    private fun ancestorsOf(
        resource: Resource,
        superClasses: Map<Resource, List<Resource>>,
        seen: Set<Resource> = emptySet(),
    ): Set<Resource> {
        val direct = superClasses[resource].orEmpty().filterNot { it in seen }
        return direct.toSet() + direct.flatMap { ancestor ->
            ancestorsOf(ancestor, superClasses, seen + ancestor)
        }
    }

    private fun validateProvenance(model: Model): List<String> {
        val sourceRecords = model.listSubjectsWithProperty(RDF.type, SOURCE_RECORD).toList()
        if (sourceRecords.isEmpty()) {
            return listOf("Provenance gate failed: candidate graph has no dcai:SourceRecord")
        }

        val incompleteSourceRecords = sourceRecords.filterNot { sourceRecord ->
            model.contains(sourceRecord, HAS_SOURCE_RECORD_ID) &&
                model.contains(sourceRecord, HAS_SOURCE_SYSTEM) &&
                model.contains(sourceRecord, HAS_SOURCE_PAYLOAD_HASH) &&
                model.contains(sourceRecord, WAS_GENERATED_BY)
        }
        if (incompleteSourceRecords.isNotEmpty()) {
            return listOf("Provenance gate failed: ${incompleteSourceRecords.size} SourceRecord resources are incomplete")
        }

        val promotionActivities = model.listSubjectsWithProperty(RDF.type, PROMOTION_ACTIVITY).toList()
        if (promotionActivities.isEmpty()) {
            return listOf("Provenance gate failed: candidate graph has no dcai:PromotionActivity")
        }

        val hasTimestampedPromotion = promotionActivities.any { activity ->
            model.contains(activity, GENERATED_AT_TIME)
        }
        if (!hasTimestampedPromotion) {
            return listOf("Provenance gate failed: no PromotionActivity has prov:generatedAtTime")
        }

        return emptyList()
    }

    private companion object {
        private val SOURCE_RECORD = ResourceFactory.createResource("urn:dcai:ontology:SourceRecord")
        private val PROMOTION_ACTIVITY = ResourceFactory.createResource("urn:dcai:ontology:PromotionActivity")
        private val HAS_SOURCE_RECORD_ID = ResourceFactory.createProperty("urn:dcai:ontology:hasSourceRecordId")
        private val HAS_SOURCE_SYSTEM = ResourceFactory.createProperty("urn:dcai:ontology:hasSourceSystem")
        private val HAS_SOURCE_PAYLOAD_HASH = ResourceFactory.createProperty("urn:dcai:ontology:hasSourcePayloadHash")
        private val WAS_GENERATED_BY = ResourceFactory.createProperty("http://www.w3.org/ns/prov#wasGeneratedBy")
        private val GENERATED_AT_TIME = ResourceFactory.createProperty("http://www.w3.org/ns/prov#generatedAtTime")
    }
}

data class ProductionGraphValidationReport(
    val conforms: Boolean,
    val tripleCount: Int,
    val errors: List<String> = emptyList(),
)
