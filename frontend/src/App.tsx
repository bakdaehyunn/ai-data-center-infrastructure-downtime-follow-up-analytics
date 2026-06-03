import { type ReactNode, useEffect, useMemo, useState } from 'react'
import {
  AlertTriangle,
  Boxes,
  Clock3,
  Cpu,
  Database,
  Filter,
  RefreshCcw,
  ShieldAlert,
  ShieldCheck,
  Wrench,
  Zap,
} from 'lucide-react'
import {
  Bar,
  BarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import {
  type DashboardData,
  type DashboardFilters,
  type FilterMetadata,
  type FollowUpItem,
  type RequestDetail,
  fetchDashboardData,
  fetchFilterMetadata,
  fetchRequestDetail,
} from './api'
import './App.css'

const stageColors = ['#b84f45', '#2f766d', '#4f6f9c', '#ba7a28', '#6d5b9a', '#5d6973']

function App() {
  const [dashboard, setDashboard] = useState<DashboardData | null>(null)
  const [metadata, setMetadata] = useState<FilterMetadata | null>(null)
  const [filters, setFilters] = useState<DashboardFilters>({})
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [detail, setDetail] = useState<RequestDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [detailLoading, setDetailLoading] = useState(false)
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
        const dashboardData = await fetchDashboardData(filters)
        if (!cancelled) {
          setDashboard(dashboardData)
          setSelectedId((current) => {
            if (current && dashboardData.followUps.some((row) => row.incident_id === current)) {
              return current
            }
            return dashboardData.followUps[0]?.incident_id ?? null
          })
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
  }, [filters])

  useEffect(() => {
    if (!selectedId) {
      return
    }
    const requestId = selectedId
    let cancelled = false
    async function loadDetail() {
      setDetailLoading(true)
      try {
        const requestDetail = await fetchRequestDetail(requestId)
        if (!cancelled) setDetail(requestDetail)
      } catch {
        if (!cancelled) setDetail(null)
      } finally {
        if (!cancelled) setDetailLoading(false)
      }
    }
    loadDetail()
    return () => {
      cancelled = true
    }
  }, [selectedId])

  const stageChartData = useMemo(
    () =>
      (dashboard?.stageBottlenecks ?? []).slice(0, 6).map((row, index) => ({
        ...row,
        fill: stageColors[index % stageColors.length],
      })),
    [dashboard],
  )
  const visibleDetail = selectedId && detail?.request.incident_id === selectedId ? detail : null
  const visibleDetailLoading = detailLoading || Boolean(selectedId && detail && detail.request.incident_id !== selectedId)

  const setFilter = (key: keyof DashboardFilters, value: string) => {
    setFilters((current) => ({ ...current, [key]: value || undefined }))
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">AI infrastructure operations</p>
          <h1>AI Data Center Infrastructure Downtime Follow-up Analytics</h1>
        </div>
        <button className="icon-button" onClick={() => setFilters({})} title="Reset filters">
          <RefreshCcw size={18} />
        </button>
      </header>

      {error ? <div className="error-banner">{error}</div> : null}

      <section className="filters" aria-label="Dashboard filters">
        <Filter size={18} />
        <Select label="Zone" value={filters.zone_id ?? ''} options={metadata?.infrastructure_zones ?? []} onChange={(value) => setFilter('zone_id', value)} />
        <Select label="Asset" value={filters.asset_id ?? ''} options={metadata?.assets ?? []} onChange={(value) => setFilter('asset_id', value)} />
        <Select label="Priority" value={filters.priority_level ?? ''} values={metadata?.priority_levels ?? []} onChange={(value) => setFilter('priority_level', value)} />
        <Select label="Stage" value={filters.stage ?? ''} values={metadata?.stages ?? []} onChange={(value) => setFilter('stage', value)} />
      </section>

      <section className="kpi-grid">
        <Kpi icon={<Wrench size={18} />} label="Open incidents" value={dashboard?.overview.open_requests ?? 0} />
        <Kpi icon={<Clock3 size={18} />} label="Delayed follow-ups" value={dashboard?.overview.delayed_requests ?? 0} tone="warning" />
        <Kpi icon={<AlertTriangle size={18} />} label="Critical follow-ups" value={dashboard?.overview.critical_asset_delayed ?? 0} tone="danger" />
        <Kpi icon={<Zap size={18} />} label="Capacity at risk" value={`${(dashboard?.overview.capacity_risk_kw ?? 0).toFixed(0)} kW`} tone="danger" />
        <Kpi icon={<Cpu size={18} />} label="Affected GPUs" value={dashboard?.overview.affected_gpu_count ?? 0} tone="warning" />
      </section>

      <section className="exposure-strip" aria-label="Operational exposure">
        <ExposureMetric icon={<ShieldAlert size={16} />} label="Redundancy lost" value={dashboard?.overview.redundancy_lost_incidents ?? 0} tone="danger" />
        <ExposureMetric icon={<Clock3 size={16} />} label="Vendor ETA missed" value={dashboard?.overview.vendor_eta_missed_count ?? 0} tone="warning" />
        <ExposureMetric icon={<Boxes size={16} />} label="Spare/vendor wait" value={formatHours(dashboard?.overview.spare_waiting_delay_hours ?? 0)} />
        <ExposureMetric icon={<Database size={16} />} label="Evidence status" value={formatDataQualityStatus(dashboard?.overview.data_quality_status)} tone={dashboard?.overview.data_quality_status === 'PASS' ? 'ok' : 'danger'} />
      </section>

      <section className="dashboard-layout">
        <div className="main-stack">
          <section className="panel queue-panel">
            <PanelHeader title="Follow-up Queue" subtitle="Work ordered by recovery delay, blocker, infrastructure impact, and evidence confidence" />
            {loading ? <div className="empty-state">Loading follow-up queue</div> : <FollowUpTable rows={dashboard?.followUps ?? []} selectedId={selectedId} onSelect={setSelectedId} />}
          </section>

          <section className="panel">
            <PanelHeader title="Active Stage Bottlenecks" subtitle={`Top blocker: ${dashboard?.overview.top_bottleneck_stage ?? 'None'}`} />
            <div className="chart-frame">
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={stageChartData} layout="vertical" margin={{ left: 12, right: 24, top: 8, bottom: 8 }}>
                  <XAxis type="number" tickFormatter={(value) => `${value}h`} />
                  <YAxis type="category" dataKey="stage" width={168} tick={{ fontSize: 12 }} />
                  <Tooltip formatter={(value) => [`${value}h`, 'Delay']} />
                  <Bar dataKey="total_delay_hours" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </section>

          <section className="split-panels">
            <section className="panel">
              <PanelHeader title="Asset Impact" subtitle="Where delayed incidents concentrate by infrastructure asset" />
              <CompactRows rows={(dashboard?.assetDelays ?? []).slice(0, 5)} getKey={(row) => row.asset_id} left={(row) => row.asset_name} right={(row) => formatHours(row.total_downtime_hours)} />
            </section>

            <section className="panel">
              <PanelHeader title="Zone Impact" subtitle="AI data center zones carrying delayed infrastructure work" />
              <CompactRows rows={dashboard?.zoneDelays ?? []} getKey={(row) => row.zone_id} left={(row) => row.zone_name} right={(row) => formatHours(row.total_downtime_hours)} />
            </section>
          </section>

          <section className="panel">
            <PanelHeader title="Data Trust" subtitle={`${dashboard?.qualityChecks.length ?? 0} source data issues found in the latest analysis run`} />
            <div className="quality-list">
              {(dashboard?.qualityChecks ?? []).map((check) => (
                <div className="quality-row" key={check.check_result_id}>
                  <strong>{sourceFeedLabel(check.target_table)}</strong>
                  <span>{trustIssueLabel(check.check_name)}</span>
                  <small>{check.failed_row_count} affected row{check.failed_row_count === 1 ? '' : 's'} · {check.target_table}</small>
                </div>
              ))}
            </div>
          </section>
        </div>

        <aside className="side-stack">
          <section className="panel detail-panel">
            <PanelHeader title="Incident Drilldown" subtitle={visibleDetail?.request.request_number ?? 'Select a queued incident'} />
            {visibleDetailLoading ? <div className="empty-state">Loading request detail</div> : <RequestDetailView detail={visibleDetail} />}
          </section>

          <section className="panel">
            <PanelHeader title="Spares and Vendor Waiting" subtitle="Follow-up work blocked by spare availability or vendor dispatch" />
            <CompactRows rows={dashboard?.spareWaiting ?? []} getKey={(row) => row.spare_id} left={(row) => row.spare_name} right={(row) => formatHours(row.total_wait_hours)} />
          </section>

          <section className="panel">
            <PanelHeader title="Impact Summary" subtitle="Active incidents with capacity, redundancy, thermal, vendor, and mitigation context" />
            <CompactRows
              rows={[
                { id: 'capacity', label: 'Capacity risk', value: `${(dashboard?.impactSummary.capacity_risk_kw ?? 0).toFixed(0)} kW` },
                { id: 'gpu', label: 'Affected GPUs', value: `${dashboard?.impactSummary.affected_gpu_count ?? 0}` },
                { id: 'mitigation', label: 'Mitigated incidents', value: `${dashboard?.impactSummary.mitigated_incidents ?? 0}` },
                { id: 'thermal', label: 'Thermal breach', value: `${dashboard?.impactSummary.thermal_breach_minutes ?? 0}m` },
                { id: 'warning', label: 'Impact warnings', value: `${dashboard?.impactSummary.warning_impact_count ?? 0}` },
                { id: 'unverified', label: 'Unverified impact', value: `${dashboard?.impactSummary.unverified_impact_count ?? 0}` },
              ]}
              getKey={(row) => row.id}
              left={(row) => row.label}
              right={(row) => row.value}
            />
          </section>
        </aside>
      </section>
    </main>
  )
}

