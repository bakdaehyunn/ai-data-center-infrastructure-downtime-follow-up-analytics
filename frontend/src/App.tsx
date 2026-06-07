import { type ReactNode, useEffect, useMemo, useState } from 'react'
import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  Boxes,
  Clock3,
  Cpu,
  Database,
  Filter,
  Network,
  RefreshCcw,
  ShieldAlert,
  Wrench,
  Zap,
} from 'lucide-react'
import { Link, Route, Routes, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import {
  type DashboardData,
  type DashboardFilters,
  type FilterMetadata,
  type FollowUpItem,
  type InfrastructureDependency,
  type RequestDetail,
  type RequestSemanticContext,
  fetchDashboardData,
  fetchFilterMetadata,
  fetchRequestDetail,
  fetchRequestSemanticContext,
  fetchTopologyDependencies,
} from './api'
import './App.css'

type DetailTab = 'summary' | 'impact' | 'trust' | 'dependencies'

const detailTabs: { id: DetailTab; label: string }[] = [
  { id: 'summary', label: 'Summary' },
  { id: 'impact', label: 'Impact' },
  { id: 'trust', label: 'Trust' },
  { id: 'dependencies', label: 'Dependencies' },
]

const queueScopes = {
  criticalDelayed: { critical_asset_delayed: true },
  redundancyLost: { redundancy_lost: true },
  vendorEtaMissed: { vendor_eta_missed: true },
  spareVendorWait: { stage: 'SPARE_VENDOR_WAITING' },
  evidenceReview: { evidence_review: true },
} satisfies Record<string, DashboardFilters>

const queueScopeControls: { id: string; label: string; filters: DashboardFilters }[] = [
  { id: 'all', label: 'All queue', filters: {} },
  { id: 'critical-asset-delay', label: 'Critical asset delay', filters: queueScopes.criticalDelayed },
  { id: 'vendor-eta-missed', label: 'Vendor ETA missed', filters: queueScopes.vendorEtaMissed },
  { id: 'spare-vendor-wait', label: 'Spare/vendor wait', filters: queueScopes.spareVendorWait },
  { id: 'evidence-review', label: 'Evidence review', filters: queueScopes.evidenceReview },
  { id: 'n-1-exposure', label: 'N-1 exposure', filters: queueScopes.redundancyLost },
]

function App() {
  return (
    <Routes>
      <Route path="/" element={<FollowUpQueuePage />} />
      <Route path="/follow-ups/:incidentId" element={<FollowUpDetailPage />} />
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}

function FollowUpQueuePage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const filterQuery = searchParams.toString()
  const filters = useMemo(() => filtersFromQuery(filterQuery), [filterQuery])
  const [dashboard, setDashboard] = useState<DashboardData | null>(null)
  const [metadata, setMetadata] = useState<FilterMetadata | null>(null)
  const [selectedIncidentId, setSelectedIncidentId] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    async function loadMetadata() {
      try {
        const filterMetadata = await fetchFilterMetadata()
        if (!cancelled) setMetadata(filterMetadata)
      } catch {
        if (!cancelled) setMetadata(null)
      }
    }
    loadMetadata()
    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    let cancelled = false
    async function load() {
      setLoading(true)
      setError(null)
      try {
        const dashboardData = await fetchDashboardData(filtersFromQuery(filterQuery))
        if (!cancelled) {
          setDashboard(dashboardData)
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : 'Failed to load dashboard')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    load()
    return () => {
      cancelled = true
    }
  }, [filterQuery])

  const setFilter = (key: keyof DashboardFilters, value: string) => {
    applyFilters(setSearchParams, { ...filters, [key]: value || undefined })
  }

  const setQueueScope = (scope: DashboardFilters) => {
    applyFilters(setSearchParams, scope)
  }
  const followUps = dashboard?.followUps ?? []
  const queueSummary = summarizeQueue(followUps)
  const selectedFollowUp = followUps.find((row) => row.incident_id === selectedIncidentId) ?? null

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">AI infrastructure operations</p>
          <h1>AI Data Center Infrastructure Downtime Follow-up Analytics</h1>
        </div>
        <button className="icon-button" onClick={() => applyFilters(setSearchParams, {})} title="Reset filters">
          <RefreshCcw size={18} />
        </button>
      </header>

      {error ? <div className="error-banner">{error}</div> : null}

      <SectionLabel label="Filters" />
      <section className="filters" aria-label="Dashboard filters">
        <Filter size={18} />
        <Select label="Zone" value={filters.zone_id ?? ''} options={metadata?.infrastructure_zones ?? []} onChange={(value) => setFilter('zone_id', value)} />
        <Select label="Asset" value={filters.asset_id ?? ''} options={metadata?.assets ?? []} onChange={(value) => setFilter('asset_id', value)} />
        <Select label="Priority" value={filters.priority_level ?? ''} values={metadata?.priority_levels ?? []} onChange={(value) => setFilter('priority_level', value)} />
        <Select label="Stage" value={filters.stage ?? ''} values={metadata?.stages ?? []} onChange={(value) => setFilter('stage', value)} />
      </section>

      <SectionLabel label="Dashboard Summary" />
      <section className="kpi-grid">
        <Kpi icon={<Wrench size={18} />} label="Queue items" value={queueSummary.queueItems} />
        <Kpi icon={<Clock3 size={18} />} label="Delayed queue items" value={queueSummary.delayedItems} tone="warning" />
        <Kpi icon={<AlertTriangle size={18} />} label="Critical priority" value={queueSummary.criticalPriorityItems} tone="danger" />
        <Kpi icon={<Zap size={18} />} label="Capacity at risk" value={`${queueSummary.capacityRiskKw.toFixed(0)} kW`} tone="danger" />
        <Kpi icon={<Cpu size={18} />} label="Affected GPUs" value={queueSummary.affectedGpuCount} tone="warning" />
      </section>

      <section className="exposure-strip" aria-label="Operational exposure">
        <ExposureMetric icon={<ShieldAlert size={16} />} label="N-1 exposure" value={queueSummary.n1ExposureItems} tone="danger" />
        <ExposureMetric icon={<Clock3 size={16} />} label="Vendor ETA missed" value={queueSummary.vendorEtaMissedItems} tone="warning" />
        <ExposureMetric icon={<Boxes size={16} />} label="Spare/vendor wait" value={`${queueSummary.spareVendorWaitItems} / ${formatHours(queueSummary.spareVendorWaitHours)}`} />
        <ExposureMetric icon={<Database size={16} />} label="Evidence review" value={queueSummary.evidenceReviewItems} tone={queueSummary.evidenceReviewItems ? 'danger' : 'ok'} />
      </section>

      <SectionLabel label="Queue Intelligence" />
      <QueueIntelligence rows={followUps} selectedRow={selectedFollowUp} summary={queueSummary} />

      <SectionLabel label="Follow-up Queue" />
      <section className="queue-scope-bar" aria-label="Queue scopes">
        <div>
          {queueScopeControls.map((scope) => (
            <button
              key={scope.id}
              type="button"
              data-scope-id={scope.id}
              className={isExactScopeActive(filters, scope.filters) ? 'active' : ''}
              aria-pressed={isExactScopeActive(filters, scope.filters)}
              onClick={() => setQueueScope(scope.filters)}
            >
              {scope.label}
            </button>
          ))}
        </div>
      </section>

      <section className="queue-workspace">
        <section className="panel queue-panel">
          {loading ? (
            <div className="empty-state">Loading follow-up queue</div>
          ) : (
            <FollowUpTable rows={followUps} selectedIncidentId={selectedFollowUp?.incident_id ?? null} onSelect={setSelectedIncidentId} />
          )}
        </section>
      </section>
    </main>
  )
}

