const SEMANTIC_API_BASE_URL = import.meta.env.VITE_SEMANTIC_API_BASE_URL ?? 'http://127.0.0.1:18080'

export type Overview = {
  total_requests: number
  open_requests: number
  delayed_requests: number
  critical_asset_delayed: number
  avg_downtime_hours: number
  top_bottleneck_stage: string | null
  spare_waiting_delay_hours: number
  repeat_failure_asset_count: number
  engineer_assignment_delay_hours: number
  capacity_risk_kw: number
  affected_gpu_count: number
  redundancy_lost_incidents: number
  vendor_eta_missed_count: number
  latest_pipeline_run_status: string | null
  data_quality_status: string
}

export type FollowUpItem = {
  priority_rank: number
  incident_id: string
  request_number: string
  request_title: string
  asset_id: string
  asset_name: string
  zone_id: string
  zone_name: string
  current_stage: string
  current_status: string
  hours_in_current_stage: number
  needed_by_at: string
  priority_level: string
  business_impact: string
  asset_criticality_score: number
  downtime_score: number
  stage_delay_score: number
  infrastructure_zone_impact_score: number
  needed_by_urgency_score: number
  repeat_failure_score: number
  spare_risk_score: number
  capacity_risk_score: number
  redundancy_risk_score: number
  thermal_risk_score: number
  vendor_eta_risk_score: number
  mitigation_credit_score: number
  total_priority_score: number
  recommended_action: string
  reason_summary: string
  redundancy_state: string | null
  affected_gpu_count: number
  estimated_capacity_risk_kw: number
  mitigation_status: string | null
  vendor_status: string | null
  impact_confidence_status: string
  impact_trust_issue_count: number
  restore_readiness_status: string
  restore_readiness_summary: string | null
}

export type StageBottleneck = {
  stage: string
  request_count: number
  delayed_count: number
  delay_rate: number
  avg_duration_hours: number
  p90_duration_hours: number
  total_delay_hours: number
}

export type InfrastructureAssetDelay = {
  asset_id: string
  asset_name: string
  zone_id: string
  zone_name: string
  request_count: number
  delayed_request_count: number
  repeat_failure_count: number
  total_downtime_hours: number
  avg_repair_duration_hours: number
  top_failure_mode: string
}

export type InfrastructureZoneDelay = {
  zone_id: string
  zone_name: string
  open_request_count: number
  delayed_request_count: number
  critical_asset_delayed_count: number
  total_downtime_hours: number
  top_bottleneck_stage: string
}

export type SpareWaiting = {
  spare_id: string
  spare_name: string
  spare_category: string
  waiting_request_count: number
  total_wait_hours: number
  avg_wait_hours: number
  critical_spare: boolean
  stock_status: string
}

export type DataQualityCheck = {
  check_result_id: string
  pipeline_run_id: string
  check_name: string
  target_table: string
  severity: string
  status: string
  failed_row_count: number
  sample_failed_keys: string[]
  message: string
  created_at: string
}

export type ImpactSummary = {
  incident_count: number
  capacity_risk_kw: number
  affected_rack_count: number
  affected_gpu_count: number
  redundancy_lost_incidents: number
  vendor_eta_missed_count: number
  mitigated_incidents: number
  thermal_breach_minutes: number
  trusted_impact_count: number
  warning_impact_count: number
  unverified_impact_count: number
}

export type InfrastructureDependency = {
  dependency_id: string
  dependent_asset_id: string
  dependent_asset_name: string
  dependent_asset_type: string
  dependent_status: string
  dependency_asset_id: string
  dependency_asset_name: string
  dependency_asset_type: string
  dependency_status: string
  dependency_type: string
  dependency_role: string
  impact_scope: string
  dependent_active_incident_count: number
  dependency_active_incident_count: number
}

export type SemanticDependencyEdge = {
  dependency_id: string
  dependent_asset_id: string
  dependency_asset_id: string
  dependency_type: string
  dependency_role: string
}

export type SemanticDependencyImpact = {
  asset_id: string
  direct_dependency_count: number
  direct_dependencies: SemanticDependencyEdge[]
  inferred_downstream_assets: string[]
}

export type SemanticIncidentEvidence = {
  incident_id: string
  found: boolean
  request_title: string | null
  asset_id: string | null
  workflow_stage: string | null
  current_status: string | null
  priority_level: string | null
  trust_issue_ids: string[]
}

export type SemanticBlastRadius = {
  asset_id: string
  inferred_downstream_assets: string[]
  affected_incident_count: number
  affected_incidents: {
    incident_id: string
    asset_id: string
    title: string
    stage: string
  }[]
}

export type SemanticValidation = {
  conforms: boolean
  issue_count: number
  issues: {
    focus_node: string
    result_path: string
    message: string
    severity: string
  }[]
}

export type RequestSemanticContext = {
  validation: SemanticValidation
  incidentEvidence: SemanticIncidentEvidence
  dependencyImpact: SemanticDependencyImpact
  blastRadius: SemanticBlastRadius
}

export type StageLeadTime = {
  stage: string
  entered_at: string
  exited_at: string | null
  duration_hours: number
  threshold_hours: number
  is_bottleneck: boolean
  delay_hours: number
}

export type TimelineEvent = {
  event_id: string
  stage: string
  event_type: string
  event_status: string
  occurred_at: string
  actor_type: string
  reason_code: string | null
  message: string | null
}

export type WorkOrder = {
  work_order_id: string
  assigned_team: string
  assigned_engineer_id: string | null
  work_order_status: string
  planned_start_at: string | null
  actual_start_at: string | null
  actual_completed_at: string | null
  required_spare_id: string | null
  required_spare_name: string | null
  stock_status: string | null
}