function Kpi({ icon, label, value, tone }: { icon: ReactNode; label: string; value: ReactNode; tone?: 'ok' | 'warning' | 'danger' }) {
  return (
    <div className={`kpi ${tone ?? ''}`}>
      <div className="kpi-icon">{icon}</div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function ExposureMetric({ icon, label, value, tone }: { icon: ReactNode; label: string; value: ReactNode; tone?: 'ok' | 'warning' | 'danger' }) {
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

function PanelHeader({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div className="panel-header">
      <h2>{title}</h2>
      <p>{subtitle}</p>
    </div>
  )
}

function FollowUpTable({ rows, selectedId, onSelect }: { rows: FollowUpItem[]; selectedId: string | null; onSelect: (id: string) => void }) {
  if (!rows.length) {
    return <div className="empty-state">No delayed follow-up incidents match the current filters</div>
  }
  return (
    <div className="followup-list">
      {rows.map((row) => (
        <button key={row.incident_id} type="button" className={selectedId === row.incident_id ? 'followup-card selected' : 'followup-card'} onClick={() => onSelect(row.incident_id)}>
          <div className="queue-rank">
            <strong>#{row.priority_rank}</strong>
            <span className={`priority-pill ${row.priority_level.toLowerCase()}`}>{formatStage(row.priority_level)}</span>
          </div>

          <div className="queue-identity">
            <span>Incident</span>
            <strong>{row.request_number}</strong>
            <small>{row.request_title}</small>
          </div>

          <div className="queue-asset">
            <span>Asset / zone</span>
            <strong>{row.asset_name}</strong>
            <small>{row.zone_name}</small>
          </div>

          <div className="queue-blocker">
            <span>Recovery blocker</span>
            <strong>{formatStage(row.current_stage)}</strong>
            <small>{formatHours(row.hours_in_current_stage)} in stage</small>
          </div>

          <div className="queue-impact">
            <span>Impact</span>
            <strong>{row.affected_gpu_count ? `${row.affected_gpu_count} GPUs` : 'No GPU impact'}</strong>
            <small>{impactLabel(row)}</small>
          </div>

          <div className="queue-action">
            <span>Next follow-up</span>
            <strong>{row.recommended_action}</strong>
          </div>

          <div className="queue-evidence">
            <span>Evidence</span>
            <TrustBadge status={row.impact_confidence_status} count={row.impact_trust_issue_count} />
          </div>
        </button>
      ))}
    </div>
  )
}

function RequestDetailView({ detail }: { detail: RequestDetail | null }) {
  if (!detail) {
    return <div className="empty-state">Select a queued incident to inspect the blocker</div>
  }
  return (
    <div className="detail-stack">
      <div className="detail-hero">
        <div>
          <strong>{detail.request.request_title}</strong>
          <span>{formatStage(detail.request.priority_level)} priority · blocked at {formatStage(detail.request.current_stage)}</span>
        </div>
        <TrustBadge status={detail.impact_confidence_status} count={detail.impact_trust_flags.length} />
      </div>

      <div className="detail-action">
        <span>Next operational action</span>
        <strong>{detail.request.recommended_action}</strong>
      </div>

      <div className="detail-summary">
        <span>Why it matters</span>
        <p>{detail.request.reason_summary}</p>
      </div>

      <div className="detail-section evidence-section">
        <strong className="detail-section-title">Recovery blocker</strong>
        <div className="timeline">
          {detail.stage_lead_times.map((stage) => (
            <div className={stage.is_bottleneck ? 'timeline-row bottleneck' : 'timeline-row'} key={`${stage.stage}-${stage.entered_at}`}>
              <span>{formatStage(stage.stage)}</span>
              <strong>{formatHours(stage.duration_hours)}</strong>
            </div>
          ))}
        </div>
        <div className="work-order">
          {detail.work_orders.map((order) => (
            <div key={order.work_order_id}>
              <strong>{order.assigned_team}</strong>
              <span>{formatStage(order.work_order_status)}</span>
              {order.required_spare_name ? <span>{order.required_spare_name} · {formatStage(order.stock_status ?? 'unknown')}</span> : null}
            </div>
          ))}
        </div>
      </div>

      {detail.impact_snapshot ? (
        <div className="detail-section evidence-section">
          <strong className="detail-section-title">Impact evidence</strong>
          <div className="impact-context">
            <div>
              <span>Redundancy</span>
              <strong>{detail.impact_snapshot.redundancy_state}</strong>
            </div>
            <div>
              <span>Capacity risk</span>
              <strong>{detail.impact_snapshot.estimated_capacity_risk_kw.toFixed(0)} kW</strong>
            </div>
            <div>
              <span>Affected GPUs</span>
              <strong>{detail.impact_snapshot.affected_gpu_count}</strong>
            </div>
            <div>
              <span>Vendor</span>
              <strong>{formatStage(detail.impact_snapshot.vendor_status)}</strong>
            </div>
            <div>
              <span>Mitigation</span>
              <strong>{formatStage(detail.impact_snapshot.mitigation_status)}</strong>
            </div>
            <div>
              <span>Thermal breach</span>
              <strong>{detail.impact_snapshot.thermal_breach_minutes}m</strong>
            </div>
          </div>
          {detail.impact_snapshot.telemetry_readings.length ? (
            <div className="telemetry-evidence">
              {detail.impact_snapshot.telemetry_readings.map((reading) => (
                <div key={reading.metric}>
                  <span>{formatStage(reading.metric)}</span>
                  <strong>{reading.value} {reading.unit}</strong>
                </div>
              ))}
            </div>
          ) : null}
        </div>
      ) : null}

      <div className="impact-trust evidence-section">
        <strong className="detail-section-title">Trust and source evidence</strong>
        <div className={`trust-summary ${trustTone(detail.impact_confidence_status)}`}>
          {detail.impact_confidence_status === 'TRUSTED' ? <ShieldCheck size={16} /> : <ShieldAlert size={16} />}
          <strong>{trustStatusLabel(detail.impact_confidence_status)}</strong>
          <span>{detail.impact_trust_flags.length ? `${detail.impact_trust_flags.length} impact evidence issue${detail.impact_trust_flags.length === 1 ? '' : 's'} to review` : 'Impact context matches latest-run evidence'}</span>
        </div>
        {detail.quality_flags.length ? (
          <div className="detail-quality-flags" aria-label="Request quality flags">
            {detail.quality_flags.map((flag) => (
              <div key={flag}>
                <AlertTriangle size={15} />
                <span>{trustIssueLabel(flag)}</span>
              </div>
            ))}
          </div>
        ) : null}
        {detail.impact_trust_flags.map((flag) => (
          <div className="impact-trust-flag" key={`${flag.issue_type}-${flag.message}`}>
            <strong>{trustIssueLabel(flag.issue_type)}</strong>
            <span>{flag.message}</span>
            {Object.keys(flag.evidence).length ? <small>{formatEvidence(flag.evidence)}</small> : null}
          </div>
        ))}
      </div>

      <div className="detail-section evidence-section secondary-evidence">
        <strong className="detail-section-title">Priority score evidence</strong>
        <div className="score-grid">
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

function Score({ label, value }: { label: string; value: number }) {
  return (
    <div>
      <span>{label}</span>
      <strong>{value.toFixed(1)}</strong>
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

function CompactRows<T>({ rows, getKey, left, right }: { rows: T[]; getKey: (row: T) => string; left: (row: T) => string; right: (row: T) => string }) {
  if (!rows.length) {
    return <div className="empty-state">No records</div>
  }
  return (
    <div className="compact-list">
      {rows.map((row) => (
        <div className="compact-row" key={getKey(row)}>
          <span>{left(row)}</span>
          <strong>{right(row)}</strong>
        </div>
      ))}
    </div>
  )
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

function formatDataQualityStatus(status?: string | null) {
  if (status === 'PASS') return 'Trusted'
  if (status === 'FAILED') return 'Needs review'
  return 'Unknown'
}

function trustStatusLabel(status: string) {
  if (status === 'TRUSTED') return 'Trusted'
  if (status === 'WARNING') return 'Review evidence'
  return 'Unverified'
}

function sourceFeedLabel(tableName: string) {
  const labels: Record<string, string> = {
    raw_infrastructure_incidents: 'Incident source feed',
    infrastructure_incidents: 'Incident core records',
    incident_stage_events: 'Stage event history',
    validation_results: 'Validation records',
    facility_work_orders: 'Work order records',
    impact_snapshots: 'Impact snapshots',
    telemetry_alerts: 'Telemetry alerts',
  }
  return labels[tableName] ?? formatStage(tableName)
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

function impactLabel(row: FollowUpItem) {
  const labels = [
    row.redundancy_state ? row.redundancy_state : null,
    row.vendor_status ? formatStage(row.vendor_status) : null,
    row.mitigation_status ? formatStage(row.mitigation_status) : null,
  ].filter(Boolean)
  return labels.length ? labels.join(' / ') : 'No impact context'
}

function trustTone(status: string) {
  if (status === 'TRUSTED') return 'trusted'
  if (status === 'WARNING') return 'warning'
  return 'unverified'
}

function formatEvidence(evidence: Record<string, unknown>) {
  return Object.entries(evidence)
    .slice(0, 4)
    .map(([key, value]) => `${formatStage(key)}: ${String(value)}`)
    .join(' · ')
}

export default App
