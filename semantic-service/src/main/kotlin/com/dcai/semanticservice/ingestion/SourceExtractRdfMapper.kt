package com.dcai.semanticservice.ingestion

import java.net.URLEncoder
import java.nio.charset.StandardCharsets
import java.time.Instant
import org.apache.jena.datatypes.xsd.XSDDatatype
import org.apache.jena.rdf.model.Model
import org.apache.jena.rdf.model.ModelFactory
import org.apache.jena.rdf.model.Resource
import org.apache.jena.rdf.model.ResourceFactory
import org.apache.jena.vocabulary.RDF
import org.apache.jena.vocabulary.RDFS

class SourceExtractRdfMapper {
    fun map(batch: SourceExtractBatch): SourceExtractRdfMapping {
        val sourceModel = ModelFactory.createDefaultModel()
        val canonicalModel = ModelFactory.createDefaultModel()
        val provenanceModel = ModelFactory.createDefaultModel()
        val context = MappingContext(batch, sourceModel, canonicalModel, provenanceModel)

        context.addBatchProvenance()
        batch.facilities.forEach { context.mapFacility(it) }
        batch.zones.forEach { context.mapZone(it) }
        batch.assets.forEach { context.mapAsset(it) }
        batch.incidents.forEach { context.mapIncident(it) }
        batch.dependencies.forEach { context.mapDependency(it) }
        batch.workflowEvents.forEach { context.mapWorkflowEvent(it) }
        batch.impacts.forEach { context.mapImpact(it) }
        batch.evidence.forEach { context.mapEvidence(it) }
        context.addPromotionProvenance()

        return SourceExtractRdfMapping(
            sourceModel = sourceModel,
            canonicalModel = canonicalModel,
            provenanceModel = provenanceModel,
        )
    }

