import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  AreaChart, Area, BarChart, Bar, Cell, PieChart, Pie,
} from 'recharts';
import {
  Cpu, HardDrive, Activity, Wifi, Monitor, BatteryCharging,
  RefreshCw, ChevronUp, ChevronDown, Zap,
} from 'lucide-react';
import { Card, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { LoadingState, ErrorState, EmptyState } from '@/components/ui/States';
import * as engine from '@/api/engineClient';
import type { SystemSnapshot, ProcessInfo, DiskPartition, SystemHistoryPoint } from '@/api/types';
import { cn } from '@/lib/utils';

function formatBytes(bytes: number, decimals = 1): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(decimals)) + ' ' + sizes[i];
}

function formatUptime(seconds: number): string {
  const d = Math.floor(seconds / 86400);
  const h = Math.floor((seconds % 86400) / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const parts: string[] = [];
  if (d > 0) parts.push(`${d}d`);
  if (h > 0) parts.push(`${h}h`);
  parts.push(`${m}m`);
  return parts.join(' ');
}

function getUsageColor(pct: number): string {
  if (pct < 50) return '#22c55e';
  if (pct < 75) return '#f59e0b';
  if (pct < 90) return '#f97316';
  return '#ef4444';
}

export default function DeviceMonitor() {
  const [procSort, setProcSort] = useState<'cpu' | 'memory'>('cpu');

  // Auto-refresh system stats every 3 seconds
  const { data: stats, isLoading: statsLoading, error: statsError, refetch: refetchStats } = useQuery({
    queryKey: ['system-stats'],
    queryFn: engine.getSystemStats,
    refetchInterval: 3_000,
  });

  // Process list every 5 seconds
  const { data: procData } = useQuery({
    queryKey: ['system-processes', procSort],
    queryFn: () => engine.getSystemProcesses(20, procSort),
    refetchInterval: 5_000,
  });

  // Disk partitions every 30 seconds
  const { data: diskData } = useQuery({
    queryKey: ['system-disks'],
    queryFn: engine.getSystemDisks,
    refetchInterval: 30_000,
  });

  // History for charts every 3 seconds
  const { data: historyData } = useQuery({
    queryKey: ['system-history'],
    queryFn: engine.getSystemHistory,
    refetchInterval: 3_000,
  });

  if (statsLoading) return <LoadingState message="Connecting to system monitor..." />;
  if (statsError) return <ErrorState message="System monitor unavailable. Ensure copilot-engine is running with psutil installed." onRetry={refetchStats} />;
  if (!stats) return <EmptyState message="No system data available" />;

  const history = historyData?.history ?? [];
  const processes = procData?.processes ?? [];
  const disks = diskData?.partitions ?? [];

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center gap-3">
            <Monitor className="w-7 h-7 text-brand-400" />
            Device Monitor
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            {stats.system.hostname} · {stats.system.platform} {stats.system.platform_release} · {stats.system.architecture} · Up {formatUptime(stats.system.uptime_seconds)}
          </p>
        </div>
        <div className="flex items-center gap-3">
          {stats.battery && (
            <div className="flex items-center gap-1.5 text-xs text-gray-400">
              <BatteryCharging className="w-4 h-4 text-accent-green" />
              {stats.battery.percent}%
              {stats.battery.plugged ? ' (Plugged)' : ''}
            </div>
          )}
          <button onClick={() => refetchStats()} className="p-2 rounded-lg bg-surface-3 hover:bg-surface-4 text-gray-400 transition-colors">
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Top-level gauges */}
      <div className="grid grid-cols-4 gap-4">
        <GaugeCard
          icon={Cpu}
          label="CPU"
          value={stats.cpu.percent}
          subtitle={`${stats.cpu.cores_physical}C/${stats.cpu.cores_logical}T · ${stats.cpu.freq_current} MHz`}
        />
        <GaugeCard
          icon={Activity}
          label="Memory"
          value={stats.memory.percent}
          subtitle={`${formatBytes(stats.memory.used)} / ${formatBytes(stats.memory.total)}`}
        />
        <GaugeCard
          icon={HardDrive}
          label="Disk"
          value={stats.disk.percent}
          subtitle={`${formatBytes(stats.disk.used)} / ${formatBytes(stats.disk.total)}`}
        />
        <GaugeCard
          icon={Wifi}
          label="Network"
          value={-1}
          subtitle={`↑ ${formatBytes(stats.network.bytes_sent)} · ↓ ${formatBytes(stats.network.bytes_recv)}`}
          isNetwork
        />
      </div>

      {/* Charts + Per-core */}
      <div className="grid grid-cols-12 gap-4">
        {/* CPU/Memory history chart */}
        <div className="col-span-8">
          <Card>
            <CardHeader>
              <CardTitle>Resource Usage (Live)</CardTitle>
              <div className="flex items-center gap-3 text-xs text-gray-500">
                <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-brand-500 inline-block" /> CPU</span>
                <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-full bg-accent-purple inline-block" /> Memory</span>
              </div>
            </CardHeader>
            {history.length > 2 ? (
              <ResponsiveContainer width="100%" height={220}>
                <AreaChart data={history} margin={{ top: 5, right: 10, left: -15, bottom: 5 }}>
                  <defs>
                    <linearGradient id="cpuGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.25} />
                      <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="memGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#a855f7" stopOpacity={0.25} />
                      <stop offset="95%" stopColor="#a855f7" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e1e2e" />
                  <XAxis dataKey="timestamp" tick={false} stroke="#38384a" />
                  <YAxis domain={[0, 100]} tick={{ fill: '#6b7280', fontSize: 10 }} stroke="#38384a" />
                  <Tooltip
                    contentStyle={{ backgroundColor: '#1a1a2e', border: '1px solid #2e2e46', borderRadius: 8, fontSize: 12 }}
                    labelFormatter={() => ''}
                    formatter={(val: number, name: string) => [`${val.toFixed(1)}%`, name === 'cpu' ? 'CPU' : 'Memory']}
                  />
                  <Area type="monotone" dataKey="cpu" stroke="#3b82f6" fill="url(#cpuGrad)" strokeWidth={2} dot={false} />
                  <Area type="monotone" dataKey="memory" stroke="#a855f7" fill="url(#memGrad)" strokeWidth={2} dot={false} />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <EmptyState message="Collecting data... refresh in a few seconds" />
            )}
          </Card>
        </div>

        {/* Per-core CPU bars */}
        <div className="col-span-4">
          <Card>
            <CardHeader>
              <CardTitle>CPU Cores ({stats.cpu.cores_logical})</CardTitle>
            </CardHeader>
            <div className="space-y-1.5 max-h-[220px] overflow-y-auto pr-1">
              {stats.cpu.per_core.map((pct, i) => (
                <div key={i} className="flex items-center gap-2">
                  <span className="text-[10px] text-gray-600 w-5 text-right">{i}</span>
                  <div className="flex-1 h-3 bg-surface-3 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{ width: `${pct}%`, backgroundColor: getUsageColor(pct) }}
                    />
                  </div>
                  <span className="text-[10px] text-gray-400 w-8 text-right">{pct}%</span>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>

      {/* Bottom row: Processes + Disks */}
      <div className="grid grid-cols-12 gap-4">
        {/* Process table */}
        <div className="col-span-8">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="w-4 h-4 text-accent-amber" />
                Top Processes
              </CardTitle>
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setProcSort('cpu')}
                  className={cn(
                    'px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors',
                    procSort === 'cpu' ? 'bg-brand-600/20 text-brand-400' : 'text-gray-500 hover:text-gray-300'
                  )}
                >
                  CPU
                </button>
                <button
                  onClick={() => setProcSort('memory')}
                  className={cn(
                    'px-2.5 py-1 rounded-md text-[11px] font-medium transition-colors',
                    procSort === 'memory' ? 'bg-accent-purple/20 text-accent-purple' : 'text-gray-500 hover:text-gray-300'
                  )}
                >
                  Memory
                </button>
              </div>
            </CardHeader>
            <div className="overflow-auto max-h-[320px]">
              <table className="w-full text-xs">
                <thead>
                  <tr className="text-gray-600 border-b border-surface-4">
                    <th className="text-left py-1.5 px-2 font-medium">PID</th>
                    <th className="text-left py-1.5 px-2 font-medium">Process</th>
                    <th className="text-right py-1.5 px-2 font-medium">CPU %</th>
                    <th className="text-right py-1.5 px-2 font-medium">MEM %</th>
                    <th className="text-left py-1.5 px-2 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {processes.map((proc) => (
                    <tr key={proc.pid} className="border-b border-surface-4/30 hover:bg-surface-3/30">
                      <td className="py-1.5 px-2 text-gray-600 font-mono">{proc.pid}</td>
                      <td className="py-1.5 px-2 text-gray-300 font-medium truncate max-w-[180px]">{proc.name}</td>
                      <td className="py-1.5 px-2 text-right">
                        <span style={{ color: getUsageColor(proc.cpu_percent * 5) }}>{proc.cpu_percent}</span>
                      </td>
                      <td className="py-1.5 px-2 text-right">
                        <span style={{ color: getUsageColor(proc.memory_percent * 5) }}>{proc.memory_percent}</span>
                      </td>
                      <td className="py-1.5 px-2">
                        <span className={cn(
                          'text-[10px] px-1.5 py-0.5 rounded',
                          proc.status === 'running' ? 'bg-accent-green/10 text-accent-green' : 'bg-surface-4 text-gray-500'
                        )}>
                          {proc.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>

        {/* Disk partitions */}
        <div className="col-span-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <HardDrive className="w-4 h-4 text-accent-green" />
                Disk Partitions
              </CardTitle>
            </CardHeader>
            <div className="space-y-3">
              {disks.map((disk) => (
                <div key={disk.mountpoint} className="bg-surface-3/30 rounded-lg p-3 border border-surface-4/50">
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs font-medium text-gray-300">{disk.device}</span>
                    <span className="text-[10px] text-gray-500">{disk.mountpoint} · {disk.fstype}</span>
                  </div>
                  <div className="h-2 bg-surface-4 rounded-full overflow-hidden mb-1">
                    <div
                      className="h-full rounded-full transition-all"
                      style={{ width: `${disk.percent}%`, backgroundColor: getUsageColor(disk.percent) }}
                    />
                  </div>
                  <div className="flex justify-between text-[10px] text-gray-500">
                    <span>{formatBytes(disk.used)} used</span>
                    <span>{formatBytes(disk.free)} free</span>
                  </div>
                </div>
              ))}
              {disks.length === 0 && <EmptyState message="No disk data" />}
            </div>
          </Card>
        </div>
      </div>

      {/* Swap memory */}
      {stats.memory.swap_total > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Swap Memory</CardTitle>
            <Badge variant={stats.memory.swap_percent > 80 ? 'danger' : stats.memory.swap_percent > 50 ? 'warning' : 'success'}>
              {stats.memory.swap_percent}%
            </Badge>
          </CardHeader>
          <div className="flex items-center gap-4">
            <div className="flex-1 h-3 bg-surface-3 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full"
                style={{ width: `${stats.memory.swap_percent}%`, backgroundColor: getUsageColor(stats.memory.swap_percent) }}
              />
            </div>
            <span className="text-xs text-gray-400">
              {formatBytes(stats.memory.swap_used)} / {formatBytes(stats.memory.swap_total)}
            </span>
          </div>
        </Card>
      )}
    </div>
  );
}

// ===== Gauge Card Component =====
function GaugeCard({
  icon: Icon,
  label,
  value,
  subtitle,
  isNetwork = false,
}: {
  icon: React.ElementType;
  label: string;
  value: number;
  subtitle: string;
  isNetwork?: boolean;
}) {
  return (
    <Card>
      <div className="flex items-center gap-3">
        <div className={cn(
          'w-10 h-10 rounded-xl flex items-center justify-center',
          isNetwork ? 'bg-accent-green/10' : value < 50 ? 'bg-accent-green/10' : value < 80 ? 'bg-accent-amber/10' : 'bg-accent-red/10'
        )}>
          <Icon className={cn(
            'w-5 h-5',
            isNetwork ? 'text-accent-green' : value < 50 ? 'text-accent-green' : value < 80 ? 'text-accent-amber' : 'text-accent-red'
          )} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-400 font-medium">{label}</span>
            {!isNetwork && <span className="text-lg font-bold text-white">{value.toFixed(1)}%</span>}
          </div>
          <p className="text-[10px] text-gray-600 truncate mt-0.5">{subtitle}</p>
          {!isNetwork && (
            <div className="h-1.5 bg-surface-3 rounded-full overflow-hidden mt-1.5">
              <div
                className="h-full rounded-full transition-all duration-700"
                style={{ width: `${value}%`, backgroundColor: getUsageColor(value) }}
              />
            </div>
          )}
        </div>
      </div>
    </Card>
  );
}