export type RequestDetail = {
  request: FollowUpItem
  stage_lead_times: StageLeadTime[]
  timeline: TimelineEvent[]
  work_orders: WorkOrder[]
  validation_results: {
    validation_id: string
    validation_status: string
    validator_id: string | null
    validation_started_at: string | null
    validation_completed_at: string | null
    failure_reason: string | null
  }[]
  telemetry_alerts: {
    telemetry_alert_id: string
    asset_id: string
    alert_type: string
    severity: string
    triggered_at: string
    resolved_at: string | null
  }[]
  impact_snapshot: {
    impact_snapshot_id: string
    incident_id: string
    asset_id: string
    zone_id: string
    snapshot_at: string
    redundancy_state: string
    affected_rack_count: number
    affected_gpu_count: number
    estimated_capacity_risk_kw: number
    estimated_gpu_capacity_risk_pct: number
    thermal_breach_minutes: number
    power_redundancy_lost: boolean
    cooling_redundancy_lost: boolean
    mitigation_status: string
    vendor_eta_at: string | null
    vendor_status: string
    source_system: string
    telemetry_readings: {
      metric: string
      value: number
      unit: string
      status: string
    }[]
  } | null
  quality_flags: string[]
  restore_readiness: {
    status: string
    summary: string | null
    finding_uri: string | null
  }
  impact_confidence_status: string
  impact_trust_flags: {
    issue_type: string
    severity: string
    message: string
    evidence: Record<string, unknown>
  }[]
}

export type FilterOption = {
  id: string
  name: string
}

export type FilterMetadata = {
  infrastructure_zones: FilterOption[]
  assets: FilterOption[]
  asset_types: string[]
  facilities_teams: string[]
  spare_categories: string[]
  priority_levels: string[]
  request_types: string[]
  failure_modes: string[]
  stages: string[]
}

export type DashboardFilters = {
  zone_id?: string
  asset_id?: string
  priority_level?: string
  stage?: string
  delayed_only?: boolean
  critical_asset_delayed?: boolean
  capacity_risk?: boolean
  affected_gpu?: boolean
  evidence_review?: boolean
  redundancy_lost?: boolean
  vendor_eta_missed?: boolean
}

export type DashboardData = {
  overview: Overview
  followUps: FollowUpItem[]
  stageBottlenecks: StageBottleneck[]
  assetDelays: InfrastructureAssetDelay[]
  zoneDelays: InfrastructureZoneDelay[]
  spareWaiting: SpareWaiting[]
  qualityChecks: DataQualityCheck[]
  impactSummary: ImpactSummary
  topologyDependencies: InfrastructureDependency[]
}

type SemanticEnvelope<T> = {
  queryId: string
  resultType: string
  recordCount: number
  records: T[]
  provenance: {
    queryId: string
    graphScope: string
    contractVersion: string
  }
}

type SemanticDashboardOverviewRecord = {
  totalIncidents: number
  assetCount: number
  zoneCount: number
  impactObservationCount: number
  capacityRiskKw: number
  affectedGpuCount: number
  dependencyEdgeCount: number
  trustFindingCount: number
  avgDurationHours?: number
  totalDurationHours?: number
  totalDelayHours?: number
  mitigatedIncidentCount?: number
  affectedRackCount?: number
  thermalBreachMinutes?: number
  redundancyLostIncidentCount?: number
  vendorEtaMissedCount?: number
  repeatFailureAssetCount?: number
  engineerAssignmentDelayHours?: number
}

type SemanticFollowUpQueueRecord = {
  graphUri: string
  incidentUri: string
  incidentId: string
  assetUri: string
  assetId: string
  zoneUri: string
  zoneId: string
  stageUri: string
  stageLabel?: string
  sourceRecordUri: string
  priorityRank?: number
  requestTitle?: string
  currentStatus?: string
  hoursInCurrentStage?: number
  neededByAt?: string
  priorityLevel?: string
  businessImpact?: string
  assetCriticalityScore?: number
  downtimeScore?: number
  stageDelayScore?: number
  infrastructureZoneImpactScore?: number
  neededByUrgencyScore?: number
  repeatFailureScore?: number
  repeatFailureAssetCount?: number
  engineerAssignmentDelayHours?: number
  spareRiskScore?: number
  capacityRiskScore?: number
  redundancyRiskScore?: number
  thermalRiskScore?: number
  vendorEtaRiskScore?: number
  mitigationCreditScore?: number
  totalPriorityScore?: number
}

type SemanticFollowUpDetailRecord = SemanticFollowUpQueueRecord & {
  impactUri?: string
  capacityRiskKw?: number
  affectedGpuCount?: number
  followUpDecisionUri?: string
  recommendedAction?: string
  recoveryBlockerUri?: string
  blockerSummary?: string
  restoreReadinessUri?: string
  restoreReadinessSummary?: string
  trustFindingUri?: string
  trustSummary?: string
  redundancyState?: string
  affectedRackCount?: number
  estimatedGpuCapacityRiskPct?: number
  thermalBreachMinutes?: number
  powerRedundancyLost?: boolean
  coolingRedundancyLost?: boolean
  mitigationStatus?: string
  vendorEtaAt?: string
  vendorStatus?: string
}

type SemanticFilterMetadataRecord = {
  filterType: string
  id: string
  label?: string
}

type SemanticImpactSummaryRecord = {
  impactObservationCount: number
  incidentCount: number
  capacityRiskKw: number
  affectedGpuCount: number
  trustFindingCount: number
  affectedRackCount?: number
  thermalBreachMinutes?: number
  redundancyLostIncidentCount?: number
  vendorEtaMissedCount?: number
  mitigatedIncidentCount?: number
}

type SemanticStageBottleneckRecord = {
  stageUri: string
  stageLabel?: string
  incidentCount: number
  delayedCount?: number
  avgDurationHours?: number
  p90DurationHours?: number
  totalDelayHours?: number
  sourceRecordUri: string
}

type SemanticAssetDelaySummaryRecord = {
  assetId: string
  zoneId: string
  incidentCount: number
  impactObservationCount: number
  capacityRiskKw: number
  affectedGpuCount: number
  delayedIncidentCount?: number
  repeatFailureCount?: number
  totalDurationHours?: number
  avgDurationHours?: number
  topFailureMode?: string
  sourceRecordUri: string
}

type SemanticZoneDelaySummaryRecord = {
  zoneId: string
  assetCount: number
  incidentCount: number
  impactObservationCount: number
  capacityRiskKw: number
  affectedGpuCount: number
  delayedIncidentCount?: number
  criticalIncidentCount?: number
  totalDurationHours?: number
  topBottleneckStage?: string
  sourceRecordUri: string
}

type SemanticSpareWaitSummaryRecord = {
  stageUri: string
  stageLabel?: string
  incidentCount: number
  recoveryBlockerCount: number
  totalWaitHours?: number
  avgWaitHours?: number
  stockStatus?: string
  sourceRecordUri: string
}

