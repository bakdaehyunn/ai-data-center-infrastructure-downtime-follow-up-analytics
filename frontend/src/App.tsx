import { useEffect, useMemo, useState } from 'react'
import {
  AlertTriangle,
  ArrowUpRight,
  Boxes,
  CheckCircle2,
  Clock3,
  Database,
  RefreshCcw,
  ShieldAlert,
  Truck,
} from 'lucide-react'
import {
  Bar,
  BarChart,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import {
  type CriticalRequest,
  type DashboardData,
  type RequestDetail,
  type StageBottleneck,
  fetchDashboardData,
  fetchRequestDetail,
} from './api'
import './App.css'

const stageColors = [
  '#c75b4f',
  '#2f7a6d',
  '#6c6fb6',
  '#be8a2f',
  '#4e7896',
  '#8b6f47',
  '#697178',
  '#9b5f75',
]

function App() {
  const [dashboard, setDashboard] = useState<DashboardData | null>(null)
  const [selectedRequestId, setSelectedRequestId] = useState<string | null>(null)
  const [requestDetail, setRequestDetail] = useState<RequestDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const detailLoading = Boolean(
    selectedRequestId && requestDetail?.request.request_id !== selectedRequestId,
  )

  async function loadDashboard() {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchDashboardData()
      setDashboard(data)
      const nextSelected = selectedRequestId ?? data.criticalRequests[0]?.request_id ?? null
      setSelectedRequestId(nextSelected)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    let cancelled = false
    fetchDashboardData()
      .then((data) => {
        if (!cancelled) {
          setDashboard(data)
          setSelectedRequestId(data.criticalRequests[0]?.request_id ?? null)
        }
      })
      .catch((caught) => {
        if (!cancelled) {
          setError(caught instanceof Error ? caught.message : 'Failed to load dashboard data')
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (!selectedRequestId) {
      return
    }

    let cancelled = false
    fetchRequestDetail(selectedRequestId)
      .then((detail) => {
        if (!cancelled) {
          setRequestDetail(detail)
        }
      })
      .catch((caught) => {
        if (!cancelled) {
          setError(caught instanceof Error ? caught.message : 'Failed to load request detail')
        }
      })

    return () => {
      cancelled = true
    }
  }, [selectedRequestId])

  const topStages = useMemo(
    () => dashboard?.stageBottlenecks.slice(0, 7) ?? [],
    [dashboard],
  )

  return (
    <main className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">Procurement operations</p>
          <h1>Critical Procurement Bottleneck Analytics</h1>
        </div>
        <button className="icon-button" type="button" onClick={() => void loadDashboard()}>
          <RefreshCcw size={17} aria-hidden="true" />
          Refresh
        </button>
      </header>

      {error ? (
        <section className="notice error-notice">
          <AlertTriangle size={18} aria-hidden="true" />
          <span>{error}</span>
        </section>
      ) : null}

      {loading || !dashboard ? (
        <section className="loading-state">
          <Database size={26} aria-hidden="true" />
          <span>Loading operational data</span>
        </section>
      ) : (
        <>
          <section className="kpi-grid" aria-label="Operations summary">
            <KpiItem
              label="Open requests"
              value={dashboard.overview.open_requests}
              icon={<Boxes size={18} aria-hidden="true" />}
            />
            <KpiItem
              label="Delayed requests"
              value={dashboard.overview.delayed_requests}
              tone="risk"
              icon={<Clock3 size={18} aria-hidden="true" />}
            />
            <KpiItem
              label="Critical open"
              value={dashboard.overview.critical_open_requests}
              tone="critical"
              icon={<ShieldAlert size={18} aria-hidden="true" />}
            />
            <KpiItem
              label="Delay hours"
              value={formatNumber(dashboard.overview.total_delay_hours)}
              icon={<AlertTriangle size={18} aria-hidden="true" />}
            />
            <KpiItem
              label="Top bottleneck"
              value={formatStage(dashboard.overview.top_bottleneck_stage)}
              icon={<ArrowUpRight size={18} aria-hidden="true" />}
            />
            <KpiItem
              label="Data quality"
              value={dashboard.overview.data_quality_status}
              tone={dashboard.overview.data_quality_status === 'PASS' ? 'good' : 'risk'}
              icon={<Database size={18} aria-hidden="true" />}
            />
          </section>

          <section className="dashboard-grid">
            <section className="panel panel-chart" aria-labelledby="stage-bottlenecks-title">
              <PanelTitle
                title="Stage Bottlenecks"
                subtitle="Total delay hours by workflow stage"
              />
              <StageDelayChart stages={topStages} />
            </section>

            <section className="panel panel-quality" aria-labelledby="quality-title">
              <PanelTitle
                title="Pipeline Trust"
                subtitle={`${dashboard.failedQualityChecks.length} failed checks from latest runs`}
              />
              <QualityList checks={dashboard.failedQualityChecks} />
            </section>
          </section>

          <section className="workbench">
            <section className="panel queue-panel" aria-labelledby="queue-title">
              <PanelTitle
                title="Critical Request Queue"
                subtitle="Ranked by criticality, delay, urgency, business impact, and vendor risk"
              />
              <CriticalQueue
                requests={dashboard.criticalRequests}
                selectedRequestId={selectedRequestId}
                onSelect={setSelectedRequestId}
              />
            </section>

            <section className="panel detail-panel" aria-labelledby="detail-title">
              <PanelTitle
                title="Request Drilldown"
                subtitle="Stage lead times, timeline, related PO, and quality flags"
              />
              <RequestDetailPanel detail={requestDetail} loading={detailLoading} />
            </section>
          </section>

          <section className="panel vendor-panel" aria-labelledby="vendor-title">
            <PanelTitle
              title="Vendor Delay Pattern"
              subtitle="Confirmation and delivery reliability from purchase order history"
            />
            <VendorTable vendors={dashboard.vendorBottlenecks} />
          </section>
        </>
      )}
    </main>
  )
}

function KpiItem({
  label,
  value,
  icon,
  tone,
}: {
  label: string
  value: string | number
  icon: React.ReactNode
  tone?: 'risk' | 'critical' | 'good'
}) {
  return (
    <div className={`kpi-item ${tone ?? ''}`}>
      <div className="kpi-icon">{icon}</div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function PanelTitle({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div className="panel-title">
      <h2>{title}</h2>
      <p>{subtitle}</p>
    </div>
  )
}

function StageDelayChart({ stages }: { stages: StageBottleneck[] }) {
  return (
    <div className="chart-frame">
      <ResponsiveContainer width="100%" height={304}>
        <BarChart
          data={stages}
          layout="vertical"
          margin={{ top: 8, right: 20, bottom: 8, left: 10 }}
        >
          <XAxis type="number" hide />
          <YAxis
            type="category"
            dataKey="stage"
            width={148}
            tickFormatter={formatStage}
            tick={{ fontSize: 12, fill: '#5f6871' }}
          />
          <Tooltip
            cursor={{ fill: 'rgba(14, 21, 29, 0.05)' }}
            formatter={(value) => [`${Number(value).toFixed(0)}h`, 'Delay']}
            labelFormatter={(label) => formatStage(String(label))}
          />
          <Bar dataKey="total_delay_hours" radius={[0, 5, 5, 0]}>
            {stages.map((stage, index) => (
              <Cell key={stage.stage} fill={stageColors[index % stageColors.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}

function QualityList({ checks }: { checks: DashboardData['failedQualityChecks'] }) {
  if (!checks.length) {
    return (
      <div className="empty-state">
        <CheckCircle2 size={18} aria-hidden="true" />
        <span>No failed data quality checks</span>
      </div>
    )
  }

  return (
    <ul className="quality-list">
      {checks.slice(0, 4).map((check) => (
        <li key={check.check_result_id}>
          <span className="status-dot"></span>
          <div>
            <strong>{check.check_name}</strong>
            <p>{check.target_table}</p>
          </div>
          <b>{check.failed_row_count}</b>
        </li>
      ))}
    </ul>
  )
}

function CriticalQueue({
  requests,
  selectedRequestId,
  onSelect,
}: {
  requests: CriticalRequest[]
  selectedRequestId: string | null
  onSelect: (requestId: string) => void
}) {
  return (
    <div className="table-scroll">
      <table className="ops-table">
        <thead>
          <tr>
            <th>Rank</th>
            <th>Request</th>
            <th>Stage</th>
            <th>Days</th>
            <th>Score</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {requests.map((request) => (
            <tr
              key={request.request_id}
              className={request.request_id === selectedRequestId ? 'selected-row' : ''}
              onClick={() => onSelect(request.request_id)}
            >
              <td>#{request.priority_rank}</td>
              <td>
                <button className="link-button" type="button">
                  <strong>{request.request_number}</strong>
                  <span>{request.request_title}</span>
                </button>
              </td>
              <td>
                <span className="stage-pill">{formatStage(request.current_stage)}</span>
              </td>
              <td>{request.days_in_current_stage.toFixed(1)}</td>
              <td>
                <strong>{request.total_priority_score.toFixed(0)}</strong>
              </td>
              <td>{request.recommended_action}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function RequestDetailPanel({
  detail,
  loading,
}: {
  detail: RequestDetail | null
  loading: boolean
}) {
  if (loading) {
    return <div className="loading-inline">Loading request detail</div>
  }

  if (!detail) {
    return <div className="empty-state">Select a request from the queue</div>
  }

  const delayedStageCount = detail.stage_lead_times.filter((stage) => stage.is_bottleneck).length

  return (
    <div className="detail-content">
      <div className="detail-header">
        <div>
          <h3>{detail.request.request_number}</h3>
          <p>{detail.request.request_title}</p>
        </div>
        <span className="score-badge">{detail.request.total_priority_score.toFixed(0)}</span>
      </div>

      <div className="detail-facts">
        <span>{formatStage(detail.request.current_stage)}</span>
        <span>{detail.request.criticality_level}</span>
        <span>{delayedStageCount} delayed stages</span>
      </div>

      <section className="detail-section">
        <h4>Recommended Action</h4>
        <p>{detail.request.recommended_action}</p>
        <small>{detail.request.reason_summary}</small>
      </section>

      <section className="detail-section">
        <h4>Stage Lead Times</h4>
        <div className="lead-time-list">
          {detail.stage_lead_times.map((stage) => (
            <div key={`${stage.stage}-${stage.entered_at}`} className="lead-time-row">
              <span>{formatStage(stage.stage)}</span>
              <strong className={stage.is_bottleneck ? 'risk-text' : ''}>
                {formatHours(stage.duration_hours)}
              </strong>
            </div>
          ))}
        </div>
      </section>

      <section className="detail-section">
        <h4>Timeline</h4>
        <ol className="timeline-list">
          {detail.timeline.slice(0, 8).map((event) => (
            <li key={event.event_id}>
              <span>{formatDateTime(event.occurred_at)}</span>
              <strong>{formatStage(event.stage)}</strong>
              <p>{event.event_type}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="detail-section split-section">
        <div>
          <h4>Related PO</h4>
          {detail.related_po ? (
            <p>
              {detail.related_po.po_number} · {detail.related_po.vendor_name}
            </p>
          ) : (
            <p>No purchase order yet</p>
          )}
        </div>
        <div>
          <h4>Receipt</h4>
          <p>{detail.receipt ? detail.receipt.inspection_status : 'No receipt yet'}</p>
        </div>
      </section>

      {detail.quality_flags.length ? (
        <section className="detail-section quality-flags">
          <h4>Quality Flags</h4>
          {detail.quality_flags.map((flag) => (
            <p key={flag}>{flag}</p>
          ))}
        </section>
      ) : null}
    </div>
  )
}

function VendorTable({ vendors }: { vendors: DashboardData['vendorBottlenecks'] }) {
  return (
    <div className="table-scroll">
      <table className="ops-table compact-table">
        <thead>
          <tr>
            <th>Vendor</th>
            <th>Tier</th>
            <th>POs</th>
            <th>Delayed</th>
            <th>Delay Rate</th>
            <th>Confirmation Avg</th>
            <th>Delay Hours</th>
          </tr>
        </thead>
        <tbody>
          {vendors.map((vendor) => (
            <tr key={vendor.vendor_id}>
              <td>
                <span className="vendor-name">
                  <Truck size={15} aria-hidden="true" />
                  {vendor.vendor_name}
                </span>
              </td>
              <td>{vendor.reliability_tier}</td>
              <td>{vendor.total_po_count}</td>
              <td>{vendor.delayed_po_count}</td>
              <td>{formatPercent(vendor.delay_rate)}</td>
              <td>{formatHours(vendor.avg_confirmation_hours)}</td>
              <td>{formatHours(vendor.total_delay_hours)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function formatStage(stage: string | null) {
  if (!stage) {
    return 'None'
  }
  return stage
    .toLowerCase()
    .split('_')
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ')
}

function formatNumber(value: number) {
  return new Intl.NumberFormat('en-US', { maximumFractionDigits: 0 }).format(value)
}

function formatPercent(value: number) {
  return `${Math.round(value * 100)}%`
}

function formatHours(value: number) {
  return `${formatNumber(value)}h`
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

export default App
