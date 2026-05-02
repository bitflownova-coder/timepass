import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Settings, FolderOpen, Plus, Trash2, RefreshCw, Server, Database,
  Sliders, HardDrive, CheckCircle, XCircle, Activity,
} from 'lucide-react';
import { Card, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { LoadingState, ErrorState, EmptyState } from '@/components/ui/States';
import { useWorkspace } from '@/contexts/WorkspaceContext';
import { useNotifications } from '@/contexts/NotificationContext';
import * as engine from '@/api/engineClient';
import { cn } from '@/lib/utils';

type Tab = 'workspaces' | 'services' | 'autonomous' | 'cache';

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState<Tab>('workspaces');

  const tabs: { id: Tab; label: string; icon: React.ElementType }[] = [
    { id: 'workspaces', label: 'Workspaces', icon: FolderOpen },
    { id: 'services', label: 'Services', icon: Server },
    { id: 'autonomous', label: 'Autonomous Worker', icon: Activity },
    { id: 'cache', label: 'Cache', icon: Database },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-3">
          <Settings className="w-7 h-7 text-gray-400" />
          Settings
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Manage workspaces, services, and system configuration
        </p>
      </div>

      {/* Tabs */}
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

      <div className="page-enter">
        {activeTab === 'workspaces' && <WorkspacesPanel />}
        {activeTab === 'services' && <ServicesPanel />}
        {activeTab === 'autonomous' && <AutonomousPanel />}
        {activeTab === 'cache' && <CachePanel />}
      </div>
    </div>
  );
}