type SemanticTrustFindingRecord = {
  trustFindingUri: string
  trustFindingId?: string
  summary: string
  sourceFactUri: string
  activityUri?: string
  severity?: string
  status?: string
  createdAt?: string
}

type SemanticTopologyDependencyRecord = {
  dependencyEdgeUri: string
  dependencyId: string
  dependentAssetId: string
  dependencyAssetId: string
  dependencyRole: string
  impactScope?: string
  pathId?: string
  sourceRecordUri: string
}

type SemanticValidationSummaryRecord = {
  sourceRecordCount: number
  incidentCount: number
  incidentWithProvenanceCount: number
  assetCount: number
  assetWithProvenanceCount: number
}

type SemanticIncidentEvidenceRecord = {
  incidentId: string
  stageUri: string
  stageLabel?: string
  sourceRecordUri: string
  impactUri?: string
  evidenceUri?: string
  evidenceClassUri?: string
  evidenceTimestamp?: string
  confidenceState?: string
  metricName?: string
  metricValue?: number
  metricUnit?: string
  telemetryStatus?: string
  telemetryAlertId?: string
  alertType?: string
  alertSeverity?: string
  alertTriggeredAt?: string
  alertResolvedAt?: string
  validationId?: string
  validationStatus?: string
  validatorId?: string
  validationStartedAt?: string
  validationCompletedAt?: string
  failureReason?: string
  workOrderId?: string
  assignedTeam?: string
  assignedEngineerId?: string
  workOrderStatus?: string
  plannedStartAt?: string
  actualStartAt?: string
  actualCompletedAt?: string
  requiredSpareId?: string
  requiredSpareName?: string
  stockStatus?: string
  trustFindingUri?: string
  trustSummary?: string
}

type SemanticIncidentTimelineRecord = {
  incidentId: string
  eventUri: string
  eventId?: string
  stageUri: string
  stageLabel?: string
  eventStatus?: string
  enteredAt?: string
  exitedAt?: string
  durationHours?: number
  thresholdHours?: number
  delayHours?: number
  sourceRecordUri: string
}

type SemanticDependencyImpactRecord = {
  assetId: string
  dependencyId?: string
  dependencyAssetId?: string
  dependencyRole?: string
  impactScope?: string
  findingUri?: string
  findingSummary?: string
  sourceRecordUri?: string
}

type SemanticBlastRadiusRecord = {
  assetId: string
  downstreamAssetId?: string
  incidentId?: string
  findingUri?: string
  findingSummary?: string
}

export async function fetchDashboardData(filters: DashboardFilters = {}): Promise<DashboardData> {
  const [
    overviewRecords,
    queueRecords,
    detailRecords,
    stageBottlenecks,
    assetDelays,
    zoneDelays,
    spareWaiting,
    trustFindings,
    impactRecords,
    dependencyRecords,
  ] = await Promise.all([
    postSemanticQuery<SemanticDashboardOverviewRecord>('semanticDashboardOverview'),
    postSemanticQuery<SemanticFollowUpQueueRecord>('semanticFollowUpQueueList'),
    postSemanticQuery<SemanticFollowUpDetailRecord>('semanticFollowUpDetail'),
    postSemanticQuery<SemanticStageBottleneckRecord>('semanticStageBottlenecks'),
    postSemanticQuery<SemanticAssetDelaySummaryRecord>('semanticAssetDelaySummary'),
    postSemanticQuery<SemanticZoneDelaySummaryRecord>('semanticZoneDelaySummary'),
    postSemanticQuery<SemanticSpareWaitSummaryRecord>('semanticSpareWaitSummary'),
    postSemanticQuery<SemanticTrustFindingRecord>('semanticTrustFindingList'),
    postSemanticQuery<SemanticImpactSummaryRecord>('semanticImpactSummary'),
    postSemanticQuery<SemanticTopologyDependencyRecord>('semanticTopologyDependencies'),
  ])

  const followUps = applyDashboardFilters(buildFollowUps(queueRecords, detailRecords), filters)

  return {
    overview: buildOverview(overviewRecords[0], followUps),
    followUps,
    stageBottlenecks: stageBottlenecks.map(mapStageBottleneck),
    assetDelays: assetDelays.map(mapAssetDelaySummary),
    zoneDelays: zoneDelays.map(mapZoneDelaySummary),
    spareWaiting: spareWaiting.map(mapSpareWaitSummary),
    qualityChecks: trustFindings.map(mapTrustFinding),
    impactSummary: buildImpactSummary(impactRecords[0], followUps),
    topologyDependencies: buildTopologyDependencies(dependencyRecords, followUps),
  }
}

export async function fetchFilterMetadata(): Promise<FilterMetadata> {
  const records = await postSemanticQuery<SemanticFilterMetadataRecord>('semanticFilterMetadata')
  const grouped = records.reduce<Record<string, FilterOption[]>>((summary, record) => {
    const key = record.filterType
    summary[key] = summary[key] ?? []
    summary[key].push({
      id: record.id,
      name: record.label ?? humanize(record.id),
    })
    return summary
  }, {})
  return {
    infrastructure_zones: grouped.zone ?? [],
    assets: grouped.asset ?? [],
    asset_types: unique(records.filter((record) => record.filterType === 'assetType').map((record) => record.label ?? record.id)),
    facilities_teams: [],
    spare_categories: [],
    priority_levels: ['CRITICAL', 'HIGH', 'MEDIUM'],
    request_types: [],
    failure_modes: [],
    stages: unique(records.filter((record) => record.filterType === 'stage').map((record) => record.label ?? record.id)),
  }
}

export async function fetchRequestDetail(infrastructureRequestId: string): Promise<RequestDetail> {
  const [queueRecords, detailRecords, evidenceRecords, timelineRecords] = await Promise.all([
    postSemanticQuery<SemanticFollowUpQueueRecord>('semanticFollowUpQueueList'),
    postSemanticQuery<SemanticFollowUpDetailRecord>('semanticFollowUpDetail', { incidentIdParam: infrastructureRequestId }),
    postSemanticQuery<SemanticIncidentEvidenceRecord>('semanticIncidentEvidence', { incidentIdParam: infrastructureRequestId }),
    postSemanticQuery<SemanticIncidentTimelineRecord>('semanticIncidentTimeline', { incidentIdParam: infrastructureRequestId }),
  ])
  const request = buildFollowUps(queueRecords, detailRecords).find((row) => row.incident_id === infrastructureRequestId)
  if (!request) {
    throw new Error(`Semantic follow-up not found: ${infrastructureRequestId}`)
  }
  const detailRecord = detailRecords.find((record) => record.incidentId === infrastructureRequestId)
  const evidence = evidenceRecords
  const timeline = timelineRecords
  return buildRequestDetail(request, detailRecord, evidence, timeline)
}