    private class MappingContext(
        private val batch: SourceExtractBatch,
        private val sourceModel: Model,
        private val canonicalModel: Model,
        private val provenanceModel: Model,
    ) {
        private val sourceSystem = sourceSystem(batch.sourceSystemId)
        private val sourceExtract = sourceExtract(batch.batchId)
        private val importActivity = importActivity(batch.batchId)
        private val promotionActivity = promotionActivity(batch.batchId)
        private val generatedCanonicalResources = mutableSetOf<Resource>()

        fun addBatchProvenance() {
            listOf(sourceModel, provenanceModel).forEach { model ->
                model.add(sourceSystem, RDF.type, Dcai.SourceSystem)
                model.add(sourceSystem, RDFS.label, batch.sourceSystemLabel)
                model.add(sourceExtract, RDF.type, Dcai.SourceExtract)
                model.add(sourceExtract, Dcai.hasIdentifier, batch.batchId)
                model.add(sourceExtract, Dcai.hasSourceSystem, sourceSystem)
                model.add(sourceExtract, Prov.wasGeneratedBy, importActivity)
                model.add(importActivity, RDF.type, Dcai.ImportActivity)
                model.add(importActivity, Prov.generatedAtTime, literal(batch.importedAt))
            }

            batch.allSourceRecords.forEach { record ->
                addSourceRecord(record)
            }
        }

        fun mapFacility(record: FacilitySourceRecord) {
            val facility = facility(record.facilityId)
            canonicalModel.add(facility, RDF.type, Dcai.Facility)
            canonicalModel.add(facility, Dcai.hasIdentifier, record.facilityId)
            record.label?.let { canonicalModel.add(facility, RDFS.label, it) }
            derivedFrom(facility, record)
        }

        fun mapZone(record: ZoneSourceRecord) {
            val zone = zone(record.zoneId)
            canonicalModel.add(zone, RDF.type, Dcai.InfrastructureZone)
            canonicalModel.add(zone, Dcai.hasIdentifier, record.zoneId)
            canonicalModel.add(zone, Dcai.zoneInFacility, facility(record.facilityId))
            record.label?.let { canonicalModel.add(zone, RDFS.label, it) }
            derivedFrom(zone, record)
        }

        fun mapAsset(record: AssetSourceRecord) {
            val asset = asset(record.assetId)
            canonicalModel.add(asset, RDF.type, record.assetClass.rdfClass())
            record.assetType.specificAssetClass()?.let { canonicalModel.add(asset, RDF.type, it) }
            canonicalModel.add(asset, Dcai.hasIdentifier, record.assetId)
            canonicalModel.add(asset, Dcai.locatedIn, zone(record.zoneId))
            canonicalModel.add(asset, Dcai.hasAssetType, record.assetType)
            record.hallId?.let { hallId ->
                val hall = hall(hallId)
                canonicalModel.add(hall, RDF.type, Dcai.DataHall)
                canonicalModel.add(hall, Dcai.hasIdentifier, hallId)
                derivedFrom(hall, record)
                canonicalModel.add(zone(record.zoneId), Dcai.zoneInHall, hall)
            }
            record.rowId?.let { rowId ->
                val row = infrastructureRow(rowId)
                canonicalModel.add(row, RDF.type, Dcai.InfrastructureRow)
                canonicalModel.add(row, Dcai.hasIdentifier, rowId)
                canonicalModel.add(row, Dcai.rowInZone, zone(record.zoneId))
                derivedFrom(row, record)
            }
            record.rackId?.let { rackId ->
                val rack = rack(rackId)
                canonicalModel.add(rack, RDF.type, Dcai.Rack)
                canonicalModel.add(rack, Dcai.hasIdentifier, rackId)
                record.rowId?.let { canonicalModel.add(rack, Dcai.rackInRow, infrastructureRow(it)) }
                canonicalModel.add(asset, Dcai.assetInRack, rack)
                derivedFrom(rack, record)
            }
            record.capacityGroupId?.let { capacityGroupId ->
                val capacityGroup = capacityGroup(capacityGroupId)
                canonicalModel.add(capacityGroup, RDF.type, Dcai.ComputeCapacityGroup)
                canonicalModel.add(capacityGroup, RDF.type, Dcai.GpuPod)
                canonicalModel.add(capacityGroup, Dcai.hasIdentifier, capacityGroupId)
                canonicalModel.add(asset, Dcai.assetInCapacityGroup, capacityGroup)
                derivedFrom(capacityGroup, record)
            }
            record.criticalityLevel?.let {
                canonicalModel.add(asset, Dcai.hasCriticalityLevel, it)
                canonicalModel.add(asset, Dcai.hasCriticality, controlledState(Dcai.CriticalityLevel, "criticality", it))
            }
            record.operationalStatus?.let {
                canonicalModel.add(asset, Dcai.hasOperationalStatus, it)
                canonicalModel.add(asset, Dcai.hasOperationalState, controlledState(Dcai.OperationalStatus, "operational-status", it))
            }
            derivedFrom(asset, record)
        }

        fun mapIncident(record: IncidentSourceRecord) {
            val stage = stage(record.currentStageId)
            canonicalModel.add(stage, RDF.type, Dcai.WorkflowStage)
            canonicalModel.add(stage, RDFS.label, record.currentStageLabel)

            val incident = incident(record.incidentId)
            canonicalModel.add(incident, RDF.type, Dcai.InfrastructureIncident)
            canonicalModel.add(incident, Dcai.hasIdentifier, record.incidentId)
            canonicalModel.add(incident, Dcai.affectsAsset, asset(record.assetId))
            canonicalModel.add(incident, Dcai.hasCurrentStage, stage)
            canonicalModel.add(incident, Dcai.hasIncidentStageState, controlledState(Dcai.IncidentStageState, "incident-stage", record.currentStageId))
            derivedFrom(incident, record)
        }

        fun mapDependency(record: DependencySourceRecord) {
            val edge = dependencyEdge(record.edgeId)
            canonicalModel.add(edge, RDF.type, Dcai.DependencyEdge)
            canonicalModel.add(edge, Dcai.hasIdentifier, record.edgeId)
            canonicalModel.add(edge, Dcai.hasDependentAsset, asset(record.dependentAssetId))
            canonicalModel.add(edge, Dcai.hasDependencyAsset, asset(record.dependencyAssetId))
            canonicalModel.add(edge, Dcai.hasDependencyRole, record.dependencyRole)
            canonicalModel.add(edge, Dcai.hasDependencyRoleConcept, controlledState(Dcai.DependencyRole, "dependency-role", record.dependencyRole))
            canonicalModel.add(edge, Dcai.hasImpactScope, record.impactScope)
            canonicalModel.add(edge, Dcai.hasImpactScopeConcept, controlledState(Dcai.ImpactScope, "impact-scope", record.impactScope))
            derivedFrom(edge, record)

            record.pathId?.let { pathId ->
                val path = dependencyPath(pathId)
                canonicalModel.add(path, RDF.type, record.pathClass.rdfClass())
                canonicalModel.add(path, Dcai.hasIdentifier, pathId)
                canonicalModel.add(path, Dcai.hasPathStep, edge)
                derivedFrom(path, record)
            }
        }

        fun mapWorkflowEvent(record: WorkflowEventSourceRecord) {
            val stage = stage(record.enteredStageId)
            canonicalModel.add(stage, RDF.type, Dcai.WorkflowStage)
            canonicalModel.add(stage, RDFS.label, record.enteredStageLabel)

            val event = workflowEvent(record.eventId)
            canonicalModel.add(event, RDF.type, Dcai.WorkflowEvent)
            canonicalModel.add(event, Dcai.hasEventId, record.eventId)
            canonicalModel.add(event, Dcai.eventForIncident, incident(record.incidentId))
            canonicalModel.add(event, Dcai.enteredStage, stage)
            canonicalModel.add(event, Dcai.hasEventStatus, record.status)
            canonicalModel.add(event, Dcai.hasWorkflowEventStatus, controlledState(Dcai.WorkflowEventStatus, "workflow-event-status", record.status))
            canonicalModel.add(event, Dcai.enteredAt, literal(record.enteredAt))
            record.exitedAt?.let { canonicalModel.add(event, Dcai.exitedAt, literal(it)) }
            record.durationHours?.let { canonicalModel.add(event, Dcai.hasDurationHours, literal(it.toPlainString(), XSDDatatype.XSDdecimal)) }
            record.delayHours?.let { canonicalModel.add(event, Dcai.hasDelayHours, literal(it.toPlainString(), XSDDatatype.XSDdecimal)) }
            derivedFrom(event, record)
        }

        fun mapImpact(record: ImpactSourceRecord) {
            val impact = impact(record.impactId)
            canonicalModel.add(impact, RDF.type, Dcai.ImpactObservation)
            canonicalModel.add(impact, Dcai.impactForIncident, incident(record.incidentId))
            record.estimatedCapacityRiskKw?.let {
                canonicalModel.add(impact, Dcai.estimatedCapacityRiskKw, literal(it.toPlainString(), XSDDatatype.XSDdecimal))
            }
            record.affectedGpuCount?.let {
                canonicalModel.add(impact, Dcai.affectedGpuCount, literal(it.toString(), XSDDatatype.XSDinteger))
            }
            record.affectedRackCount?.let {
                canonicalModel.add(impact, Dcai.affectedRackCount, literal(it.toString(), XSDDatatype.XSDinteger))
            }
            record.redundancyState?.let { canonicalModel.add(impact, Dcai.hasRedundancyState, it) }
            record.redundancyState?.let {
                canonicalModel.add(impact, Dcai.hasRedundancyStateConcept, controlledState(Dcai.RedundancyState, "redundancy-state", it))
            }
            record.mitigationState?.let {
                canonicalModel.add(impact, Dcai.hasMitigationState, it)
                canonicalModel.add(impact, Dcai.hasMitigationStateConcept, controlledState(Dcai.MitigationState, "mitigation-state", it))
            }
            record.vendorState?.let {
                canonicalModel.add(impact, Dcai.hasVendorState, it)
                canonicalModel.add(impact, Dcai.hasVendorStateConcept, controlledState(Dcai.VendorState, "vendor-state", it))
            }
            record.vendorEtaAt?.let { canonicalModel.add(impact, Dcai.vendorEtaAt, literal(it)) }
            derivedFrom(impact, record)
        }

        fun mapEvidence(record: EvidenceSourceRecord) {
            val evidence = evidence(record.evidenceId)
            canonicalModel.add(evidence, RDF.type, record.evidenceClass.rdfClass())
            canonicalModel.add(evidence, Dcai.supportsFact, supportedResource(record.supportsId))
            canonicalModel.add(evidence, Dcai.hasConfidenceState, record.confidenceState)
            canonicalModel.add(evidence, Dcai.hasEvidenceConfidence, controlledState(Dcai.EvidenceConfidenceState, "evidence-confidence", record.confidenceState))
            canonicalModel.add(evidence, Dcai.hasEvidenceTimestamp, literal(record.timestamp))
            record.metricName?.let { canonicalModel.add(evidence, Dcai.hasMetricName, it) }
            record.metricValue?.let { canonicalModel.add(evidence, Dcai.hasMetricValue, literal(it.toPlainString(), XSDDatatype.XSDdecimal)) }
            record.metricUnit?.let { canonicalModel.add(evidence, Dcai.hasMetricUnit, it) }
            record.telemetryStatus?.let {
                canonicalModel.add(evidence, Dcai.hasTelemetryStatus, it)
                canonicalModel.add(evidence, Dcai.hasTelemetryState, controlledState(Dcai.TelemetryStatus, "telemetry-status", it))
            }
            record.validationId?.let { canonicalModel.add(evidence, Dcai.hasValidationId, it) }
            record.validationStatus?.let {
                canonicalModel.add(evidence, Dcai.hasValidationStatus, it)
                canonicalModel.add(evidence, Dcai.hasValidationState, controlledState(Dcai.ValidationStatus, "validation-status", it))
            }
            record.workOrderId?.let { canonicalModel.add(evidence, Dcai.hasWorkOrderId, it) }
            record.workOrderStatus?.let {
                canonicalModel.add(evidence, Dcai.hasWorkOrderStatus, it)
                canonicalModel.add(evidence, Dcai.hasWorkOrderState, controlledState(Dcai.WorkOrderStatus, "work-order-status", it))
            }
            record.assignedTeam?.let { canonicalModel.add(evidence, Dcai.hasAssignedTeam, it) }
            derivedFrom(evidence, record)
        }

        fun addPromotionProvenance() {
            provenanceModel.add(promotionActivity, RDF.type, Dcai.PromotionActivity)
            provenanceModel.add(promotionActivity, Prov.generatedAtTime, literal(batch.importedAt))
            provenanceModel.add(promotionActivity, Dcai.hasIdentifier, batch.batchId)
            batch.allSourceRecords.forEach { record ->
                provenanceModel.add(promotionActivity, Prov.used, sourceRecord(record.recordId))
            }
            generatedCanonicalResources.forEach { resource ->
                provenanceModel.add(promotionActivity, Prov.generated, resource)
                provenanceModel.add(resource, Prov.wasGeneratedBy, promotionActivity)
            }
        }

        private fun derivedFrom(resource: Resource, record: SourceRecordIdentity) {
            canonicalModel.add(resource, Prov.wasDerivedFrom, sourceRecord(record.recordId))
            generatedCanonicalResources += resource
        }

        private fun supportedResource(id: String): Resource {
            return when {
                id.startsWith("INC-") -> incident(id)
                id.startsWith("IMPACT-") -> impact(id)
                id.startsWith("WO-") -> evidence(id)
                else -> ResourceFactory.createResource("urn:dcai:resource:${encode(id)}")
            }
        }

        private fun SourceRecordIdentity.requireRecord() {
            require(recordId.isNotBlank()) { "source record id must not be blank" }
            require(payloadHash.isNotBlank()) { "source record payloadHash must not be blank" }
        }

        private fun addSourceRecord(record: SourceRecordIdentity): Resource {
            record.requireRecord()
            val sourceRecord = sourceRecord(record.recordId)
            listOf(sourceModel, provenanceModel).forEach { model ->
                model.add(sourceRecord, RDF.type, Dcai.SourceRecord)
                model.add(sourceRecord, Dcai.hasSourceRecordId, record.recordId)
                model.add(sourceRecord, Dcai.hasSourceSystem, sourceSystem)
                model.add(sourceRecord, Dcai.hasSourcePayloadHash, record.payloadHash)
                model.add(sourceRecord, Prov.wasGeneratedBy, importActivity)
                model.add(sourceRecord, Prov.wasDerivedFrom, sourceExtract)
                model.add(importActivity, Prov.generated, sourceRecord)
            }
            return sourceRecord
        }

        private fun sourceSystem(id: String) = ResourceFactory.createResource("urn:dcai:source-system:${encode(id)}")

        private fun sourceExtract(id: String) = ResourceFactory.createResource("urn:dcai:source-extract:${encode(id)}")

        private fun sourceRecord(id: String) = ResourceFactory.createResource("urn:dcai:source-record:${encode(batch.sourceSystemId)}:${encode(id)}")

        private fun importActivity(id: String) = ResourceFactory.createResource("urn:dcai:import-activity:${encode(id)}")

        private fun promotionActivity(id: String) = ResourceFactory.createResource("urn:dcai:promotion-activity:${encode(id)}")

        private fun facility(id: String) = ResourceFactory.createResource("urn:dcai:facility:${encode(id)}")

        private fun hall(id: String) = ResourceFactory.createResource("urn:dcai:hall:${encode(id)}")

        private fun zone(id: String) = ResourceFactory.createResource("urn:dcai:zone:${encode(id)}")

        private fun infrastructureRow(id: String) = ResourceFactory.createResource("urn:dcai:row:${encode(id)}")

        private fun rack(id: String) = ResourceFactory.createResource("urn:dcai:rack:${encode(id)}")

        private fun capacityGroup(id: String) = ResourceFactory.createResource("urn:dcai:capacity-group:${encode(id)}")

        private fun asset(id: String) = ResourceFactory.createResource("urn:dcai:asset:${encode(id)}")

        private fun incident(id: String) = ResourceFactory.createResource("urn:dcai:incident:${encode(id)}")

        private fun stage(id: String) = ResourceFactory.createResource("urn:dcai:workflow-stage:${encode(id)}")

        private fun dependencyEdge(id: String) = ResourceFactory.createResource("urn:dcai:dependency-edge:${encode(id)}")

        private fun dependencyPath(id: String) = ResourceFactory.createResource("urn:dcai:dependency-path:${encode(id)}")

        private fun workflowEvent(id: String) = ResourceFactory.createResource("urn:dcai:workflow-event:${encode(id)}")

        private fun impact(id: String) = ResourceFactory.createResource("urn:dcai:impact:${encode(id)}")

        private fun evidence(id: String) = ResourceFactory.createResource("urn:dcai:evidence:${encode(id)}")

        private fun controlledState(type: Resource, category: String, value: String): Resource {
            val state = ResourceFactory.createResource("urn:dcai:state:$category:${encode(normalizedToken(value))}")
            canonicalModel.add(state, RDF.type, type)
            canonicalModel.add(state, Dcai.hasIdentifier, normalizedToken(value))
            canonicalModel.add(state, RDFS.label, value)
            return state
        }
    }

