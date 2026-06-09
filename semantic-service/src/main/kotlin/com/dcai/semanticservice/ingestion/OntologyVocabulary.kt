package com.dcai.semanticservice.ingestion

import org.apache.jena.rdf.model.ResourceFactory

internal object Dcterms {
    const val NAMESPACE = "http://purl.org/dc/terms/"
    val title = ResourceFactory.createProperty("${NAMESPACE}title")
}

internal object Prov {
    const val NAMESPACE = "http://www.w3.org/ns/prov#"
    val generated = ResourceFactory.createProperty("${NAMESPACE}generated")
    val generatedAtTime = ResourceFactory.createProperty("${NAMESPACE}generatedAtTime")
    val used = ResourceFactory.createProperty("${NAMESPACE}used")
    val wasDerivedFrom = ResourceFactory.createProperty("${NAMESPACE}wasDerivedFrom")
    val wasGeneratedBy = ResourceFactory.createProperty("${NAMESPACE}wasGeneratedBy")
}

internal object Dcai {
    const val NAMESPACE = "urn:dcai:ontology:"

    val SourceSystem = resource("SourceSystem")
    val SourceExtract = resource("SourceExtract")
    val SourceRecord = resource("SourceRecord")
    val ImportActivity = resource("ImportActivity")
    val PromotionActivity = resource("PromotionActivity")
    val ReasoningActivity = resource("ReasoningActivity")

    val Facility = resource("Facility")
    val InfrastructureZone = resource("InfrastructureZone")
    val InfrastructureAsset = resource("InfrastructureAsset")
    val PowerAsset = resource("PowerAsset")
    val CoolingAsset = resource("CoolingAsset")
    val ControlTelemetryAsset = resource("ControlTelemetryAsset")

    val InfrastructureIncident = resource("InfrastructureIncident")
    val WorkflowStage = resource("WorkflowStage")
    val WorkflowEvent = resource("WorkflowEvent")

    val DependencyEdge = resource("DependencyEdge")
    val DependencyPath = resource("DependencyPath")
    val PowerPath = resource("PowerPath")
    val CoolingPath = resource("CoolingPath")
    val TelemetryPath = resource("TelemetryPath")
    val RedundancyPath = resource("RedundancyPath")

    val ImpactObservation = resource("ImpactObservation")
    val TelemetryEvidence = resource("TelemetryEvidence")
    val ValidationEvidence = resource("ValidationEvidence")
    val WorkOrderEvidence = resource("WorkOrderEvidence")
    val DependencyImpactFinding = resource("DependencyImpactFinding")
    val BlastRadiusFinding = resource("BlastRadiusFinding")

    val hasIdentifier = property("hasIdentifier")
    val hasSourceSystem = property("hasSourceSystem")
    val hasSourceRecordId = property("hasSourceRecordId")
    val hasSourcePayloadHash = property("hasSourcePayloadHash")

    val zoneInFacility = property("zoneInFacility")
    val locatedIn = property("locatedIn")
    val hasAssetType = property("hasAssetType")
    val hasCriticalityLevel = property("hasCriticalityLevel")
    val hasOperationalStatus = property("hasOperationalStatus")

    val affectsAsset = property("affectsAsset")
    val hasCurrentStage = property("hasCurrentStage")
    val enteredStage = property("enteredStage")
    val eventForIncident = property("eventForIncident")
    val hasEventId = property("hasEventId")
    val hasEventStatus = property("hasEventStatus")
    val enteredAt = property("enteredAt")
    val exitedAt = property("exitedAt")
    val hasDurationHours = property("hasDurationHours")
    val hasDelayHours = property("hasDelayHours")

    val hasDependentAsset = property("hasDependentAsset")
    val hasDependencyAsset = property("hasDependencyAsset")
    val hasDependencyRole = property("hasDependencyRole")
    val hasImpactScope = property("hasImpactScope")
    val hasPathStep = property("hasPathStep")

    val impactForIncident = property("impactForIncident")
    val estimatedCapacityRiskKw = property("estimatedCapacityRiskKw")
    val affectedGpuCount = property("affectedGpuCount")
    val affectedRackCount = property("affectedRackCount")
    val hasRedundancyState = property("hasRedundancyState")
    val hasMitigationState = property("hasMitigationState")
    val hasVendorState = property("hasVendorState")
    val vendorEtaAt = property("vendorEtaAt")

    val supportsFact = property("supportsFact")
    val hasConfidenceState = property("hasConfidenceState")
    val hasEvidenceTimestamp = property("hasEvidenceTimestamp")
    val hasMetricName = property("hasMetricName")
    val hasMetricValue = property("hasMetricValue")
    val hasMetricUnit = property("hasMetricUnit")
    val hasTelemetryStatus = property("hasTelemetryStatus")
    val hasValidationId = property("hasValidationId")
    val hasValidationStatus = property("hasValidationStatus")
    val hasWorkOrderId = property("hasWorkOrderId")
    val hasAssignedTeam = property("hasAssignedTeam")
    val hasFindingSummary = property("hasFindingSummary")

    private fun resource(localName: String) = ResourceFactory.createResource("$NAMESPACE$localName")

    private fun property(localName: String) = ResourceFactory.createProperty("$NAMESPACE$localName")
}