function filtersFromQuery(filterQuery: string): DashboardFilters {
  const searchParams = new URLSearchParams(filterQuery)
  return {
    zone_id: searchParams.get('zone_id') || undefined,
    asset_id: searchParams.get('asset_id') || undefined,
    priority_level: searchParams.get('priority_level') || undefined,
    stage: searchParams.get('stage') || undefined,
    delayed_only: searchParams.get('delayed_only') === 'true' || undefined,
    critical_asset_delayed: searchParams.get('critical_asset_delayed') === 'true' || undefined,
    capacity_risk: searchParams.get('capacity_risk') === 'true' || undefined,
    affected_gpu: searchParams.get('affected_gpu') === 'true' || undefined,
    evidence_review: searchParams.get('evidence_review') === 'true' || undefined,
    redundancy_lost: searchParams.get('redundancy_lost') === 'true' || undefined,
    vendor_eta_missed: searchParams.get('vendor_eta_missed') === 'true' || undefined,
  }
}

function applyFilters(setSearchParams: (nextInit: URLSearchParams) => void, filters: DashboardFilters) {
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([key, value]) => {
    if (value) {
      params.set(key, String(value))
    }
  })
  setSearchParams(params)
}

function isExactScopeActive(filters: DashboardFilters, scope: DashboardFilters) {
  const filterEntries = Object.entries(filters).filter(([, value]) => Boolean(value))
  const scopeEntries = Object.entries(scope).filter(([, value]) => Boolean(value))
  return filterEntries.length === scopeEntries.length
    && scopeEntries.every(([key, value]) => filters[key as keyof DashboardFilters] === value)
}

function summarizeQueue(rows: FollowUpItem[]) {
  return {
    queueItems: rows.length,
    delayedItems: rows.filter((row) => row.hours_in_current_stage > 0).length,
    criticalPriorityItems: rows.filter((row) => row.priority_level === 'CRITICAL').length,
    capacityRiskKw: rows.reduce((total, row) => total + row.estimated_capacity_risk_kw, 0),
    affectedGpuCount: rows.reduce((total, row) => total + row.affected_gpu_count, 0),
    n1ExposureItems: rows.filter((row) => row.redundancy_state === 'N-1').length,
    vendorEtaMissedItems: rows.filter((row) => row.vendor_status === 'ETA_MISSED').length,
    spareVendorWaitItems: rows.filter((row) => row.current_stage === 'SPARE_VENDOR_WAITING').length,
    spareVendorWaitHours: rows
      .filter((row) => row.current_stage === 'SPARE_VENDOR_WAITING')
      .reduce((total, row) => total + row.hours_in_current_stage, 0),
    evidenceReviewItems: rows.filter((row) => row.impact_confidence_status !== 'TRUSTED').length,
  }
}

type QueueIntelligenceItem = {
  label: string
  value: string
  tone?: 'ok' | 'warning' | 'danger'
}

function QueueIntelligence({ rows, selectedRow, summary }: {
  rows: FollowUpItem[]
  selectedRow: FollowUpItem | null
  summary: ReturnType<typeof summarizeQueue>
}) {
  const items = selectedRow ? buildSelectedFollowUpIntelligence(selectedRow) : buildQueueIntelligence(rows, summary)
  return (
    <section className={`queue-intelligence ${selectedRow ? 'selected' : ''}`} aria-label="Queue intelligence">
      <div className="queue-intelligence-grid">
        {items.map((item) => (
          <div className={`queue-intelligence-item ${item.tone ?? ''}`} key={item.label}>
            <span>{item.label}</span>
            <strong>{item.value}</strong>
          </div>
        ))}
      </div>
    </section>
  )
}