    private companion object {
        private fun AssetClass.rdfClass(): Resource {
            return when (this) {
                AssetClass.INFRASTRUCTURE -> Dcai.InfrastructureAsset
                AssetClass.POWER -> Dcai.PowerAsset
                AssetClass.COOLING -> Dcai.CoolingAsset
                AssetClass.CONTROL_TELEMETRY -> Dcai.ControlTelemetryAsset
            }
        }

        private fun DependencyPathClass.rdfClass(): Resource {
            return when (this) {
                DependencyPathClass.DEPENDENCY -> Dcai.DependencyPath
                DependencyPathClass.POWER -> Dcai.PowerPath
                DependencyPathClass.COOLING -> Dcai.CoolingPath
                DependencyPathClass.TELEMETRY -> Dcai.TelemetryPath
                DependencyPathClass.REDUNDANCY -> Dcai.RedundancyPath
            }
        }

        private fun EvidenceClass.rdfClass(): Resource {
            return when (this) {
                EvidenceClass.TELEMETRY -> Dcai.TelemetryEvidence
                EvidenceClass.VALIDATION -> Dcai.ValidationEvidence
                EvidenceClass.WORK_ORDER -> Dcai.WorkOrderEvidence
            }
        }

        private fun String.specificAssetClass(): Resource? {
            val normalized = normalizedToken(this)
            return when {
                "ups" in normalized -> Dcai.UpsAsset
                "pdu" in normalized -> Dcai.PowerDistributionUnit
                "generator" in normalized || "transfer" in normalized -> Dcai.GeneratorAsset
                "chw" in normalized || "chilled-water" in normalized -> Dcai.ChilledWaterLoop
                "cooling-loop" in normalized -> Dcai.CoolingLoop
                "crac" in normalized || "crah" in normalized -> Dcai.CracAsset
                "chiller" in normalized -> Dcai.ChillerAsset
                "dcim" in normalized || "telemetry-bridge" in normalized -> Dcai.TelemetryBridge
                "gpu" in normalized || "capacity" in normalized -> Dcai.GpuPod
                else -> null
            }
        }

        private fun literal(value: Instant) = ResourceFactory.createTypedLiteral(value.toString(), XSDDatatype.XSDdateTime)

        private fun literal(value: String, datatype: XSDDatatype) = ResourceFactory.createTypedLiteral(value, datatype)

        private fun encode(value: String): String {
            require(value.isNotBlank()) { "resource identifier must not be blank" }
            return URLEncoder.encode(value, StandardCharsets.UTF_8).replace("+", "%20")
        }

        private fun normalizedToken(value: String): String {
            return value.trim()
                .lowercase()
                .replace(Regex("[^a-z0-9]+"), "-")
                .trim('-')
                .ifBlank { "unspecified" }
        }
    }
}

data class SourceExtractRdfMapping(
    val sourceModel: Model,
    val canonicalModel: Model,
    val provenanceModel: Model,
) {
    fun combinedValidationModel(): Model {
        return ModelFactory.createDefaultModel()
            .add(sourceModel)
            .add(canonicalModel)
            .add(provenanceModel)
    }
}
