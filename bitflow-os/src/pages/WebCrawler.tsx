import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Globe, Play, Pause, Square, RotateCcw, Clock, FileText,
  Link2, AlertCircle, Zap, Settings2, ChevronDown, ExternalLink,
} from 'lucide-react';
import { Card, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { LoadingState, ErrorState, EmptyState } from '@/components/ui/States';
import * as crawler from '@/api/crawlerClient';
import type { CrawlConfig } from '@/api/types';
import { cn } from '@/lib/utils';

type Tab = 'crawl' | 'active' | 'history';

export default function WebCrawler() {
  const [activeTab, setActiveTab] = useState<Tab>('crawl');

  const tabs: { id: Tab; label: string; icon: React.ElementType }[] = [
    { id: 'crawl', label: 'New Crawl', icon: Play },
    { id: 'active', label: 'Active Crawls', icon: Zap },
    { id: 'history', label: 'Crawl History', icon: Clock },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-3">
          <Globe className="w-7 h-7 text-brand-400" />
          Web Crawler
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          Crawl, extract, and analyze website structures
        </p>
      </div>

      {/* Health Check */}
      <CrawlerHealthBar />

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
        {activeTab === 'crawl' && <NewCrawlPanel onStarted={() => setActiveTab('active')} />}
        {activeTab === 'active' && <ActiveCrawlsPanel />}
        {activeTab === 'history' && <CrawlHistoryPanel />}
      </div>
    </div>
  );
}

// ===== Crawler Health Bar =====
function CrawlerHealthBar() {
  const { data, isLoading } = useQuery({
    queryKey: ['crawler-health'],
    queryFn: crawler.getCrawlerHealth,
    refetchInterval: 10000,
  });

  if (isLoading) return null;

  const isOnline = !!data;

  return (
    <div className={cn(
      'flex items-center gap-3 px-4 py-2 rounded-lg text-xs',
      isOnline
        ? 'bg-accent-green/5 border border-accent-green/20 text-accent-green'
        : 'bg-accent-red/5 border border-accent-red/20 text-accent-red'
    )}>
      <div className={cn('w-2 h-2 rounded-full', isOnline ? 'bg-accent-green animate-pulse' : 'bg-accent-red')} />
      <span className="font-medium">{isOnline ? 'Crawler Service Online' : 'Crawler Service Offline'}</span>
      {isOnline && data?.version && (
        <span className="text-gray-500 ml-auto">v{data.version}</span>
      )}
    </div>
  );
}

// ===== New Crawl Panel =====
function NewCrawlPanel({ onStarted }: { onStarted: () => void }) {
  const queryClient = useQueryClient();

  const [formData, setFormData] = useState({
    url: '',
    depth: 3,
    concurrency: 5,
    delay: 1.0,
    include_regex: '',
    exclude_regex: '',
    respectRobots: true,
  });

  const startMutation = useMutation({
    mutationFn: () => {
      const config: CrawlConfig = {
        url: formData.url,
        depth: formData.depth,
        concurrency: formData.concurrency,
        delay: formData.delay,
        user_agent_strategy: 'random',
        allow_regex: formData.include_regex || undefined,
        deny_regex: formData.exclude_regex || undefined,
      };
      return crawler.startCrawl(config);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['active-crawls'] });
      onStarted();
    },
  });

  const updateField = (field: string, value: any) =>
    setFormData((prev) => ({ ...prev, [field]: value }));

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Settings2 className="w-4 h-4 text-brand-400" />
          Crawl Configuration
        </CardTitle>
      </CardHeader>

      <div className="space-y-5">
        {/* Target URL */}
        <div>
          <label className="block text-xs text-gray-400 mb-1.5">Target URL *</label>
          <input
            type="url"
            value={formData.url}
            onChange={(e) => updateField('url', e.target.value)}
            placeholder="https://example.com"
            className="w-full bg-surface-3 border border-surface-4 text-gray-200 placeholder-gray-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand-500 focus:ring-1 focus:ring-brand-500/30"
          />
        </div>

        {/* Grid row */}
        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="block text-xs text-gray-400 mb-1.5">Max Depth</label>
            <input
              type="number"
              min={1}
              max={20}
              value={formData.depth}
              onChange={(e) => updateField('depth', Number(e.target.value))}
              className="w-full bg-surface-3 border border-surface-4 text-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand-500"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1.5">Concurrency</label>
            <input
              type="number"
              min={1}
              max={50}
              value={formData.concurrency}
              onChange={(e) => updateField('concurrency', Number(e.target.value))}
              className="w-full bg-surface-3 border border-surface-4 text-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand-500"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1.5">Delay (sec)</label>
            <input
              type="number"
              min={0}
              max={30}
              step={0.5}
              value={formData.delay}
              onChange={(e) => updateField('delay', Number(e.target.value))}
              className="w-full bg-surface-3 border border-surface-4 text-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand-500"
            />
          </div>
        </div>

        {/* Regex filters */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-xs text-gray-400 mb-1.5">Include Regex</label>
            <input
              type="text"
              value={formData.include_regex}
              onChange={(e) => updateField('include_regex', e.target.value)}
              placeholder="e.g. /blog/.*"
              className="w-full bg-surface-3 border border-surface-4 text-gray-200 placeholder-gray-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand-500"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1.5">Exclude Regex</label>
            <input
              type="text"
              value={formData.exclude_regex}
              onChange={(e) => updateField('exclude_regex', e.target.value)}
              placeholder="e.g. .*\\.pdf$"
              className="w-full bg-surface-3 border border-surface-4 text-gray-200 placeholder-gray-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand-500"
            />
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-between pt-2">
          <p className="text-[11px] text-gray-600">
            {formData.url ? `Will crawl up to ${formData.depth} levels deep with ${formData.concurrency} parallel workers` : 'Enter a URL to start'}
          </p>
          <button
            onClick={() => startMutation.mutate()}
            disabled={!formData.url || startMutation.isPending}
            className="flex items-center gap-2 px-5 py-2 bg-brand-600 hover:bg-brand-700 disabled:opacity-40 disabled:cursor-not-allowed rounded-lg text-sm font-medium transition-colors"
          >
            {startMutation.isPending ? (
              <RotateCcw className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4" />
            )}
            {startMutation.isPending ? 'Starting...' : 'Start Crawl'}
          </button>
        </div>

        {startMutation.error && (
          <div className="flex items-center gap-2 text-accent-red text-xs bg-accent-red/5 border border-accent-red/20 rounded-lg px-3 py-2">
            <AlertCircle className="w-3.5 h-3.5" />
            Failed to start crawl. Is the crawler service running?
          </div>
        )}
      </div>
    </Card>
  );
}

