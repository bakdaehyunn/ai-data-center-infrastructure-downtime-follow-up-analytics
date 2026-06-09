package com.dcai.semanticservice.reasoning

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

class ReasoningValidationGate(
    private val repoRoot: Path,
) {
    fun validate(model: Model): ReasoningValidationReport {
        val errors = validateShacl(model) + validateReasoningProvenance(model)
        return ReasoningValidationReport(
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

    private fun validateReasoningProvenance(model: Model): List<String> {
        val activities = model.listSubjectsWithProperty(RDF.type, REASONING_ACTIVITY).toList()
        if (activities.isEmpty()) {
            return listOf("Reasoning provenance gate failed: no dcai:ReasoningActivity")
        }

        val incompleteActivities = activities.filterNot { activity ->
            model.contains(activity, USED) &&
                model.contains(activity, GENERATED) &&
                model.contains(activity, GENERATED_AT_TIME)
        }
        if (incompleteActivities.isNotEmpty()) {
            return listOf("Reasoning provenance gate failed: ${incompleteActivities.size} ReasoningActivity resources are incomplete")
        }

        val findings = model.listSubjectsWithProperty(RDF.type, DEPENDENCY_IMPACT_FINDING).toList() +
            model.listSubjectsWithProperty(RDF.type, BLAST_RADIUS_FINDING).toList()
        if (findings.isEmpty()) {
            return listOf("Reasoning provenance gate failed: reasoning output has no approved finding")
        }

        val findingsWithoutActivity = findings.filterNot { finding ->
            model.contains(finding, WAS_GENERATED_BY)
        }
        if (findingsWithoutActivity.isNotEmpty()) {
            return listOf("Reasoning provenance gate failed: ${findingsWithoutActivity.size} findings have no generating activity")
        }

        return emptyList()
    }

    private companion object {
        private val REASONING_ACTIVITY = ResourceFactory.createResource("urn:dcai:ontology:ReasoningActivity")
        private val DEPENDENCY_IMPACT_FINDING = ResourceFactory.createResource("urn:dcai:ontology:DependencyImpactFinding")
        private val BLAST_RADIUS_FINDING = ResourceFactory.createResource("urn:dcai:ontology:BlastRadiusFinding")
        private val USED = ResourceFactory.createProperty("http://www.w3.org/ns/prov#used")
        private val GENERATED = ResourceFactory.createProperty("http://www.w3.org/ns/prov#generated")
        private val GENERATED_AT_TIME = ResourceFactory.createProperty("http://www.w3.org/ns/prov#generatedAtTime")
        private val WAS_GENERATED_BY = ResourceFactory.createProperty("http://www.w3.org/ns/prov#wasGeneratedBy")
    }
}

data class ReasoningValidationReport(
    val conforms: Boolean,
    val tripleCount: Int,
    val errors: List<String> = emptyList(),
)