export async function fetchDataQualityCheck(checkResultId: string): Promise<DataQualityCheck> {
  const records = await postSemanticQuery<SemanticTrustFindingRecord>('semanticTrustFindingList', {
    trustFindingIdParam: checkResultId,
  })
  const selected = records[0]
  if (!selected) {
    throw new Error(`Semantic trust finding not found: ${checkResultId}`)
  }
  return mapTrustFinding(selected)
}

export async function fetchTopologyDependencies(): Promise<InfrastructureDependency[]> {
  const [dependencyRecords, queueRecords, detailRecords] = await Promise.all([
    postSemanticQuery<SemanticTopologyDependencyRecord>('semanticTopologyDependencies'),
    postSemanticQuery<SemanticFollowUpQueueRecord>('semanticFollowUpQueueList'),
    postSemanticQuery<SemanticFollowUpDetailRecord>('semanticFollowUpDetail'),
  ])
  return buildTopologyDependencies(dependencyRecords, buildFollowUps(queueRecords, detailRecords))
}

export async function fetchRequestSemanticContext(
  incidentId: string,
  assetId: string,
): Promise<RequestSemanticContext> {
  const [validationRecords, evidenceRecords, dependencyRecords, blastRadiusRecords] = await Promise.all([
    postSemanticQuery<SemanticValidationSummaryRecord>('semanticValidationSummary'),
    postSemanticQuery<SemanticIncidentEvidenceRecord>('semanticIncidentEvidence', { incidentIdParam: incidentId }),
    postSemanticQuery<SemanticDependencyImpactRecord>('semanticDependencyImpactByAsset', { assetIdParam: assetId }),
    postSemanticQuery<SemanticBlastRadiusRecord>('semanticBlastRadiusByAsset', { assetIdParam: assetId }),
  ])
  const incidentEvidenceRecords = evidenceRecords
  const dependencyImpactRecords = dependencyRecords
  const selectedBlastRadiusRecords = blastRadiusRecords
  return {
    validation: mapSemanticValidation(validationRecords),
    incidentEvidence: mapSemanticIncidentEvidence(incidentId, incidentEvidenceRecords),
    dependencyImpact: mapSemanticDependencyImpact(assetId, dependencyImpactRecords),
    blastRadius: mapSemanticBlastRadius(assetId, selectedBlastRadiusRecords),
  }
}

async function postSemanticQuery<T>(
  queryId: string,
  parameters: Record<string, string> = {},
): Promise<T[]> {
  const response = await fetch(`${SEMANTIC_API_BASE_URL}/semantic/query/${queryId}`, {
    method: 'POST',
    headers: Object.keys(parameters).length ? { 'Content-Type': 'application/json' } : undefined,
    body: Object.keys(parameters).length ? JSON.stringify({ parameters }) : undefined,
  })
  if (!response.ok) {
    const payload = await response.text()
    throw new Error(`Semantic query failed: ${queryId} ${response.status} ${response.statusText} ${payload}`)
  }
  const payload = await response.json() as SemanticEnvelope<T>
  return payload.records
}

function buildFollowUps(
  queueRecords: SemanticFollowUpQueueRecord[],
  detailRecords: SemanticFollowUpDetailRecord[],
): FollowUpItem[] {
  const detailsByIncident = new Map(detailRecords.map((record) => [record.incidentId, record]))
  return queueRecords
    .map((record) => mapFollowUp(record, detailsByIncident.get(record.incidentId)))
    .sort((left, right) => left.priority_rank - right.priority_rank || right.total_priority_score - left.total_priority_score || left.incident_id.localeCompare(right.incident_id))
    .map((row, index) => ({ ...row, priority_rank: row.priority_rank || index + 1 }))
}

function mapFollowUp(record: SemanticFollowUpQueueRecord, detail?: SemanticFollowUpDetailRecord): FollowUpItem {
  const semantic = detail ?? record
  const stage = canonicalStage(semantic.stageLabel ?? record.stageLabel ?? record.stageUri)
  const capacityRiskKw = detail?.capacityRiskKw ?? 0
  const affectedGpuCount = detail?.affectedGpuCount ?? 0
  const trustIssueCount = detail?.trustFindingUri ? 1 : 0
  const restoreReadinessStatus = restoreReadinessStatusFor(detail?.restoreReadinessSummary)
  const priorityLevel = semantic.priorityLevel ?? priorityFor(capacityRiskKw, affectedGpuCount, trustIssueCount)
  const redundancyState = detail?.redundancyState ?? (capacityRiskKw > 0 ? 'N-1' : 'N')
  const vendorStatus = detail?.vendorStatus ?? (stage === 'SPARE_VENDOR_WAITING' ? 'ETA_MISSED' : null)
  const totalPriorityScore = semantic.totalPriorityScore ?? capacityRiskKw / 10 + affectedGpuCount / 4 + trustIssueCount * 20

  return {
    priority_rank: semantic.priorityRank ?? 0,
    incident_id: record.incidentId,
    request_number: record.incidentId,
    request_title: semantic.requestTitle ?? detail?.blockerSummary ?? detail?.recommendedAction ?? `${humanize(record.assetId)} follow-up`,
    asset_id: record.assetId,
    asset_name: humanize(record.assetId),
    zone_id: record.zoneId,
    zone_name: humanize(record.zoneId),
    current_stage: stage,
    current_status: semantic.currentStatus ?? (capacityRiskKw > 0 ? 'BLOCKED' : 'GRAPH_ACTIVE'),
    hours_in_current_stage: semantic.hoursInCurrentStage ?? 0,
    needed_by_at: semantic.neededByAt ?? '',
    priority_level: priorityLevel,
    business_impact: semantic.businessImpact ?? (affectedGpuCount ? `${affectedGpuCount} GPUs affected` : 'Semantic graph follow-up'),
    asset_criticality_score: semantic.assetCriticalityScore ?? (affectedGpuCount ? 20 : 0),
    downtime_score: semantic.downtimeScore ?? 0,
    stage_delay_score: semantic.stageDelayScore ?? 0,
    infrastructure_zone_impact_score: semantic.infrastructureZoneImpactScore ?? (capacityRiskKw ? 20 : 0),
    needed_by_urgency_score: semantic.neededByUrgencyScore ?? 0,
    repeat_failure_score: semantic.repeatFailureScore ?? 0,
    spare_risk_score: semantic.spareRiskScore ?? (stage === 'SPARE_VENDOR_WAITING' ? 20 : 0),
    capacity_risk_score: semantic.capacityRiskScore ?? Math.min(30, capacityRiskKw / 30),
    redundancy_risk_score: semantic.redundancyRiskScore ?? (redundancyState === 'N-1' ? 24 : 0),
    thermal_risk_score: semantic.thermalRiskScore ?? 0,
    vendor_eta_risk_score: semantic.vendorEtaRiskScore ?? (vendorStatus === 'ETA_MISSED' ? 22 : 0),
    mitigation_credit_score: semantic.mitigationCreditScore ?? 0,
    total_priority_score: totalPriorityScore,
    recommended_action: detail?.recommendedAction ?? `Review semantic graph evidence for ${record.incidentId}`,
    reason_summary: `${record.incidentId} is linked to ${humanize(record.assetId)} in ${humanize(record.zoneId)} through canonical RDF source ${lastSegment(record.sourceRecordUri)}.`,
    redundancy_state: redundancyState,
    affected_gpu_count: affectedGpuCount,
    estimated_capacity_risk_kw: capacityRiskKw,
    mitigation_status: detail?.mitigationStatus ?? (capacityRiskKw > 0 ? 'RUNNING_DEGRADED' : null),
    vendor_status: vendorStatus,
    impact_confidence_status: trustIssueCount ? 'WARNING' : 'TRUSTED',
    impact_trust_issue_count: trustIssueCount,
    restore_readiness_status: restoreReadinessStatus,
    restore_readiness_summary: detail?.restoreReadinessSummary ?? null,
  }
}

