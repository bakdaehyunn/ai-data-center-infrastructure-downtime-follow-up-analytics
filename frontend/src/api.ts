export type Overview = {
  total_requests: number
  open_requests: number
  delayed_requests: number
  critical_open_requests: number
  avg_cycle_time_hours: number
  total_delay_hours: number
  top_bottleneck_stage: string | null
  latest_pipeline_run_status: string | null
  data_quality_status: string
}

export type CriticalRequest = {
  priority_rank: number
  request_id: string
  request_number: string
  request_title: string
  department_id: string
  department_name: string
  current_stage: string
  current_status: string
  days_in_current_stage: number
  needed_by_date: string
  criticality_level: string
  business_impact: string
  criticality_score: number
  delay_score: number
  business_impact_score: number
  needed_by_urgency_score: number
  vendor_risk_score: number
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

export type VendorBottleneck = {
  vendor_id: string
  vendor_name: string
  total_po_count: number
  delayed_po_count: number
  delay_rate: number
  avg_confirmation_hours: number
  avg_delivery_delay_days: number
  reliability_tier: string
  total_delay_hours: number
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

export type PipelineRun = {
  pipeline_run_id: string
  pipeline_name: string
  started_at: string
  finished_at: string | null
  status: string
  rows_extracted: number
  rows_loaded: number
  rows_rejected: number
  error_message: string | null
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

export type PurchaseOrderSummary = {
  po_id: string
  po_number: string
  vendor_id: string
  vendor_name: string
  po_status: string
  expected_delivery_date: string | null
  actual_delivery_date: string | null
}

export type ReceiptSummary = {
  receipt_id: string
  received_at: string | null
  inspection_status: string
  inspection_completed_at: string | null
}

export type RequestDetail = {
  request: CriticalRequest
  stage_lead_times: StageLeadTime[]
  timeline: TimelineEvent[]
  related_po: PurchaseOrderSummary | null
  receipt: ReceiptSummary | null
  quality_flags: string[]
}

export type DashboardData = {
  overview: Overview
  criticalRequests: CriticalRequest[]
  stageBottlenecks: StageBottleneck[]
  vendorBottlenecks: VendorBottleneck[]
  failedQualityChecks: DataQualityCheck[]
}

export type FilterOption = {
  id: string
  name: string
}

export type FilterMetadata = {
  departments: FilterOption[]
  vendors: FilterOption[]
  item_categories: string[]
  criticality_levels: string[]
  stages: string[]
}

export type DashboardFilters = {
  stage?: string
  department_id?: string
  vendor_id?: string
  criticality_level?: string
  item_category?: string
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(path)
  if (!response.ok) {
    throw new Error(`${response.status} ${response.statusText}`)
  }
  return response.json() as Promise<T>
}

function buildQuery(params: Record<string, string | number | undefined>) {
  const query = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== '') {
      query.set(key, String(value))
    }
  }
  const queryString = query.toString()
  return queryString ? `?${queryString}` : ''
}

export async function fetchDashboardData(filters: DashboardFilters = {}): Promise<DashboardData> {
  const pipelineRuns = await getJson<PipelineRun[]>('/api/pipeline-runs?limit=1')
  const latestPipelineRunId = pipelineRuns[0]?.pipeline_run_id
  const criticalQuery = buildQuery({
    limit: 10,
    stage: filters.stage,
    department_id: filters.department_id,
    vendor_id: filters.vendor_id,
    criticality_level: filters.criticality_level,
    item_category: filters.item_category,
  })
  const stageBottleneckQuery = buildQuery({
    stage: filters.stage,
    department_id: filters.department_id,
    vendor_id: filters.vendor_id,
    criticality_level: filters.criticality_level,
    item_category: filters.item_category,
  })
  const vendorQuery = buildQuery({
    stage: filters.stage,
    department_id: filters.department_id,
    vendor_id: filters.vendor_id,
    criticality_level: filters.criticality_level,
    item_category: filters.item_category,
  })
  const qualityQuery = buildQuery({
    status: 'FAILED',
    limit: 8,
    pipeline_run_id: latestPipelineRunId,
  })
  const [
    overview,
    criticalRequests,
    stageBottlenecks,
    vendorBottlenecks,
    failedQualityChecks,
  ] = await Promise.all([
    getJson<Overview>('/api/overview'),
    getJson<CriticalRequest[]>(`/api/requests/critical${criticalQuery}`),
    getJson<StageBottleneck[]>(`/api/bottlenecks/stages${stageBottleneckQuery}`),
    getJson<VendorBottleneck[]>(`/api/bottlenecks/vendors${vendorQuery}`),
    getJson<DataQualityCheck[]>(`/api/data-quality/checks${qualityQuery}`),
  ])

  return {
    overview,
    criticalRequests,
    stageBottlenecks,
    vendorBottlenecks,
    failedQualityChecks,
  }
}

export function fetchFilterMetadata(): Promise<FilterMetadata> {
  return getJson<FilterMetadata>('/api/metadata/filters')
}

export function fetchRequestDetail(requestId: string): Promise<RequestDetail> {
  return getJson<RequestDetail>(`/api/requests/${requestId}`)
}

export function fetchDataQualityCheck(checkResultId: string): Promise<DataQualityCheck> {
  return getJson<DataQualityCheck>(`/api/data-quality/checks/${checkResultId}`)
}
