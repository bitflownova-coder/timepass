import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from 'recharts';
import {
  Brain, AlertTriangle, FileCode, Network, CircleDot, Trash2, Filter, RefreshCw,
  ChevronRight, ChevronDown,
} from 'lucide-react';
import { Card, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { RiskGauge } from '@/components/ui/RiskGauge';
import { LoadingState, ErrorState, EmptyState } from '@/components/ui/States';
import * as engine from '@/api/engineClient';
import { cn, getSeverityColor, getRiskColor } from '@/lib/utils';
import type { DriftEvent, EntityInfo } from '@/api/types';
import { useWorkspace } from '@/contexts/WorkspaceContext';

type Tab = 'risk' | 'drifts' | 'entities' | 'graph' | 'circular' | 'deadcode';

export default function AIIntelligence() {
  const [activeTab, setActiveTab] = useState<Tab>('risk');
  const [entityFilter, setEntityFilter] = useState<string>('');
  const [expandedEntity, setExpandedEntity] = useState<string | null>(null);

  const tabs: { id: Tab; label: string; icon: React.ElementType; badge?: string }[] = [
    { id: 'risk', label: 'Risk Breakdown', icon: Brain },
    { id: 'drifts', label: 'Drift Events', icon: AlertTriangle },
    { id: 'entities', label: 'Entity Explorer', icon: FileCode },
    { id: 'graph', label: 'Dependency Graph', icon: Network },
    { id: 'circular', label: 'Circular Deps', icon: CircleDot },
    { id: 'deadcode', label: 'Dead Code', icon: Trash2 },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-3">
          <Brain className="w-7 h-7 text-accent-purple" />
          AI Intelligence
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Autonomous code analysis, drift detection, and dependency intelligence
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="flex items-center gap-1 bg-surface-2 border border-surface-4 rounded-xl p-1">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all',
                activeTab === tab.id
                  ? 'bg-brand-600/20 text-brand-400'
                  : 'text-gray-500 hover:text-gray-300 hover:bg-surface-3'
              )}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* Tab Content */}
      <div className="page-enter">
        {activeTab === 'risk' && <RiskBreakdownPanel />}
        {activeTab === 'drifts' && <DriftEventsPanel />}
        {activeTab === 'entities' && (
          <EntityExplorerPanel filter={entityFilter} onFilterChange={setEntityFilter} />
        )}
        {activeTab === 'graph' && <DependencyGraphPanel />}
        {activeTab === 'circular' && <CircularDepsPanel />}
        {activeTab === 'deadcode' && <DeadCodePanel />}
      </div>
    </div>
  );
}

