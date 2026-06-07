package com.dcai.semanticservice.fixtures

import java.nio.file.Path
import kotlin.io.path.exists
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

class FixtureValidationGate(
    private val repoRoot: Path,
) {
    fun validate(fixture: FixtureGraphTarget): ValidatedFixtureGraph {
        val model = ModelFactory.createDefaultModel()
        val errors = mutableListOf<String>()

        if (!fixture.path.exists()) {
            errors += "Missing fixture: ${repoRoot.relativize(fixture.path)}"
            return ValidatedFixtureGraph(
                target = fixture,
                model = model,
                validation = FixtureValidationReport(conforms = false, tripleCount = 0, errors = errors),
            )
        }

        runCatching {
            RDFDataMgr.read(model, fixture.path.toUri().toString())
        }.onFailure { error ->
            errors += "Unable to parse fixture ${repoRoot.relativize(fixture.path)}: ${error.message}"
        }

        if (errors.isEmpty()) {
            errors += validateShacl(model)
            errors += validateProvenance(model)
        }

        return ValidatedFixtureGraph(
            target = fixture,
            model = model,
            validation = FixtureValidationReport(
                conforms = errors.isEmpty(),
                tripleCount = model.size().toInt(),
                errors = errors,
            ),
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
            return listOf("Provenance gate failed: fixture has no dcai:SourceRecord")
        }

        val hasCompleteSourceRecord = sourceRecords.any { sourceRecord ->
            model.contains(sourceRecord, HAS_SOURCE_RECORD_ID) &&
                model.contains(sourceRecord, HAS_SOURCE_SYSTEM) &&
                model.contains(sourceRecord, HAS_SOURCE_PAYLOAD_HASH) &&
                model.contains(sourceRecord, WAS_GENERATED_BY)
        }
        if (!hasCompleteSourceRecord) {
            return listOf("Provenance gate failed: no SourceRecord has id, source system, payload hash, and import activity")
        }

        val importActivities = model.listSubjectsWithProperty(RDF.type, IMPORT_ACTIVITY).toList()
        val hasTimestampedImportActivity = importActivities.any { activity ->
            model.contains(activity, GENERATED_AT_TIME)
        }
        if (!hasTimestampedImportActivity) {
            return listOf("Provenance gate failed: no ImportActivity has prov:generatedAtTime")
        }

        return emptyList()
    }

    companion object {
        private val SOURCE_RECORD = ResourceFactory.createResource("urn:dcai:ontology:SourceRecord")
        private val IMPORT_ACTIVITY = ResourceFactory.createResource("urn:dcai:ontology:ImportActivity")
        private val HAS_SOURCE_RECORD_ID = ResourceFactory.createProperty("urn:dcai:ontology:hasSourceRecordId")
        private val HAS_SOURCE_SYSTEM = ResourceFactory.createProperty("urn:dcai:ontology:hasSourceSystem")
        private val HAS_SOURCE_PAYLOAD_HASH = ResourceFactory.createProperty("urn:dcai:ontology:hasSourcePayloadHash")
        private val WAS_GENERATED_BY = ResourceFactory.createProperty("http://www.w3.org/ns/prov#wasGeneratedBy")
        private val GENERATED_AT_TIME = ResourceFactory.createProperty("http://www.w3.org/ns/prov#generatedAtTime")
    }
}

data class ValidatedFixtureGraph(
    val target: FixtureGraphTarget,
    val model: Model,
    val validation: FixtureValidationReport,
)

data class FixtureValidationReport(
    val conforms: Boolean,
    val tripleCount: Int,
    val errors: List<String> = emptyList(),
)