function applyDashboardFilters(rows: FollowUpItem[], filters: DashboardFilters): FollowUpItem[] {
  return rows.filter((row) => {
    if (filters.zone_id && row.zone_id !== filters.zone_id) return false
    if (filters.asset_id && row.asset_id !== filters.asset_id) return false
    if (filters.priority_level && row.priority_level !== filters.priority_level) return false
    if (filters.stage && row.current_stage !== canonicalStage(filters.stage)) return false
    if (filters.critical_asset_delayed && row.priority_level !== 'CRITICAL') return false
    if (filters.capacity_risk && row.estimated_capacity_risk_kw <= 0) return false
    if (filters.affected_gpu && row.affected_gpu_count <= 0) return false
    if (filters.evidence_review && row.impact_confidence_status === 'TRUSTED') return false
    if (filters.redundancy_lost && row.redundancy_state !== 'N-1') return false
    if (filters.vendor_eta_missed && row.vendor_status !== 'ETA_MISSED') return false
    if (filters.delayed_only && row.hours_in_current_stage <= 0 && row.estimated_capacity_risk_kw <= 0) return false
    return true
  })
}

function buildOverview(record: SemanticDashboardOverviewRecord | undefined, followUps: FollowUpItem[]): Overview {
  const capacityRiskKw = record?.capacityRiskKw ?? followUps.reduce((total, row) => total + row.estimated_capacity_risk_kw, 0)
  const affectedGpuCount = record?.affectedGpuCount ?? followUps.reduce((total, row) => total + row.affected_gpu_count, 0)
  return {
    total_requests: record?.totalIncidents ?? followUps.length,
    open_requests: followUps.length,
    delayed_requests: followUps.filter((row) => row.estimated_capacity_risk_kw > 0 || row.hours_in_current_stage > 0).length,
    critical_asset_delayed: followUps.filter((row) => row.priority_level === 'CRITICAL').length,
    avg_downtime_hours: record?.avgDurationHours ?? 0,
    top_bottleneck_stage: topStage(followUps),
    spare_waiting_delay_hours: followUps.filter((row) => row.current_stage === 'SPARE_VENDOR_WAITING').reduce((total, row) => total + row.hours_in_current_stage, 0),
    repeat_failure_asset_count: record?.repeatFailureAssetCount ?? 0,
    engineer_assignment_delay_hours: record?.engineerAssignmentDelayHours ?? 0,
    capacity_risk_kw: capacityRiskKw,
    affected_gpu_count: affectedGpuCount,
    redundancy_lost_incidents: record?.redundancyLostIncidentCount ?? followUps.filter((row) => row.redundancy_state === 'N-1').length,
    vendor_eta_missed_count: record?.vendorEtaMissedCount ?? followUps.filter((row) => row.vendor_status === 'ETA_MISSED').length,
    latest_pipeline_run_status: 'SEMANTIC_GRAPH',
    data_quality_status: (record?.trustFindingCount ?? 0) > 0 ? 'Needs review' : 'Trusted',
  }
}

function buildImpactSummary(record: SemanticImpactSummaryRecord | undefined, followUps: FollowUpItem[]): ImpactSummary {
  const warningCount = followUps.filter((row) => row.impact_confidence_status !== 'TRUSTED').length
  return {
    incident_count: record?.incidentCount ?? followUps.length,
    capacity_risk_kw: record?.capacityRiskKw ?? followUps.reduce((total, row) => total + row.estimated_capacity_risk_kw, 0),
    affected_rack_count: record?.affectedRackCount ?? 0,
    affected_gpu_count: record?.affectedGpuCount ?? followUps.reduce((total, row) => total + row.affected_gpu_count, 0),
    redundancy_lost_incidents: followUps.filter((row) => row.redundancy_state === 'N-1').length,
    vendor_eta_missed_count: followUps.filter((row) => row.vendor_status === 'ETA_MISSED').length,
    mitigated_incidents: record?.mitigatedIncidentCount ?? 0,
    thermal_breach_minutes: record?.thermalBreachMinutes ?? 0,
    trusted_impact_count: followUps.length - warningCount,
    warning_impact_count: warningCount,
    unverified_impact_count: 0,
  }
}

