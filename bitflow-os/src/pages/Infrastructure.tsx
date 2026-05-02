import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import {
  Server, Activity, AlertTriangle, Shield, Plus, Trash2, Play, RefreshCw,
  CheckCircle, XCircle, Clock, Zap, Globe, Eye, EyeOff, Bell,
} from 'lucide-react';
import { Card, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { LoadingState, ErrorState, EmptyState } from '@/components/ui/States';
import * as engine from '@/api/engineClient';
import type { InfraEndpoint, CheckResult, InfraAlert } from '@/api/types';
import { cn } from '@/lib/utils';

function formatMs(ms: number): string {
  if (ms < 1000) return `${Math.round(ms)}ms`;
  return `${(ms / 1000).toFixed(2)}s`;
}

function timeAgo(iso: string): string {
  if (!iso) return '—';
  const diff = Date.now() - new Date(iso).getTime();
  const s = Math.floor(diff / 1000);
  if (s < 60) return `${s}s ago`;
  const m = Math.floor(s / 60);
  if (m < 60) return `${m}m ago`;
  const h = Math.floor(m / 60);
  return `${h}h ago`;
}

// ── Stats Cards ──
function StatsCards() {
  const { data } = useQuery({ queryKey: ['infra-stats'], queryFn: engine.getInfraStats, refetchInterval: 10_000 });
  if (!data) return null;
  const cards = [
    { label: 'Total Endpoints', value: data.total_endpoints, icon: Globe, color: 'text-brand-400' },
    { label: 'Up', value: data.endpoints_up, icon: CheckCircle, color: 'text-green-400' },
    { label: 'Down', value: data.endpoints_down, icon: XCircle, color: data.endpoints_down > 0 ? 'text-red-400' : 'text-gray-500' },
    { label: 'Avg Response', value: formatMs(data.avg_response_time_ms), icon: Zap, color: 'text-amber-400' },
    { label: 'Alerts', value: data.unacknowledged_alerts, icon: Bell, color: data.unacknowledged_alerts > 0 ? 'text-red-400' : 'text-gray-500' },
    { label: 'Total Checks', value: data.total_checks, icon: Activity, color: 'text-purple-400' },
  ];
  return (
    <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-3 mb-6">
      {cards.map(c => (
        <div key={c.label} className="bg-surface-2 rounded-xl p-4 flex items-center gap-3">
          <c.icon className={cn('w-7 h-7', c.color)} />
          <div>
            <p className="text-xl font-bold text-white">{c.value}</p>
            <p className="text-[10px] text-gray-500 uppercase">{c.label}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Add Endpoint Form ──
function AddEndpointForm({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient();
  const [name, setName] = useState('');
  const [url, setUrl] = useState('');
  const [method, setMethod] = useState('GET');
  const [expectedStatus, setExpectedStatus] = useState(200);
  const [timeout, setTimeout_] = useState(10);
  const [category, setCategory] = useState('api');

  const mutation = useMutation({
    mutationFn: () => engine.addInfraEndpoint({
      name, url, method, expected_status: expectedStatus,
      timeout_seconds: timeout, category,
    }),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['infra-endpoints'] }); qc.invalidateQueries({ queryKey: ['infra-stats'] }); onClose(); },
  });

  return (
    <Card className="mb-4 border border-brand-500/30">
      <CardHeader><CardTitle className="text-sm">Add Endpoint</CardTitle></CardHeader>
      <div className="px-4 pb-4 space-y-3">
        <div className="flex gap-3">
          <input className="flex-1 bg-surface-3 text-white rounded-lg px-3 py-2 text-sm focus:ring-1 focus:ring-brand-500 outline-none" placeholder="Name" value={name} onChange={e => setName(e.target.value)} />
          <select className="bg-surface-3 text-white rounded-lg px-3 py-2 text-sm outline-none" value={category} onChange={e => setCategory(e.target.value)}>
            <option value="api">API</option><option value="website">Website</option><option value="service">Service</option><option value="database">Database</option>
          </select>
        </div>
        <input className="w-full bg-surface-3 text-white rounded-lg px-3 py-2 text-sm focus:ring-1 focus:ring-brand-500 outline-none" placeholder="https://example.com/health" value={url} onChange={e => setUrl(e.target.value)} />
        <div className="flex gap-3">
          <select className="bg-surface-3 text-white rounded-lg px-3 py-2 text-sm outline-none" value={method} onChange={e => setMethod(e.target.value)}>
            <option value="GET">GET</option><option value="POST">POST</option><option value="HEAD">HEAD</option>
          </select>
          <input type="number" className="w-28 bg-surface-3 text-white rounded-lg px-3 py-2 text-sm outline-none" placeholder="Expected" value={expectedStatus} onChange={e => setExpectedStatus(Number(e.target.value))} />
          <input type="number" className="w-28 bg-surface-3 text-white rounded-lg px-3 py-2 text-sm outline-none" placeholder="Timeout (s)" value={timeout} onChange={e => setTimeout_(Number(e.target.value))} />
        </div>
        <div className="flex justify-end gap-2">
          <button onClick={onClose} className="px-3 py-1.5 rounded-lg bg-surface-3 text-gray-400 text-sm hover:text-white">Cancel</button>
          <button onClick={() => mutation.mutate()} disabled={!name || !url || mutation.isPending} className="px-3 py-1.5 rounded-lg bg-brand-600 text-white text-sm hover:bg-brand-500 disabled:opacity-50">
            {mutation.isPending ? 'Adding...' : 'Add'}
          </button>
        </div>
      </div>
    </Card>
  );
}

// ── Endpoints Tab ──
function EndpointsTab() {
  const [showForm, setShowForm] = useState(false);
  const qc = useQueryClient();
  const { data, isLoading, error } = useQuery({ queryKey: ['infra-endpoints'], queryFn: engine.listInfraEndpoints, refetchInterval: 10_000 });
  const deleteMut = useMutation({
    mutationFn: (id: string) => engine.deleteInfraEndpoint(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['infra-endpoints'] }); qc.invalidateQueries({ queryKey: ['infra-stats'] }); },
  });
  const toggleMut = useMutation({
    mutationFn: (ep: InfraEndpoint) => engine.updateInfraEndpoint(ep.id, { enabled: ep.enabled ? 0 : 1 } as any),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['infra-endpoints'] }),
  });
  const checkMut = useMutation({
    mutationFn: (id: string) => engine.checkEndpoint(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['infra-endpoints'] }); qc.invalidateQueries({ queryKey: ['infra-stats'] }); },
  });

  if (isLoading) return <LoadingState message="Loading endpoints..." />;
  if (error) return <ErrorState message="Failed to load endpoints" />;
  const endpoints = data?.endpoints || [];

  return (
    <div>
      <div className="flex justify-end mb-4">
        <button onClick={() => setShowForm(v => !v)} className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-brand-600 text-white text-sm hover:bg-brand-500">
          <Plus className="w-4 h-4" /> Add Endpoint
        </button>
      </div>
      {showForm && <AddEndpointForm onClose={() => setShowForm(false)} />}

      {endpoints.length === 0 ? <EmptyState message="No endpoints configured yet." /> : (
        <div className="space-y-2">
          {endpoints.map(ep => {
            const lc = ep.latest_check;
            const isUp = lc ? lc.is_up : null;
            return (
              <Card key={ep.id} className="hover:border-surface-4 transition-colors">
                <div className="p-4 flex items-center gap-4">
                  {/* Status indicator */}
                  <div className={cn('w-3 h-3 rounded-full flex-shrink-0',
                    isUp === null ? 'bg-gray-500' : isUp ? 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.4)]' : 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.4)]'
                  )} />

                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <h3 className="text-sm font-medium text-white truncate">{ep.name}</h3>
                      <Badge className="bg-surface-4 text-gray-400">{ep.method}</Badge>
                      <Badge className="bg-surface-4 text-gray-400">{ep.category}</Badge>
                      {!ep.enabled && <Badge className="bg-red-500/20 text-red-400">Disabled</Badge>}
                    </div>
                    <p className="text-xs text-gray-500 truncate mt-0.5">{ep.url}</p>
                  </div>

                  {/* Metrics */}
                  <div className="flex items-center gap-6 flex-shrink-0">
                    <div className="text-center">
                      <p className={cn('text-sm font-mono font-medium', lc ? (lc.is_up ? 'text-green-400' : 'text-red-400') : 'text-gray-500')}>
                        {lc ? `${lc.status_code}` : '—'}
                      </p>
                      <p className="text-[10px] text-gray-600">Status</p>
                    </div>
                    <div className="text-center">
                      <p className="text-sm font-mono text-gray-300">{lc ? formatMs(lc.response_time_ms) : '—'}</p>
                      <p className="text-[10px] text-gray-600">Latency</p>
                    </div>
                    <div className="text-center">
                      <p className={cn('text-sm font-mono font-medium',
                        ep.uptime_24h >= 99 ? 'text-green-400' : ep.uptime_24h >= 95 ? 'text-amber-400' : 'text-red-400'
                      )}>{ep.uptime_24h}%</p>
                      <p className="text-[10px] text-gray-600">24h</p>
                    </div>
                    <div className="text-center">
                      <p className="text-xs text-gray-500">{lc ? timeAgo(lc.checked_at) : 'Never'}</p>
                      <p className="text-[10px] text-gray-600">Last</p>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-1 flex-shrink-0">
                    <button onClick={() => checkMut.mutate(ep.id)} className="p-1.5 rounded text-gray-500 hover:text-brand-400" title="Check now">
                      <Play className="w-4 h-4" />
                    </button>
                    <button onClick={() => toggleMut.mutate(ep)} className="p-1.5 rounded text-gray-500 hover:text-amber-400" title={ep.enabled ? 'Disable' : 'Enable'}>
                      {ep.enabled ? <Eye className="w-4 h-4" /> : <EyeOff className="w-4 h-4" />}
                    </button>
                    <button onClick={() => deleteMut.mutate(ep.id)} className="p-1.5 rounded text-gray-500 hover:text-red-400" title="Delete">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}

// ── Alerts Tab ──
function AlertsTab() {
  const [showAcknowledged, setShowAcknowledged] = useState(false);
  const qc = useQueryClient();
  const { data, isLoading, error } = useQuery({
    queryKey: ['infra-alerts', showAcknowledged],
    queryFn: () => engine.getInfraAlerts(showAcknowledged ? undefined : false),
    refetchInterval: 10_000,
  });
  const ackMut = useMutation({
    mutationFn: (id: string) => engine.acknowledgeAlert(id),
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['infra-alerts'] }); qc.invalidateQueries({ queryKey: ['infra-stats'] }); },
  });

  if (isLoading) return <LoadingState message="Loading alerts..." />;
  if (error) return <ErrorState message="Failed to load alerts" />;
  const alerts = data?.alerts || [];

  const SEVERITY_COLORS: Record<string, string> = {
    error: 'bg-red-500/20 text-red-400',
    warning: 'bg-amber-500/20 text-amber-400',
    info: 'bg-blue-500/20 text-blue-400',
  };

  return (
    <div>
      <div className="flex justify-end mb-4">
        <button onClick={() => setShowAcknowledged(v => !v)}
          className={cn('px-3 py-1.5 rounded-lg text-sm', showAcknowledged ? 'bg-brand-600 text-white' : 'bg-surface-3 text-gray-400 hover:text-white')}>
          {showAcknowledged ? 'Show All' : 'Show Unacknowledged'}
        </button>
      </div>
      {alerts.length === 0 ? <EmptyState message="No alerts." /> : (
        <div className="space-y-2">
          {alerts.map((a: InfraAlert) => (
            <div key={a.id} className={cn('bg-surface-2 rounded-lg p-4 flex items-start gap-3', a.acknowledged && 'opacity-50')}>
              <AlertTriangle className={cn('w-5 h-5 flex-shrink-0 mt-0.5',
                a.severity === 'error' ? 'text-red-400' : a.severity === 'warning' ? 'text-amber-400' : 'text-blue-400'
              )} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <Badge className={SEVERITY_COLORS[a.severity] || ''}>{a.severity}</Badge>
                  <span className="text-xs text-gray-500">{a.endpoint_name}</span>
                  <span className="text-xs text-gray-600">{timeAgo(a.created_at)}</span>
                </div>
                <p className="text-sm text-gray-300">{a.message}</p>
                <p className="text-xs text-gray-500 mt-1 truncate">{a.endpoint_url}</p>
              </div>
              {!a.acknowledged && (
                <button onClick={() => ackMut.mutate(a.id)} className="px-2 py-1 rounded bg-surface-3 text-xs text-gray-400 hover:text-white flex-shrink-0">
                  Acknowledge
                </button>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Live Check Tab ──
function LiveCheckTab() {
  const qc = useQueryClient();
  const [results, setResults] = useState<CheckResult[]>([]);
  const [checking, setChecking] = useState(false);

  const checkAll = useMutation({
    mutationFn: engine.checkAllEndpoints,
    onMutate: () => { setChecking(true); setResults([]); },
    onSuccess: (data) => { setResults(data.results || []); setChecking(false); qc.invalidateQueries({ queryKey: ['infra-endpoints'] }); qc.invalidateQueries({ queryKey: ['infra-stats'] }); },
    onError: () => setChecking(false),
  });

  const checkOne = useMutation({
    mutationFn: (id: string) => engine.checkEndpoint(id),
    onSuccess: (result) => {
      setResults(prev => {
        const idx = prev.findIndex(r => r.endpoint_id === result.endpoint_id);
        if (idx >= 0) { const next = [...prev]; next[idx] = result; return next; }
        return [...prev, result];
      });
      qc.invalidateQueries({ queryKey: ['infra-endpoints'] });
    },
  });

  const { data: endpointList } = useQuery({ queryKey: ['infra-endpoints'], queryFn: engine.listInfraEndpoints });
  const endpoints = endpointList?.endpoints || [];

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm text-gray-400">Run health checks against all configured endpoints.</p>
        <button onClick={() => checkAll.mutate()} disabled={checking}
          className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-green-600 text-white text-sm hover:bg-green-500 disabled:opacity-50">
          {checking ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
          {checking ? 'Checking...' : 'Check All'}
        </button>
      </div>

      {results.length > 0 && (
        <div className="space-y-2 mb-6">
          <h3 className="text-xs font-semibold text-gray-500 uppercase">Results</h3>
          {results.map((r, i) => (
            <div key={i} className={cn('bg-surface-2 rounded-lg p-3 flex items-center gap-3 border-l-2',
              r.is_up ? 'border-green-500' : 'border-red-500')}>
              {r.is_up ? <CheckCircle className="w-5 h-5 text-green-400" /> : <XCircle className="w-5 h-5 text-red-400" />}
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white">{r.name}</p>
                <p className="text-xs text-gray-500 truncate">{r.url}</p>
              </div>
              <span className={cn('text-sm font-mono', r.is_up ? 'text-green-400' : 'text-red-400')}>HTTP {r.status_code || '—'}</span>
              <span className="text-sm font-mono text-gray-400">{formatMs(r.response_time_ms)}</span>
              {r.error_message && <span className="text-xs text-red-400 max-w-48 truncate">{r.error_message}</span>}
            </div>
          ))}
        </div>
      )}

      {/* Per-endpoint check buttons */}
      <h3 className="text-xs font-semibold text-gray-500 uppercase mb-2">Individual Checks</h3>
      {endpoints.length === 0 ? <EmptyState message="No endpoints configured." /> : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {endpoints.map(ep => (
            <div key={ep.id} className="bg-surface-2 rounded-lg p-3 flex items-center gap-3">
              <div className={cn('w-2 h-2 rounded-full', ep.latest_check?.is_up ? 'bg-green-500' : ep.latest_check ? 'bg-red-500' : 'bg-gray-500')} />
              <span className="text-sm text-gray-300 flex-1 truncate">{ep.name}</span>
              <button onClick={() => checkOne.mutate(ep.id)} className="px-2 py-1 rounded bg-surface-3 text-xs text-gray-400 hover:text-white">
                <Play className="w-3 h-3 inline mr-1" />Check
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Stats Tab ──
function StatsTab() {
  const { data: stats } = useQuery({ queryKey: ['infra-stats'], queryFn: engine.getInfraStats, refetchInterval: 10_000 });
  const { data: endpointList } = useQuery({ queryKey: ['infra-endpoints'], queryFn: engine.listInfraEndpoints });
  const [selectedEp, setSelectedEp] = useState<string | null>(null);
  const { data: history } = useQuery({
    queryKey: ['infra-history', selectedEp],
    queryFn: () => selectedEp ? engine.getCheckHistory(selectedEp, 50) : Promise.resolve({ history: [] }),
    enabled: !!selectedEp,
  });

  const endpoints = endpointList?.endpoints || [];
  const chartData = (history?.history || []).reverse().map((h: any) => ({
    time: new Date(h.checked_at).toLocaleTimeString(),
    response_time: h.response_time_ms,
    status: h.is_up ? 1 : 0,
  }));

  return (
    <div>
      <StatsCards />

      <Card className="mt-4">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm">Response Time History</CardTitle>
            <select className="bg-surface-3 text-white rounded px-2 py-1 text-xs outline-none"
              value={selectedEp || ''} onChange={e => setSelectedEp(e.target.value || null)}>
              <option value="">Select endpoint...</option>
              {endpoints.map(ep => <option key={ep.id} value={ep.id}>{ep.name}</option>)}
            </select>
          </div>
        </CardHeader>
        <div className="p-4">
          {chartData.length === 0 ? (
            <p className="text-center text-gray-500 text-sm py-8">Select an endpoint to see its response time history.</p>
          ) : (
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e1e2e" />
                <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#6b7280' }} />
                <YAxis tick={{ fontSize: 10, fill: '#6b7280' }} unit="ms" />
                <Tooltip contentStyle={{ background: '#1a1a2e', border: '1px solid #2a2a3e', borderRadius: '8px', fontSize: '12px' }} />
                <Line type="monotone" dataKey="response_time" stroke="#3b82f6" strokeWidth={2} dot={false} name="Response Time" />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      </Card>
    </div>
  );
}

// ── Main Page ──
type Tab = 'endpoints' | 'alerts' | 'live-check' | 'stats';

export default function Infrastructure() {
  const [tab, setTab] = useState<Tab>('endpoints');

  const tabs: { key: Tab; label: string; icon: React.ElementType }[] = [
    { key: 'endpoints', label: 'Endpoints', icon: Globe },
    { key: 'alerts', label: 'Alerts', icon: Bell },
    { key: 'live-check', label: 'Live Check', icon: Activity },
    { key: 'stats', label: 'Stats', icon: Shield },
  ];

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <Server className="w-6 h-6 text-brand-400" />
        <h1 className="text-xl font-bold text-white">Infrastructure</h1>
      </div>

      <div className="flex gap-1 mb-6 bg-surface-1 p-1 rounded-xl w-fit">
        {tabs.map(t => (
          <button key={t.key} onClick={() => setTab(t.key)}
            className={cn('flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors',
              tab === t.key ? 'bg-surface-3 text-white' : 'text-gray-500 hover:text-gray-300')}>
            <t.icon className="w-4 h-4" />{t.label}
          </button>
        ))}
      </div>

      {tab === 'endpoints' && <EndpointsTab />}
      {tab === 'alerts' && <AlertsTab />}
      {tab === 'live-check' && <LiveCheckTab />}
      {tab === 'stats' && <StatsTab />}
    </div>
  );
}