// ===== Active Crawls =====
function ActiveCrawlsPanel() {
  const [crawlIds, setCrawlIds] = useState<string[]>([]);

  // Poll for crawl status if we have active IDs
  const statusQueries = crawlIds.map((id) =>
    useQuery({
      queryKey: ['crawl-status', id],
      queryFn: () => crawler.getCrawlStatus(id),
      refetchInterval: 3000,
    })
  );

  // Note: In a real scenario, we'd track IDs from startCrawl responses
  // For now, show a placeholder or fetch from server
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Zap className="w-4 h-4 text-accent-amber" />
          Active Crawls
        </CardTitle>
      </CardHeader>

      {crawlIds.length === 0 ? (
        <div className="text-center py-8">
          <Zap className="w-8 h-8 text-gray-600 mx-auto mb-3" />
          <p className="text-sm text-gray-500">No active crawls right now</p>
          <p className="text-xs text-gray-600 mt-1">Start a new crawl from the "New Crawl" tab</p>
        </div>
      ) : (
        <div className="space-y-3">
          {statusQueries.map((query, i) => {
            const status = query.data;
            return (
              <div key={crawlIds[i]} className="bg-surface-3/30 border border-surface-4/50 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <div>
                    <p className="text-sm font-medium text-gray-300">{status?.url || crawlIds[i]}</p>
                    <p className="text-[11px] text-gray-600 mt-0.5">ID: {crawlIds[i]}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    <CrawlControlButton crawlId={crawlIds[i]} action="pause" />
                    <CrawlControlButton crawlId={crawlIds[i]} action="resume" />
                    <CrawlControlButton crawlId={crawlIds[i]} action="stop" />
                  </div>
                </div>
                {status && (
                  <div className="grid grid-cols-4 gap-4 text-center">
                    <div>
                      <p className="text-lg font-bold text-white">{status.pages_crawled ?? 0}</p>
                      <p className="text-[10px] text-gray-600">Pages</p>
                    </div>
                    <div>
                      <p className="text-lg font-bold text-brand-400">{status.pages_queued ?? 0}</p>
                      <p className="text-[10px] text-gray-600">Queued</p>
                    </div>
                    <div>
                      <p className="text-lg font-bold text-accent-red">{status.errors ?? 0}</p>
                      <p className="text-[10px] text-gray-600">Errors</p>
                    </div>
                    <div>
                      <p className="text-lg font-bold text-accent-green">{status.status ?? '—'}</p>
                      <p className="text-[10px] text-gray-600">Status</p>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </Card>
  );
}

function CrawlControlButton({ crawlId, action }: { crawlId: string; action: 'pause' | 'resume' | 'stop' }) {
  const queryClient = useQueryClient();
  const mutation = useMutation({
    mutationFn: () => crawler.controlCrawl(crawlId, action),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['crawl-status', crawlId] }),
  });

  const icons = { pause: Pause, resume: Play, stop: Square };
  const colors = { pause: 'text-accent-amber', resume: 'text-accent-green', stop: 'text-accent-red' };
  const Icon = icons[action];

  return (
    <button
      onClick={() => mutation.mutate()}
      disabled={mutation.isPending}
      className={cn('p-1.5 rounded-lg hover:bg-surface-4 transition-colors', colors[action])}
      title={action.charAt(0).toUpperCase() + action.slice(1)}
    >
      <Icon className="w-3.5 h-3.5" />
    </button>
  );
}

// ===== Crawl History =====
function CrawlHistoryPanel() {
  // This would fetch from the crawler's history endpoint
  // For now, show placeholder until we integrate with the actual API
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-gray-400" />
          Crawl History
        </CardTitle>
      </CardHeader>
      <div className="text-center py-8">
        <Clock className="w-8 h-8 text-gray-600 mx-auto mb-3" />
        <p className="text-sm text-gray-500">Previous crawl results will appear here</p>
        <p className="text-xs text-gray-600 mt-1">Start a crawl to populate this history</p>
      </div>
    </Card>
  );
}
