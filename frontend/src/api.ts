const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'

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
  total_priority_score: number
  recommended_action: string
  reason_summary: string
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
  quality_flags: string[]
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
}

export type DashboardData = {
  overview: Overview
  followUps: FollowUpItem[]
  stageBottlenecks: StageBottleneck[]
  assetDelays: InfrastructureAssetDelay[]
  zoneDelays: InfrastructureZoneDelay[]
  spareWaiting: SpareWaiting[]
  qualityChecks: DataQualityCheck[]
}

export async function fetchDashboardData(filters: DashboardFilters = {}): Promise<DashboardData> {
  const query = buildQuery(filters)
  const [overview, followUps, stageBottlenecks, assetDelays, zoneDelays, spareWaiting, qualityChecks] =
    await Promise.all([
      getJson<Overview>('/api/overview'),
      getJson<FollowUpItem[]>(`/api/follow-ups${query}`),
      getJson<StageBottleneck[]>('/api/downtime/stages'),
      getJson<InfrastructureAssetDelay[]>('/api/assets/delays'),
      getJson<InfrastructureZoneDelay[]>('/api/zones/delays'),
      getJson<SpareWaiting[]>('/api/spares/waiting'),
      getJson<DataQualityCheck[]>('/api/data-quality/checks?status=FAILED&limit=8'),
    ])

  return { overview, followUps, stageBottlenecks, assetDelays, zoneDelays, spareWaiting, qualityChecks }
}

export function fetchFilterMetadata(): Promise<FilterMetadata> {
  return getJson<FilterMetadata>('/api/metadata/filters')
}

export function fetchRequestDetail(infrastructureRequestId: string): Promise<RequestDetail> {
  return getJson<RequestDetail>(`/api/follow-ups/${infrastructureRequestId}`)
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`)
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status} ${response.statusText}`)
  }
  return response.json() as Promise<T>
}

function buildQuery(filters: DashboardFilters): string {
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([key, value]) => {
    if (value) {
      params.set(key, value)
    }
  })
  const query = params.toString()
  return query ? `?${query}` : ''
}
