import { useEffect, useMemo, useState } from 'react'
import {
  AlertTriangle,
  ArrowUpRight,
  Boxes,
  CheckCircle2,
  Clock3,
  Database,
  Filter,
  RefreshCcw,
  ShieldAlert,
  Truck,
  Wrench,
  X,
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
  type DashboardFilters,
  type DataQualityCheck,
  type FilterMetadata,
  type MaintenanceCriticalRequest,
  type MaintenanceDashboardData,
  type MaintenanceDashboardFilters,
  type MaintenanceFilterMetadata,
  type MaintenanceRequestDetail,
  type PartsWaiting,
  type ProductionLineDelay,
  type RequestDetail,
  type StageBottleneck,
  fetchDashboardData,
  fetchDataQualityCheck,
  fetchFilterMetadata,
  fetchMaintenanceDashboardData,
  fetchMaintenanceFilterMetadata,
  fetchMaintenanceRequestDetail,
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
  const [mode, setMode] = useState<'procurement' | 'maintenance'>('procurement')

  return mode === 'maintenance' ? (
    <MaintenanceDashboard onSwitchMode={() => setMode('procurement')} />
  ) : (
    <ProcurementDashboard onSwitchMode={() => setMode('maintenance')} />
  )
}

function ProcurementDashboard({ onSwitchMode }: { onSwitchMode: () => void }) {
  const [dashboard, setDashboard] = useState<DashboardData | null>(null)
  const [filterMetadata, setFilterMetadata] = useState<FilterMetadata | null>(null)
  const [filters, setFilters] = useState<DashboardFilters>({})
  const [selectedRequestId, setSelectedRequestId] = useState<string | null>(null)
  const [requestDetail, setRequestDetail] = useState<RequestDetail | null>(null)
  const [selectedQualityCheckId, setSelectedQualityCheckId] = useState<string | null>(null)
  const [selectedQualityCheck, setSelectedQualityCheck] = useState<DataQualityCheck | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const detailLoading = Boolean(
    selectedRequestId && requestDetail?.request.request_id !== selectedRequestId,
  )

  async function loadDashboard(nextFilters: DashboardFilters = filters) {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchDashboardData(nextFilters)
      setDashboard(data)
      const selectedStillVisible = data.criticalRequests.some(
        (request) => request.request_id === selectedRequestId,
      )
      const nextSelected = selectedStillVisible
        ? selectedRequestId
        : data.criticalRequests[0]?.request_id ?? null
      if (requestDetail?.request.request_id !== nextSelected) {
        setRequestDetail(null)
      }
      setSelectedRequestId(nextSelected)
      const selectedCheckStillVisible = data.failedQualityChecks.some(
        (check) => check.check_result_id === selectedQualityCheckId,
      )
      const nextSelectedCheck = selectedCheckStillVisible
        ? selectedQualityCheckId
        : data.failedQualityChecks[0]?.check_result_id ?? null
      if (selectedQualityCheck?.check_result_id !== nextSelectedCheck) {
        setSelectedQualityCheck(null)
      }
      setSelectedQualityCheckId(nextSelectedCheck)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Failed to load dashboard data')
    } finally {
      setLoading(false)
    }
  }

  function resetFilters() {
    const nextFilters = {}
    setFilters(nextFilters)
    void loadDashboard(nextFilters)
  }

  useEffect(() => {
    let cancelled = false
    Promise.all([fetchDashboardData(), fetchFilterMetadata()])
      .then(([data, metadata]) => {
        if (!cancelled) {
          setDashboard(data)
          setFilterMetadata(metadata)
          setSelectedRequestId(data.criticalRequests[0]?.request_id ?? null)
          setSelectedQualityCheckId(data.failedQualityChecks[0]?.check_result_id ?? null)
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

  useEffect(() => {
    if (!selectedQualityCheckId) {
      return
    }

    let cancelled = false
    fetchDataQualityCheck(selectedQualityCheckId)
      .then((check) => {
        if (!cancelled) {
          setSelectedQualityCheck(check)
        }
      })
      .catch((caught) => {
        if (!cancelled) {
          setError(caught instanceof Error ? caught.message : 'Failed to load quality check detail')
        }
      })

    return () => {
      cancelled = true
    }
  }, [selectedQualityCheckId])

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
        <div className="header-actions">
          <button className="icon-button secondary-button" type="button" onClick={onSwitchMode}>
            <Wrench size={17} aria-hidden="true" />
            Maintenance
          </button>
          <button className="icon-button" type="button" onClick={() => void loadDashboard(filters)}>
            <RefreshCcw size={17} aria-hidden="true" />
            Refresh
          </button>
        </div>
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

          <FilterBar
            metadata={filterMetadata}
            filters={filters}
            onChange={setFilters}
            onApply={() => void loadDashboard(filters)}
            onReset={resetFilters}
          />

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
                subtitle={`${dashboard.failedQualityChecks.length} failed checks from latest run`}
              />
              <QualityDrilldown
                checks={dashboard.failedQualityChecks}
                selectedCheckId={selectedQualityCheckId}
                selectedCheck={selectedQualityCheck}
                onSelect={setSelectedQualityCheckId}
                onOpenRequest={setSelectedRequestId}
              />
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

function MaintenanceDashboard({ onSwitchMode }: { onSwitchMode: () => void }) {
  const [dashboard, setDashboard] = useState<MaintenanceDashboardData | null>(null)
  const [filterMetadata, setFilterMetadata] = useState<MaintenanceFilterMetadata | null>(null)
  const [filters, setFilters] = useState<MaintenanceDashboardFilters>({})
  const [selectedRequestId, setSelectedRequestId] = useState<string | null>(null)
  const [requestDetail, setRequestDetail] = useState<MaintenanceRequestDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const detailLoading = Boolean(
    selectedRequestId && requestDetail?.request.maintenance_request_id !== selectedRequestId,
  )

  async function loadDashboard(nextFilters: MaintenanceDashboardFilters = filters) {
    setLoading(true)
    setError(null)
    try {
      const data = await fetchMaintenanceDashboardData(nextFilters)
      setDashboard(data)
      const selectedStillVisible = data.criticalRequests.some(
        (request) => request.maintenance_request_id === selectedRequestId,
      )
      const nextSelected = selectedStillVisible
        ? selectedRequestId
        : data.criticalRequests[0]?.maintenance_request_id ?? null
      if (requestDetail?.request.maintenance_request_id !== nextSelected) {
        setRequestDetail(null)
      }
      setSelectedRequestId(nextSelected)
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : 'Failed to load maintenance data')
    } finally {
      setLoading(false)
    }
  }

  function resetFilters() {
    const nextFilters = {}
    setFilters(nextFilters)
    void loadDashboard(nextFilters)
  }

  useEffect(() => {
    let cancelled = false
    Promise.all([fetchMaintenanceDashboardData(), fetchMaintenanceFilterMetadata()])
      .then(([data, metadata]) => {
        if (!cancelled) {
          setDashboard(data)
          setFilterMetadata(metadata)
          setSelectedRequestId(data.criticalRequests[0]?.maintenance_request_id ?? null)
        }
      })
      .catch((caught) => {
        if (!cancelled) {
          setError(caught instanceof Error ? caught.message : 'Failed to load maintenance data')
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
    fetchMaintenanceRequestDetail(selectedRequestId)
      .then((detail) => {
        if (!cancelled) {
          setRequestDetail(detail)
        }
      })
      .catch((caught) => {
        if (!cancelled) {
          setError(caught instanceof Error ? caught.message : 'Failed to load maintenance detail')
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
    <main className="app-shell maintenance-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">Industrial maintenance</p>
          <h1>Industrial Maintenance Bottleneck Analytics</h1>
        </div>
        <div className="header-actions">
          <button className="icon-button secondary-button" type="button" onClick={onSwitchMode}>
            <Boxes size={17} aria-hidden="true" />
            Procurement
          </button>
          <button className="icon-button" type="button" onClick={() => void loadDashboard(filters)}>
            <RefreshCcw size={17} aria-hidden="true" />
            Refresh
          </button>
        </div>
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
          <span>Loading maintenance data</span>
        </section>
      ) : (
        <>
          <section className="kpi-grid" aria-label="Maintenance operations summary">
            <KpiItem
              label="Open requests"
              value={dashboard.overview.open_requests}
              icon={<Wrench size={18} aria-hidden="true" />}
            />
            <KpiItem
              label="Delayed"
              value={dashboard.overview.delayed_requests}
              tone="risk"
              icon={<Clock3 size={18} aria-hidden="true" />}
            />
            <KpiItem
              label="Critical delayed"
              value={dashboard.overview.critical_equipment_delayed}
              tone="critical"
              icon={<ShieldAlert size={18} aria-hidden="true" />}
            />
            <KpiItem
              label="Parts wait"
              value={formatHours(dashboard.overview.parts_waiting_delay_hours)}
              tone="risk"
              icon={<Boxes size={18} aria-hidden="true" />}
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

          <MaintenanceFilterBar
            metadata={filterMetadata}
            filters={filters}
            onChange={setFilters}
            onApply={() => void loadDashboard(filters)}
            onReset={resetFilters}
          />

          <section className="dashboard-grid">
            <section className="panel panel-chart" aria-labelledby="maintenance-stage-bottlenecks-title">
              <PanelTitle title="Maintenance Bottlenecks" subtitle="Total delay hours by maintenance stage" />
              <StageDelayChart stages={topStages} />
            </section>

            <section className="panel panel-quality" aria-labelledby="maintenance-parts-title">
              <PanelTitle title="Parts Waiting" subtitle="Required parts delaying active maintenance" />
              <PartsWaitingPanel parts={dashboard.partsWaiting} />
            </section>
          </section>

          <section className="workbench">
            <section className="panel queue-panel" aria-labelledby="maintenance-queue-title">
              <PanelTitle
                title="Critical Maintenance Queue"
                subtitle="Ranked by equipment criticality, downtime, delay, line impact, repeat failures, and parts risk"
              />
              <MaintenanceQueue
                requests={dashboard.criticalRequests}
                selectedRequestId={selectedRequestId}
                onSelect={setSelectedRequestId}
              />
            </section>

            <section className="panel detail-panel" aria-labelledby="maintenance-detail-title">
              <PanelTitle
                title="Maintenance Drilldown"
                subtitle="Timeline, lead times, parts, work order, inspection, sensor alerts, and quality flags"
              />
              <MaintenanceDetailPanel detail={requestDetail} loading={detailLoading} />
            </section>
          </section>

          <section className="dashboard-grid">
            <section className="panel" aria-labelledby="equipment-delay-title">
              <PanelTitle title="Equipment Delay Pattern" subtitle="Repeat failures and downtime by asset" />
              <EquipmentDelayTable equipment={dashboard.equipmentDelays} />
            </section>
            <section className="panel" aria-labelledby="line-delay-title">
              <PanelTitle title="Line Delay Pattern" subtitle="Delayed maintenance concentration by production line" />
              <LineDelayTable lines={dashboard.lineDelays} />
            </section>
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

type FilterKey = keyof DashboardFilters

function FilterBar({
  metadata,
  filters,
  onChange,
  onApply,
  onReset,
}: {
  metadata: FilterMetadata | null
  filters: DashboardFilters
  onChange: (filters: DashboardFilters) => void
  onApply: () => void
  onReset: () => void
}) {
  const isDisabled = metadata === null

  function setFilter(key: FilterKey, value: string) {
    onChange({
      ...filters,
      [key]: value || undefined,
    })
  }

  return (
    <section className="filter-panel" aria-label="Dashboard filters">
      <div className="filter-title">
        <Filter size={17} aria-hidden="true" />
        <span>Filters</span>
      </div>
      <div className="filter-controls">
        <FilterSelect
          label="Stage"
          value={filters.stage ?? ''}
          disabled={isDisabled}
          options={metadata?.stages.map((stage) => ({ id: stage, name: formatStage(stage) })) ?? []}
          onChange={(value) => setFilter('stage', value)}
        />
        <FilterSelect
          label="Department"
          value={filters.department_id ?? ''}
          disabled={isDisabled}
          options={metadata?.departments ?? []}
          onChange={(value) => setFilter('department_id', value)}
        />
        <FilterSelect
          label="Vendor"
          value={filters.vendor_id ?? ''}
          disabled={isDisabled}
          options={metadata?.vendors ?? []}
          onChange={(value) => setFilter('vendor_id', value)}
        />
        <FilterSelect
          label="Criticality"
          value={filters.criticality_level ?? ''}
          disabled={isDisabled}
          options={
            metadata?.criticality_levels.map((level) => ({ id: level, name: formatStage(level) })) ??
            []
          }
          onChange={(value) => setFilter('criticality_level', value)}
        />
        <FilterSelect
          label="Category"
          value={filters.item_category ?? ''}
          disabled={isDisabled}
          options={
            metadata?.item_categories.map((category) => ({
              id: category,
              name: formatStage(category),
            })) ?? []
          }
          onChange={(value) => setFilter('item_category', value)}
        />
      </div>
      <div className="filter-actions">
        <button className="icon-button" type="button" onClick={onApply} disabled={isDisabled}>
          <Filter size={16} aria-hidden="true" />
          Apply
        </button>
        <button className="icon-button secondary-button" type="button" onClick={onReset}>
          <X size={16} aria-hidden="true" />
          Clear
        </button>
      </div>
    </section>
  )
}

function FilterSelect({
  label,
  value,
  options,
  disabled,
  onChange,
}: {
  label: string
  value: string
  options: { id: string; name: string }[]
  disabled: boolean
  onChange: (value: string) => void
}) {
  return (
    <label className="filter-select">
      <span>{label}</span>
      <select value={value} disabled={disabled} onChange={(event) => onChange(event.target.value)}>
        <option value="">All</option>
        {options.map((option) => (
          <option key={option.id} value={option.id}>
            {option.name}
          </option>
        ))}
      </select>
    </label>
  )
}

type MaintenanceFilterKey = keyof MaintenanceDashboardFilters

function MaintenanceFilterBar({
  metadata,
  filters,
  onChange,
  onApply,
  onReset,
}: {
  metadata: MaintenanceFilterMetadata | null
  filters: MaintenanceDashboardFilters
  onChange: (filters: MaintenanceDashboardFilters) => void
  onApply: () => void
  onReset: () => void
}) {
  const isDisabled = metadata === null

  function setFilter(key: MaintenanceFilterKey, value: string) {
    onChange({
      ...filters,
      [key]: value || undefined,
    })
  }

  return (
    <section className="filter-panel maintenance-filters" aria-label="Maintenance dashboard filters">
      <div className="filter-title">
        <Filter size={17} aria-hidden="true" />
        <span>Filters</span>
      </div>
      <div className="filter-controls">
        <FilterSelect
          label="Stage"
          value={filters.stage ?? ''}
          disabled={isDisabled}
          options={metadata?.stages.map((stage) => ({ id: stage, name: formatStage(stage) })) ?? []}
          onChange={(value) => setFilter('stage', value)}
        />
        <FilterSelect
          label="Line"
          value={filters.line_id ?? ''}
          disabled={isDisabled}
          options={metadata?.production_lines ?? []}
          onChange={(value) => setFilter('line_id', value)}
        />
        <FilterSelect
          label="Equipment"
          value={filters.equipment_id ?? ''}
          disabled={isDisabled}
          options={metadata?.equipment ?? []}
          onChange={(value) => setFilter('equipment_id', value)}
        />
        <FilterSelect
          label="Team"
          value={filters.technician_team ?? ''}
          disabled={isDisabled}
          options={metadata?.technician_teams.map((team) => ({ id: team, name: team })) ?? []}
          onChange={(value) => setFilter('technician_team', value)}
        />
        <FilterSelect
          label="Part"
          value={filters.part_category ?? ''}
          disabled={isDisabled}
          options={
            metadata?.part_categories.map((category) => ({
              id: category,
              name: formatStage(category),
            })) ?? []
          }
          onChange={(value) => setFilter('part_category', value)}
        />
      </div>
      <div className="filter-actions">
        <button className="icon-button" type="button" onClick={onApply} disabled={isDisabled}>
          <Filter size={16} aria-hidden="true" />
          Apply
        </button>
        <button className="icon-button secondary-button" type="button" onClick={onReset}>
          <X size={16} aria-hidden="true" />
          Clear
        </button>
      </div>
    </section>
  )
}

function StageDelayChart({ stages }: { stages: StageBottleneck[] }) {
  if (!stages.length) {
    return <div className="empty-state chart-empty">No stage bottlenecks match the current filters</div>
  }

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

function QualityDrilldown({
  checks,
  selectedCheckId,
  selectedCheck,
  onSelect,
  onOpenRequest,
}: {
  checks: DashboardData['failedQualityChecks']
  selectedCheckId: string | null
  selectedCheck: DataQualityCheck | null
  onSelect: (checkResultId: string) => void
  onOpenRequest: (requestId: string) => void
}) {
  if (!checks.length) {
    return (
      <div className="empty-state">
        <CheckCircle2 size={18} aria-hidden="true" />
        <span>No failed data quality checks</span>
      </div>
    )
  }

  return (
    <div className="quality-drilldown">
      <ul className="quality-list">
        {checks.map((check) => (
          <li key={check.check_result_id}>
            <button
              className={`quality-row ${check.check_result_id === selectedCheckId ? 'selected' : ''}`}
              type="button"
              onClick={() => onSelect(check.check_result_id)}
            >
              <span className="status-dot"></span>
              <div>
                <strong>{formatStage(check.check_name)}</strong>
                <p>{check.target_table}</p>
              </div>
              <b>{check.failed_row_count}</b>
            </button>
          </li>
        ))}
      </ul>
      <QualityDetail check={selectedCheck} onOpenRequest={onOpenRequest} />
    </div>
  )
}

function QualityDetail({
  check,
  onOpenRequest,
}: {
  check: DataQualityCheck | null
  onOpenRequest: (requestId: string) => void
}) {
  if (!check) {
    return <div className="quality-detail empty-state">Select a failed check</div>
  }

  const impactedRequestIds = extractRequestIds(check)

  return (
    <div className="quality-detail">
      <div className="quality-detail-header">
        <div>
          <span className="detail-kicker">{check.target_table}</span>
          <h3>{formatStage(check.check_name)}</h3>
        </div>
        <span className={`quality-status ${check.severity.toLowerCase()}`}>
          {check.status} / {check.severity}
        </span>
      </div>

      <dl className="quality-meta-grid">
        <div>
          <dt>Failed rows</dt>
          <dd>{check.failed_row_count}</dd>
        </div>
        <div>
          <dt>Pipeline run</dt>
          <dd>{check.pipeline_run_id}</dd>
        </div>
      </dl>

      <p className="quality-message">{check.message}</p>

      <div className="quality-detail-section">
        <h4>Sample failed keys</h4>
        <ul className="quality-key-list">
          {check.sample_failed_keys.map((key) => (
            <li key={key}>{key}</li>
          ))}
        </ul>
      </div>

      <div className="quality-detail-section">
        <h4>Related requests</h4>
        {impactedRequestIds.length ? (
          <div className="quality-request-list">
            {impactedRequestIds.map((requestId) => (
              <button key={requestId} type="button" onClick={() => onOpenRequest(requestId)}>
                {requestId}
              </button>
            ))}
          </div>
        ) : (
          <p>No request id in the sampled failed keys</p>
        )}
      </div>
    </div>
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
  if (!requests.length) {
    return <div className="empty-state table-empty">No critical requests match the current filters</div>
  }

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

function MaintenanceQueue({
  requests,
  selectedRequestId,
  onSelect,
}: {
  requests: MaintenanceCriticalRequest[]
  selectedRequestId: string | null
  onSelect: (requestId: string) => void
}) {
  if (!requests.length) {
    return <div className="empty-state table-empty">No critical maintenance requests match the current filters</div>
  }

  return (
    <div className="table-scroll">
      <table className="ops-table">
        <thead>
          <tr>
            <th>Rank</th>
            <th>Request</th>
            <th>Equipment</th>
            <th>Stage</th>
            <th>Hours</th>
            <th>Score</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody>
          {requests.map((request) => (
            <tr
              key={request.maintenance_request_id}
              className={request.maintenance_request_id === selectedRequestId ? 'selected-row' : ''}
              onClick={() => onSelect(request.maintenance_request_id)}
            >
              <td>#{request.priority_rank}</td>
              <td>
                <button className="link-button" type="button">
                  <strong>{request.request_number}</strong>
                  <span>{request.request_title}</span>
                </button>
              </td>
              <td>
                <strong>{request.equipment_name}</strong>
                <span className="table-subtext">{request.line_name}</span>
              </td>
              <td>
                <span className="stage-pill">{formatStage(request.current_stage)}</span>
              </td>
              <td>{formatHours(request.hours_in_current_stage)}</td>
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
        <h4>Priority Score Breakdown</h4>
        <ScoreBreakdown request={detail.request} />
      </section>

      <section className="detail-section">
        <h4>Stage Lead Times</h4>
        <div className="lead-time-list">
          {detail.stage_lead_times.map((stage) => (
            <div key={`${stage.stage}-${stage.entered_at}`} className="lead-time-row">
              <span className="lead-time-stage">{formatStage(stage.stage)}</span>
              <div>
                <strong className={stage.is_bottleneck ? 'risk-text' : ''}>
                  {formatHours(stage.duration_hours)}
                </strong>
                <small>
                  Threshold {formatHours(stage.threshold_hours)}
                  {stage.is_bottleneck ? ` · Delay ${formatHours(stage.delay_hours)}` : ''}
                </small>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="detail-section">
        <h4>Timeline</h4>
        <ol className="timeline-list">
          {detail.timeline.map((event) => (
            <li key={event.event_id}>
              <span>{formatDateTime(event.occurred_at)}</span>
              <strong>{formatStage(event.stage)}</strong>
              <p>
                {formatStage(event.event_type)}
                <small>
                  {formatStage(event.event_status)} · {formatStage(event.actor_type)}
                  {event.reason_code ? ` · ${formatStage(event.reason_code)}` : ''}
                </small>
                {event.message ? <em>{event.message}</em> : null}
              </p>
            </li>
          ))}
        </ol>
      </section>

      <section className="detail-section split-section">
        <div>
          <h4>Related PO</h4>
          {detail.related_po ? (
            <dl className="record-facts">
              <div>
                <dt>PO</dt>
                <dd>{detail.related_po.po_number}</dd>
              </div>
              <div>
                <dt>Vendor</dt>
                <dd>{detail.related_po.vendor_name}</dd>
              </div>
              <div>
                <dt>Status</dt>
                <dd>{formatStage(detail.related_po.po_status)}</dd>
              </div>
              <div>
                <dt>Expected</dt>
                <dd>{formatDate(detail.related_po.expected_delivery_date)}</dd>
              </div>
              <div>
                <dt>Actual</dt>
                <dd>{formatDate(detail.related_po.actual_delivery_date)}</dd>
              </div>
            </dl>
          ) : (
            <p>No purchase order yet</p>
          )}
        </div>
        <div>
          <h4>Receipt</h4>
          {detail.receipt ? (
            <dl className="record-facts">
              <div>
                <dt>Receipt</dt>
                <dd>{detail.receipt.receipt_id}</dd>
              </div>
              <div>
                <dt>Received</dt>
                <dd>{formatDateTimeNullable(detail.receipt.received_at)}</dd>
              </div>
              <div>
                <dt>Inspection</dt>
                <dd>{formatStage(detail.receipt.inspection_status)}</dd>
              </div>
              <div>
                <dt>Completed</dt>
                <dd>{formatDateTimeNullable(detail.receipt.inspection_completed_at)}</dd>
              </div>
            </dl>
          ) : (
            <p>No receipt yet</p>
          )}
        </div>
      </section>

      {detail.quality_flags.length ? (
        <section className="detail-section quality-flags">
          <h4>Quality Flags</h4>
          <ul>
            {detail.quality_flags.map((flag) => (
              <li key={flag}>
                <AlertTriangle size={14} aria-hidden="true" />
                <span>{flag}</span>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  )
}

function MaintenanceDetailPanel({
  detail,
  loading,
}: {
  detail: MaintenanceRequestDetail | null
  loading: boolean
}) {
  if (loading) {
    return <div className="loading-inline">Loading maintenance detail</div>
  }

  if (!detail) {
    return <div className="empty-state">Select a maintenance request from the queue</div>
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
        <span>{detail.request.equipment_name}</span>
        <span>{detail.request.line_name}</span>
        <span>{formatStage(detail.request.current_stage)}</span>
        <span>{delayedStageCount} delayed stages</span>
      </div>

      <section className="detail-section">
        <h4>Recommended Action</h4>
        <p>{detail.request.recommended_action}</p>
        <small>{detail.request.reason_summary}</small>
      </section>

      <section className="detail-section">
        <h4>Priority Score Breakdown</h4>
        <MaintenanceScoreBreakdown request={detail.request} />
      </section>

      <section className="detail-section">
        <h4>Stage Lead Times</h4>
        <div className="lead-time-list">
          {detail.stage_lead_times.map((stage) => (
            <div key={`${stage.stage}-${stage.entered_at}`} className="lead-time-row">
              <span className="lead-time-stage">{formatStage(stage.stage)}</span>
              <div>
                <strong className={stage.is_bottleneck ? 'risk-text' : ''}>
                  {formatHours(stage.duration_hours)}
                </strong>
                <small>
                  Threshold {formatHours(stage.threshold_hours)}
                  {stage.is_bottleneck ? ` · Delay ${formatHours(stage.delay_hours)}` : ''}
                </small>
              </div>
            </div>
          ))}
        </div>
      </section>

      <section className="detail-section">
        <h4>Timeline</h4>
        <TimelineList events={detail.timeline} />
      </section>

      <section className="detail-section">
        <h4>Work Orders and Parts</h4>
        <div className="mini-card-grid">
          {detail.work_orders.map((workOrder) => (
            <dl key={workOrder.work_order_id} className="record-facts mini-card">
              <div>
                <dt>Work order</dt>
                <dd>{workOrder.work_order_id}</dd>
              </div>
              <div>
                <dt>Team</dt>
                <dd>{workOrder.assigned_team}</dd>
              </div>
              <div>
                <dt>Status</dt>
                <dd>{formatStage(workOrder.work_order_status)}</dd>
              </div>
              <div>
                <dt>Part</dt>
                <dd>{workOrder.required_part_name ?? workOrder.required_part_id ?? 'Not set'}</dd>
              </div>
              <div>
                <dt>Stock</dt>
                <dd>{formatStage(workOrder.stock_status)}</dd>
              </div>
            </dl>
          ))}
        </div>
      </section>

      <section className="detail-section split-section">
        <div>
          <h4>Inspection</h4>
          {detail.inspection_results.length ? (
            <dl className="record-facts">
              <div>
                <dt>Status</dt>
                <dd>{formatStage(detail.inspection_results[0].inspection_status)}</dd>
              </div>
              <div>
                <dt>Inspector</dt>
                <dd>{detail.inspection_results[0].inspector_id ?? 'Not assigned'}</dd>
              </div>
              <div>
                <dt>Started</dt>
                <dd>{formatDateTimeNullable(detail.inspection_results[0].inspection_started_at)}</dd>
              </div>
              <div>
                <dt>Completed</dt>
                <dd>{formatDateTimeNullable(detail.inspection_results[0].inspection_completed_at)}</dd>
              </div>
            </dl>
          ) : (
            <p>No inspection result yet</p>
          )}
        </div>
        <div>
          <h4>Sensor Alerts</h4>
          {detail.sensor_alerts.length ? (
            <dl className="record-facts">
              <div>
                <dt>Type</dt>
                <dd>{formatStage(detail.sensor_alerts[0].alert_type)}</dd>
              </div>
              <div>
                <dt>Severity</dt>
                <dd>{formatStage(detail.sensor_alerts[0].severity)}</dd>
              </div>
              <div>
                <dt>Triggered</dt>
                <dd>{formatDateTime(detail.sensor_alerts[0].triggered_at)}</dd>
              </div>
              <div>
                <dt>Resolved</dt>
                <dd>{formatDateTimeNullable(detail.sensor_alerts[0].resolved_at)}</dd>
              </div>
            </dl>
          ) : (
            <p>No linked sensor alert</p>
          )}
        </div>
      </section>

      {detail.quality_flags.length ? (
        <section className="detail-section quality-flags">
          <h4>Quality Flags</h4>
          <ul>
            {detail.quality_flags.map((flag) => (
              <li key={flag}>
                <AlertTriangle size={14} aria-hidden="true" />
                <span>{flag}</span>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  )
}

function TimelineList({ events }: { events: MaintenanceRequestDetail['timeline'] | RequestDetail['timeline'] }) {
  return (
    <ol className="timeline-list">
      {events.map((event) => (
        <li key={event.event_id}>
          <span>{formatDateTime(event.occurred_at)}</span>
          <strong>{formatStage(event.stage)}</strong>
          <p>
            {formatStage(event.event_type)}
            <small>
              {formatStage(event.event_status)} · {formatStage(event.actor_type)}
              {event.reason_code ? ` · ${formatStage(event.reason_code)}` : ''}
            </small>
            {event.message ? <em>{event.message}</em> : null}
          </p>
        </li>
      ))}
    </ol>
  )
}

function ScoreBreakdown({ request }: { request: CriticalRequest }) {
  const components = [
    { label: 'Criticality', value: request.criticality_score },
    { label: 'Delay', value: request.delay_score },
    { label: 'Business impact', value: request.business_impact_score },
    { label: 'Needed by urgency', value: request.needed_by_urgency_score },
    { label: 'Vendor risk', value: request.vendor_risk_score },
  ]

  return (
    <div className="score-breakdown">
      {components.map((component) => (
        <div key={component.label} className="score-component">
          <span>{component.label}</span>
          <strong>{component.value.toFixed(0)}</strong>
        </div>
      ))}
      <div className="score-component total">
        <span>Total</span>
        <strong>{request.total_priority_score.toFixed(0)}</strong>
      </div>
    </div>
  )
}

function MaintenanceScoreBreakdown({ request }: { request: MaintenanceCriticalRequest }) {
  const components = [
    { label: 'Equipment', value: request.equipment_criticality_score },
    { label: 'Downtime', value: request.downtime_score },
    { label: 'Delay', value: request.stage_delay_score },
    { label: 'Line impact', value: request.production_line_impact_score },
    { label: 'Urgency', value: request.needed_by_urgency_score },
    { label: 'Repeat', value: request.repeat_failure_score },
    { label: 'Parts', value: request.parts_risk_score },
  ]

  return (
    <div className="score-breakdown">
      {components.map((component) => (
        <div key={component.label} className="score-component">
          <span>{component.label}</span>
          <strong>{component.value.toFixed(0)}</strong>
        </div>
      ))}
      <div className="score-component total">
        <span>Total</span>
        <strong>{request.total_priority_score.toFixed(0)}</strong>
      </div>
    </div>
  )
}

function VendorTable({ vendors }: { vendors: DashboardData['vendorBottlenecks'] }) {
  if (!vendors.length) {
    return <div className="empty-state table-empty">No vendor delay patterns match the current filters</div>
  }

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

function PartsWaitingPanel({ parts }: { parts: PartsWaiting[] }) {
  if (!parts.length) {
    return <div className="empty-state table-empty">No parts-waiting delays match the current filters</div>
  }

  return (
    <div className="table-scroll">
      <table className="ops-table compact-table">
        <thead>
          <tr>
            <th>Part</th>
            <th>Category</th>
            <th>Stock</th>
            <th>Requests</th>
            <th>Wait</th>
          </tr>
        </thead>
        <tbody>
          {parts.map((part) => (
            <tr key={part.part_id}>
              <td>
                <strong>{part.part_name}</strong>
                <span className="table-subtext">{part.part_id}</span>
              </td>
              <td>{formatStage(part.part_category)}</td>
              <td>{formatStage(part.stock_status)}</td>
              <td>{part.waiting_request_count}</td>
              <td>{formatHours(part.total_wait_hours)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function EquipmentDelayTable({ equipment }: { equipment: MaintenanceDashboardData['equipmentDelays'] }) {
  if (!equipment.length) {
    return <div className="empty-state table-empty">No equipment delay patterns match the current filters</div>
  }

  return (
    <div className="table-scroll">
      <table className="ops-table compact-table">
        <thead>
          <tr>
            <th>Equipment</th>
            <th>Line</th>
            <th>Requests</th>
            <th>Delayed</th>
            <th>Repeat</th>
            <th>Downtime</th>
            <th>Failure</th>
          </tr>
        </thead>
        <tbody>
          {equipment.map((item) => (
            <tr key={item.equipment_id}>
              <td>
                <strong>{item.equipment_name}</strong>
                <span className="table-subtext">{item.equipment_id}</span>
              </td>
              <td>{item.line_name}</td>
              <td>{item.request_count}</td>
              <td>{item.delayed_request_count}</td>
              <td>{item.repeat_failure_count}</td>
              <td>{formatHours(item.total_downtime_hours)}</td>
              <td>{formatStage(item.top_failure_mode)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function LineDelayTable({ lines }: { lines: ProductionLineDelay[] }) {
  if (!lines.length) {
    return <div className="empty-state table-empty">No line delay patterns match the current filters</div>
  }

  return (
    <div className="table-scroll">
      <table className="ops-table compact-table">
        <thead>
          <tr>
            <th>Line</th>
            <th>Open</th>
            <th>Delayed</th>
            <th>Critical</th>
            <th>Downtime</th>
            <th>Bottleneck</th>
          </tr>
        </thead>
        <tbody>
          {lines.map((line) => (
            <tr key={line.line_id}>
              <td>
                <strong>{line.line_name}</strong>
                <span className="table-subtext">{line.line_id}</span>
              </td>
              <td>{line.open_request_count}</td>
              <td>{line.delayed_request_count}</td>
              <td>{line.critical_equipment_delayed_count}</td>
              <td>{formatHours(line.total_downtime_hours)}</td>
              <td>{formatStage(line.top_bottleneck_stage)}</td>
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

function extractRequestIds(check: DataQualityCheck) {
  const matches = check.sample_failed_keys.flatMap((key) => key.match(/REQ-\d{4}/g) ?? [])
  return Array.from(new Set(matches))
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

function formatDate(value: string | null) {
  if (!value) {
    return 'Not set'
  }
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  }).format(new Date(value))
}

function formatDateTime(value: string) {
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

function formatDateTimeNullable(value: string | null) {
  return value ? formatDateTime(value) : 'Not set'
}

export default App
