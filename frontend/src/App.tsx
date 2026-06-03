import { type ReactNode, useEffect, useMemo, useState } from 'react'
import {
  AlertTriangle,
  Boxes,
  Clock3,
  Database,
  Filter,
  RefreshCcw,
  Wrench,
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
            if (current && dashboardData.followUps.some((row) => row.maintenance_request_id === current)) {
              return current
            }
            return dashboardData.followUps[0]?.maintenance_request_id ?? null
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
      setDetail(null)
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

  const setFilter = (key: keyof DashboardFilters, value: string) => {
    setFilters((current) => ({ ...current, [key]: value || undefined }))
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Downtime follow-up</p>
          <h1>Maintenance Downtime Follow-up Analytics</h1>
        </div>
        <button className="icon-button" onClick={() => setFilters({})} title="Reset filters">
          <RefreshCcw size={18} />
        </button>
      </header>

      {error ? <div className="error-banner">{error}</div> : null}

      <section className="filters" aria-label="Dashboard filters">
        <Filter size={18} />
        <Select label="Line" value={filters.line_id ?? ''} options={metadata?.production_lines ?? []} onChange={(value) => setFilter('line_id', value)} />
        <Select label="Equipment" value={filters.equipment_id ?? ''} options={metadata?.equipment ?? []} onChange={(value) => setFilter('equipment_id', value)} />
        <Select label="Priority" value={filters.priority_level ?? ''} values={metadata?.priority_levels ?? []} onChange={(value) => setFilter('priority_level', value)} />
        <Select label="Stage" value={filters.stage ?? ''} values={metadata?.stages ?? []} onChange={(value) => setFilter('stage', value)} />
      </section>

      <section className="kpi-grid">
        <Kpi icon={<Wrench size={18} />} label="Open requests" value={dashboard?.overview.open_requests ?? 0} />
        <Kpi icon={<Clock3 size={18} />} label="Delayed requests" value={dashboard?.overview.delayed_requests ?? 0} tone="warning" />
        <Kpi icon={<AlertTriangle size={18} />} label="Critical delayed" value={dashboard?.overview.critical_equipment_delayed ?? 0} tone="danger" />
        <Kpi icon={<Boxes size={18} />} label="Parts wait" value={formatHours(dashboard?.overview.parts_waiting_delay_hours ?? 0)} />
        <Kpi icon={<Database size={18} />} label="Latest-run trust" value={dashboard?.overview.data_quality_status ?? 'UNKNOWN'} tone={dashboard?.overview.data_quality_status === 'PASS' ? 'ok' : 'danger'} />
      </section>

      <section className="layout">
        <div className="primary-column">
          <section className="panel">
            <PanelHeader title="Follow-up Queue" subtitle="Requests ranked by return-to-service delay, blocker stage, line impact, urgency, repeat failure, and parts risk" />
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
              <PanelHeader title="Equipment Impact" subtitle="Where delayed requests concentrate by asset" />
              <CompactRows rows={(dashboard?.equipmentDelays ?? []).slice(0, 5)} getKey={(row) => row.equipment_id} left={(row) => row.equipment_name} right={(row) => formatHours(row.total_downtime_hours)} />
            </section>
            <section className="panel">
              <PanelHeader title="Line Impact" subtitle="Production lines carrying delayed maintenance work" />
              <CompactRows rows={dashboard?.lineDelays ?? []} getKey={(row) => row.line_id} left={(row) => row.line_name} right={(row) => formatHours(row.total_downtime_hours)} />
            </section>
          </section>
        </div>

        <aside className="detail-column">
          <section className="panel detail-panel">
            <PanelHeader title="Request Drilldown" subtitle={detail?.request.request_number ?? 'Select a queued request'} />
            {detailLoading ? <div className="empty-state">Loading request detail</div> : <RequestDetailView detail={detail} />}
          </section>

          <section className="panel">
            <PanelHeader title="Parts Waiting" subtitle="Follow-up work blocked by spare availability" />
            <CompactRows rows={dashboard?.partsWaiting ?? []} getKey={(row) => row.part_id} left={(row) => row.part_name} right={(row) => formatHours(row.total_wait_hours)} />
          </section>

          <section className="panel">
            <PanelHeader title="Data Trust" subtitle={`${dashboard?.qualityChecks.length ?? 0} failed latest-run checks`} />
            <div className="quality-list">
              {(dashboard?.qualityChecks ?? []).map((check) => (
                <div className="quality-row" key={check.check_result_id}>
                  <strong>{check.target_table}</strong>
                  <span>{check.check_name}</span>
                </div>
              ))}
            </div>
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
    return <div className="empty-state">No delayed follow-up requests match the current filters</div>
  }
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Rank</th>
            <th>Request</th>
            <th>Equipment</th>
            <th>Stage</th>
            <th>Delay</th>
            <th>Action</th>
            <th>Score</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.maintenance_request_id} className={selectedId === row.maintenance_request_id ? 'selected' : ''} onClick={() => onSelect(row.maintenance_request_id)}>
              <td>#{row.priority_rank}</td>
              <td>
                <strong>{row.request_number}</strong>
                <span>{row.priority_level}</span>
              </td>
              <td>
                <strong>{row.equipment_name}</strong>
                <span>{row.line_name}</span>
              </td>
              <td>{formatStage(row.current_stage)}</td>
              <td>{formatHours(row.hours_in_current_stage)}</td>
              <td>{row.recommended_action}</td>
              <td>{row.total_priority_score.toFixed(1)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function RequestDetailView({ detail }: { detail: RequestDetail | null }) {
  if (!detail) {
    return <div className="empty-state">Select a queued request to inspect the blocker</div>
  }
  return (
    <div className="detail-stack">
      <div className="detail-summary">
        <strong>{detail.request.request_title}</strong>
        <span>{detail.request.reason_summary}</span>
      </div>
      {detail.quality_flags.length ? (
        <div className="detail-quality-flags" aria-label="Request quality flags">
          {detail.quality_flags.map((flag) => (
            <div key={flag}>
              <AlertTriangle size={15} />
              <span>{flag}</span>
            </div>
          ))}
        </div>
      ) : null}
      <div className="score-grid">
        <Score label="Downtime" value={detail.request.downtime_score} />
        <Score label="Stage delay" value={detail.request.stage_delay_score} />
        <Score label="Parts risk" value={detail.request.parts_risk_score} />
        <Score label="Line impact" value={detail.request.production_line_impact_score} />
      </div>
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
            <span>{order.work_order_status}</span>
            {order.required_part_name ? <span>{order.required_part_name} · {order.stock_status}</span> : null}
          </div>
        ))}
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

export default App
