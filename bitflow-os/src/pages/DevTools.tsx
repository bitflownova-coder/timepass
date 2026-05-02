import React, { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import {
  Wrench, Database, Sparkles, Radar, Layers, AlertTriangle,
  Play, RefreshCw, Copy, CheckCircle, XCircle, Search,
  FileCode, ChevronRight, ExternalLink,
} from 'lucide-react';
import { Card, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { LoadingState, ErrorState, EmptyState } from '@/components/ui/States';
import { useWorkspace } from '@/contexts/WorkspaceContext';
import { useNotifications } from '@/contexts/NotificationContext';
import * as engine from '@/api/engineClient';
import { cn, getSeverityColor } from '@/lib/utils';

type Tab = 'sql' | 'prompt' | 'api' | 'stack' | 'error';

export default function DevTools() {
  const [activeTab, setActiveTab] = useState<Tab>('prompt');

  const tabs: { id: Tab; label: string; icon: React.ElementType }[] = [
    { id: 'prompt', label: 'Prompt Builder', icon: Sparkles },
    { id: 'error', label: 'Error Parser', icon: AlertTriangle },
    { id: 'sql', label: 'SQL Analyzer', icon: Database },
    { id: 'api', label: 'API Explorer', icon: Radar },
    { id: 'stack', label: 'Stack Detector', icon: Layers },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white flex items-center gap-3">
          <Wrench className="w-7 h-7 text-brand-400" />
          Dev Tools
        </h1>
        <p className="text-sm text-gray-500 mt-1">
          SQL analysis, prompt optimization, API discovery, and more
        </p>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 bg-surface-2 border border-surface-4 rounded-xl p-1 overflow-x-auto">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={cn(
                'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all whitespace-nowrap',
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
        {activeTab === 'prompt' && <PromptBuilderPanel />}
        {activeTab === 'error' && <ErrorParserPanel />}
        {activeTab === 'sql' && <SQLAnalyzerPanel />}
        {activeTab === 'api' && <APIExplorerPanel />}
        {activeTab === 'stack' && <StackDetectorPanel />}
      </div>
    </div>
  );
}

// ===== Prompt Builder =====
function PromptBuilderPanel() {
  const { workspace } = useWorkspace();
  const { addToast } = useNotifications();
  const [task, setTask] = useState('');
  const [currentFile, setCurrentFile] = useState('');
  const [errorText, setErrorText] = useState('');
  const [mode, setMode] = useState<'optimize' | 'context' | 'debug'>('optimize');

  const mutation = useMutation({
    mutationFn: () => {
      if (mode === 'optimize') {
        return engine.optimizePrompt({
          workspace_path: workspace,
          task,
          current_file: currentFile || undefined,
          error_text: errorText || undefined,
        });
      } else if (mode === 'context') {
        return engine.buildContext({
          workspace_path: workspace,
          task,
          current_file: currentFile || undefined,
          include_schema: true,
        });
      } else {
        return engine.debugContext({
          error_text: errorText || task,
          workspace_path: workspace,
          file_path: currentFile || undefined,
        });
      }
    },
  });

  const result = mutation.data;

  const copyToClipboard = () => {
    if (result?.prompt) {
      navigator.clipboard.writeText(result.prompt);
      addToast('success', 'Copied to clipboard');
    }
  };

  return (
    <div className="grid grid-cols-2 gap-5">
      {/* Input */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-accent-purple" />
            Build AI Prompt
          </CardTitle>
        </CardHeader>

        <div className="space-y-4">
          {/* Mode selector */}
          <div className="flex gap-2">
            {[
              { id: 'optimize' as const, label: 'Optimize' },
              { id: 'context' as const, label: 'Context' },
              { id: 'debug' as const, label: 'Debug' },
            ].map((m) => (
              <button
                key={m.id}
                onClick={() => setMode(m.id)}
                className={cn(
                  'px-3 py-1.5 rounded-lg text-xs font-medium transition-colors',
                  mode === m.id ? 'bg-brand-600/20 text-brand-400' : 'bg-surface-3 text-gray-500 hover:text-gray-300'
                )}
              >
                {m.label}
              </button>
            ))}
          </div>

          <div>
            <label className="block text-xs text-gray-400 mb-1.5">Task / Question *</label>
            <textarea
              value={task}
              onChange={(e) => setTask(e.target.value)}
              placeholder={mode === 'debug' ? 'Paste the error or describe the bug...' : 'What do you want AI to help with?'}
              rows={4}
              className="w-full bg-surface-3 border border-surface-4 text-gray-200 placeholder-gray-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand-500 resize-none"
            />
          </div>

          <div>
            <label className="block text-xs text-gray-400 mb-1.5">Current File (optional)</label>
            <input
              value={currentFile}
              onChange={(e) => setCurrentFile(e.target.value)}
              placeholder="e.g. src/server.py"
              className="w-full bg-surface-3 border border-surface-4 text-gray-200 placeholder-gray-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand-500"
            />
          </div>

          {mode !== 'context' && (
            <div>
              <label className="block text-xs text-gray-400 mb-1.5">Error Text (optional)</label>
              <textarea
                value={errorText}
                onChange={(e) => setErrorText(e.target.value)}
                placeholder="Paste error output here..."
                rows={3}
                className="w-full bg-surface-3 border border-surface-4 text-gray-200 placeholder-gray-600 rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-brand-500 resize-none font-mono text-xs"
              />
            </div>
          )}

          <button
            onClick={() => mutation.mutate()}
            disabled={!task || mutation.isPending}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-brand-600 hover:bg-brand-700 disabled:opacity-40 rounded-lg text-sm font-medium transition-colors"
          >
            {mutation.isPending ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
            {mutation.isPending ? 'Building...' : `Build ${mode === 'optimize' ? 'Optimized' : mode === 'context' ? 'Context' : 'Debug'} Prompt`}
          </button>
        </div>
      </Card>

      {/* Output */}
      <Card>
        <CardHeader>
          <CardTitle>Generated Prompt</CardTitle>
          {result && (
            <div className="flex items-center gap-2">
              <Badge variant="info">~{result.token_estimate} tokens</Badge>
              <button onClick={copyToClipboard} className="p-1.5 rounded-lg hover:bg-surface-3 text-gray-500 hover:text-gray-200 transition-colors">
                <Copy className="w-4 h-4" />
              </button>
            </div>
          )}
        </CardHeader>

        {mutation.isPending && <LoadingState message="Gathering project context..." />}
        {mutation.error && <ErrorState message="Failed to generate prompt" onRetry={() => mutation.mutate()} />}

        {result ? (
          <div className="space-y-3">
            <pre className="bg-surface-3/50 rounded-lg p-4 text-xs text-gray-300 font-mono overflow-x-auto max-h-[500px] overflow-y-auto whitespace-pre-wrap leading-relaxed">
              {result.prompt}
            </pre>
            {result.metadata && Object.keys(result.metadata).length > 0 && (
              <div className="flex flex-wrap gap-2">
                {Object.entries(result.metadata).map(([key, val]) => (
                  <span key={key} className="text-[10px] text-gray-600 bg-surface-3 px-2 py-0.5 rounded">
                    {key}: {typeof val === 'object' ? JSON.stringify(val) : String(val)}
                  </span>
                ))}
              </div>
            )}
          </div>
        ) : !mutation.isPending ? (
          <div className="text-center py-12">
            <Sparkles className="w-8 h-8 text-gray-600 mx-auto mb-3" />
            <p className="text-sm text-gray-500">Enter a task and click Build to generate</p>
            <p className="text-xs text-gray-600 mt-1">The engine injects your project schemas, API contracts, and file structure automatically</p>
          </div>
        ) : null}
      </Card>
    </div>
  );
}

// ===== Error Parser =====
function ErrorParserPanel() {
  const { workspace } = useWorkspace();
  const [errorText, setErrorText] = useState('');

  const parseMutation = useMutation({
    mutationFn: () => engine.parseError({ error_text: errorText, workspace_path: workspace }),
  });

  const similarMutation = useMutation({
    mutationFn: () => engine.findSimilarErrors({ error_text: errorText, workspace_path: workspace }),
  });

  const parsed = parseMutation.data;

  return (
    <div className="space-y-5">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-accent-amber" />
            Paste Any Error
          </CardTitle>
        </CardHeader>
        <div className="space-y-3">
          <textarea
            value={errorText}
            onChange={(e) => setErrorText(e.target.value)}
            placeholder="Paste terminal error, stack trace, compiler output, etc..."
            rows={6}
            className="w-full bg-surface-3 border border-surface-4 text-gray-200 placeholder-gray-600 rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:border-brand-500 resize-none"
          />
          <div className="flex gap-3">
            <button
              onClick={() => parseMutation.mutate()}
              disabled={!errorText || parseMutation.isPending}
              className="flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-700 disabled:opacity-40 rounded-lg text-sm font-medium transition-colors"
            >
              {parseMutation.isPending ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
              Parse Error
            </button>
            <button
              onClick={() => similarMutation.mutate()}
              disabled={!errorText || similarMutation.isPending}
              className="flex items-center gap-2 px-4 py-2 bg-surface-3 hover:bg-surface-4 border border-surface-4 disabled:opacity-40 rounded-lg text-sm font-medium text-gray-400 transition-colors"
            >
              {similarMutation.isPending ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Search className="w-3.5 h-3.5" />}
              Find Similar
            </button>
          </div>
        </div>
      </Card>

      {/* Parsed Result */}
      {parseMutation.isPending && <LoadingState message="Parsing error..." />}
      {parsed && (
        <Card>
          <CardHeader>
            <CardTitle>Analysis</CardTitle>
            <Badge variant={parsed.error_type === 'unknown' ? 'warning' : 'info'}>{parsed.error_type}</Badge>
          </CardHeader>
          <div className="space-y-3">
            <div className="bg-surface-3/30 rounded-lg p-3 border border-surface-4/50">
              <p className="text-xs font-medium text-gray-300">{parsed.message}</p>
              {parsed.file_path && (
                <p className="text-[11px] text-gray-600 font-mono mt-1">
                  {parsed.file_path}{parsed.line_number ? `:${parsed.line_number}` : ''}
                </p>
              )}
              <p className="text-[11px] text-gray-500 mt-1">Language: {parsed.language}</p>
            </div>

            {parsed.suggestions && parsed.suggestions.length > 0 && (
              <div>
                <p className="text-xs font-medium text-gray-400 mb-2">Suggestions</p>
                <div className="space-y-1.5">
                  {parsed.suggestions.map((s: string, i: number) => (
                    <div key={i} className="flex items-start gap-2 text-xs">
                      <span className="text-accent-green mt-0.5">💡</span>
                      <span className="text-gray-300">{s}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {parsed.related_files && parsed.related_files.length > 0 && (
              <div>
                <p className="text-xs font-medium text-gray-400 mb-1.5">Related Files</p>
                <div className="flex flex-wrap gap-1.5">
                  {parsed.related_files.map((f: string, i: number) => (
                    <span key={i} className="text-[10px] font-mono text-gray-500 bg-surface-3 px-2 py-0.5 rounded">
                      {f}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </Card>
      )}

      {/* Similar Errors */}
      {similarMutation.isPending && <LoadingState message="Searching past errors & fixes..." />}
      {similarMutation.data && (
        <Card>
          <CardHeader>
            <CardTitle>Similar Past Errors & Fixes</CardTitle>
          </CardHeader>
          {Array.isArray(similarMutation.data) && similarMutation.data.length > 0 ? (
            <div className="space-y-2">
              {similarMutation.data.map((item: any, i: number) => (
                <div key={i} className="bg-surface-3/30 rounded-lg p-3 border border-surface-4/50">
                  <p className="text-xs text-gray-300">{item.error_type}: {item.message}</p>
                  {item.fix && <p className="text-[11px] text-accent-green mt-1">Fix: {item.fix}</p>}
                  <p className="text-[10px] text-gray-600 mt-1">{item.timestamp}</p>
                </div>
              ))}
            </div>
          ) : (
            <EmptyState message="No similar past errors found" />
          )}
        </Card>
      )}
    </div>
  );
}

// ===== SQL Analyzer =====
function SQLAnalyzerPanel() {
  const { workspace } = useWorkspace();
  const [query, setQuery] = useState('');
  const [mode, setMode] = useState<'analyze' | 'validate'>('analyze');

  const mutation = useMutation({
    mutationFn: () =>
      mode === 'analyze'
        ? engine.analyzeSQL(query, workspace)
        : engine.validateSQL(query),
  });

  const result = mutation.data;

  return (
    <div className="space-y-5">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Database className="w-4 h-4 text-accent-purple" />
            SQL Query Analyzer
          </CardTitle>
        </CardHeader>
        <div className="space-y-3">
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="SELECT * FROM users WHERE id = $1..."
            rows={5}
            className="w-full bg-surface-3 border border-surface-4 text-gray-200 placeholder-gray-600 rounded-lg px-3 py-2 text-sm font-mono focus:outline-none focus:border-brand-500 resize-none"
          />
          <div className="flex items-center gap-3">
            <div className="flex gap-2">
              {(['analyze', 'validate'] as const).map((m) => (
                <button
                  key={m}
                  onClick={() => setMode(m)}
                  className={cn(
                    'px-3 py-1.5 rounded-lg text-xs font-medium transition-colors capitalize',
                    mode === m ? 'bg-brand-600/20 text-brand-400' : 'bg-surface-3 text-gray-500 hover:text-gray-300'
                  )}
                >
                  {m}
                </button>
              ))}
            </div>
            <button
              onClick={() => mutation.mutate()}
              disabled={!query || mutation.isPending}
              className="flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-700 disabled:opacity-40 rounded-lg text-sm font-medium transition-colors ml-auto"
            >
              {mutation.isPending ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
              {mode === 'analyze' ? 'Analyze' : 'Validate'}
            </button>
          </div>
        </div>
      </Card>

      {mutation.isPending && <LoadingState message={`${mode === 'analyze' ? 'Analyzing' : 'Validating'} SQL...`} />}
      {result && (
        <Card>
          <CardHeader>
            <CardTitle>Results</CardTitle>
          </CardHeader>
          <pre className="bg-surface-3/50 rounded-lg p-4 text-xs text-gray-300 font-mono overflow-x-auto max-h-[400px] overflow-y-auto whitespace-pre-wrap">
            {JSON.stringify(result, null, 2)}
          </pre>
        </Card>
      )}
    </div>
  );
}

// ===== API Explorer =====
function APIExplorerPanel() {
  const { workspace } = useWorkspace();

  const detectMutation = useMutation({
    mutationFn: () => engine.detectAPIs(workspace),
  });

  const result = detectMutation.data;

  return (
    <div className="space-y-5">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Radar className="w-4 h-4 text-accent-green" />
            Discover API Endpoints
          </CardTitle>
          <button
            onClick={() => detectMutation.mutate()}
            disabled={detectMutation.isPending}
            className="flex items-center gap-2 px-3 py-1.5 bg-brand-600 hover:bg-brand-700 disabled:opacity-50 rounded-lg text-xs font-medium transition-colors"
          >
            {detectMutation.isPending ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Radar className="w-3.5 h-3.5" />}
            {detectMutation.isPending ? 'Scanning...' : 'Scan Workspace'}
          </button>
        </CardHeader>
        <p className="text-xs text-gray-500">
          Automatically discovers REST endpoints, route definitions, and API patterns across your codebase
        </p>
      </Card>

      {detectMutation.isPending && <LoadingState message="Scanning for API endpoints..." />}

      {result && (
        <Card>
          <CardHeader>
            <CardTitle>Discovered Endpoints</CardTitle>
            <Badge variant="info">{Array.isArray(result.endpoints) ? result.endpoints.length : '—'} found</Badge>
          </CardHeader>
          {Array.isArray(result.endpoints) && result.endpoints.length > 0 ? (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-[11px] text-gray-600 uppercase tracking-wider border-b border-surface-4">
                    <th className="pb-2 pr-4">Method</th>
                    <th className="pb-2 pr-4">Path</th>
                    <th className="pb-2 pr-4">Handler</th>
                    <th className="pb-2">File</th>
                  </tr>
                </thead>
                <tbody>
                  {result.endpoints.map((ep: any, i: number) => (
                    <tr key={i} className="border-b border-surface-3/50 hover:bg-surface-3/30">
                      <td className="py-2 pr-4">
                        <Badge variant={ep.method === 'GET' ? 'success' : ep.method === 'POST' ? 'info' : ep.method === 'DELETE' ? 'danger' : 'warning'}>
                          {ep.method}
                        </Badge>
                      </td>
                      <td className="py-2 pr-4 text-xs font-mono text-gray-300">{ep.path || ep.route}</td>
                      <td className="py-2 pr-4 text-xs text-gray-400">{ep.handler || ep.function_name}</td>
                      <td className="py-2 text-xs font-mono text-gray-600">{ep.file?.split(/[/\\]/).pop()}:{ep.line}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <pre className="bg-surface-3/50 rounded-lg p-4 text-xs text-gray-300 font-mono overflow-x-auto whitespace-pre-wrap">
              {JSON.stringify(result, null, 2)}
            </pre>
          )}
        </Card>
      )}
    </div>
  );
}

// ===== Stack Detector =====
function StackDetectorPanel() {
  const { workspace } = useWorkspace();

  const mutation = useMutation({
    mutationFn: () => engine.detectStack(workspace),
  });

  const result = mutation.data;

  return (
    <div className="space-y-5">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-brand-400" />
            Tech Stack Detection
          </CardTitle>
          <button
            onClick={() => mutation.mutate()}
            disabled={mutation.isPending}
            className="flex items-center gap-2 px-3 py-1.5 bg-brand-600 hover:bg-brand-700 disabled:opacity-50 rounded-lg text-xs font-medium transition-colors"
          >
            {mutation.isPending ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
            {mutation.isPending ? 'Detecting...' : 'Detect Stack'}
          </button>
        </CardHeader>
        <p className="text-xs text-gray-500">
          Analyzes your workspace to detect languages, frameworks, databases, and tools
        </p>
      </Card>

      {mutation.isPending && <LoadingState message="Analyzing workspace tech stack..." />}

      {result && (
        <Card>
          <CardHeader>
            <CardTitle>Detected Stack</CardTitle>
          </CardHeader>
          {typeof result === 'object' && !Array.isArray(result) ? (
            <div className="grid grid-cols-2 gap-4">
              {Object.entries(result).map(([category, items]) => (
                <div key={category} className="bg-surface-3/30 rounded-lg p-3 border border-surface-4/50">
                  <p className="text-xs font-medium text-gray-400 capitalize mb-2">{category.replace(/_/g, ' ')}</p>
                  {Array.isArray(items) ? (
                    <div className="flex flex-wrap gap-1.5">
                      {(items as string[]).map((item, i) => (
                        <Badge key={i} variant="default">{item}</Badge>
                      ))}
                    </div>
                  ) : typeof items === 'string' ? (
                    <p className="text-sm text-gray-300">{items}</p>
                  ) : (
                    <pre className="text-[10px] text-gray-400 font-mono">{JSON.stringify(items, null, 2)}</pre>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <pre className="bg-surface-3/50 rounded-lg p-4 text-xs text-gray-300 font-mono overflow-x-auto whitespace-pre-wrap">
              {JSON.stringify(result, null, 2)}
            </pre>
          )}
        </Card>
      )}
    </div>
  );
}
