import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell, Treemap,
} from 'recharts';
import {
  Briefcase, FileCode, BarChart3, Heart, RefreshCw, FolderOpen,
  Code, TrendingUp, ArrowRight, Shield, AlertTriangle, GitBranch,
  CheckCircle, XCircle, Activity, Layers, Scale,
} from 'lucide-react';
import { Card, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { LoadingState, ErrorState, EmptyState } from '@/components/ui/States';
import { useWorkspace } from '@/contexts/WorkspaceContext';
import * as engine from '@/api/engineClient';
import type { WorkspaceSummary, ProjectHealth, LanguageStat } from '@/api/types';
import { cn } from '@/lib/utils';

type Tab = 'overview' | 'languages' | 'health' | 'files';

const LANG_COLORS: Record<string, string> = {
  Kotlin: '#A97BFF', TypeScript: '#3178C6', Python: '#3572A5', JavaScript: '#F1E05A',
  Java: '#B07219', HTML: '#E34C26', CSS: '#563D7C', SCSS: '#C6538C',
  JSON: '#6B7280', YAML: '#CB171E', Markdown: '#083FA1', Shell: '#89E051',
  SQL: '#E38C00', Go: '#00ADD8', Rust: '#DEA584', 'C++': '#F34B7D',
  C: '#555555', 'C#': '#178600', Gradle: '#02303A', Batch: '#C1F12E',
  Config: '#6B7280', Other: '#4B5563',
};

function formatBytes(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

function formatNumber(n: number): string {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + 'M';
  if (n >= 1_000) return (n / 1_000).toFixed(1) + 'K';
  return n.toString();
}

export default function Business() {
  const { workspace, workspaces } = useWorkspace();
  const [activeTab, setActiveTab] = useState<Tab>('overview');

  const tabs: { id: Tab; label: string; icon: React.ElementType }[] = [
    { id: 'overview', label: 'Overview', icon: BarChart3 },
    { id: 'languages', label: 'Languages', icon: Code },
    { id: 'health', label: 'Project Health', icon: Heart },
    { id: 'files', label: 'Largest Files', icon: FileCode },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-3">
          <Briefcase className="w-7 h-7 text-accent-purple" />
          Business Intelligence
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Workspace analytics, language breakdown, and project health scoring
        </p>
      </div>

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
                  ? 'bg-accent-purple/20 text-accent-purple'
                  : 'text-gray-500 hover:text-gray-300 hover:bg-surface-3'
              )}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      <div className="page-enter">
        {activeTab === 'overview' && <OverviewPanel />}
        {activeTab === 'languages' && <LanguagesPanel />}
        {activeTab === 'health' && <HealthPanel />}
        {activeTab === 'files' && <FilesPanel />}
      </div>
    </div>
  );
}