// ===== Workspaces =====
function WorkspacesPanel() {
  const { workspace, workspaces, setWorkspace, registerWorkspace, removeWorkspace, isLoading } = useWorkspace();
  const { addToast } = useNotifications();
  const [newPath, setNewPath] = useState('');
  const [newName, setNewName] = useState('');

  const handleRegister = async () => {
    if (!newPath) return;
    try {
      await registerWorkspace(newPath, newName || undefined);
      addToast('success', 'Workspace registered', newPath);
      setNewPath('');
      setNewName('');
    } catch (e: any) {
      addToast('error', 'Failed to register workspace', e.message);
    }
  };

  return (
    <div className="space-y-5">
      {/* Add new workspace */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Plus className="w-4 h-4 text-accent-green" />
            Register Workspace
          </CardTitle>
        </CardHeader>
        <div className="grid grid-cols-12 gap-3">
          <div className="col-span-6">
            <label className="block text-xs text-gray-400 mb-1.5">Path *</label>
            <input
              value={newPath}
              onChange={(e) => setNewPath(e.target.value)}
              placeholder="D:\Projects\my-project"
              className="w-full bg-surface-3 border border-surface-4 text-gray-200 placeholder-gray-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand-500"
            />
          </div>
          <div className="col-span-4">
            <label className="block text-xs text-gray-400 mb-1.5">Name (optional)</label>
            <input
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="My Project"
              className="w-full bg-surface-3 border border-surface-4 text-gray-200 placeholder-gray-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand-500"
            />
          </div>
          <div className="col-span-2 flex items-end">
            <button
              onClick={handleRegister}
              disabled={!newPath}
              className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-brand-600 hover:bg-brand-700 disabled:opacity-40 rounded-lg text-sm font-medium transition-colors"
            >
              <Plus className="w-4 h-4" />
              Add
            </button>
          </div>
        </div>
      </Card>

      {/* Workspace list */}
      <Card>
        <CardHeader>
          <CardTitle>Registered Workspaces</CardTitle>
          <Badge variant="info">{workspaces.length} workspaces</Badge>
        </CardHeader>

        {isLoading ? (
          <LoadingState message="Loading workspaces..." />
        ) : workspaces.length > 0 ? (
          <div className="space-y-2">
            {workspaces.map((ws) => (
              <div
                key={ws.id}
                className={cn(
                  'flex items-center gap-3 rounded-lg p-3 border transition-colors cursor-pointer',
                  ws.path === workspace
                    ? 'bg-brand-600/10 border-brand-600/30'
                    : 'bg-surface-3/30 border-surface-4/50 hover:bg-surface-3/50'
                )}
                onClick={() => setWorkspace(ws.path)}
              >
                <FolderOpen className={cn('w-4 h-4', ws.path === workspace ? 'text-brand-400' : 'text-gray-500')} />
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-gray-300">{ws.name || ws.path.split(/[/\\]/).pop()}</p>
                  <p className="text-[10px] text-gray-600 font-mono truncate">{ws.path}</p>
                </div>
                <div className="flex items-center gap-2">
                  {ws.framework && <Badge variant="default">{ws.framework}</Badge>}
                  {ws.language && <Badge variant="info">{ws.language}</Badge>}
                  {ws.path === workspace && <Badge variant="success">Active</Badge>}
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      removeWorkspace(ws.id);
                      addToast('info', 'Workspace removed');
                    }}
                    className="p-1.5 rounded-lg hover:bg-accent-red/10 text-gray-600 hover:text-accent-red transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState message="No workspaces registered yet" />
        )}
      </Card>
    </div>
  );
}

// ===== Services =====
function ServicesPanel() {
  const [statuses, setStatuses] = useState<ServiceStatus[]>([]);

  React.useEffect(() => {
    window.electronAPI?.getServiceStatuses?.().then(setStatuses).catch(() => {});
    const unsub = window.electronAPI?.onServiceStatus?.(setStatuses);
    return () => unsub?.();
  }, []);

  const handleAction = async (serviceId: string, action: 'start' | 'stop' | 'restart') => {
    try {
      const fns = {
        start: window.electronAPI?.startService,
        stop: window.electronAPI?.stopService,
        restart: window.electronAPI?.restartService,
      };
      const result = await fns[action]?.(serviceId);
      if (result) setStatuses(result);
    } catch {}
  };

  const statusColors: Record<string, string> = {
    running: 'text-accent-green',
    starting: 'text-accent-amber',
    stopped: 'text-gray-500',
    error: 'text-accent-red',
    disabled: 'text-gray-700',
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Server className="w-4 h-4 text-brand-400" />
          Backend Services
        </CardTitle>
      </CardHeader>

      {statuses.length > 0 ? (
        <div className="space-y-3">
          {statuses.map((svc) => (
            <div key={svc.id} className="flex items-center gap-4 bg-surface-3/30 rounded-lg p-4 border border-surface-4/50">
              <div className={cn('w-3 h-3 rounded-full', svc.status === 'running' ? 'bg-accent-green animate-pulse' : svc.status === 'error' ? 'bg-accent-red' : 'bg-gray-600')} />
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-300">{svc.name}</p>
                <p className="text-[10px] text-gray-600">
                  Port {svc.port} · {svc.status}
                  {svc.pid ? ` · PID ${svc.pid}` : ''}
                  {svc.uptime ? ` · Up ${Math.round(svc.uptime / 60)}m` : ''}
                </p>
                {svc.lastError && <p className="text-[10px] text-accent-red mt-0.5 truncate">{svc.lastError}</p>}
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleAction(svc.id, svc.status === 'running' ? 'stop' : 'start')}
                  className={cn(
                    'px-3 py-1 rounded-lg text-xs font-medium transition-colors',
                    svc.status === 'running'
                      ? 'bg-accent-red/10 text-accent-red hover:bg-accent-red/20'
                      : 'bg-accent-green/10 text-accent-green hover:bg-accent-green/20'
                  )}
                >
                  {svc.status === 'running' ? 'Stop' : 'Start'}
                </button>
                <button
                  onClick={() => handleAction(svc.id, 'restart')}
                  className="px-3 py-1 rounded-lg text-xs font-medium bg-surface-4 text-gray-400 hover:text-gray-200 transition-colors"
                >
                  Restart
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState message="No services detected. Are you running inside Electron?" />
      )}
    </Card>
  );
}

// ===== Autonomous Worker =====
function AutonomousPanel() {
  const { workspace } = useWorkspace();
  const { addToast } = useNotifications();

  const { data: status, isLoading, refetch } = useQuery({
    queryKey: ['autonomous-status'],
    queryFn: engine.getAutonomousStatus,
  });

  const initMutation = useMutation({
    mutationFn: () => engine.initializeAutonomous(workspace),
    onSuccess: () => {
      addToast('success', 'Autonomous worker initialized');
      refetch();
    },
  });

  const [thresholds, setThresholds] = useState({
    risk_threshold: 5.0,
    scan_interval: 300,
    drift_sensitivity: 0.5,
  });

  const configureMutation = useMutation({
    mutationFn: () => engine.configureAutonomous(workspace, thresholds),
    onSuccess: () => addToast('success', 'Configuration updated'),
  });

  return (
    <div className="space-y-5">
      {/* Status */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="w-4 h-4 text-accent-purple" />
            Worker Status
          </CardTitle>
          <div className="flex gap-2">
            <button
              onClick={() => initMutation.mutate()}
              disabled={initMutation.isPending}
              className="flex items-center gap-2 px-3 py-1.5 bg-brand-600 hover:bg-brand-700 disabled:opacity-50 rounded-lg text-xs font-medium transition-colors"
            >
              {initMutation.isPending ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Activity className="w-3.5 h-3.5" />}
              Initialize
            </button>
            <button
              onClick={() => refetch()}
              className="px-3 py-1.5 bg-surface-3 hover:bg-surface-4 border border-surface-4 rounded-lg text-xs text-gray-400 transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5" />
            </button>
          </div>
        </CardHeader>
        {isLoading ? (
          <LoadingState message="Loading status..." />
        ) : status ? (
          <pre className="bg-surface-3/50 rounded-lg p-4 text-xs text-gray-300 font-mono overflow-x-auto whitespace-pre-wrap">
            {JSON.stringify(status, null, 2)}
          </pre>
        ) : (
          <EmptyState message="Worker not initialized" />
        )}
      </Card>

      {/* Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sliders className="w-4 h-4 text-brand-400" />
            Configuration
          </CardTitle>
        </CardHeader>
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="block text-xs text-gray-400 mb-1.5">Risk Threshold</label>
            <input
              type="number"
              min={1}
              max={10}
              step={0.5}
              value={thresholds.risk_threshold}
              onChange={(e) => setThresholds((p) => ({ ...p, risk_threshold: Number(e.target.value) }))}
              className="w-full bg-surface-3 border border-surface-4 text-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand-500"
            />
            <p className="text-[10px] text-gray-600 mt-1">Alert when risk exceeds this</p>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1.5">Scan Interval (s)</label>
            <input
              type="number"
              min={60}
              max={3600}
              step={60}
              value={thresholds.scan_interval}
              onChange={(e) => setThresholds((p) => ({ ...p, scan_interval: Number(e.target.value) }))}
              className="w-full bg-surface-3 border border-surface-4 text-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand-500"
            />
            <p className="text-[10px] text-gray-600 mt-1">Seconds between auto-scans</p>
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1.5">Drift Sensitivity</label>
            <input
              type="number"
              min={0.1}
              max={1.0}
              step={0.1}
              value={thresholds.drift_sensitivity}
              onChange={(e) => setThresholds((p) => ({ ...p, drift_sensitivity: Number(e.target.value) }))}
              className="w-full bg-surface-3 border border-surface-4 text-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand-500"
            />
            <p className="text-[10px] text-gray-600 mt-1">0.1 = strict, 1.0 = lenient</p>
          </div>
        </div>
        <div className="mt-4">
          <button
            onClick={() => configureMutation.mutate()}
            disabled={configureMutation.isPending}
            className="flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-700 disabled:opacity-50 rounded-lg text-sm font-medium transition-colors"
          >
            {configureMutation.isPending ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle className="w-3.5 h-3.5" />}
            Save Configuration
          </button>
        </div>
      </Card>
    </div>
  );
}

// ===== Cache Management =====
function CachePanel() {
  const { addToast } = useNotifications();
  const queryClient = useQueryClient();

  const { data: stats, isLoading, refetch } = useQuery({
    queryKey: ['cache-stats'],
    queryFn: engine.getCacheStats,
  });

  const clearMutation = useMutation({
    mutationFn: engine.clearCache,
    onSuccess: () => {
      addToast('success', 'Cache cleared');
      refetch();
      queryClient.clear();
    },
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Database className="w-4 h-4 text-accent-amber" />
          Cache Management
        </CardTitle>
        <div className="flex gap-2">
          <button
            onClick={() => refetch()}
            className="px-3 py-1.5 bg-surface-3 hover:bg-surface-4 border border-surface-4 rounded-lg text-xs text-gray-400 transition-colors"
          >
            <RefreshCw className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => clearMutation.mutate()}
            disabled={clearMutation.isPending}
            className="flex items-center gap-2 px-3 py-1.5 bg-accent-red/10 text-accent-red hover:bg-accent-red/20 rounded-lg text-xs font-medium transition-colors"
          >
            {clearMutation.isPending ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Trash2 className="w-3.5 h-3.5" />}
            Clear All
          </button>
        </div>
      </CardHeader>

      {isLoading ? (
        <LoadingState message="Loading cache stats..." />
      ) : stats ? (
        <div className="grid grid-cols-3 gap-4">
          {Object.entries(stats).map(([key, val]) => (
            <div key={key} className="bg-surface-3/30 rounded-lg p-3 border border-surface-4/50">
              <p className="text-xs text-gray-500 capitalize">{key.replace(/_/g, ' ')}</p>
              <p className="text-lg font-bold text-white mt-1">
                {typeof val === 'number' ? val.toLocaleString() : String(val)}
              </p>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState message="No cache stats available" />
      )}
    </Card>
  );
}
