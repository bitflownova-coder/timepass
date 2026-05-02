import React, { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Area, AreaChart,
} from 'recharts';
import {
  AlertTriangle, GitBranch, Shield, Zap, FileWarning, CircleDot, Trash2, Activity,
} from 'lucide-react';
import { Card, CardHeader, CardTitle } from '@/components/ui/Card';
import { StatCard } from '@/components/ui/StatCard';
import { ServiceHealthRow } from '@/components/ui/StatusDot';
import { RiskGauge } from '@/components/ui/RiskGauge';
import { LoadingState, ErrorState } from '@/components/ui/States';
import { Badge } from '@/components/ui/Badge';
import * as engine from '@/api/engineClient';
import { formatTimestamp, getSeverityColor } from '@/lib/utils';
import { useWorkspace } from '@/contexts/WorkspaceContext';

export default function Dashboard() {
  const { workspace: WORKSPACE } = useWorkspace();
  const [serviceStatuses, setServiceStatuses] = useState<ServiceStatus[]>([]);

  useEffect(() => {
    window.electronAPI?.getServiceStatuses?.().then(setServiceStatuses).catch(() => {});
    const unsub = window.electronAPI?.onServiceStatus?.(setServiceStatuses);
    return () => unsub?.();
  }, []);

  // Fetch autonomous dashboard data
  const { data: dashData, isLoading, error, refetch } = useQuery({
    queryKey: ['autonomous-dashboard', WORKSPACE],
    queryFn: () => engine.getAutonomousDashboard(WORKSPACE),
    refetchInterval: 30_000,
  });

  // Fetch graph stats
  const { data: graphStats } = useQuery({
    queryKey: ['graph-stats'],
    queryFn: () => engine.getGraphStats(),
    refetchInterval: 60_000,
  });

  // Fetch behavior status
  const { data: behavior } = useQuery({
    queryKey: ['behavior', WORKSPACE],
    queryFn: () => engine.getBehaviorStatus(WORKSPACE),
    refetchInterval: 15_000,
  });

  const handleRestart = async (id: string) => {
    const statuses = await window.electronAPI?.restartService(id);
    if (statuses) setServiceStatuses(statuses);
  };

  const riskScore = dashData?.health?.overall_score ?? 0;
  const riskTrend = dashData?.risk_trend ?? [];
  const driftCount = dashData?.unresolved_drifts?.length ?? 0;
  const circularCount = dashData?.circular_dependencies?.length ?? 0;
  const deadCodeCount = dashData?.dead_code_files?.length ?? 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Command Center</h1>
          <p className="text-sm text-gray-500 mt-1">Real-time overview of your development ecosystem</p>
        </div>
        <ServiceHealthRow services={serviceStatuses} onRestart={handleRestart} />
      </div>

      {/* Top Row: Risk Gauge + Stats */}
      <div className="grid grid-cols-12 gap-5">
        {/* Risk Gauge */}
        <Card className="col-span-3 flex flex-col items-center justify-center">
          <CardTitle className="mb-3">Overall Risk Score</CardTitle>
          {isLoading ? (
            <LoadingState message="Analyzing..." />
          ) : error ? (
            <ErrorState message="Engine offline" onRetry={refetch} />
          ) : (
            <RiskGauge score={riskScore} size="lg" />
          )}
        </Card>

        {/* Quick Stats */}
        <div className="col-span-9 grid grid-cols-4 gap-4">
          <StatCard
            title="Unresolved Drifts"
            value={driftCount}
            icon={AlertTriangle}
            color="accent-amber"
            subtitle="Schema & API drifts"
          />
          <StatCard
            title="Dead Code Files"
            value={deadCodeCount}
            icon={Trash2}
            color="accent-red"
            subtitle="Unreferenced files"
          />
          <StatCard
            title="Circular Deps"
            value={circularCount}
            icon={CircleDot}
            color="accent-purple"
            subtitle="Dependency cycles"
          />
          <StatCard
            title="Total Files Indexed"
            value={graphStats?.total_files ?? '—'}
            icon={FileWarning}
            color="brand-400"
            subtitle={`${graphStats?.file_edges ?? 0} dependency edges`}
          />
        </div>
      </div>

      {/* Middle Row: Risk Trend Chart + Behavior */}
      <div className="grid grid-cols-12 gap-5">
        {/* Risk Trend */}
        <Card className="col-span-8">
          <CardHeader>
            <CardTitle>Risk Score Trend</CardTitle>
            <Badge variant="info">Last 50 snapshots</Badge>
          </CardHeader>
          {riskTrend.length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <AreaChart data={riskTrend}>
                <defs>
                  <linearGradient id="riskGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#1a1a24" />
                <XAxis
                  dataKey="timestamp"
                  tickFormatter={(t) => formatTimestamp(t)}
                  stroke="#38384a"
                  tick={{ fontSize: 10, fill: '#666' }}
                />
                <YAxis domain={[0, 10]} stroke="#38384a" tick={{ fontSize: 10, fill: '#666' }} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#1a1a24', border: '1px solid #38384a', borderRadius: 8, fontSize: 12 }}
                  labelStyle={{ color: '#9ca3af' }}
                />
                <Area type="monotone" dataKey="overall_score" stroke="#3b82f6" fill="url(#riskGrad)" strokeWidth={2} />
                <Line type="monotone" dataKey="security" stroke="#ef4444" strokeWidth={1} dot={false} />
                <Line type="monotone" dataKey="drift" stroke="#f59e0b" strokeWidth={1} dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-60 flex items-center justify-center text-gray-600 text-sm">
              No trend data yet. Initialize workspace analysis to begin.
            </div>
          )}
        </Card>

        {/* Developer Behavior */}
        <Card className="col-span-4">
          <CardHeader>
            <CardTitle>Developer Status</CardTitle>
            <Activity className="w-4 h-4 text-gray-600" />
          </CardHeader>
          {behavior ? (
            <div className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-500">Session Time</span>
                <span className="text-sm font-medium text-white">{behavior.session_minutes}m</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-500">Errors</span>
                <span className="text-sm font-medium text-accent-red">{behavior.error_count}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-500">Files Visited</span>
                <span className="text-sm font-medium text-white">{behavior.files_visited}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-500">Terminal Runs</span>
                <span className="text-sm font-medium text-white">{behavior.terminal_runs}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-500">File Saves</span>
                <span className="text-sm font-medium text-white">{behavior.saves}</span>
              </div>
              {behavior.focus_mode_suggested && (
                <div className="mt-3 p-2 bg-accent-amber/10 border border-accent-amber/30 rounded-lg">
                  <p className="text-[11px] text-accent-amber font-medium">⚡ Focus mode suggested</p>
                  <p className="text-[10px] text-gray-500 mt-0.5">{behavior.message}</p>
                </div>
              )}
            </div>
          ) : (
            <div className="text-sm text-gray-600">No session data</div>
          )}
        </Card>
      </div>

      {/* Bottom Row: Recent Drifts */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Drift Events</CardTitle>
          <Badge variant="warning">{driftCount} unresolved</Badge>
        </CardHeader>
        {dashData?.unresolved_drifts && dashData.unresolved_drifts.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-[11px] text-gray-600 uppercase tracking-wider border-b border-surface-4">
                  <th className="pb-2 pr-4">Severity</th>
                  <th className="pb-2 pr-4">File</th>
                  <th className="pb-2 pr-4">Entity</th>
                  <th className="pb-2 pr-4">Drift Type</th>
                  <th className="pb-2">Time</th>
                </tr>
              </thead>
              <tbody>
                {dashData.unresolved_drifts.slice(0, 8).map((drift) => (
                  <tr key={drift.id} className="border-b border-surface-3/50 hover:bg-surface-3/30">
                    <td className="py-2 pr-4">
                      <span className={`text-[11px] font-semibold px-2 py-0.5 rounded ${getSeverityColor(drift.severity)}`}>
                        {drift.severity}
                      </span>
                    </td>
                    <td className="py-2 pr-4 text-gray-400 font-mono text-xs truncate max-w-[200px]">
                      {drift.file_path.split(/[/\\]/).pop()}
                    </td>
                    <td className="py-2 pr-4 text-gray-300 text-xs">{drift.entity_name}</td>
                    <td className="py-2 pr-4 text-gray-500 text-xs">{drift.drift_type}</td>
                    <td className="py-2 text-gray-600 text-xs">{formatTimestamp(drift.timestamp)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <p className="text-sm text-gray-600">No drift events detected. System is clean.</p>
        )}
      </Card>
    </div>
  );
}