// ===== Overview Panel =====
function OverviewPanel() {
  const { workspace } = useWorkspace();

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['workspace-summary', workspace],
    queryFn: () => engine.getWorkspaceSummary(workspace),
  });

  const { data: health } = useQuery({
    queryKey: ['project-health', workspace],
    queryFn: () => engine.getProjectHealth(workspace),
  });

  if (isLoading) return <LoadingState message="Analyzing workspace..." />;
  if (error) return <ErrorState message="Failed to analyze workspace" onRetry={refetch} />;
  if (!data) return <EmptyState message="No data" />;

  const topLangs = data.languages.slice(0, 8);
  const healthScore = health?.score ?? 0;
  const healthLevel = health?.health_level ?? 'UNKNOWN';

  const healthColor =
    healthScore >= 90 ? 'text-accent-green' :
    healthScore >= 70 ? 'text-brand-400' :
    healthScore >= 50 ? 'text-accent-amber' :
    'text-accent-red';

  return (
    <div className="space-y-5">
      {/* Stat cards */}
      <div className="grid grid-cols-5 gap-4">
        <StatBox icon={FileCode} label="Files" value={formatNumber(data.total_files)} color="text-brand-400" />
        <StatBox icon={Code} label="Lines of Code" value={formatNumber(data.total_lines)} color="text-accent-green" />
        <StatBox icon={FolderOpen} label="Directories" value={data.directories.toString()} color="text-accent-amber" />
        <StatBox icon={Layers} label="Languages" value={data.languages.length.toString()} color="text-accent-purple" />
        <StatBox icon={Heart} label="Health" value={`${healthScore}/100`} color={healthColor} />
      </div>

      {/* Language breakdown chart */}
      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-7">
          <Card>
            <CardHeader>
              <CardTitle>Lines by Language</CardTitle>
              <span className="text-xs text-gray-500">{data.analysis_time_seconds}s scan</span>
            </CardHeader>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={topLangs} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e1e2e" />
                <XAxis dataKey="language" tick={{ fill: '#9ca3af', fontSize: 10 }} stroke="#38384a" />
                <YAxis tick={{ fill: '#6b7280', fontSize: 10 }} stroke="#38384a" tickFormatter={formatNumber} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #2e2e46', borderRadius: 8, fontSize: 12 }}
                  formatter={(val: number) => [formatNumber(val), 'Lines']}
                />
                <Bar dataKey="lines" radius={[4, 4, 0, 0]}>
                  {topLangs.map((entry, i) => (
                    <Cell key={i} fill={LANG_COLORS[entry.language] || LANG_COLORS.Other} fillOpacity={0.85} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </div>

        <div className="col-span-5">
          <Card>
            <CardHeader>
              <CardTitle>Language Distribution</CardTitle>
            </CardHeader>
            <div className="flex items-center gap-4">
              <ResponsiveContainer width={140} height={140}>
                <PieChart>
                  <Pie
                    data={topLangs}
                    dataKey="files"
                    nameKey="language"
                    cx="50%"
                    cy="50%"
                    innerRadius={35}
                    outerRadius={65}
                    strokeWidth={0}
                  >
                    {topLangs.map((entry, i) => (
                      <Cell key={i} fill={LANG_COLORS[entry.language] || LANG_COLORS.Other} />
                    ))}
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
              <div className="space-y-1 flex-1">
                {topLangs.slice(0, 8).map((l) => (
                  <div key={l.language} className="flex items-center gap-2 text-xs">
                    <span className="w-2.5 h-2.5 rounded-sm flex-shrink-0" style={{ backgroundColor: LANG_COLORS[l.language] || LANG_COLORS.Other }} />
                    <span className="text-gray-400 flex-1 truncate">{l.language}</span>
                    <span className="text-gray-500">{l.files}</span>
                  </div>
                ))}
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}

// ===== Languages Deep Dive =====
function LanguagesPanel() {
  const { workspace } = useWorkspace();

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['workspace-summary', workspace],
    queryFn: () => engine.getWorkspaceSummary(workspace),
  });

  if (isLoading) return <LoadingState message="Scanning languages..." />;
  if (error) return <ErrorState message="Failed to load data" onRetry={refetch} />;
  if (!data) return <EmptyState message="No data" />;

  return (
    <Card>
      <CardHeader>
        <CardTitle>All Languages</CardTitle>
        <Badge variant="info">{data.languages.length} detected</Badge>
      </CardHeader>
      <div className="overflow-auto">
        <table className="w-full text-xs">
          <thead>
            <tr className="text-gray-600 border-b border-surface-4">
              <th className="text-left py-2 px-3 font-medium">Language</th>
              <th className="text-right py-2 px-3 font-medium">Files</th>
              <th className="text-right py-2 px-3 font-medium">Lines</th>
              <th className="text-right py-2 px-3 font-medium">Size</th>
              <th className="text-left py-2 px-3 font-medium w-1/3">Share</th>
            </tr>
          </thead>
          <tbody>
            {data.languages.map((lang) => {
              const pct = data.total_lines > 0 ? (lang.lines / data.total_lines * 100) : 0;
              return (
                <tr key={lang.language} className="border-b border-surface-4/30 hover:bg-surface-3/30">
                  <td className="py-2 px-3">
                    <div className="flex items-center gap-2">
                      <span className="w-2.5 h-2.5 rounded-sm" style={{ backgroundColor: LANG_COLORS[lang.language] || LANG_COLORS.Other }} />
                      <span className="text-gray-300 font-medium">{lang.language}</span>
                    </div>
                  </td>
                  <td className="py-2 px-3 text-right text-gray-400">{lang.files.toLocaleString()}</td>
                  <td className="py-2 px-3 text-right text-gray-300 font-medium">{lang.lines.toLocaleString()}</td>
                  <td className="py-2 px-3 text-right text-gray-400">{formatBytes(lang.bytes)}</td>
                  <td className="py-2 px-3">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-2 bg-surface-3 rounded-full overflow-hidden">
                        <div
                          className="h-full rounded-full"
                          style={{ width: `${pct}%`, backgroundColor: LANG_COLORS[lang.language] || LANG_COLORS.Other }}
                        />
                      </div>
                      <span className="text-gray-500 w-10 text-right">{pct.toFixed(1)}%</span>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

// ===== Health Panel =====
function HealthPanel() {
  const { workspace } = useWorkspace();

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['project-health', workspace],
    queryFn: () => engine.getProjectHealth(workspace),
  });

  if (isLoading) return <LoadingState message="Computing health score..." />;
  if (error) return <ErrorState message="Failed to compute health" onRetry={refetch} />;
  if (!data) return <EmptyState message="No health data" />;

  const scoreColor =
    data.score >= 90 ? 'text-accent-green' :
    data.score >= 70 ? 'text-brand-400' :
    data.score >= 50 ? 'text-accent-amber' :
    'text-accent-red';

  const scoreBg =
    data.score >= 90 ? 'bg-accent-green/10 border-accent-green/20' :
    data.score >= 70 ? 'bg-brand-600/10 border-brand-600/20' :
    data.score >= 50 ? 'bg-accent-amber/10 border-accent-amber/20' :
    'bg-accent-red/10 border-accent-red/20';

  const statusIcon = (status: string) => {
    switch (status) {
      case 'good': return <CheckCircle className="w-4 h-4 text-accent-green" />;
      case 'warning': return <AlertTriangle className="w-4 h-4 text-accent-amber" />;
      case 'critical': return <XCircle className="w-4 h-4 text-accent-red" />;
      default: return <Activity className="w-4 h-4 text-gray-500" />;
    }
  };

  const categoryIcon: Record<string, React.ElementType> = {
    risk: TrendingUp,
    security: Shield,
    contracts: Scale,
    drift: GitBranch,
    structure: FolderOpen,
  };

  return (
    <div className="space-y-5">
      {/* Score hero */}
      <div className={cn('rounded-2xl border p-6 flex items-center gap-6', scoreBg)}>
        <div className="text-center">
          <p className={cn('text-5xl font-black', scoreColor)}>{data.score}</p>
          <p className="text-xs text-gray-500 mt-1">/ 100</p>
        </div>
        <div>
          <Badge variant={data.score >= 70 ? 'success' : data.score >= 50 ? 'warning' : 'danger'}>
            {data.health_level}
          </Badge>
          <p className="text-sm text-gray-400 mt-2">
            Composite score from risk analysis, security scanning, contract validation, drift detection, and project structure.
          </p>
        </div>
      </div>

      {/* Breakdown cards */}
      <div className="grid grid-cols-5 gap-4">
        {Object.entries(data.breakdown).map(([key, item]) => {
          const Icon = categoryIcon[key] || Activity;
          return (
            <Card key={key}>
              <div className="flex items-center gap-3 mb-3">
                <Icon className="w-4 h-4 text-gray-400" />
                <span className="text-xs font-semibold text-gray-300 capitalize">{key}</span>
                {statusIcon(item.status)}
              </div>
              <div className="flex items-baseline gap-2">
                <span className={cn(
                  'text-lg font-bold',
                  item.penalty === 0 ? 'text-accent-green' : item.penalty < 10 ? 'text-accent-amber' : 'text-accent-red'
                )}>
                  -{item.penalty}
                </span>
                <span className="text-[10px] text-gray-600">penalty</span>
              </div>
              <div className="mt-2 text-[10px] text-gray-500">
                {Object.entries(item)
                  .filter(([k]) => !['status', 'penalty'].includes(k))
                  .map(([k, v]) => (
                    <div key={k} className="flex justify-between">
                      <span className="capitalize">{k.replace(/_/g, ' ')}</span>
                      <span className="text-gray-400">{String(v)}</span>
                    </div>
                  ))}
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
}

// ===== Largest Files Panel =====
function FilesPanel() {
  const { workspace } = useWorkspace();

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['workspace-summary', workspace],
    queryFn: () => engine.getWorkspaceSummary(workspace),
  });

  if (isLoading) return <LoadingState message="Scanning files..." />;
  if (error) return <ErrorState message="Failed to scan" onRetry={refetch} />;
  if (!data) return <EmptyState message="No data" />;

  const largest = data.largest_files.slice(0, 25);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Largest Files (by Lines)</CardTitle>
        <Badge variant="default">{data.total_files} total files</Badge>
      </CardHeader>
      <div className="overflow-auto max-h-[500px]">
        <table className="w-full text-xs">
          <thead className="sticky top-0 bg-surface-2">
            <tr className="text-gray-600 border-b border-surface-4">
              <th className="text-left py-2 px-3 font-medium">#</th>
              <th className="text-left py-2 px-3 font-medium">File</th>
              <th className="text-left py-2 px-3 font-medium">Language</th>
              <th className="text-right py-2 px-3 font-medium">Lines</th>
              <th className="text-right py-2 px-3 font-medium">Size</th>
            </tr>
          </thead>
          <tbody>
            {largest.map((file, i) => (
              <tr key={file.path} className="border-b border-surface-4/30 hover:bg-surface-3/30">
                <td className="py-2 px-3 text-gray-600">{i + 1}</td>
                <td className="py-2 px-3 text-gray-300 font-mono text-[11px] truncate max-w-[300px]" title={file.path}>
                  {file.path}
                </td>
                <td className="py-2 px-3">
                  <div className="flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-sm" style={{ backgroundColor: LANG_COLORS[file.language] || LANG_COLORS.Other }} />
                    <span className="text-gray-400">{file.language}</span>
                  </div>
                </td>
                <td className="py-2 px-3 text-right text-gray-300 font-medium">{file.lines.toLocaleString()}</td>
                <td className="py-2 px-3 text-right text-gray-400">{formatBytes(file.size)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

// ===== Stat Box Component =====
function StatBox({
  icon: Icon,
  label,
  value,
  color,
}: {
  icon: React.ElementType;
  label: string;
  value: string;
  color: string;
}) {
  return (
    <Card>
      <div className="flex items-center gap-3">
        <div className="w-9 h-9 rounded-xl bg-surface-3 flex items-center justify-center">
          <Icon className={cn('w-4.5 h-4.5', color)} />
        </div>
        <div>
          <p className="text-xs text-gray-500">{label}</p>
          <p className={cn('text-lg font-bold', color)}>{value}</p>
        </div>
      </div>
    </Card>
  );
}