function mapStageBottleneck(record: SemanticStageBottleneckRecord): StageBottleneck {
  return {
    stage: canonicalStage(record.stageLabel ?? record.stageUri),
    request_count: record.incidentCount,
    delayed_count: record.delayedCount ?? 0,
    delay_rate: record.incidentCount ? (record.delayedCount ?? 0) / record.incidentCount : 0,
    avg_duration_hours: record.avgDurationHours ?? 0,
    p90_duration_hours: record.p90DurationHours ?? 0,
    total_delay_hours: record.totalDelayHours ?? 0,
  }
}

function mapAssetDelaySummary(record: SemanticAssetDelaySummaryRecord): InfrastructureAssetDelay {
  return {
    asset_id: record.assetId,
    asset_name: humanize(record.assetId),
    zone_id: record.zoneId,
    zone_name: humanize(record.zoneId),
    request_count: record.incidentCount,
    delayed_request_count: record.delayedIncidentCount ?? (record.capacityRiskKw > 0 ? record.incidentCount : 0),
    repeat_failure_count: record.repeatFailureCount ?? 0,
    total_downtime_hours: record.totalDurationHours ?? 0,
    avg_repair_duration_hours: record.avgDurationHours ?? 0,
    top_failure_mode: record.topFailureMode ?? (record.impactObservationCount ? 'Semantic impact observation' : 'None'),
  }
}

function mapZoneDelaySummary(record: SemanticZoneDelaySummaryRecord): InfrastructureZoneDelay {
  return {
    zone_id: record.zoneId,
    zone_name: humanize(record.zoneId),
    open_request_count: record.incidentCount,
    delayed_request_count: record.delayedIncidentCount ?? (record.capacityRiskKw > 0 ? record.incidentCount : 0),
    critical_asset_delayed_count: record.criticalIncidentCount ?? (record.affectedGpuCount > 0 ? record.incidentCount : 0),
    total_downtime_hours: record.totalDurationHours ?? 0,
    top_bottleneck_stage: canonicalStage(record.topBottleneckStage ?? 'SEMANTIC_GRAPH'),
  }
}

function mapSpareWaitSummary(record: SemanticSpareWaitSummaryRecord): SpareWaiting {
  return {
    spare_id: lastSegment(record.stageUri),
    spare_name: humanize(record.stageLabel ?? record.stageUri),
    spare_category: 'Semantic recovery blocker',
    waiting_request_count: record.incidentCount,
    total_wait_hours: record.totalWaitHours ?? 0,
    avg_wait_hours: record.avgWaitHours ?? 0,
    critical_spare: record.recoveryBlockerCount > 0,
    stock_status: record.stockStatus ?? (record.recoveryBlockerCount > 0 ? 'REVIEW' : 'OK'),
  }
}

function mapTrustFinding(record: SemanticTrustFindingRecord): DataQualityCheck {
  return {
    check_result_id: record.trustFindingId ?? record.trustFindingUri,
    pipeline_run_id: record.activityUri ?? 'semantic-service',
    check_name: 'Semantic evidence issue',
    target_table: 'semantic_reasoning_graph',
    severity: record.severity ?? 'WARNING',
    status: record.status ?? 'FAILED',
    failed_row_count: 1,
    sample_failed_keys: [record.sourceFactUri],
    message: record.summary,
    created_at: record.createdAt ?? '',
  }
}

function buildTopologyDependencies(
  records: SemanticTopologyDependencyRecord[],
  followUps: FollowUpItem[],
): InfrastructureDependency[] {
  const activeByAsset = followUps.reduce<Map<string, number>>((summary, row) => {
    summary.set(row.asset_id, (summary.get(row.asset_id) ?? 0) + 1)
    return summary
  }, new Map())
  return records.map((record) => ({
    dependency_id: record.dependencyId,
    dependent_asset_id: record.dependentAssetId,
    dependent_asset_name: humanize(record.dependentAssetId),
    dependent_asset_type: 'Semantic asset',
    dependent_status: statusForAsset(record.dependentAssetId, activeByAsset),
    dependency_asset_id: record.dependencyAssetId,
    dependency_asset_name: humanize(record.dependencyAssetId),
    dependency_asset_type: 'Semantic asset',
    dependency_status: statusForAsset(record.dependencyAssetId, activeByAsset),
    dependency_type: record.pathId ?? 'SEMANTIC_DEPENDENCY',
    dependency_role: record.dependencyRole,
    impact_scope: record.impactScope ?? 'unknown',
    dependent_active_incident_count: activeByAsset.get(record.dependentAssetId) ?? 0,
    dependency_active_incident_count: activeByAsset.get(record.dependencyAssetId) ?? 0,
  }))
}