function buildSelectedFollowUpIntelligence(row: FollowUpItem): QueueIntelligenceItem[] {
  return [
    {
      label: 'Incident',
      value: row.request_number,
      tone: row.priority_level === 'CRITICAL' ? 'danger' : row.priority_level === 'HIGH' ? 'warning' : undefined,
    },
    {
      label: 'Summary',
      value: row.request_title,
    },
    {
      label: 'Next action',
      value: row.recommended_action,
      tone: row.priority_level === 'CRITICAL' ? 'danger' : row.priority_level === 'HIGH' ? 'warning' : undefined,
    },
    {
      label: 'Blocker',
      value: formatStage(row.current_stage),
      tone: row.hours_in_current_stage > 0 ? 'warning' : undefined,
    },
    {
      label: 'Time',
      value: formatHours(row.hours_in_current_stage),
      tone: row.hours_in_current_stage > 0 ? 'warning' : undefined,
    },
    {
      label: 'GPUs',
      value: row.affected_gpu_count ? String(row.affected_gpu_count) : '0',
      tone: row.affected_gpu_count > 0 ? 'warning' : undefined,
    },
    {
      label: 'Capacity risk',
      value: `${row.estimated_capacity_risk_kw.toFixed(0)} kW`,
      tone: row.redundancy_state === 'N-1' || row.estimated_capacity_risk_kw > 0 ? 'danger' : undefined,
    },
    {
      label: 'Trust',
      value: trustStatusLabel(row.impact_confidence_status),
      tone: row.impact_confidence_status === 'TRUSTED' ? 'ok' : 'warning',
    },
  ]
}

function buildQueueIntelligence(rows: FollowUpItem[], summary: ReturnType<typeof summarizeQueue>): QueueIntelligenceItem[] {
  const topBlocker = topBlockerSignal(rows)
  const exposureTone = summary.capacityRiskKw > 0 ? 'danger' : undefined
  return [
    {
      label: 'Top blocker',
      value: topBlocker.value,
      tone: topBlocker.tone,
    },
    {
      label: 'Capacity risk',
      value: `${summary.capacityRiskKw.toFixed(0)} kW`,
      tone: exposureTone,
    },
    {
      label: 'Affected GPUs',
      value: String(summary.affectedGpuCount),
      tone: summary.affectedGpuCount > 0 ? 'warning' : undefined,
    },
    {
      label: 'Trust load',
      value: summary.evidenceReviewItems ? `${summary.evidenceReviewItems} need review` : 'Trusted queue',
      tone: summary.evidenceReviewItems ? 'warning' : 'ok',
    },
    primaryRiskSignal(summary),
  ]
}

function topBlockerSignal(rows: FollowUpItem[]): QueueIntelligenceItem {
  if (!rows.length) {
    return {
      label: 'Top blocker',
      value: 'No blocker',
    }
  }
  const stages = rows.reduce<Map<string, { count: number; hours: number }>>((stats, row) => {
    const current = stats.get(row.current_stage) ?? { count: 0, hours: 0 }
    current.count += 1
    current.hours += row.hours_in_current_stage
    stats.set(row.current_stage, current)
    return stats
  }, new Map())
  const [stage, stats] = [...stages.entries()].sort(([, left], [, right]) => right.hours - left.hours || right.count - left.count)[0]
  return {
    label: 'Top blocker',
    value: formatStage(stage),
    tone: stats.hours > 0 ? 'warning' : undefined,
  }
}

function primaryRiskSignal(summary: ReturnType<typeof summarizeQueue>): QueueIntelligenceItem {
  if (!summary.queueItems) {
    return {
      label: 'Primary risk',
      value: 'No active risk',
    }
  }
  if (summary.n1ExposureItems && summary.vendorEtaMissedItems) {
    return {
      label: 'Primary risk',
      value: 'N-1 + missed ETA',
      tone: 'danger',
    }
  }
  if (summary.n1ExposureItems) {
    return {
      label: 'Primary risk',
      value: 'N-1 exposure',
      tone: 'danger',
    }
  }
  if (summary.vendorEtaMissedItems) {
    return {
      label: 'Primary risk',
      value: 'Vendor ETA missed',
      tone: 'warning',
    }
  }
  if (summary.spareVendorWaitItems) {
    return {
      label: 'Primary risk',
      value: 'Spare/vendor wait',
      tone: 'warning',
    }
  }
  return {
    label: 'Primary risk',
    value: 'Delay queue',
    tone: summary.delayedItems ? 'warning' : undefined,
  }
}

