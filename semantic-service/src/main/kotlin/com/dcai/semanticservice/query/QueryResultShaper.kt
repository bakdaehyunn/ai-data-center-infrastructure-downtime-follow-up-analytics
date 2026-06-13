package com.dcai.semanticservice.query

class QueryResultShaper(
    private val manifest: ApprovedQueryManifest,
) {
    fun shape(report: QueryExecutionReport): QueryResultEnvelope {
        val definition = manifest.requireQuery(report.queryId)
        require(report.mode == definition.mode) {
            "Query result mode mismatch for ${report.queryId}: report=${report.mode.value}, manifest=${definition.mode.value}"
        }
        require(report.mode == QueryMode.SELECT) {
            "Query result envelopes are only defined for SELECT results: ${report.queryId}"
        }
        return when (report.queryId) {
            "fixtureNamedGraphInventory" -> shapeNamedGraphInventory(report, definition)
            "fixtureIncidentSummary" -> shapeIncidentSummary(report, definition)
            "fixtureProvenanceSourceRecords" -> shapeProvenanceSourceRecords(report, definition)
            "semanticFollowUpQueueList" -> shapeFollowUpQueue(report, definition)
            "semanticDashboardOverview" -> shapeDashboardOverview(report, definition)
            "semanticFilterMetadata" -> shapeFilterMetadata(report, definition)
            "semanticFollowUpDetail" -> shapeFollowUpDetail(report, definition)
            "semanticImpactSummary" -> shapeImpactSummary(report, definition)
            "semanticTopologyDependencies" -> shapeTopologyDependencies(report, definition)
            "semanticTrustFindingList" -> shapeTrustFindings(report, definition)
            "semanticStageBottlenecks" -> shapeStageBottlenecks(report, definition)
            "semanticAssetDelaySummary" -> shapeAssetDelaySummary(report, definition)
            "semanticZoneDelaySummary" -> shapeZoneDelaySummary(report, definition)
            "semanticSpareWaitSummary" -> shapeSpareWaitSummary(report, definition)
            "semanticValidationSummary" -> shapeValidationSummary(report, definition)
            "semanticIncidentEvidence" -> shapeIncidentEvidence(report, definition)
            "semanticIncidentTimeline" -> shapeIncidentTimeline(report, definition)
            "semanticDependencyImpactByAsset" -> shapeDependencyImpact(report, definition)
            "semanticBlastRadiusByAsset" -> shapeBlastRadius(report, definition)
            else -> error("No result envelope contract for query id: ${report.queryId}")
        }
    }

    private fun shapeNamedGraphInventory(
        report: QueryExecutionReport,
        definition: ApprovedQueryDefinition,
    ): NamedGraphInventoryEnvelope {
        return NamedGraphInventoryEnvelope(
            queryId = report.queryId,
            records = report.rows.map { row ->
                NamedGraphInventoryRecord(
                    graphUri = row.required("graph"),
                    subjectCount = row.required("subjectCount").toInt(),
                )
            },
            provenance = provenance(definition),
        )
    }

    private fun shapeIncidentSummary(
        report: QueryExecutionReport,
        definition: ApprovedQueryDefinition,
    ): IncidentSummaryEnvelope {
        return IncidentSummaryEnvelope(
            queryId = report.queryId,
            records = report.rows.map { row ->
                IncidentSummaryRecord(
                    graphUri = row.required("graph"),
                    incidentUri = row.required("incident"),
                    incidentId = row.required("incidentId"),
                    assetUri = row.required("asset"),
                    stageUri = row.required("stage"),
                    sourceRecordUri = row.optional("sourceRecord"),
                )
            },
            provenance = provenance(definition),
        )
    }

    private fun shapeProvenanceSourceRecords(
        report: QueryExecutionReport,
        definition: ApprovedQueryDefinition,
    ): ProvenanceSourceRecordsEnvelope {
        return ProvenanceSourceRecordsEnvelope(
            queryId = report.queryId,
            records = report.rows.map { row ->
                ProvenanceSourceRecord(
                    graphUri = row.required("graph"),
                    sourceRecordUri = row.required("sourceRecord"),
                    sourceRecordId = row.required("sourceRecordId"),
                    sourceSystemUri = row.required("sourceSystem"),
                    payloadHash = row.required("payloadHash"),
                    activityUri = row.required("activity"),
                )
            },
            provenance = provenance(definition),
        )
    }

    private fun shapeFollowUpQueue(
        report: QueryExecutionReport,
        definition: ApprovedQueryDefinition,
    ): FollowUpQueueEnvelope {
        return FollowUpQueueEnvelope(
            queryId = report.queryId,
            records = report.rows.map { row ->
                FollowUpQueueRecord(
                    graphUri = row.required("graph"),
                    incidentUri = row.required("incident"),
                    incidentId = row.required("incidentId"),
                    assetUri = row.required("asset"),
                    assetId = row.required("assetId"),
                    zoneUri = row.required("zone"),
                    zoneId = row.required("zoneId"),
                    stageUri = row.required("stage"),
                    stageLabel = row.optional("stageLabel"),
                    sourceRecordUri = row.required("sourceRecord"),
                    priorityRank = row.optionalInt("priorityRank"),
                    requestTitle = row.optional("requestTitle"),
                    currentStatus = row.optional("currentStatus"),
                    hoursInCurrentStage = row.optionalDouble("hoursInCurrentStage"),
                    neededByAt = row.optional("neededByAt"),
                    priorityLevel = row.optional("priorityLevel"),
                    businessImpact = row.optional("businessImpact"),
                    assetCriticalityScore = row.optionalDouble("assetCriticalityScore"),
                    downtimeScore = row.optionalDouble("downtimeScore"),
                    stageDelayScore = row.optionalDouble("stageDelayScore"),
                    infrastructureZoneImpactScore = row.optionalDouble("infrastructureZoneImpactScore"),
                    neededByUrgencyScore = row.optionalDouble("neededByUrgencyScore"),
                    repeatFailureScore = row.optionalDouble("repeatFailureScore"),
                    spareRiskScore = row.optionalDouble("spareRiskScore"),
                    capacityRiskScore = row.optionalDouble("capacityRiskScore"),
                    redundancyRiskScore = row.optionalDouble("redundancyRiskScore"),
                    thermalRiskScore = row.optionalDouble("thermalRiskScore"),
                    vendorEtaRiskScore = row.optionalDouble("vendorEtaRiskScore"),
                    mitigationCreditScore = row.optionalDouble("mitigationCreditScore"),
                    totalPriorityScore = row.optionalDouble("totalPriorityScore"),
                )
            },
            provenance = provenance(definition),
        )
    }

    private fun shapeDashboardOverview(
        report: QueryExecutionReport,
        definition: ApprovedQueryDefinition,
    ): DashboardOverviewEnvelope {
        return DashboardOverviewEnvelope(
            queryId = report.queryId,
            records = report.rows.map { row ->
                DashboardOverviewRecord(
                    graphUri = row.required("graph"),
                    totalIncidents = row.requiredInt("totalIncidents"),
                    assetCount = row.requiredInt("assetCount"),
                    zoneCount = row.requiredInt("zoneCount"),
                    impactObservationCount = row.requiredInt("impactObservationCount"),
                    capacityRiskKw = row.requiredDouble("capacityRiskKw"),
                    affectedGpuCount = row.requiredInt("affectedGpuCount"),
                    dependencyEdgeCount = row.requiredInt("dependencyEdgeCount"),
                    trustFindingCount = row.requiredInt("trustFindingCount"),
                    avgDurationHours = row.optionalDouble("avgDurationHours"),
                    totalDurationHours = row.optionalDouble("totalDurationHours"),
                    totalDelayHours = row.optionalDouble("totalDelayHours"),
                    mitigatedIncidentCount = row.optionalInt("mitigatedIncidentCount"),
                    affectedRackCount = row.optionalInt("affectedRackCount"),
                    thermalBreachMinutes = row.optionalInt("thermalBreachMinutes"),
                    redundancyLostIncidentCount = row.optionalInt("redundancyLostIncidentCount"),
                    vendorEtaMissedCount = row.optionalInt("vendorEtaMissedCount"),
                    repeatFailureAssetCount = row.optionalInt("repeatFailureAssetCount"),
                    engineerAssignmentDelayHours = row.optionalDouble("engineerAssignmentDelayHours"),
                )
            },
            provenance = provenance(definition),
        )
    }

    private fun shapeFilterMetadata(
        report: QueryExecutionReport,
        definition: ApprovedQueryDefinition,
    ): FilterMetadataEnvelope {
        return FilterMetadataEnvelope(
            queryId = report.queryId,
            records = report.rows.map { row ->
                FilterMetadataRecord(
                    graphUri = row.required("graph"),
                    filterType = row.required("filterType"),
                    resourceUri = row.required("resource"),
                    id = row.required("id"),
                    label = row.optional("label"),
                    sourceRecordUri = row.optional("sourceRecord"),
                )
            },
            provenance = provenance(definition),
        )
    }

    private fun shapeFollowUpDetail(
        report: QueryExecutionReport,
        definition: ApprovedQueryDefinition,
    ): FollowUpDetailEnvelope {
        return FollowUpDetailEnvelope(
            queryId = report.queryId,
            records = report.rows.map { row ->
                FollowUpDetailRecord(
                    graphUri = row.required("graph"),
                    incidentUri = row.required("incident"),
                    incidentId = row.required("incidentId"),
                    assetUri = row.required("asset"),
                    assetId = row.required("assetId"),
                    zoneUri = row.required("zone"),
                    zoneId = row.required("zoneId"),
                    stageUri = row.required("stage"),
                    stageLabel = row.optional("stageLabel"),
                    sourceRecordUri = row.required("sourceRecord"),
                    impactUri = row.optional("impact"),
                    capacityRiskKw = row.optionalDouble("capacityRiskKw"),
                    affectedGpuCount = row.optionalInt("affectedGpuCount"),
                    followUpDecisionUri = row.optional("followUpDecision"),
                    recommendedAction = row.optional("recommendedAction"),
                    recoveryBlockerUri = row.optional("recoveryBlocker"),
                    blockerSummary = row.optional("blockerSummary"),
                    restoreReadinessUri = row.optional("restoreReadiness"),
                    restoreReadinessSummary = row.optional("restoreReadinessSummary"),
                    trustFindingUri = row.optional("trustFinding"),
                    trustSummary = row.optional("trustSummary"),
                    priorityRank = row.optionalInt("priorityRank"),
                    requestTitle = row.optional("requestTitle"),
                    currentStatus = row.optional("currentStatus"),
                    hoursInCurrentStage = row.optionalDouble("hoursInCurrentStage"),
                    neededByAt = row.optional("neededByAt"),
                    priorityLevel = row.optional("priorityLevel"),
                    businessImpact = row.optional("businessImpact"),
                    assetCriticalityScore = row.optionalDouble("assetCriticalityScore"),
                    downtimeScore = row.optionalDouble("downtimeScore"),
                    stageDelayScore = row.optionalDouble("stageDelayScore"),
                    infrastructureZoneImpactScore = row.optionalDouble("infrastructureZoneImpactScore"),
                    neededByUrgencyScore = row.optionalDouble("neededByUrgencyScore"),
                    repeatFailureScore = row.optionalDouble("repeatFailureScore"),
                    repeatFailureAssetCount = row.optionalInt("repeatFailureAssetCount"),
                    engineerAssignmentDelayHours = row.optionalDouble("engineerAssignmentDelayHours"),
                    spareRiskScore = row.optionalDouble("spareRiskScore"),
                    capacityRiskScore = row.optionalDouble("capacityRiskScore"),
                    redundancyRiskScore = row.optionalDouble("redundancyRiskScore"),
                    thermalRiskScore = row.optionalDouble("thermalRiskScore"),
                    vendorEtaRiskScore = row.optionalDouble("vendorEtaRiskScore"),
                    mitigationCreditScore = row.optionalDouble("mitigationCreditScore"),
                    totalPriorityScore = row.optionalDouble("totalPriorityScore"),
                    redundancyState = row.optional("redundancyState"),
                    affectedRackCount = row.optionalInt("affectedRackCount"),
                    estimatedGpuCapacityRiskPct = row.optionalDouble("estimatedGpuCapacityRiskPct"),
                    thermalBreachMinutes = row.optionalInt("thermalBreachMinutes"),
                    powerRedundancyLost = row.optionalBoolean("powerRedundancyLost"),
                    coolingRedundancyLost = row.optionalBoolean("coolingRedundancyLost"),
                    mitigationStatus = row.optional("mitigationStatus"),
                    vendorEtaAt = row.optional("vendorEtaAt"),
                    vendorStatus = row.optional("vendorStatus"),
                )
            },
            provenance = provenance(definition),
        )
    }

    private fun shapeImpactSummary(
        report: QueryExecutionReport,
        definition: ApprovedQueryDefinition,
    ): ImpactSummaryEnvelope {
        return ImpactSummaryEnvelope(
            queryId = report.queryId,
            records = report.rows.map { row ->
                ImpactSummaryRecord(
                    graphUri = row.required("graph"),
                    impactObservationCount = row.requiredInt("impactObservationCount"),
                    incidentCount = row.requiredInt("incidentCount"),
                    capacityRiskKw = row.requiredDouble("capacityRiskKw"),
                    affectedGpuCount = row.requiredInt("affectedGpuCount"),
                    trustFindingCount = row.requiredInt("trustFindingCount"),
                    affectedRackCount = row.optionalInt("affectedRackCount"),
                    thermalBreachMinutes = row.optionalInt("thermalBreachMinutes"),
                    redundancyLostIncidentCount = row.optionalInt("redundancyLostIncidentCount"),
                    vendorEtaMissedCount = row.optionalInt("vendorEtaMissedCount"),
                    mitigatedIncidentCount = row.optionalInt("mitigatedIncidentCount"),
                )
            },
            provenance = provenance(definition),
        )
    }

    private fun shapeTopologyDependencies(
        report: QueryExecutionReport,
        definition: ApprovedQueryDefinition,
    ): TopologyDependenciesEnvelope {
        return TopologyDependenciesEnvelope(
            queryId = report.queryId,
            records = report.rows.map { row ->
                TopologyDependencyRecord(
                    graphUri = row.required("graph"),
                    dependencyEdgeUri = row.required("dependencyEdge"),
                    dependencyId = row.required("dependencyId"),
                    dependentAssetUri = row.required("dependentAsset"),
                    dependentAssetId = row.required("dependentAssetId"),
                    dependencyAssetUri = row.required("dependencyAsset"),
                    dependencyAssetId = row.required("dependencyAssetId"),
                    dependencyRole = row.required("dependencyRole"),
                    impactScope = row.optional("impactScope"),
                    dependencyPathUri = row.optional("dependencyPath"),
                    pathId = row.optional("pathId"),
                    sourceRecordUri = row.required("sourceRecord"),
                )
            },
            provenance = provenance(definition),
        )
    }

    private fun shapeTrustFindings(
        report: QueryExecutionReport,
        definition: ApprovedQueryDefinition,
    ): TrustFindingsEnvelope {
        return TrustFindingsEnvelope(
            queryId = report.queryId,
            records = report.rows.map { row ->
                TrustFindingRecord(
                    graphUri = row.required("graph"),
                    trustFindingUri = row.required("trustFinding"),
                    trustFindingId = row.optional("trustFindingId"),
                    summary = row.required("summary"),
                    sourceFactUri = row.required("sourceFact"),
                    activityUri = row.optional("activity"),
                    severity = row.optional("severity"),
                    status = row.optional("status"),
                    createdAt = row.optional("createdAt"),
                )
            },
            provenance = provenance(definition),
        )
    }

    private fun shapeStageBottlenecks(
        report: QueryExecutionReport,
        definition: ApprovedQueryDefinition,
    ): StageBottlenecksEnvelope {
        return StageBottlenecksEnvelope(
            queryId = report.queryId,
            records = report.rows.map { row ->
                StageBottleneckRecord(
                    graphUri = row.required("graph"),
                    stageUri = row.required("stage"),
                    stageLabel = row.optional("stageLabel"),
                    incidentCount = row.requiredInt("incidentCount"),
                    delayedCount = row.optionalInt("delayedCount"),
                    avgDurationHours = row.optionalDouble("avgDurationHours"),
                    p90DurationHours = row.optionalDouble("p90DurationHours"),
                    totalDelayHours = row.optionalDouble("totalDelayHours"),
                    sourceRecordUri = row.required("sourceRecord"),
                )
            },
            provenance = provenance(definition),
        )
    }

    private fun shapeAssetDelaySummary(
        report: QueryExecutionReport,
        definition: ApprovedQueryDefinition,
    ): AssetDelaySummaryEnvelope {
        return AssetDelaySummaryEnvelope(
            queryId = report.queryId,
            records = report.rows.map { row ->
                AssetDelaySummaryRecord(
                    graphUri = row.required("graph"),
                    assetUri = row.required("asset"),
                    assetId = row.required("assetId"),
                    zoneUri = row.required("zone"),
                    zoneId = row.required("zoneId"),
                    incidentCount = row.requiredInt("incidentCount"),
                    impactObservationCount = row.requiredInt("impactObservationCount"),
                    capacityRiskKw = row.requiredDouble("capacityRiskKw"),
                    affectedGpuCount = row.requiredInt("affectedGpuCount"),
                    delayedIncidentCount = row.optionalInt("delayedIncidentCount"),
                    repeatFailureCount = row.optionalInt("repeatFailureCount"),
                    totalDurationHours = row.optionalDouble("totalDurationHours"),
                    avgDurationHours = row.optionalDouble("avgDurationHours"),
                    topFailureMode = row.optional("topFailureMode"),
                    sourceRecordUri = row.required("sourceRecord"),
                )
            },
            provenance = provenance(definition),
        )
    }

    private fun shapeZoneDelaySummary(
        report: QueryExecutionReport,
        definition: ApprovedQueryDefinition,
    ): ZoneDelaySummaryEnvelope {
        return ZoneDelaySummaryEnvelope(
            queryId = report.queryId,
            records = report.rows.map { row ->
                ZoneDelaySummaryRecord(
                    graphUri = row.required("graph"),
                    zoneUri = row.required("zone"),
                    zoneId = row.required("zoneId"),
                    assetCount = row.requiredInt("assetCount"),
                    incidentCount = row.requiredInt("incidentCount"),
                    impactObservationCount = row.requiredInt("impactObservationCount"),
                    capacityRiskKw = row.requiredDouble("capacityRiskKw"),
                    affectedGpuCount = row.requiredInt("affectedGpuCount"),
                    delayedIncidentCount = row.optionalInt("delayedIncidentCount"),
                    criticalIncidentCount = row.optionalInt("criticalIncidentCount"),
                    totalDurationHours = row.optionalDouble("totalDurationHours"),
                    topBottleneckStage = row.optional("topBottleneckStage"),
                    sourceRecordUri = row.required("sourceRecord"),
                )
            },
            provenance = provenance(definition),
        )
    }

    private fun shapeSpareWaitSummary(
        report: QueryExecutionReport,
        definition: ApprovedQueryDefinition,
    ): SpareWaitSummaryEnvelope {
        return SpareWaitSummaryEnvelope(
            queryId = report.queryId,
            records = report.rows.map { row ->
                SpareWaitSummaryRecord(
                    graphUri = row.required("graph"),
                    stageUri = row.required("stage"),
                    stageLabel = row.optional("stageLabel"),
                    incidentCount = row.requiredInt("incidentCount"),
                    recoveryBlockerCount = row.requiredInt("recoveryBlockerCount"),
                    totalWaitHours = row.optionalDouble("totalWaitHours"),
                    avgWaitHours = row.optionalDouble("avgWaitHours"),
                    stockStatus = row.optional("stockStatus"),
                    sourceRecordUri = row.required("sourceRecord"),
                )
            },
            provenance = provenance(definition),
        )
    }

    private fun shapeValidationSummary(
        report: QueryExecutionReport,
        definition: ApprovedQueryDefinition,
    ): ValidationSummaryEnvelope {
        return ValidationSummaryEnvelope(
            queryId = report.queryId,
            records = report.rows.map { row ->
                ValidationSummaryRecord(
                    graphUri = row.required("graph"),
                    sourceRecordCount = row.requiredInt("sourceRecordCount"),
                    incidentCount = row.requiredInt("incidentCount"),
                    incidentWithProvenanceCount = row.requiredInt("incidentWithProvenanceCount"),
                    assetCount = row.requiredInt("assetCount"),
                    assetWithProvenanceCount = row.requiredInt("assetWithProvenanceCount"),
                )
            },
            provenance = provenance(definition),
        )
    }

    private fun shapeIncidentEvidence(
        report: QueryExecutionReport,
        definition: ApprovedQueryDefinition,
    ): IncidentEvidenceEnvelope {
        return IncidentEvidenceEnvelope(
            queryId = report.queryId,
            records = report.rows.map { row ->
                IncidentEvidenceRecord(
                    graphUri = row.required("graph"),
                    incidentUri = row.required("incident"),
                    incidentId = row.required("incidentId"),
                    stageUri = row.required("stage"),
                    stageLabel = row.optional("stageLabel"),
                    sourceRecordUri = row.required("sourceRecord"),
                    impactUri = row.optional("impact"),
                    evidenceUri = row.optional("evidence"),
                    evidenceClassUri = row.optional("evidenceClass"),
                    evidenceTimestamp = row.optional("evidenceTimestamp"),
                    confidenceState = row.optional("confidenceState"),
                    metricName = row.optional("metricName"),
                    metricValue = row.optionalDouble("metricValue"),
                    metricUnit = row.optional("metricUnit"),
                    telemetryStatus = row.optional("telemetryStatus"),
                    telemetryAlertId = row.optional("telemetryAlertId"),
                    alertType = row.optional("alertType"),
                    alertSeverity = row.optional("alertSeverity"),
                    alertTriggeredAt = row.optional("alertTriggeredAt"),
                    alertResolvedAt = row.optional("alertResolvedAt"),
                    validationId = row.optional("validationId"),
                    validationStatus = row.optional("validationStatus"),
                    validatorId = row.optional("validatorId"),
                    validationStartedAt = row.optional("validationStartedAt"),
                    validationCompletedAt = row.optional("validationCompletedAt"),
                    failureReason = row.optional("failureReason"),
                    workOrderId = row.optional("workOrderId"),
                    assignedTeam = row.optional("assignedTeam"),
                    assignedEngineerId = row.optional("assignedEngineerId"),
                    workOrderStatus = row.optional("workOrderStatus"),
                    plannedStartAt = row.optional("plannedStartAt"),
                    actualStartAt = row.optional("actualStartAt"),
                    actualCompletedAt = row.optional("actualCompletedAt"),
                    requiredSpareId = row.optional("requiredSpareId"),
                    requiredSpareName = row.optional("requiredSpareName"),
                    stockStatus = row.optional("stockStatus"),
                    trustFindingUri = row.optional("trustFinding"),
                    trustSummary = row.optional("trustSummary"),
                )
            },
            provenance = provenance(definition),
        )
    }

    private fun shapeIncidentTimeline(
        report: QueryExecutionReport,
        definition: ApprovedQueryDefinition,
    ): IncidentTimelineEnvelope {
        return IncidentTimelineEnvelope(
            queryId = report.queryId,
            records = report.rows.map { row ->
                IncidentTimelineRecord(
                    graphUri = row.required("graph"),
                    incidentUri = row.required("incident"),
                    incidentId = row.required("incidentId"),
                    eventUri = row.required("event"),
                    eventId = row.optional("eventId"),
                    stageUri = row.required("stage"),
                    stageLabel = row.optional("stageLabel"),
                    eventStatus = row.optional("eventStatus"),
                    enteredAt = row.optional("enteredAt"),
                    exitedAt = row.optional("exitedAt"),
                    durationHours = row.optionalDouble("durationHours"),
                    thresholdHours = row.optionalDouble("thresholdHours"),
                    delayHours = row.optionalDouble("delayHours"),
                    sourceRecordUri = row.required("sourceRecord"),
                )
            },
            provenance = provenance(definition),
        )
    }

    private fun shapeDependencyImpact(
        report: QueryExecutionReport,
        definition: ApprovedQueryDefinition,
    ): DependencyImpactEnvelope {
        return DependencyImpactEnvelope(
            queryId = report.queryId,
            records = report.rows.map { row ->
                DependencyImpactRecord(
                    graphUri = row.required("graph"),
                    assetUri = row.required("asset"),
                    assetId = row.required("assetId"),
                    dependencyEdgeUri = row.optional("dependencyEdge"),
                    dependencyId = row.optional("dependencyId"),
                    dependencyAssetUri = row.optional("dependencyAsset"),
                    dependencyAssetId = row.optional("dependencyAssetId"),
                    dependencyRole = row.optional("dependencyRole"),
                    impactScope = row.optional("impactScope"),
                    findingUri = row.optional("finding"),
                    findingSummary = row.optional("findingSummary"),
                    sourceRecordUri = row.optional("sourceRecord"),
                )
            },
            provenance = provenance(definition),
        )
    }

    private fun shapeBlastRadius(
        report: QueryExecutionReport,
        definition: ApprovedQueryDefinition,
    ): BlastRadiusEnvelope {
        return BlastRadiusEnvelope(
            queryId = report.queryId,
            records = report.rows.map { row ->
                BlastRadiusRecord(
                    graphUri = row.required("graph"),
                    assetUri = row.required("asset"),
                    assetId = row.required("assetId"),
                    downstreamAssetUri = row.optional("downstreamAsset"),
                    downstreamAssetId = row.optional("downstreamAssetId"),
                    incidentUri = row.optional("incident"),
                    incidentId = row.optional("incidentId"),
                    findingUri = row.optional("finding"),
                    findingSummary = row.optional("findingSummary"),
                )
            },
            provenance = provenance(definition),
        )
    }

    private fun provenance(definition: ApprovedQueryDefinition): QueryResultEnvelopeProvenance {
        return QueryResultEnvelopeProvenance(
            queryId = definition.id,
            graphScope = definition.graphScope,
        )
    }

    private fun Map<String, String>.required(key: String): String {
        val value = this[key]
        require(!value.isNullOrBlank()) { "Missing required binding '$key'" }
        return value
    }

    private fun Map<String, String>.optional(key: String): String? {
        return this[key]?.takeIf { it.isNotBlank() }
    }

    private fun Map<String, String>.requiredInt(key: String): Int {
        return required(key).toDouble().toInt()
    }

    private fun Map<String, String>.optionalInt(key: String): Int? {
        return optional(key)?.toDouble()?.toInt()
    }

    private fun Map<String, String>.requiredDouble(key: String): Double {
        return required(key).toDouble()
    }

    private fun Map<String, String>.optionalDouble(key: String): Double? {
        return optional(key)?.toDouble()
    }

    private fun Map<String, String>.optionalBoolean(key: String): Boolean? {
        return optional(key)?.toBooleanStrictOrNull()
    }
}