function buildRequestDetail(
  request: FollowUpItem,
  detail: SemanticFollowUpDetailRecord | undefined,
  evidence: SemanticIncidentEvidenceRecord[],
  workflowTimeline: SemanticIncidentTimelineRecord[],
): RequestDetail {
  const evidenceIssues = uniqueTrustFindingEvidence(evidence.filter((record) => record.trustFindingUri))
  const telemetryEvidence = evidence.filter(isTelemetryEvidence)
  const validationEvidence = evidence.filter(isValidationEvidence)
  const workOrderEvidence = evidence.filter(isWorkOrderEvidence)
  const evidenceTimeline = evidence
    .filter((record) => record.evidenceUri || record.trustFindingUri)
    .map((record) => ({
      event_id: record.evidenceUri ?? record.trustFindingUri ?? record.sourceRecordUri,
      stage: canonicalStage(record.stageLabel ?? record.stageUri),
      event_type: evidenceTypeLabel(record),
      event_status: record.telemetryStatus ?? record.validationStatus ?? record.workOrderStatus ?? record.confidenceState ?? 'ASSERTED',
      occurred_at: record.evidenceTimestamp ?? '',
      actor_type: record.validatorId ?? record.assignedTeam ?? 'semantic-service',
      reason_code: record.trustFindingUri ? 'TRUST_FINDING' : null,
      message: record.trustSummary ?? record.failureReason ?? null,
    }))
    .sort((left, right) => left.occurred_at.localeCompare(right.occurred_at))
  const workflowEvents = workflowTimeline.map((record) => ({
    event_id: record.eventId ?? record.eventUri,
    stage: canonicalStage(record.stageLabel ?? record.stageUri),
    event_type: 'WORKFLOW_STAGE',
    event_status: record.eventStatus ?? 'ASSERTED',
    occurred_at: record.enteredAt ?? '',
    actor_type: 'semantic-service',
    reason_code: null,
    message: record.delayHours && record.delayHours > 0 ? `${record.delayHours}h over threshold` : null,
  }))
  const timeline = [...workflowEvents, ...evidenceTimeline].sort((left, right) => left.occurred_at.localeCompare(right.occurred_at))
  const workOrders = workOrderEvidence.length
    ? workOrderEvidence.map((record) => ({
        work_order_id: record.workOrderId ?? record.evidenceUri ?? `${request.incident_id}:semantic-work-order`,
        assigned_team: record.assignedTeam ?? 'Semantic Operations',
        assigned_engineer_id: record.assignedEngineerId ?? null,
        work_order_status: record.workOrderStatus ?? record.confidenceState ?? 'REVIEW',
        planned_start_at: record.plannedStartAt ?? null,
        actual_start_at: record.actualStartAt ?? null,
        actual_completed_at: record.actualCompletedAt ?? null,
        required_spare_id: record.requiredSpareId ?? null,
        required_spare_name: record.requiredSpareName ?? null,
        stock_status: record.stockStatus ?? null,
      }))
    : [
        {
          work_order_id: detail?.followUpDecisionUri ?? `${request.incident_id}:semantic-follow-up`,
          assigned_team: 'Semantic Operations',
          assigned_engineer_id: null,
          work_order_status: detail?.recommendedAction ? 'RECOMMENDED' : 'REVIEW',
          planned_start_at: null,
          actual_start_at: null,
          actual_completed_at: null,
          required_spare_id: null,
          required_spare_name: null,
          stock_status: null,
        },
      ]
  return {
    request,
    stage_lead_times: workflowTimeline.length
      ? workflowTimeline.map((record) => ({
          stage: canonicalStage(record.stageLabel ?? record.stageUri),
          entered_at: record.enteredAt ?? '',
          exited_at: record.exitedAt ?? null,
          duration_hours: record.durationHours ?? 0,
          threshold_hours: record.thresholdHours ?? 0,
          is_bottleneck: (record.delayHours ?? 0) > 0,
          delay_hours: record.delayHours ?? 0,
        }))
      : [
          {
            stage: request.current_stage,
            entered_at: '',
            exited_at: null,
            duration_hours: request.hours_in_current_stage,
            threshold_hours: 0,
            is_bottleneck: request.estimated_capacity_risk_kw > 0 || request.impact_trust_issue_count > 0,
            delay_hours: request.hours_in_current_stage,
          },
        ],
    timeline,
    work_orders: workOrders,
    validation_results: validationEvidence.map((record) => ({
      validation_id: record.validationId ?? record.evidenceUri ?? `${request.incident_id}:semantic-validation`,
      validation_status: record.validationStatus ?? record.confidenceState ?? 'REVIEW',
      validator_id: record.validatorId ?? null,
      validation_started_at: record.validationStartedAt ?? record.evidenceTimestamp ?? null,
      validation_completed_at: record.validationCompletedAt ?? null,
      failure_reason: record.failureReason ?? null,
    })),
    telemetry_alerts: telemetryEvidence
      .filter((record) => record.telemetryAlertId || record.alertType || record.alertSeverity || record.alertTriggeredAt)
      .map((record) => ({
        telemetry_alert_id: record.telemetryAlertId ?? record.evidenceUri ?? `${request.incident_id}:semantic-telemetry-alert`,
        asset_id: request.asset_id,
        alert_type: record.alertType ?? record.metricName ?? 'SEMANTIC_TELEMETRY',
        severity: record.alertSeverity ?? record.telemetryStatus ?? record.confidenceState ?? 'INFO',
        triggered_at: record.alertTriggeredAt ?? record.evidenceTimestamp ?? '',
        resolved_at: record.alertResolvedAt ?? null,
      })),
    impact_snapshot: {
      impact_snapshot_id: detail?.impactUri ?? `${request.incident_id}:semantic-impact`,
      incident_id: request.incident_id,
      asset_id: request.asset_id,
      zone_id: request.zone_id,
      snapshot_at: '',
      redundancy_state: detail?.redundancyState ?? request.redundancy_state ?? 'Unknown',
      affected_rack_count: detail?.affectedRackCount ?? 0,
      affected_gpu_count: request.affected_gpu_count,
      estimated_capacity_risk_kw: request.estimated_capacity_risk_kw,
      estimated_gpu_capacity_risk_pct: detail?.estimatedGpuCapacityRiskPct ?? (request.affected_gpu_count > 0 ? 100 : 0),
      thermal_breach_minutes: detail?.thermalBreachMinutes ?? 0,
      power_redundancy_lost: detail?.powerRedundancyLost ?? request.redundancy_state === 'N-1',
      cooling_redundancy_lost: detail?.coolingRedundancyLost ?? false,
      mitigation_status: detail?.mitigationStatus ?? request.mitigation_status ?? 'UNKNOWN',
      vendor_eta_at: detail?.vendorEtaAt ?? null,
      vendor_status: detail?.vendorStatus ?? request.vendor_status ?? 'UNKNOWN',
      source_system: 'ontology-native semantic graph',
      telemetry_readings: telemetryEvidence.map((record) => ({
        metric: record.metricName ?? lastSegment(record.evidenceUri ?? 'semantic_metric'),
        value: record.metricValue ?? 0,
        unit: record.metricUnit ?? '',
        status: record.telemetryStatus ?? record.confidenceState ?? 'ASSERTED',
      })),
    },
    quality_flags: [],
    restore_readiness: {
      status: request.restore_readiness_status,
      summary: request.restore_readiness_summary,
      finding_uri: detail?.restoreReadinessUri ?? null,
    },
    impact_confidence_status: request.impact_confidence_status,
    impact_trust_flags: evidenceIssues.map((record) => ({
      issue_type: 'semantic_trust_finding',
      severity: 'WARNING',
      message: record.trustSummary ?? 'Semantic trust finding requires review',
      evidence: {
        sourceRecordUri: record.sourceRecordUri,
        trustFindingUri: record.trustFindingUri,
      },
    })),
  }
}