// ===== Risk Breakdown Panel =====
function RiskBreakdownPanel() {
  const { workspace: WORKSPACE } = useWorkspace();
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['autonomous-dashboard', WORKSPACE],
    queryFn: () => engine.getAutonomousDashboard(WORKSPACE),
    refetchInterval: 30_000,
  });

  if (isLoading) return <LoadingState message="Computing risk scores..." />;
  if (error) return <ErrorState message="Failed to fetch risk data" onRetry={refetch} />;

  const health = data?.health;
  if (!health) return <EmptyState message="No risk data available. Initialize workspace first." />;

  const categories = health.categories;
  const chartData = Object.entries(categories).map(([key, val]) => ({
    name: key.charAt(0).toUpperCase() + key.slice(1),
    score: val.score,
    issues: val.issues?.length ?? 0,
  }));

  const getBarColor = (score: number) => {
    if (score <= 2) return '#10b981';
    if (score <= 4) return '#3b82f6';
    if (score <= 6) return '#f59e0b';
    if (score <= 8) return '#f97316';
    return '#ef4444';
  };

  return (
    <div className="grid grid-cols-12 gap-5">
      {/* Left: Overall Gauge */}
      <Card className="col-span-3 flex flex-col items-center justify-center gap-4">
        <RiskGauge score={health.overall_score} size="lg" />
        <div className="text-center">
          <p className="text-xs text-gray-500">Health Level</p>
          <p className={cn('text-sm font-bold', getRiskColor(health.overall_score))}>
            {health.health_level}
          </p>
        </div>
      </Card>

      {/* Right: Category Breakdown */}
      <Card className="col-span-9">
        <CardHeader>
          <CardTitle>Risk Categories</CardTitle>
          <Badge variant="info">7 categories analyzed</Badge>
        </CardHeader>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={chartData} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="#1a1a24" horizontal={false} />
            <XAxis type="number" domain={[0, 10]} stroke="#38384a" tick={{ fontSize: 10, fill: '#666' }} />
            <YAxis
              dataKey="name"
              type="category"
              width={80}
              stroke="#38384a"
              tick={{ fontSize: 11, fill: '#9ca3af' }}
            />
            <Tooltip
              contentStyle={{ backgroundColor: '#1a1a24', border: '1px solid #38384a', borderRadius: 8, fontSize: 12 }}
            />
            <Bar dataKey="score" radius={[0, 4, 4, 0]} barSize={20}>
              {chartData.map((entry, i) => (
                <Cell key={i} fill={getBarColor(entry.score)} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>

        {/* Category details */}
        <div className="grid grid-cols-4 gap-3 mt-4">
          {Object.entries(categories).map(([key, val]) => (
            <div key={key} className="bg-surface-3/50 rounded-lg p-3">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-medium text-gray-400 capitalize">{key}</span>
                <span className={cn('text-xs font-bold', getRiskColor(val.score))}>
                  {val.score.toFixed(1)}
                </span>
              </div>
              <div className="w-full bg-surface-4 rounded-full h-1.5">
                <div
                  className="h-1.5 rounded-full transition-all duration-500"
                  style={{ width: `${(val.score / 10) * 100}%`, backgroundColor: getBarColor(val.score) }}
                />
              </div>
              {val.issues && val.issues.length > 0 && (
                <p className="text-[10px] text-gray-600 mt-1.5 truncate" title={val.issues[0]}>
                  {val.issues[0]}
                </p>
              )}
            </div>
          ))}
        </div>
      </Card>
    </div>
  );

}

// ===== Drift Events Panel =====
function DriftEventsPanel() {
  const { workspace: WORKSPACE } = useWorkspace();
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');
  
  const { data: drifts, isLoading, error, refetch } = useQuery({
    queryKey: ['drifts', WORKSPACE],
    queryFn: () => engine.getDrifts(WORKSPACE),
  });

  if (isLoading) return <LoadingState message="Loading drift events..." />;
  if (error) return <ErrorState message="Failed to fetch drifts" onRetry={refetch} />;

  const filtered = severityFilter === 'ALL'
    ? drifts ?? []
    : (drifts ?? []).filter((d) => d.severity === severityFilter);

  const severityCounts = {
    ALL: drifts?.length ?? 0,
    CRITICAL: drifts?.filter((d) => d.severity === 'CRITICAL').length ?? 0,
    HIGH: drifts?.filter((d) => d.severity === 'HIGH').length ?? 0,
    MEDIUM: drifts?.filter((d) => d.severity === 'MEDIUM').length ?? 0,
    LOW: drifts?.filter((d) => d.severity === 'LOW').length ?? 0,
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 text-accent-amber" />
          Drift Events ({drifts?.length ?? 0} unresolved)
        </CardTitle>
        <div className="flex items-center gap-1">
          {Object.entries(severityCounts).map(([key, count]) => (
            <button
              key={key}
              onClick={() => setSeverityFilter(key)}
              className={cn(
                'px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors',
                severityFilter === key
                  ? 'bg-brand-600/20 text-brand-400'
                  : 'text-gray-600 hover:text-gray-400'
              )}
            >
              {key} ({count})
            </button>
          ))}
        </div>
      </CardHeader>

      {filtered.length > 0 ? (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-[11px] text-gray-600 uppercase tracking-wider border-b border-surface-4">
                <th className="pb-2 pr-4">Severity</th>
                <th className="pb-2 pr-4">File</th>
                <th className="pb-2 pr-4">Entity</th>
                <th className="pb-2 pr-4">Type</th>
                <th className="pb-2 pr-4">Old → New</th>
                <th className="pb-2">Time</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((drift) => (
                <tr key={drift.id} className="border-b border-surface-3/50 hover:bg-surface-3/30 transition-colors">
                  <td className="py-2.5 pr-4">
                    <span className={cn('text-[11px] font-semibold px-2 py-0.5 rounded', getSeverityColor(drift.severity))}>
                      {drift.severity}
                    </span>
                  </td>
                  <td className="py-2.5 pr-4 font-mono text-xs text-gray-400 max-w-[200px] truncate">
                    {drift.file_path.split(/[/\\]/).slice(-2).join('/')}
                  </td>
                  <td className="py-2.5 pr-4 text-xs text-gray-300 font-medium">{drift.entity_name}</td>
                  <td className="py-2.5 pr-4 text-xs text-gray-500">{drift.drift_type}</td>
                  <td className="py-2.5 pr-4 text-xs">
                    {drift.old_value && (
                      <span className="text-accent-red line-through mr-1">{truncate(drift.old_value, 20)}</span>
                    )}
                    {drift.new_value && (
                      <span className="text-accent-green">{truncate(drift.new_value, 20)}</span>
                    )}
                  </td>
                  <td className="py-2.5 text-xs text-gray-600">
                    {new Date(drift.timestamp).toLocaleDateString('en-IN', { day: '2-digit', month: 'short' })}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <EmptyState message="No drift events matching filter." />
      )}
    </Card>
  );
}

function truncate(str: string, len: number) {
  return str.length > len ? str.slice(0, len) + '…' : str;
}

// ===== Entity Explorer Panel =====
function EntityExplorerPanel({ filter, onFilterChange }: { filter: string; onFilterChange: (v: string) => void }) {
  const { workspace: WORKSPACE } = useWorkspace();
  const [selectedType, setSelectedType] = useState<string>('');
  
  const { data: entities, isLoading, error, refetch } = useQuery({
    queryKey: ['entities', WORKSPACE, selectedType],
    queryFn: () => engine.getEntities(WORKSPACE, selectedType || undefined),
  });

  const entityTypes = ['', 'class', 'function', 'route', 'model', 'interface', 'enum'];

  if (isLoading) return <LoadingState message="Indexing entities..." />;
  if (error) return <ErrorState message="Failed to fetch entities" onRetry={refetch} />;

  // Group by file
  const byFile = (entities ?? []).reduce<Record<string, EntityInfo[]>>((acc, e) => {
    const file = e.file_path.split(/[/\\]/).slice(-2).join('/');
    (acc[file] = acc[file] || []).push(e);
    return acc;
  }, {});

  const filteredFiles = Object.entries(byFile).filter(([file, ents]) => {
    if (!filter) return true;
    const q = filter.toLowerCase();
    return file.toLowerCase().includes(q) || ents.some((e) => e.entity_name.toLowerCase().includes(q));
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileCode className="w-4 h-4 text-brand-400" />
          Entity Explorer ({entities?.length ?? 0} entities)
        </CardTitle>
        <div className="flex items-center gap-2">
          <select
            value={selectedType}
            onChange={(e) => setSelectedType(e.target.value)}
            className="bg-surface-3 border border-surface-4 rounded-lg px-2.5 py-1.5 text-xs text-gray-300 focus:outline-none focus:border-brand-500"
          >
            {entityTypes.map((t) => (
              <option key={t} value={t}>{t || 'All Types'}</option>
            ))}
          </select>
          <div className="relative">
            <Filter className="w-3.5 h-3.5 absolute left-2.5 top-1/2 -translate-y-1/2 text-gray-600" />
            <input
              type="text"
              value={filter}
              onChange={(e) => onFilterChange(e.target.value)}
              placeholder="Search entities..."
              className="bg-surface-3 border border-surface-4 rounded-lg pl-8 pr-3 py-1.5 text-xs text-gray-300 w-48 focus:outline-none focus:border-brand-500"
            />
          </div>
        </div>
      </CardHeader>

      <div className="max-h-[500px] overflow-y-auto space-y-1">
        {filteredFiles.map(([file, ents]) => (
          <FileEntityGroup key={file} file={file} entities={ents} />
        ))}
        {filteredFiles.length === 0 && <EmptyState message="No entities found." />}
      </div>
    </Card>
  );
}

function FileEntityGroup({ file, entities }: { file: string; entities: EntityInfo[] }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="border border-surface-4/50 rounded-lg overflow-hidden">
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full flex items-center gap-2 px-3 py-2 hover:bg-surface-3/50 transition-colors"
      >
        {expanded ? (
          <ChevronDown className="w-3.5 h-3.5 text-gray-600" />
        ) : (
          <ChevronRight className="w-3.5 h-3.5 text-gray-600" />
        )}
        <span className="text-xs font-mono text-gray-400 flex-1 text-left truncate">{file}</span>
        <Badge variant="default">{entities.length}</Badge>
      </button>
      {expanded && (
        <div className="border-t border-surface-4/50 bg-surface-3/20">
          {entities.map((ent) => (
            <div key={ent.id} className="flex items-center gap-3 px-6 py-1.5 text-xs hover:bg-surface-3/30">
              <Badge
                variant={
                  ent.entity_type === 'class' ? 'purple' :
                  ent.entity_type === 'function' ? 'info' :
                  ent.entity_type === 'route' ? 'success' :
                  'default'
                }
              >
                {ent.entity_type}
              </Badge>
              <span className="text-gray-300 font-medium font-mono">{ent.entity_name}</span>
              <span className="text-gray-600 ml-auto">L{ent.line_start}-{ent.line_end}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ===== Dependency Graph Panel =====
function DependencyGraphPanel() {
  const { data: graphStats, isLoading, error, refetch } = useQuery({
    queryKey: ['graph-stats'],
    queryFn: () => engine.getGraphStats(),
  });

  if (isLoading) return <LoadingState message="Building dependency graph..." />;
  if (error) return <ErrorState message="Failed to build graph" onRetry={refetch} />;

  return (
    <div className="grid grid-cols-12 gap-5">
      {/* Stats */}
      <Card className="col-span-4">
        <CardTitle className="mb-4">Graph Statistics</CardTitle>
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-xs text-gray-500">Total Files</span>
            <span className="text-lg font-bold text-white">{graphStats?.total_files ?? 0}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-xs text-gray-500">File Edges</span>
            <span className="text-lg font-bold text-brand-400">{graphStats?.file_edges ?? 0}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-xs text-gray-500">Entity Edges</span>
            <span className="text-lg font-bold text-accent-purple">{graphStats?.entity_edges ?? 0}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-xs text-gray-500">Circular Dependencies</span>
            <span className="text-lg font-bold text-accent-amber">{graphStats?.circular_count ?? 0}</span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-xs text-gray-500">Dead Code Files</span>
            <span className="text-lg font-bold text-accent-red">{graphStats?.dead_code_files?.length ?? 0}</span>
          </div>
        </div>
      </Card>

      {/* Most Depended Files */}
      <Card className="col-span-8">
        <CardHeader>
          <CardTitle>Most Depended-On Files</CardTitle>
          <Badge variant="info">Top 10 hotspots</Badge>
        </CardHeader>
        {graphStats?.most_depended && graphStats.most_depended.length > 0 ? (
          <div className="space-y-2">
            {graphStats.most_depended.map((item, i) => (
              <div key={i} className="flex items-center gap-3">
                <span className="text-xs text-gray-600 w-6 text-right">#{i + 1}</span>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-mono text-gray-400 truncate max-w-[300px]">
                      {item.file.split(/[/\\]/).slice(-2).join('/')}
                    </span>
                    <span className="text-xs font-bold text-brand-400">{item.dependents} deps</span>
                  </div>
                  <div className="w-full bg-surface-4 rounded-full h-1.5">
                    <div
                      className="h-1.5 rounded-full bg-brand-500 transition-all"
                      style={{ width: `${Math.min(100, (item.dependents / (graphStats.most_depended[0]?.dependents || 1)) * 100)}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState message="No dependency data. Build the graph first." />
        )}
      </Card>
    </div>
  );
}

// ===== Circular Dependencies Panel =====
function CircularDepsPanel() {
  const { data: cycles, isLoading, error, refetch } = useQuery({
    queryKey: ['circular-deps'],
    queryFn: () => engine.getCircularDeps(),
  });

  if (isLoading) return <LoadingState message="Detecting circular dependencies..." />;
  if (error) return <ErrorState message="Failed to detect cycles" onRetry={refetch} />;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CircleDot className="w-4 h-4 text-accent-amber" />
          Circular Dependencies ({cycles?.length ?? 0} cycles)
        </CardTitle>
      </CardHeader>
      {cycles && cycles.length > 0 ? (
        <div className="space-y-3">
          {cycles.map((cycle, i) => (
            <div key={i} className="bg-surface-3/50 border border-accent-amber/20 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-2">
                <Badge variant="warning">Cycle #{i + 1}</Badge>
                <span className="text-[11px] text-gray-500">{cycle.length} files in cycle</span>
              </div>
              <div className="flex items-center gap-1 flex-wrap">
                {cycle.map((file, j) => (
                  <React.Fragment key={j}>
                    <span className="text-xs font-mono text-gray-400 bg-surface-4 px-2 py-0.5 rounded">
                      {file.split(/[/\\]/).pop()}
                    </span>
                    {j < cycle.length - 1 && <span className="text-accent-amber text-xs">→</span>}
                  </React.Fragment>
                ))}
                <span className="text-accent-amber text-xs">↩</span>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState message="No circular dependencies detected. Clean architecture!" />
      )}
    </Card>
  );
}

// ===== Dead Code Panel =====
function DeadCodePanel() {
  const { data: files, isLoading, error, refetch } = useQuery({
    queryKey: ['dead-code'],
    queryFn: () => engine.getDeadCode(),
  });

  if (isLoading) return <LoadingState message="Scanning for dead code..." />;
  if (error) return <ErrorState message="Failed to detect dead code" onRetry={refetch} />;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Trash2 className="w-4 h-4 text-accent-red" />
          Dead Code Files ({files?.length ?? 0})
        </CardTitle>
        <p className="text-[11px] text-gray-600">Files with no inbound dependencies</p>
      </CardHeader>
      {files && files.length > 0 ? (
        <div className="grid grid-cols-2 gap-2">
          {files.map((file, i) => (
            <div
              key={i}
              className="flex items-center gap-2 bg-surface-3/30 border border-surface-4/50 rounded-lg px-3 py-2 hover:border-accent-red/30 transition-colors"
            >
              <FileCode className="w-3.5 h-3.5 text-gray-600 flex-shrink-0" />
              <span className="text-xs font-mono text-gray-400 truncate">
                {file.split(/[/\\]/).slice(-3).join('/')}
              </span>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState message="No dead code detected!" />
      )}
    </Card>
  );
}