function Kpi({ icon, label, value, tone }: {
  icon: ReactNode
  label: string
  value: ReactNode
  tone?: 'ok' | 'warning' | 'danger'
}) {
  return (
    <div className={`kpi ${tone ?? ''}`}>
      <div className="kpi-icon">{icon}</div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function ExposureMetric({ icon, label, value, tone }: {
  icon: ReactNode
  label: string
  value: ReactNode
  tone?: 'ok' | 'warning' | 'danger'
}) {
  return (
    <div className={`exposure-metric ${tone ?? ''}`}>
      <div className="exposure-icon">{icon}</div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function Select({
  label,
  value,
  options,
  values,
  onChange,
}: {
  label: string
  value: string
  options?: { id: string; name: string }[]
  values?: string[]
  onChange: (value: string) => void
}) {
  return (
    <label className="select-field">
      <span>{label}</span>
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="">All</option>
        {(options ?? values?.map((item) => ({ id: item, name: formatStage(item) })) ?? []).map((option) => (
          <option key={option.id} value={option.id}>
            {option.name}
          </option>
        ))}
      </select>
    </label>
  )
}

function SectionLabel({ label }: { label: string }) {
  return <div className="section-label">{label}</div>
}

function FollowUpTable({ rows, selectedIncidentId, onSelect }: {
  rows: FollowUpItem[]
  selectedIncidentId: string | null
  onSelect: (incidentId: string) => void
}) {
  if (!rows.length) {
    return <div className="empty-state">No delayed follow-up incidents match the current filters</div>
  }
  return (
    <div className="followup-table-wrap">
      <table className="followup-table">
        <thead>
          <tr>
            <th scope="col">Rank</th>
            <th scope="col">Priority</th>
            <th scope="col">Incident</th>
            <th scope="col">Asset</th>
            <th scope="col">Zone</th>
            <th scope="col">Blocker</th>
            <th scope="col">Time</th>
            <th scope="col">Action</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              className={row.incident_id === selectedIncidentId ? 'selected' : ''}
              key={row.incident_id}
              tabIndex={0}
              aria-selected={row.incident_id === selectedIncidentId}
              onClick={() => onSelect(row.incident_id)}
              onKeyDown={(event) => {
                if (event.key === 'Enter' || event.key === ' ') {
                  event.preventDefault()
                  onSelect(row.incident_id)
                }
              }}
            >
              <td data-label="Rank" className="rank-cell">
                <strong>#{row.priority_rank}</strong>
              </td>
              <td data-label="Priority">
                <span className={`priority-pill ${row.priority_level.toLowerCase()}`}>{formatStage(row.priority_level)}</span>
              </td>
              <td data-label="Incident" className="primary-cell">
                <strong>{row.request_number}</strong>
              </td>
              <td data-label="Asset" className="primary-cell">
                <strong>{row.asset_name}</strong>
              </td>
              <td data-label="Zone" className="primary-cell">
                <span>{row.zone_name}</span>
              </td>
              <td data-label="Blocker" className="primary-cell">
                <strong>{formatStage(row.current_stage)}</strong>
              </td>
              <td data-label="Time" className="primary-cell">
                <span>{formatHours(row.hours_in_current_stage)}</span>
              </td>
              <td data-label="Action" className="queue-detail-action">
                <Link to={`/follow-ups/${row.incident_id}`} onClick={(event) => event.stopPropagation()}>
                  View details
                  <ArrowRight size={15} />
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function FollowUpDetailPage() {
  const { incidentId } = useParams()
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState<DetailTab>('summary')
  const [detail, setDetail] = useState<RequestDetail | null>(null)
  const [semanticContext, setSemanticContext] = useState<RequestSemanticContext | null>(null)
  const [topologyDependencies, setTopologyDependencies] = useState<InfrastructureDependency[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    async function loadDetail() {
      if (!incidentId) {
        setError('Follow-up not found')
        setLoading(false)
        return
      }
      setLoading(true)
      setError(null)
      try {
        const requestDetail = await fetchRequestDetail(incidentId)
        const [dependencies, semantic] = await Promise.all([
          fetchTopologyDependencies(),
          fetchRequestSemanticContext(requestDetail.request.incident_id, requestDetail.request.asset_id),
        ])
        if (!cancelled) {
          setDetail(requestDetail)
          setSemanticContext(semantic)
          setTopologyDependencies(dependencies)
        }
      } catch {
        if (!cancelled) {
          setDetail(null)
          setSemanticContext(null)
          setTopologyDependencies([])
          setError('Follow-up not found or unavailable')
        }
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    loadDetail()
    return () => {
      cancelled = true
    }
  }, [incidentId])

  return (
    <main className="app-shell detail-page-shell">
      <header className="topbar detail-page-header">
        <div>
          <p className="eyebrow">Selected follow-up</p>
          <h1>{detail?.request.request_number ?? incidentId ?? 'Incident details'}</h1>
          <span>{detail?.request.request_title ?? (loading ? 'Loading selected incident' : 'Incident detail unavailable')}</span>
        </div>
        <button className="icon-button" onClick={() => navigate(-1)} title="Back">
          <ArrowLeft size={18} />
        </button>
      </header>

      <Link className="back-link" to="/">
        <ArrowLeft size={16} />
        Back to Follow-up Queue
      </Link>

      {error ? <div className="error-banner">{error}</div> : null}

      <section className="panel detail-route-panel">
        <nav className="detail-tabs" aria-label="Selected incident detail views" role="tablist">
          {detailTabs.map((tab) => (
            <button
              key={tab.id}
              type="button"
              data-tab-id={tab.id}
              role="tab"
              className={activeTab === tab.id ? 'active' : ''}
              aria-selected={activeTab === tab.id}
              onClick={() => setActiveTab(tab.id)}
            >
              {tab.label}
            </button>
          ))}
        </nav>

        <div className="detail-page-body">
          {loading ? <div className="empty-state">Loading selected incident details</div> : null}
          {!loading && activeTab === 'summary' ? <RequestDetailView detail={detail} semanticContext={semanticContext} /> : null}
          {!loading && activeTab === 'impact' ? <ImpactView detail={detail} semanticContext={semanticContext} /> : null}
          {!loading && activeTab === 'trust' ? <RequestTrustView detail={detail} semanticContext={semanticContext} /> : null}
          {!loading && activeTab === 'dependencies' ? <DependencyDetailView detail={detail} semanticContext={semanticContext} topologyDependencies={topologyDependencies} /> : null}
        </div>
      </section>
    </main>
  )
}

function NotFoundPage() {
  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">AI infrastructure operations</p>
          <h1>Page not found</h1>
        </div>
      </header>
      <Link className="back-link" to="/">
        <ArrowLeft size={16} />
        Back to Follow-up Queue
      </Link>
    </main>
  )
}

function RequestDetailView({ detail, semanticContext }: {
  detail: RequestDetail | null
  semanticContext: RequestSemanticContext | null
}) {
  if (!detail) {
    return <div className="empty-state">Select a queued incident to inspect the follow-up action</div>
  }
  const affectedGpuCount = detail.impact_snapshot?.affected_gpu_count ?? detail.request.affected_gpu_count
  const capacityRiskKw = detail.impact_snapshot?.estimated_capacity_risk_kw ?? detail.request.estimated_capacity_risk_kw
  const evidenceIssueCount = detail.impact_trust_flags.length
  return (
    <div className="detail-stack summary-brief">
      <div className="detail-hero">
        <div>
          <strong>{detail.request.request_title}</strong>
          <span>{formatStage(detail.request.priority_level)} priority · blocked at {formatStage(detail.request.current_stage)}</span>
        </div>
        <TrustBadge status={detail.impact_confidence_status} count={detail.impact_trust_flags.length} />
      </div>

      <div className="detail-action brief-action">
        <span>Next operational action</span>
        <strong>{detail.request.recommended_action}</strong>
      </div>

      <div className="summary-glance-grid" aria-label="Selected incident at a glance">
        <SummaryMetric label="Asset" value={detail.request.asset_name} />
        <SummaryMetric label="Zone" value={detail.request.zone_name} />
        <SummaryMetric label="Blocker" value={formatStage(detail.request.current_stage)} tone="danger" />
        <SummaryMetric label="Time in stage" value={formatHours(detail.request.hours_in_current_stage)} tone="danger" />
        <SummaryMetric label="Affected GPUs" value={String(affectedGpuCount)} tone={affectedGpuCount > 0 ? 'warning' : undefined} />
        <SummaryMetric label="Capacity risk" value={`${capacityRiskKw.toFixed(0)} kW`} tone={capacityRiskKw > 0 ? 'danger' : undefined} />
        <SummaryMetric label="Trust" value={trustStatusLabel(detail.impact_confidence_status)} tone={detail.impact_confidence_status === 'TRUSTED' ? 'ok' : 'warning'} />
        <SummaryMetric label="Evidence issues" value={String(evidenceIssueCount)} tone={evidenceIssueCount ? 'warning' : 'ok'} />
        <SummaryMetric
          label="Ontology validation"
          value={semanticContext?.validation.conforms ? 'Conforms' : 'Review'}
          tone={semanticContext?.validation.conforms ? 'ok' : 'warning'}
        />
        <SummaryMetric
          label="Semantic evidence"
          value={semanticContext?.incidentEvidence.found ? 'Linked' : 'Missing'}
          tone={semanticContext?.incidentEvidence.found ? 'ok' : 'warning'}
        />
      </div>

      <div className="detail-summary">
        <span>Why it matters</span>
        <p>{detail.request.reason_summary}</p>
      </div>

      <div className="detail-section evidence-section">
        <strong className="detail-section-title">Recovery blocker evidence</strong>
        <div className="blocker-stage-grid">
          {detail.stage_lead_times.map((stage) => (
            <div className={stage.is_bottleneck ? 'blocker-stage-card bottleneck' : 'blocker-stage-card'} key={`${stage.stage}-${stage.entered_at}`}>
              <span>{formatStage(stage.stage)}</span>
              <strong>{formatHours(stage.duration_hours)}</strong>
              <small>{stage.delay_hours > 0 ? `${formatHours(stage.delay_hours)} over threshold` : `Threshold ${formatHours(stage.threshold_hours)}`}</small>
            </div>
          ))}
        </div>
        <div className="work-order brief-work-orders">
          {detail.work_orders.map((order) => (
            <div key={order.work_order_id}>
              <strong>{order.assigned_team}</strong>
              <span>{formatStage(order.work_order_status)}</span>
              {order.required_spare_name ? <span>{order.required_spare_name} · {formatStage(order.stock_status ?? 'unknown')}</span> : null}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

function SummaryMetric({ label, value, detail, tone }: {
  label: string
  value: string
  detail?: string
  tone?: 'ok' | 'warning' | 'danger'
}) {
  return (
    <div className={`summary-metric ${tone ?? ''}`}>
      <span>{label}</span>
      <strong>{value}</strong>
      {detail ? <small>{detail}</small> : null}
    </div>
  )
}

function ImpactView({ detail, semanticContext }: {
  detail: RequestDetail | null
  semanticContext: RequestSemanticContext | null
}) {
  if (!detail) {
    return <div className="empty-state">Select a queued incident to inspect impact context</div>
  }
  const impact = detail.impact_snapshot
  return (
    <div className="detail-stack summary-brief">
      <div className="detail-hero">
        <div>
          <strong>Operational impact</strong>
          <span>{detail.request.request_number} · {detail.request.asset_name}</span>
        </div>
        <TrustBadge status={detail.impact_confidence_status} count={detail.impact_trust_flags.length} />
      </div>

      <div className="detail-action brief-action">
        <span>Impact question</span>
        <strong>{impact ? `${impact.affected_gpu_count} GPUs and ${impact.estimated_capacity_risk_kw.toFixed(0)} kW at risk` : 'No impact snapshot is available for this incident'}</strong>
      </div>

      {impact ? (
        <>
          <FactStrip
            ariaLabel="Selected incident impact at a glance"
            items={[
              { label: 'Redundancy', value: impact.redundancy_state, detail: `${impact.affected_rack_count} affected rack${impact.affected_rack_count === 1 ? '' : 's'}`, tone: redundancyTone(impact.redundancy_state) },
              { label: 'Capacity risk', value: `${impact.estimated_capacity_risk_kw.toFixed(0)} kW`, detail: `${impact.estimated_gpu_capacity_risk_pct.toFixed(1)}% GPU capacity risk`, tone: capacityRiskTone(impact.estimated_capacity_risk_kw, impact.estimated_gpu_capacity_risk_pct) },
              { label: 'Affected GPUs', value: String(impact.affected_gpu_count), detail: impact.source_system },
              { label: 'Thermal breach', value: `${impact.thermal_breach_minutes}m`, detail: 'Thermal exposure window', tone: impact.thermal_breach_minutes > 0 ? 'warning' : undefined },
              { label: 'Semantic asset link', value: semanticContext?.incidentEvidence.asset_id ?? 'Missing', detail: 'RDF incident-to-asset assertion', tone: semanticContext?.incidentEvidence.found ? undefined : 'warning' },
            ]}
          />

          <div className="detail-section evidence-section">
            <strong className="detail-section-title">Operational state evidence</strong>
            <EvidenceRows
              items={[
                { label: 'Vendor state', value: formatStage(impact.vendor_status), detail: impact.vendor_eta_at ? `ETA ${impact.vendor_eta_at}` : 'No vendor ETA recorded', tone: vendorStatusTone(impact.vendor_status) },
                { label: 'Mitigation', value: formatStage(impact.mitigation_status), detail: impact.mitigation_status === 'RUNNING_DEGRADED' ? 'Service remains degraded' : 'Mitigation status from impact snapshot', tone: mitigationTone(impact.mitigation_status) },
                { label: 'Power redundancy', value: impact.power_redundancy_lost ? 'Lost' : 'Available', detail: 'Power path redundancy', tone: impact.power_redundancy_lost ? 'danger' : undefined },
                { label: 'Cooling redundancy', value: impact.cooling_redundancy_lost ? 'Lost' : 'Available', detail: 'Cooling path redundancy', tone: impact.cooling_redundancy_lost ? 'danger' : undefined },
              ]}
            />
          </div>

          <div className="detail-section evidence-section">
            <strong className="detail-section-title">Telemetry evidence</strong>
            {impact.telemetry_readings.length ? (
              <EvidenceRows
                items={impact.telemetry_readings.map((reading) => ({
                  label: formatStage(reading.metric),
                  value: `${reading.value} ${reading.unit}`,
                  detail: formatStage(reading.status),
                  tone: telemetryTone(reading.status),
                }))}
              />
            ) : (
              <div className="empty-state compact-empty">No telemetry readings are attached to this impact snapshot</div>
            )}
          </div>
        </>
      ) : (
        <div className="empty-state compact-empty">No impact snapshot for the selected incident</div>
      )}

      <div className="detail-section evidence-section secondary-evidence">
        <strong className="detail-section-title">Priority score inputs</strong>
        <div className="score-list">
          <Score label="Downtime" value={detail.request.downtime_score} />
          <Score label="Stage delay" value={detail.request.stage_delay_score} />
          <Score label="Spare risk" value={detail.request.spare_risk_score} />
          <Score label="Capacity risk" value={detail.request.capacity_risk_score} />
          <Score label="Redundancy risk" value={detail.request.redundancy_risk_score} />
          <Score label="Vendor ETA risk" value={detail.request.vendor_eta_risk_score} />
          <Score label="Mitigation credit" value={detail.request.mitigation_credit_score} />
        </div>
      </div>
    </div>
  )
}

function RequestTrustView({ detail, semanticContext }: {
  detail: RequestDetail | null
  semanticContext: RequestSemanticContext | null
}) {
  if (!detail) {
    return <div className="empty-state">Select a queued incident to review data trust</div>
  }
  const validationSummaryText = validationStatusSummary(detail.validation_results)
  const trustNeedsReview = detail.impact_confidence_status !== 'TRUSTED' || detail.impact_trust_flags.length > 0 || detail.quality_flags.length > 0
  return (
    <div className="detail-stack summary-brief">
      <div className="detail-hero">
        <div>
          <strong>Recommendation trust</strong>
          <span>{detail.request.request_number} · evidence confidence for selected follow-up</span>
        </div>
        <TrustBadge status={detail.impact_confidence_status} count={detail.impact_trust_flags.length} />
      </div>

      <div className="detail-action brief-action">
        <span>Trust question</span>
        <strong>{trustNeedsReview ? 'Review evidence before relying on this recommendation' : 'Recommendation evidence is trusted for the latest analysis run'}</strong>
      </div>

      <div className="summary-glance-grid" aria-label="Selected incident trust at a glance">
        <SummaryMetric label="Impact confidence" value={trustStatusLabel(detail.impact_confidence_status)} detail="Latest impact evidence check" tone={detail.impact_confidence_status === 'TRUSTED' ? 'ok' : 'warning'} />
        <SummaryMetric label="Evidence issues" value={String(detail.impact_trust_flags.length)} detail="Impact evidence flags" tone={detail.impact_trust_flags.length ? 'warning' : 'ok'} />
        <SummaryMetric label="Source quality" value={String(detail.quality_flags.length)} detail="Incident source flags" tone={detail.quality_flags.length ? 'danger' : 'ok'} />
        <SummaryMetric label="Validation records" value={String(detail.validation_results.length)} detail={validationSummaryText} tone={validationTone(validationSummaryText)} />
        <SummaryMetric
          label="Ontology validation"
          value={semanticContext?.validation.conforms ? 'Conforms' : 'Review'}
          detail={`${semanticContext?.validation.issue_count ?? 0} SHACL issues`}
          tone={semanticContext?.validation.conforms ? 'ok' : 'warning'}
        />
        <SummaryMetric
          label="Semantic trust links"
          value={String(semanticContext?.incidentEvidence.trust_issue_ids.length ?? 0)}
          detail="Trust issues linked in RDF graph"
          tone={(semanticContext?.incidentEvidence.trust_issue_ids.length ?? 0) ? 'warning' : 'ok'}
        />
      </div>

      <div className="detail-section evidence-section">
        <strong className="detail-section-title">Ontology validation evidence</strong>
        {semanticContext?.validation.issues.length ? (
          <div className="brief-card-grid">
            {semanticContext.validation.issues.map((issue) => (
              <div className="brief-evidence-card warning" key={`${issue.focus_node}-${issue.result_path}-${issue.message}`}>
                <strong>{issue.focus_node}</strong>
                <span>{issue.message}</span>
                <small>{issue.result_path} · {issue.severity}</small>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state compact-empty">RDF graph conforms to the current SHACL ontology contract</div>
        )}
      </div>

      <div className="detail-section evidence-section">
        <strong className="detail-section-title">Impact evidence review</strong>
        {detail.impact_trust_flags.length ? (
          <div className="brief-card-grid">
            {detail.impact_trust_flags.map((flag) => (
              <div className="brief-evidence-card warning" key={`${flag.issue_type}-${flag.message}`}>
                <strong>{trustIssueLabel(flag.issue_type)}</strong>
                <span>{flag.message}</span>
                {Object.keys(flag.evidence).length ? <small>{formatEvidence(flag.evidence)}</small> : null}
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state compact-empty">Impact evidence matches the latest analysis run</div>
        )}
      </div>

      <div className="detail-section evidence-section">
        <strong className="detail-section-title">Source quality evidence</strong>
        {detail.quality_flags.length ? (
          <div className="brief-card-grid" aria-label="Request quality flags">
            {detail.quality_flags.map((flag) => (
              <div className="brief-evidence-card danger" key={flag}>
                <strong>{trustIssueLabel(flag)}</strong>
                <span>Source quality flag is attached to this selected incident</span>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state compact-empty">No source quality flags were found for this selected incident</div>
        )}
      </div>

      <div className="detail-section evidence-section secondary-evidence">
        <strong className="detail-section-title">Validation evidence</strong>
        {detail.validation_results.length ? (
          <div className="brief-card-grid">
            {detail.validation_results.map((validation) => (
              <div className={`brief-evidence-card ${validation.validation_status === 'PASSED' ? 'ok' : 'warning'}`} key={validation.validation_id}>
                <strong>{formatStage(validation.validation_status)}</strong>
                <span>{validation.validator_id ?? 'No validator assigned'}</span>
                {validation.failure_reason ? <small>{validation.failure_reason}</small> : null}
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state compact-empty">No validation records are attached to this incident</div>
        )}
      </div>
    </div>
  )
}

function DependencyDetailView({ detail, semanticContext, topologyDependencies }: {
  detail: RequestDetail | null
  semanticContext: RequestSemanticContext | null
  topologyDependencies: InfrastructureDependency[]
}) {
  const paths = buildTopologyPaths(topologyDependencies)
  const activeIncidentCount = paths.reduce((total, path) => total + path.activeIncidentCount, 0)
  if (!detail) {
    return <div className="empty-state">Select a queued incident to compare dependency context against the active blocker</div>
  }
  return (
    <div className="detail-stack summary-brief">
      <div className="detail-hero">
        <div>
          <strong>Dependency impact</strong>
          <span>{formatStage(detail.request.current_stage)} · {detail.request.asset_name}</span>
        </div>
        <TrustBadge status={detail.impact_confidence_status} count={detail.impact_trust_flags.length} />
      </div>

      <div className="detail-action brief-action">
        <span>Dependency question</span>
        <strong>Does this blocker expose power, cooling, redundancy, or GPU capacity risk?</strong>
      </div>

      <FactStrip
        ariaLabel="Selected incident dependency impact at a glance"
        items={[
          { label: 'Dependency paths', value: String(paths.length), detail: 'Power and cooling paths' },
          { label: 'Path incidents', value: String(activeIncidentCount), detail: 'Active incidents on paths', tone: activeIncidentCount > 0 ? 'warning' : undefined },
          { label: 'Capacity risk', value: `${detail.request.estimated_capacity_risk_kw.toFixed(0)} kW`, detail: `${detail.request.affected_gpu_count} affected GPUs`, tone: capacityRiskTone(detail.request.estimated_capacity_risk_kw) },
          { label: 'Redundancy', value: detail.request.redundancy_state ?? 'Unknown', detail: 'Selected incident redundancy state', tone: redundancyTone(detail.request.redundancy_state) },
          { label: 'Inferred downstream', value: String(semanticContext?.blastRadius.inferred_downstream_assets.length ?? 0), detail: 'SPARQL blast-radius traversal', tone: (semanticContext?.blastRadius.inferred_downstream_assets.length ?? 0) ? 'warning' : undefined },
        ]}
      />

      <div className="detail-section evidence-section">
        <strong className="detail-section-title">Semantic dependency evidence</strong>
        <EvidenceRows
          items={[
            {
              label: 'Direct graph edges',
              value: String(semanticContext?.dependencyImpact.direct_dependency_count ?? 0),
              detail: 'Incident asset dependency assertions',
              tone: (semanticContext?.dependencyImpact.direct_dependency_count ?? 0) ? 'warning' : undefined,
            },
            {
              label: 'Blast-radius incidents',
              value: String(semanticContext?.blastRadius.affected_incident_count ?? 0),
              detail: 'Incidents on selected asset or inferred downstream assets',
              tone: (semanticContext?.blastRadius.affected_incident_count ?? 0) ? 'warning' : undefined,
            },
          ]}
        />
      </div>

      <div className="detail-section evidence-section">
        <strong className="detail-section-title">Power and cooling paths</strong>
        <TopologyRows rows={topologyDependencies} />
      </div>
    </div>
  )
}

function Score({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <span>{label}</span>
      <strong>{value.toFixed(1)}</strong>
    </div>
  )
}

type BriefFact = {
  label: string
  value: string
  detail?: string
  tone?: 'ok' | 'warning' | 'danger'
}

function FactStrip({ ariaLabel, items }: { ariaLabel: string; items: BriefFact[] }) {
  return (
    <div className="metric-card-grid" aria-label={ariaLabel}>
      {items.map((item) => (
        <div className={item.tone ?? undefined} key={item.label}>
          <span>{item.label}</span>
          <strong>{item.value}</strong>
          {item.detail ? <small>{item.detail}</small> : null}
        </div>
      ))}
    </div>
  )
}

function EvidenceRows({ items }: { items: BriefFact[] }) {
  return (
    <div className="evidence-compact-grid">
      {items.map((item) => (
        <div className={item.tone ?? undefined} key={item.label}>
          <span>{item.label}</span>
          <strong>{item.value}</strong>
          {item.detail ? <small>{item.detail}</small> : null}
        </div>
      ))}
    </div>
  )
}

function TrustBadge({ status, count }: { status: string; count: number }) {
  return (
    <span className={`trust-badge ${trustTone(status)}`}>
      {trustStatusLabel(status)}
      {count ? ` ${count}` : ''}
    </span>
  )
}

function TopologyRows({ rows }: { rows: InfrastructureDependency[] }) {
  if (!rows.length) {
    return <div className="empty-state">No dependency evidence</div>
  }
  const paths = buildTopologyPaths(rows)
  if (!paths.length) {
    return <div className="empty-state">No configured power or cooling dependency paths match the selected evidence</div>
  }
  return (
    <div className="topology-path-list">
      {paths.map((path) => (
        <div className="topology-path" key={path.id}>
          <div className="topology-path-header">
            <Network size={16} />
            <strong>{path.label}</strong>
            <span>{path.activeIncidentCount} active incident{path.activeIncidentCount === 1 ? '' : 's'}</span>
          </div>
          <div className="topology-node-row">
            {path.nodes.map((node, index) => (
              <div className="topology-node-group" data-step={index + 1} key={`${path.id}-${node.assetId}-${index}`}>
                <div className={`topology-node ${statusTone(node.status)}`}>
                  <small>Step {index + 1}</small>
                  <strong>{node.assetName}</strong>
                  <span>{formatStage(node.status)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

type TopologyPath = {
  id: string
  label: string
  nodes: TopologyNode[]
  activeIncidentCount: number
}

type TopologyNode = {
  assetId: string
  assetName: string
  status: string
  activeIncidentCount: number
}

const topologyPathDefinitions = [
  {
    id: 'power',
    label: 'Power path',
    dependencyIds: ['DEP-RACK-PDU', 'DEP-PDU-UPS', 'DEP-UPS-SWGR', 'DEP-SWGR-GEN'],
  },
  {
    id: 'air-cooling',
    label: 'Air cooling path',
    dependencyIds: ['DEP-RACK-CRAH', 'DEP-CRAH-CHILLER'],
  },
  {
    id: 'liquid-cooling',
    label: 'Liquid cooling path',
    dependencyIds: ['DEP-RACK-CDU', 'DEP-CDU-CHILLER'],
  },
]

function buildTopologyPaths(rows: InfrastructureDependency[]): TopologyPath[] {
  const edgesById = new Map(rows.map((row) => [row.dependency_id, row]))
  return topologyPathDefinitions
    .map((definition) => {
      const edges = definition.dependencyIds
        .map((dependencyId) => edgesById.get(dependencyId))
        .filter((edge): edge is InfrastructureDependency => Boolean(edge))
      if (!edges.length) {
        return null
      }
      const nodes: TopologyNode[] = []
      edges.forEach((edge, index) => {
        if (index === 0) {
          nodes.push({
            assetId: edge.dependent_asset_id,
            assetName: edge.dependent_asset_name,
            status: edge.dependent_status,
            activeIncidentCount: edge.dependent_active_incident_count,
          })
        }
        nodes.push({
          assetId: edge.dependency_asset_id,
          assetName: edge.dependency_asset_name,
          status: edge.dependency_status,
          activeIncidentCount: edge.dependency_active_incident_count,
        })
      })
      const activeIncidentCount = nodes.reduce((total, node) => total + node.activeIncidentCount, 0)
      return {
        id: definition.id,
        label: definition.label,
        nodes,
        activeIncidentCount,
      }
    })
    .filter((path): path is TopologyPath => Boolean(path))
}

function formatHours(value: number) {
  return `${value.toFixed(value >= 100 ? 0 : 1)}h`
}

function formatStage(value: string) {
  return value
    .toLowerCase()
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
}

function trustStatusLabel(status: string) {
  if (status === 'TRUSTED') return 'Trusted'
  if (status === 'WARNING') return 'Review evidence'
  return 'Unverified'
}

function trustIssueLabel(issueName: string) {
  const labels: Record<string, string> = {
    duplicate_source_record: 'Duplicate source records detected',
    missing_required_fields: 'Required source fields are missing',
    infrastructure_incident_without_stage_event: 'Incident is missing stage history',
    stage_event_timestamp_out_of_order: 'Stage events arrived out of order',
    validation_without_completed_work: 'Validation exists without completed work',
    spare_waiting_without_required_spare: 'Spare wait has no required spare record',
    stale_impact_snapshot: 'Impact snapshot is stale',
    missing_impact_snapshot: 'Impact snapshot is missing',
    contradictory_impact_evidence: 'Impact evidence is contradictory',
  }
  return labels[issueName] ?? formatStage(issueName)
}

function trustTone(status: string) {
  if (status === 'TRUSTED') return 'trusted'
  if (status === 'WARNING') return 'warning'
  return 'unverified'
}

function validationStatusSummary(results: RequestDetail['validation_results']) {
  if (!results.length) return 'No validation records'
  const counts = results.reduce<Record<string, number>>((summary, result) => {
    summary[result.validation_status] = (summary[result.validation_status] ?? 0) + 1
    return summary
  }, {})
  return Object.entries(counts)
    .map(([status, count]) => `${count} ${formatStage(status)}`)
    .join(' / ')
}

function validationTone(summary: string): 'ok' | 'warning' | 'danger' {
  if (summary.includes('Failed') || summary.includes('Rejected')) return 'danger'
  if (summary === 'No validation records') return 'warning'
  return 'ok'
}

function redundancyTone(state?: string | null): 'warning' | 'danger' | undefined {
  if (state === 'N-1') return 'danger'
  if (state === 'N') return 'warning'
  return undefined
}

function capacityRiskTone(riskKw: number, riskPct = 0): 'warning' | 'danger' | undefined {
  if (riskKw <= 0) return undefined
  if (riskKw >= 500 || riskPct >= 25) return 'danger'
  return 'warning'
}

function vendorStatusTone(status: string): 'warning' | 'danger' | undefined {
  if (status === 'ETA_MISSED') return 'danger'
  if (status === 'WAITING_VENDOR_DISPATCH') return 'warning'
  return undefined
}

function mitigationTone(status: string): 'warning' | undefined {
  if (status === 'RUNNING_DEGRADED' || status === 'LOAD_SHIFTED') return 'warning'
  return undefined
}

function telemetryTone(status: string): 'warning' | 'danger' | undefined {
  const normalized = status.toUpperCase()
  if (normalized.includes('CRITICAL') || normalized.includes('ALARM') || normalized.includes('BREACH') || normalized.includes('FAILED')) return 'danger'
  if (normalized.includes('WARNING') || normalized.includes('DEGRADED') || normalized.includes('AT_RISK')) return 'warning'
  return undefined
}

function statusTone(status: string) {
  if (status === 'RUNNING') return 'running'
  if (status === 'DEGRADED' || status === 'AT_RISK') return 'warning'
  if (status === 'STOPPED' || status === 'LOCKED_OUT') return 'danger'
  return 'unknown'
}

function formatEvidence(evidence: Record<string, unknown>) {
  return Object.entries(evidence)
    .slice(0, 4)
    .map(([key, value]) => `${formatStage(key)}: ${String(value)}`)
    .join(' · ')
}

export default App