function restoreReadinessStatusFor(summary?: string): string {
  if (!summary) return 'UNKNOWN'
  const normalized = summary.toLowerCase()
  if (normalized.includes('not ready') || normalized.includes('blocked')) return 'NOT_READY'
  if (normalized.includes('ready for review') || normalized.includes('ready')) return 'READY'
  return 'REVIEW'
}

function uniqueTrustFindingEvidence(records: SemanticIncidentEvidenceRecord[]): SemanticIncidentEvidenceRecord[] {
  return [...records.reduce<Map<string, SemanticIncidentEvidenceRecord>>((summary, record) => {
    const key = record.trustFindingUri ?? `${record.sourceRecordUri}:${record.trustSummary ?? ''}`
    if (!summary.has(key)) {
      summary.set(key, record)
    }
    return summary
  }, new Map()).values()]
}

function mapSemanticValidation(records: SemanticValidationSummaryRecord[]): SemanticValidation {
  const issueCount = records.reduce((total, record) => {
    return total +
      Math.max(0, record.incidentCount - record.incidentWithProvenanceCount) +
      Math.max(0, record.assetCount - record.assetWithProvenanceCount)
  }, 0)
  return {
    conforms: issueCount === 0,
    issue_count: issueCount,
    issues: issueCount
      ? [{
          focus_node: 'named graph provenance',
          result_path: 'prov:wasDerivedFrom',
          message: 'Some semantic graph resources are missing provenance links.',
          severity: 'WARNING',
        }]
      : [],
  }
}

function mapSemanticIncidentEvidence(
  incidentId: string,
  records: SemanticIncidentEvidenceRecord[],
): SemanticIncidentEvidence {
  const first = records[0]
  return {
    incident_id: incidentId,
    found: records.length > 0,
    request_title: first?.trustSummary ?? null,
    asset_id: null,
    workflow_stage: first ? canonicalStage(first.stageLabel ?? first.stageUri) : null,
    current_status: first?.confidenceState ?? null,
    priority_level: null,
    trust_issue_ids: unique(records.map((record) => record.trustFindingUri).filter(Boolean) as string[]),
  }
}

function isTelemetryEvidence(record: SemanticIncidentEvidenceRecord): boolean {
  return record.evidenceClassUri?.endsWith('TelemetryEvidence') === true || Boolean(record.metricName)
}

function isValidationEvidence(record: SemanticIncidentEvidenceRecord): boolean {
  return record.evidenceClassUri?.endsWith('ValidationEvidence') === true || Boolean(record.validationId)
}

function isWorkOrderEvidence(record: SemanticIncidentEvidenceRecord): boolean {
  return record.evidenceClassUri?.endsWith('WorkOrderEvidence') === true || Boolean(record.workOrderId)
}

function evidenceTypeLabel(record: SemanticIncidentEvidenceRecord): string {
  if (isTelemetryEvidence(record)) return 'TELEMETRY_EVIDENCE'
  if (isValidationEvidence(record)) return 'VALIDATION_EVIDENCE'
  if (isWorkOrderEvidence(record)) return 'WORK_ORDER_EVIDENCE'
  return 'SEMANTIC_EVIDENCE'
}

function mapSemanticDependencyImpact(
  assetId: string,
  records: SemanticDependencyImpactRecord[],
): SemanticDependencyImpact {
  return {
    asset_id: assetId,
    direct_dependency_count: records.filter((record) => record.dependencyId).length,
    direct_dependencies: records
      .filter((record) => record.dependencyId && record.dependencyAssetId)
      .map((record) => ({
        dependency_id: record.dependencyId as string,
        dependent_asset_id: assetId,
        dependency_asset_id: record.dependencyAssetId as string,
        dependency_type: record.impactScope ?? 'SEMANTIC_DEPENDENCY',
        dependency_role: record.dependencyRole ?? 'dependency',
      })),
    inferred_downstream_assets: unique(records.map((record) => record.dependencyAssetId).filter(Boolean) as string[]),
  }
}

function mapSemanticBlastRadius(
  assetId: string,
  records: SemanticBlastRadiusRecord[],
): SemanticBlastRadius {
  return {
    asset_id: assetId,
    inferred_downstream_assets: unique(records.map((record) => record.downstreamAssetId).filter(Boolean) as string[]),
    affected_incident_count: unique(records.map((record) => record.incidentId).filter(Boolean) as string[]).length,
    affected_incidents: records
      .filter((record) => record.incidentId)
      .map((record) => ({
        incident_id: record.incidentId as string,
        asset_id: record.downstreamAssetId ?? assetId,
        title: record.findingSummary ?? 'Semantic blast-radius finding',
        stage: 'SEMANTIC_GRAPH',
      })),
  }
}

function topStage(rows: FollowUpItem[]): string | null {
  const [stage] = [...rows.reduce<Map<string, number>>((summary, row) => {
    summary.set(row.current_stage, (summary.get(row.current_stage) ?? 0) + 1)
    return summary
  }, new Map()).entries()].sort(([, left], [, right]) => right - left)[0] ?? []
  return stage ?? null
}

function priorityFor(capacityRiskKw: number, affectedGpuCount: number, trustIssueCount: number): string {
  if (capacityRiskKw >= 500 || affectedGpuCount >= 256 || trustIssueCount > 0) return 'CRITICAL'
  if (capacityRiskKw > 0 || affectedGpuCount > 0) return 'HIGH'
  return 'MEDIUM'
}

function canonicalStage(value: string): string {
  const normalized = lastSegment(value).trim()
  if (!normalized) return 'SEMANTIC_GRAPH'
  return normalized
    .replace(/([a-z0-9])([A-Z])/g, '$1_$2')
    .replace(/[\s-]+/g, '_')
    .replace(/[^A-Za-z0-9_]/g, '_')
    .replace(/_+/g, '_')
    .toUpperCase()
}

function statusForAsset(assetId: string, activeByAsset: Map<string, number>): string {
  return (activeByAsset.get(assetId) ?? 0) > 0 ? 'Degraded' : 'Running'
}

function humanize(value: string): string {
  return lastSegment(value)
    .replace(/[_-]+/g, ' ')
    .replace(/\b\w/g, (character) => character.toUpperCase())
}

function lastSegment(value: string): string {
  return value.split(/[/#:]/).filter(Boolean).at(-1) ?? value
}

function unique(values: string[]): string[] {
  return [...new Set(values)]
}
