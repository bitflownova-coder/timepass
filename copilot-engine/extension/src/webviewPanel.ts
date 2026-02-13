/**
 * Copilot Engine - Redesigned Dashboard
 * Features:
 *  - Manual + Automatic scanning controls
 *  - Scan results displayed inline (not just output channel)
 *  - Clear loading/empty states
 *  - One-click actions with visible results
 */
import * as vscode from 'vscode';
import { EngineClient } from './engineClient';
import { AutonomousEngine, DashboardData } from './autonomousEngine';
import { BackendManager, BackendStatus } from './backendManager';

export class DashboardPanel {
    private static currentPanel: DashboardPanel | undefined;
    private panel: vscode.WebviewPanel;
    private client: EngineClient;
    private autonomousEngine: AutonomousEngine;
    private backendManager: BackendManager;
    private disposables: vscode.Disposable[] = [];

    private constructor(
        panel: vscode.WebviewPanel,
        client: EngineClient,
        autonomousEngine: AutonomousEngine,
        backendManager: BackendManager
    ) {
        this.panel = panel;
        this.client = client;
        this.autonomousEngine = autonomousEngine;
        this.backendManager = backendManager;

        this.panel.webview.html = this.getHtml();

        this.panel.onDidDispose(() => {
            DashboardPanel.currentPanel = undefined;
            for (const d of this.disposables) { d.dispose(); }
        }, null, this.disposables);

        // Handle messages from webview
        this.panel.webview.onDidReceiveMessage(async (msg) => {
            await this.handleMessage(msg);
        }, null, this.disposables);

        // Subscribe to autonomous engine updates
        this.autonomousEngine.onDashboardUpdate((data) => {
            this.pushDashboardData(data);
        });

        // Subscribe to backend status changes
        this.backendManager.onStatusChange((status) => {
            this.pushBackendStatus(status);
            if (status.health === 'starting') {
                this.panel.webview.postMessage({ 
                    command: 'backendLogs', 
                    logs: this.backendManager.getLogs() 
                });
            }
        });
    }

    static show(
        context: vscode.ExtensionContext,
        client: EngineClient,
        autonomousEngine: AutonomousEngine,
        backendManager: BackendManager
    ): void {
        if (DashboardPanel.currentPanel) {
            DashboardPanel.currentPanel.panel.reveal();
            return;
        }

        const panel = vscode.window.createWebviewPanel(
            'copilotEngineDashboard',
            '⚡ Copilot Engine',
            vscode.ViewColumn.One,
            { enableScripts: true, retainContextWhenHidden: true }
        );

        DashboardPanel.currentPanel = new DashboardPanel(panel, client, autonomousEngine, backendManager);
    }

    private pushDashboardData(data: DashboardData): void {
        this.panel.webview.postMessage({ command: 'dashboard', data });
    }

    private pushBackendStatus(status: BackendStatus): void {
        this.panel.webview.postMessage({ command: 'backendStatus', status });
    }

    private async handleMessage(msg: any): Promise<void> {
        const workspacePath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
        
        // Debug logging - shows in Output channel
        console.log(`[Dashboard] Received message: ${msg.command}`);
        
        try {
            switch (msg.command) {
                // === Initialization ===
                case 'webviewReady': {
                    console.log('[Dashboard] Webview ready, detecting backend...');
                    await this.backendManager.detectExisting();
                    this.pushBackendStatus(this.backendManager.getStatus());
                    this.panel.webview.postMessage({ 
                        command: 'backendLogs', 
                        logs: this.backendManager.getLogs() 
                    });
                    // Try to get dashboard data
                    if (workspacePath) {
                        const dashData = await this.autonomousEngine.refreshDashboard(workspacePath);
                        if (dashData) {
                            this.pushDashboardData(dashData);
                        }
                    }
                    break;
                }

                // === Backend Controls ===
                case 'startBackend': {
                    console.log('[Dashboard] Starting backend...');
                    await this.backendManager.start();
                    this.pushBackendStatus(this.backendManager.getStatus());
                    this.panel.webview.postMessage({ 
                        command: 'backendLogs', 
                        logs: this.backendManager.getLogs() 
                    });
                    break;
                }
                case 'stopBackend': {
                    console.log('[Dashboard] Stopping backend...');
                    this.backendManager.stop();
                    this.pushBackendStatus(this.backendManager.getStatus());
                    this.panel.webview.postMessage({ 
                        command: 'backendLogs', 
                        logs: this.backendManager.getLogs() 
                    });
                    break;
                }
                case 'restartBackend': {
                    console.log('[Dashboard] Restarting backend...');
                    await this.backendManager.restart();
                    this.pushBackendStatus(this.backendManager.getStatus());
                    this.panel.webview.postMessage({ 
                        command: 'backendLogs', 
                        logs: this.backendManager.getLogs() 
                    });
                    break;
                }
                case 'refreshBackend': {
                    console.log('[Dashboard] Refreshing backend status...');
                    await this.backendManager.detectExisting();
                    this.pushBackendStatus(this.backendManager.getStatus());
                    this.panel.webview.postMessage({ 
                        command: 'backendLogs', 
                        logs: this.backendManager.getLogs() 
                    });
                    break;
                }

            // === Manual Scans with Results ===
            case 'initializeWorkspace': {
                if (!workspacePath) {
                    console.log('[Dashboard] No workspace folder open');
                    vscode.window.showWarningMessage('No workspace folder open');
                    break;
                }
                console.log(`[Dashboard] Initializing workspace: ${workspacePath}`);
                this.panel.webview.postMessage({ command: 'scanStarted', scanType: 'initialize' });
                try {
                    const result = await this.client.post<any>('/autonomous/initialize', {
                        workspace_path: workspacePath
                    });
                    console.log('[Dashboard] Initialize complete:', result);
                    this.panel.webview.postMessage({ 
                        command: 'scanResults', 
                        scanType: 'initialize',
                        result 
                    });
                    // Refresh dashboard after init
                    const dashData = await this.autonomousEngine.refreshDashboard(workspacePath);
                    if (dashData) this.pushDashboardData(dashData);
                } catch (e: any) {
                    console.error('[Dashboard] Initialize error:', e);
                    this.panel.webview.postMessage({ 
                        command: 'scanComplete', 
                        scanType: 'initialize',
                        success: false,
                        error: e.message 
                    });
                }
                break;
            }

            case 'runFullScan': {
                if (!workspacePath) {
                    console.log('[Dashboard] No workspace folder open');
                    vscode.window.showWarningMessage('No workspace folder open');
                    break;
                }
                console.log(`[Dashboard] Running full scan on: ${workspacePath}`);
                this.panel.webview.postMessage({ command: 'scanStarted', scanType: 'fullScan' });
                try {
                    const result = await this.client.post<any>('/pipeline/full-scan', {
                        workspace_path: workspacePath
                    });
                    console.log('[Dashboard] Full scan complete, issues:', result?.issues?.length || 0);
                    this.panel.webview.postMessage({ 
                        command: 'scanResults', 
                        scanType: 'fullScan',
                        result 
                    });
                } catch (e: any) {
                    console.error('[Dashboard] Full scan error:', e);
                    this.panel.webview.postMessage({ 
                        command: 'scanComplete', 
                        scanType: 'fullScan',
                        success: false,
                        error: e.message 
                    });
                }
                break;
            }

            case 'runSecurityScan': {
                if (!workspacePath) break;
                this.panel.webview.postMessage({ command: 'scanStarted', scanType: 'security' });
                try {
                    const result = await this.client.post<any>('/security/scan-workspace', {
                        workspace_path: workspacePath
                    });
                    this.panel.webview.postMessage({ 
                        command: 'scanResults', 
                        scanType: 'security',
                        result 
                    });
                } catch (e: any) {
                    this.panel.webview.postMessage({ 
                        command: 'scanComplete', 
                        scanType: 'security',
                        success: false,
                        error: e.message 
                    });
                }
                break;
            }

            case 'runContractScan': {
                if (!workspacePath) break;
                this.panel.webview.postMessage({ command: 'scanStarted', scanType: 'contracts' });
                try {
                    const result = await this.client.post<any>('/contracts/validate', {
                        workspace_path: workspacePath
                    });
                    this.panel.webview.postMessage({ 
                        command: 'scanResults', 
                        scanType: 'contracts',
                        result 
                    });
                } catch (e: any) {
                    this.panel.webview.postMessage({ 
                        command: 'scanComplete', 
                        scanType: 'contracts',
                        success: false,
                        error: e.message 
                    });
                }
                break;
            }

            case 'runGitAnalysis': {
                if (!workspacePath) break;
                this.panel.webview.postMessage({ command: 'scanStarted', scanType: 'git' });
                try {
                    const result = await this.client.post<any>('/git/diff', {
                        workspace_path: workspacePath
                    });
                    this.panel.webview.postMessage({ 
                        command: 'scanResults', 
                        scanType: 'git',
                        result 
                    });
                } catch (e: any) {
                    this.panel.webview.postMessage({ 
                        command: 'scanComplete', 
                        scanType: 'git',
                        success: false,
                        error: e.message 
                    });
                }
                break;
            }

            case 'detectEndpoints': {
                if (!workspacePath) break;
                this.panel.webview.postMessage({ command: 'scanStarted', scanType: 'endpoints' });
                try {
                    const result = await this.client.post<any>('/api/detect', {
                        workspace_path: workspacePath
                    });
                    this.panel.webview.postMessage({ 
                        command: 'scanResults', 
                        scanType: 'endpoints',
                        result 
                    });
                } catch (e: any) {
                    this.panel.webview.postMessage({ 
                        command: 'scanComplete', 
                        scanType: 'endpoints',
                        success: false,
                        error: e.message 
                    });
                }
                break;
            }

            case 'detectStack': {
                if (!workspacePath) break;
                this.panel.webview.postMessage({ command: 'scanStarted', scanType: 'stack' });
                try {
                    const result = await this.client.post<any>('/stack/detect', {
                        workspace_path: workspacePath
                    });
                    this.panel.webview.postMessage({ 
                        command: 'scanResults', 
                        scanType: 'stack',
                        result 
                    });
                } catch (e: any) {
                    this.panel.webview.postMessage({ 
                        command: 'scanComplete', 
                        scanType: 'stack',
                        success: false,
                        error: e.message 
                    });
                }
                break;
            }

            // === Refresh Dashboard Data ===
            case 'refreshDashboard': {
                if (!workspacePath) break;
                this.panel.webview.postMessage({ command: 'refreshing' });
                const dashData = await this.autonomousEngine.refreshDashboard(workspacePath);
                if (dashData) {
                    this.pushDashboardData(dashData);
                }
                this.panel.webview.postMessage({ command: 'refreshComplete' });
                break;
            }

            // === File Navigation ===
            case 'openFile': {
                if (msg.filePath) {
                    try {
                        const doc = await vscode.workspace.openTextDocument(msg.filePath);
                        await vscode.window.showTextDocument(doc, {
                            selection: msg.line ? new vscode.Range(msg.line - 1, 0, msg.line - 1, 0) : undefined,
                        });
                    } catch (e) {
                        vscode.window.showErrorMessage(`Could not open file: ${msg.filePath}`);
                    }
                }
                break;
            }

            // === Settings ===
            case 'openSettings':
                await vscode.commands.executeCommand('workbench.action.openSettings', 'copilotEngine');
                break;
            case 'showOutput':
                await vscode.commands.executeCommand('copilotEngine.showStatus');
                break;
            
            default:
                console.log(`[Dashboard] Unknown command: ${msg.command}`);
                break;
            }
        } catch (err: any) {
            console.error(`[Dashboard] Error handling message ${msg.command}:`, err);
            vscode.window.showErrorMessage(`Dashboard error: ${err.message}`);
        }
    }

    private getHtml(): string {
        return /*html*/`<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{
  font-family:var(--vscode-font-family);
  color:var(--vscode-foreground);
  background:var(--vscode-editor-background);
  line-height:1.5;
  overflow-y:auto;
}
::-webkit-scrollbar{width:6px}
::-webkit-scrollbar-thumb{background:var(--vscode-scrollbarSlider-background);border-radius:3px}

.shell{max-width:1100px;margin:0 auto;padding:20px}

/* Header */
.header{display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;padding-bottom:12px;border-bottom:1px solid var(--vscode-panel-border)}
.header h1{font-size:18px;font-weight:700;display:flex;align-items:center;gap:8px}
.header h1 .emoji{font-size:22px}
.header-actions{display:flex;gap:8px}
.icon-btn{padding:6px 10px;border-radius:4px;background:var(--vscode-button-secondaryBackground);color:var(--vscode-button-secondaryForeground);border:none;cursor:pointer;font-size:12px;display:flex;align-items:center;gap:4px}
.icon-btn:hover{background:var(--vscode-button-secondaryHoverBackground)}
.icon-btn.primary{background:var(--vscode-button-background);color:var(--vscode-button-foreground)}
.icon-btn.primary:hover{background:var(--vscode-button-hoverBackground)}
.icon-btn:disabled{opacity:.4;cursor:not-allowed}

/* Status Indicator */
.status-bar{display:flex;align-items:center;gap:16px;padding:12px 16px;background:var(--vscode-editor-inactiveSelectionBackground);border-radius:8px;margin-bottom:20px;flex-wrap:wrap}
.status-item{display:flex;align-items:center;gap:6px;font-size:12px}
.status-dot{width:8px;height:8px;border-radius:50%}
.status-dot.green{background:#4ade80;box-shadow:0 0 6px #4ade80}
.status-dot.yellow{background:#facc15;animation:pulse 1s ease-in-out infinite}
.status-dot.red{background:#ef4444}
.status-dot.gray{background:#6b7280}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.5}}

/* Tabs */
.tabs{display:flex;gap:4px;margin-bottom:20px;border-bottom:1px solid var(--vscode-panel-border);padding-bottom:0}
.tab{padding:8px 16px;cursor:pointer;font-size:13px;font-weight:500;border-bottom:2px solid transparent;opacity:.6;transition:all .15s}
.tab:hover{opacity:.8}
.tab.active{opacity:1;border-bottom-color:var(--vscode-focusBorder)}

/* Tab Content */
.tab-content{display:none}
.tab-content.active{display:block}

/* Cards */
.card{background:var(--vscode-editor-inactiveSelectionBackground);border:1px solid var(--vscode-panel-border);border-radius:8px;margin-bottom:16px;overflow:hidden}
.card-header{padding:12px 16px;border-bottom:1px solid var(--vscode-panel-border);display:flex;align-items:center;justify-content:space-between;background:rgba(255,255,255,.02)}
.card-title{font-size:13px;font-weight:600;display:flex;align-items:center;gap:8px}
.card-body{padding:16px}
.card-body.no-pad{padding:0}

/* Scan Buttons Grid */
.scan-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(180px,1fr));gap:12px}
.scan-btn{display:flex;flex-direction:column;align-items:center;padding:20px 16px;background:var(--vscode-editor-inactiveSelectionBackground);border:1px solid var(--vscode-panel-border);border-radius:8px;cursor:pointer;transition:all .15s;text-align:center}
.scan-btn:hover{background:var(--vscode-list-hoverBackground);border-color:var(--vscode-focusBorder);transform:translateY(-2px)}
.scan-btn:active{transform:translateY(0)}
.scan-btn.loading{opacity:.6;pointer-events:none}
.scan-btn .icon{font-size:28px;margin-bottom:8px}
.scan-btn .label{font-size:13px;font-weight:600;margin-bottom:4px}
.scan-btn .desc{font-size:11px;opacity:.5}
.scan-btn.primary{border-color:var(--vscode-button-background);background:rgba(0,122,204,.1)}

/* Results Panel */
.results-panel{margin-top:16px}
.results-header{display:flex;align-items:center;justify-content:space-between;padding:10px 14px;background:var(--vscode-editor-inactiveSelectionBackground);border-radius:6px 6px 0 0;border:1px solid var(--vscode-panel-border);border-bottom:none}
.results-title{font-size:12px;font-weight:600;display:flex;align-items:center;gap:6px}
.results-body{border:1px solid var(--vscode-panel-border);border-radius:0 0 6px 6px;max-height:400px;overflow-y:auto}
.result-row{display:flex;align-items:flex-start;gap:10px;padding:10px 14px;border-bottom:1px solid var(--vscode-panel-border);font-size:12px;cursor:pointer;transition:background .1s}
.result-row:hover{background:var(--vscode-list-hoverBackground)}
.result-row:last-child{border-bottom:none}
.result-icon{flex-shrink:0;font-size:14px}
.result-content{flex:1;min-width:0}
.result-msg{font-weight:500;word-break:break-word}
.result-meta{font-size:11px;opacity:.5;margin-top:2px}
.result-badge{padding:2px 6px;border-radius:4px;font-size:10px;font-weight:600}
.badge-critical{background:#dc262633;color:#ef4444}
.badge-high{background:#ea580c33;color:#fb923c}
.badge-medium{background:#ca8a0433;color:#facc15}
.badge-low{background:#16a34a33;color:#4ade80}

/* Empty State */
.empty-state{text-align:center;padding:40px 20px;opacity:.5}
.empty-state .icon{font-size:48px;margin-bottom:12px}
.empty-state .title{font-size:14px;font-weight:600;margin-bottom:4px}
.empty-state .desc{font-size:12px}

/* Loading State */
.loading-state{text-align:center;padding:40px 20px}
.loading-state .spinner{width:32px;height:32px;border:3px solid var(--vscode-panel-border);border-top-color:var(--vscode-focusBorder);border-radius:50%;animation:spin 1s linear infinite;margin:0 auto 12px}
@keyframes spin{to{transform:rotate(360deg)}}
.loading-state .text{font-size:13px;opacity:.7}

/* Summary Stats */
.stats-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(100px,1fr));gap:12px}
.stat-card{text-align:center;padding:16px 12px;background:var(--vscode-editor-background);border-radius:6px;border:1px solid var(--vscode-panel-border)}
.stat-value{font-size:24px;font-weight:700;line-height:1}
.stat-label{font-size:10px;text-transform:uppercase;letter-spacing:.5px;opacity:.5;margin-top:4px}
.stat-card.danger .stat-value{color:#ef4444}
.stat-card.warning .stat-value{color:#fb923c}
.stat-card.success .stat-value{color:#4ade80}

/* Backend Panel */
.backend-panel{display:flex;align-items:center;gap:16px;flex-wrap:wrap}
.backend-info{flex:1;min-width:200px}
.backend-state{font-weight:600;margin-bottom:2px}
.backend-meta{font-size:11px;opacity:.5}
.backend-actions{display:flex;gap:6px}

/* Log Output */
.log-output{background:var(--vscode-editor-background);border:1px solid var(--vscode-panel-border);border-radius:4px;padding:12px;font-family:var(--vscode-editor-font-family);font-size:11px;max-height:200px;overflow-y:auto;line-height:1.6}
.log-output:empty::before{content:'No logs yet';opacity:.4}

/* Issues List */
.issues-summary{display:flex;gap:12px;margin-bottom:12px;flex-wrap:wrap}
.issue-count{display:flex;align-items:center;gap:4px;font-size:12px;padding:4px 10px;border-radius:4px;background:var(--vscode-editor-background)}
.issue-count.critical{color:#ef4444}
.issue-count.high{color:#fb923c}
.issue-count.medium{color:#facc15}
.issue-count.low{color:#4ade80}
</style>
</head>
<body>
<div class="shell">

<!-- Header -->
<div class="header">
  <h1><span class="emoji">⚡</span> Copilot Engine</h1>
  <div class="header-actions">
    <button class="icon-btn" onclick="send('refreshDashboard')" id="btnRefresh">↻ Refresh</button>
    <button class="icon-btn" onclick="send('showOutput')">📋 Output</button>
    <button class="icon-btn" onclick="send('openSettings')">⚙️ Settings</button>
  </div>
</div>

<!-- Status Bar -->
<div class="status-bar">
  <div class="status-item">
    <span id="backendDot" class="status-dot gray"></span>
    <span id="backendLabel">Backend: Checking...</span>
  </div>
  <div class="status-item">
    <span>Port:</span>
    <strong id="portNum">7779</strong>
  </div>
  <div class="status-item">
    <span>Worker:</span>
    <strong id="workerStatus">—</strong>
  </div>
  <div class="status-item">
    <span>Events:</span>
    <strong id="eventCount">0</strong>
  </div>
</div>

<!-- Tabs -->
<div class="tabs">
  <div class="tab active" data-tab="scans">🔍 Scan & Analyze</div>
  <div class="tab" data-tab="results">📊 Results</div>
  <div class="tab" data-tab="health">❤️ Health</div>
  <div class="tab" data-tab="backend">🖥️ Backend</div>
</div>

<!-- Tab: Scans -->
<div class="tab-content active" id="tab-scans">
  <div class="card">
    <div class="card-header">
      <span class="card-title">🎯 Manual Scans</span>
      <span style="font-size:11px;opacity:.5">Click to run — results appear below</span>
    </div>
    <div class="card-body">
      <div class="scan-grid">
        <div class="scan-btn primary" onclick="runScan('initializeWorkspace')" id="btn-initialize">
          <span class="icon">🚀</span>
          <span class="label">Initialize</span>
          <span class="desc">Index workspace & build graph</span>
        </div>
        <div class="scan-btn" onclick="runScan('runFullScan')" id="btn-fullscan">
          <span class="icon">🔍</span>
          <span class="label">Full Scan</span>
          <span class="desc">Security + Contracts + All</span>
        </div>
        <div class="scan-btn" onclick="runScan('runSecurityScan')" id="btn-security">
          <span class="icon">🛡️</span>
          <span class="label">Security</span>
          <span class="desc">Find vulnerabilities</span>
        </div>
        <div class="scan-btn" onclick="runScan('runContractScan')" id="btn-contracts">
          <span class="icon">📋</span>
          <span class="label">API Contracts</span>
          <span class="desc">Validate endpoints</span>
        </div>
        <div class="scan-btn" onclick="runScan('runGitAnalysis')" id="btn-git">
          <span class="icon">📊</span>
          <span class="label">Git Analysis</span>
          <span class="desc">Review changes & risk</span>
        </div>
        <div class="scan-btn" onclick="runScan('detectEndpoints')" id="btn-endpoints">
          <span class="icon">🌐</span>
          <span class="label">Detect Endpoints</span>
          <span class="desc">Find API routes</span>
        </div>
        <div class="scan-btn" onclick="runScan('detectStack')" id="btn-stack">
          <span class="icon">🔧</span>
          <span class="label">Detect Stack</span>
          <span class="desc">Languages & frameworks</span>
        </div>
      </div>
    </div>
  </div>

  <!-- Inline Results -->
  <div id="scanResultsPanel" style="display:none">
    <div class="card">
      <div class="card-header">
        <span class="card-title" id="resultsTitle">📊 Scan Results</span>
        <button class="icon-btn" onclick="clearResults()">✕ Clear</button>
      </div>
      <div class="card-body no-pad">
        <div id="resultsSummary" class="issues-summary" style="padding:12px 16px;border-bottom:1px solid var(--vscode-panel-border)"></div>
        <div id="resultsBody" class="results-body"></div>
      </div>
    </div>
  </div>

  <!-- Loading State -->
  <div id="scanLoading" style="display:none">
    <div class="card">
      <div class="card-body">
        <div class="loading-state">
          <div class="spinner"></div>
          <div class="text" id="loadingText">Running scan...</div>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- Tab: Results History -->
<div class="tab-content" id="tab-results">
  <div class="card">
    <div class="card-header">
      <span class="card-title">📊 Last Scan Results</span>
    </div>
    <div class="card-body">
      <div id="lastResults">
        <div class="empty-state">
          <div class="icon">📭</div>
          <div class="title">No scan results yet</div>
          <div class="desc">Run a scan from the "Scan & Analyze" tab</div>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- Tab: Health -->
<div class="tab-content" id="tab-health">
  <div class="card">
    <div class="card-header">
      <span class="card-title">❤️ Workspace Health</span>
      <button class="icon-btn" onclick="send('refreshDashboard')">↻ Refresh</button>
    </div>
    <div class="card-body">
      <div id="healthContent">
        <div class="empty-state">
          <div class="icon">📊</div>
          <div class="title">No health data</div>
          <div class="desc">Click "Initialize" to index your workspace first</div>
        </div>
      </div>
    </div>
  </div>

  <div class="card">
    <div class="card-header">
      <span class="card-title">🔄 Circular Dependencies</span>
      <span class="result-badge badge-low" id="circularCount">0</span>
    </div>
    <div class="card-body no-pad">
      <div id="circularList" class="results-body" style="max-height:200px">
        <div class="empty-state" style="padding:20px">
          <div class="desc">No circular dependencies detected</div>
        </div>
      </div>
    </div>
  </div>

  <div class="card">
    <div class="card-header">
      <span class="card-title">📄 Dead Code Files</span>
      <span class="result-badge badge-low" id="deadCodeCount">0</span>
    </div>
    <div class="card-body no-pad">
      <div id="deadCodeList" class="results-body" style="max-height:200px">
        <div class="empty-state" style="padding:20px">
          <div class="desc">All files are imported somewhere</div>
        </div>
      </div>
    </div>
  </div>
</div>

<!-- Tab: Backend -->
<div class="tab-content" id="tab-backend">
  <div class="card">
    <div class="card-header">
      <span class="card-title">🖥️ Backend Server</span>
    </div>
    <div class="card-body">
      <div class="backend-panel">
        <div class="backend-info">
          <div class="backend-state" id="backendState">Stopped</div>
          <div class="backend-meta" id="backendMeta">Port: — | PID: — | Uptime: —</div>
        </div>
        <div class="backend-actions">
          <button class="icon-btn primary" id="btnStart" onclick="send('startBackend')">▶ Start</button>
          <button class="icon-btn" id="btnStop" onclick="send('stopBackend')" disabled>⏹ Stop</button>
          <button class="icon-btn" id="btnRestart" onclick="send('restartBackend')" disabled>🔄 Restart</button>
          <button class="icon-btn" onclick="send('refreshBackend')">↻ Check</button>
        </div>
      </div>
    </div>
  </div>

  <div class="card">
    <div class="card-header">
      <span class="card-title">📜 Server Logs</span>
    </div>
    <div class="card-body">
      <div id="logsContent" class="log-output"></div>
    </div>
  </div>
</div>

</div>

<!-- Debug output -->
<div id="debugOutput" style="position:fixed;bottom:0;left:0;right:0;background:#1e1e1e;border-top:2px solid #007acc;padding:8px;font-family:monospace;font-size:11px;max-height:150px;overflow-y:auto;z-index:9999;display:block;">
  <strong style="color:#007acc;">Debug Log:</strong>
  <div id="debugLog" style="margin-top:4px;color:#ccc;"></div>
</div>

<script>
// Debug helper
function debug(msg) {
  const log = document.getElementById('debugLog');
  if (log) {
    const time = new Date().toLocaleTimeString();
    log.innerHTML = '<div>[' + time + '] ' + msg + '</div>' + log.innerHTML;
    if (log.childNodes.length > 20) log.removeChild(log.lastChild);
  }
  console.log('[Webview]', msg);
}

// Wrap everything in try-catch
try {
  debug('Script starting...');
  
  const vscode = acquireVsCodeApi();
  debug('acquireVsCodeApi OK');
  
  function send(cmd, payload) { 
    debug('Sending: ' + cmd);
    vscode.postMessage({ command: cmd, ...(payload||{}) }); 
  }
  function esc(s) { return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
  function basename(p) { return (p||'').replace(/\\\\/g,'/').split('/').pop() || p; }

  // State
  let currentScan = null;
  let lastResults = null;

  debug('Setting up tab switching...');
  
  // Tab switching
  document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', () => {
      debug('Tab clicked: ' + tab.dataset.tab);
      document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      tab.classList.add('active');
      document.getElementById('tab-' + tab.dataset.tab).classList.add('active');
    });
  });

  // Run scan
  function runScan(scanType) {
    debug('runScan called: ' + scanType);
    currentScan = scanType;
  send(scanType);
}

// Clear results
function clearResults() {
  document.getElementById('scanResultsPanel').style.display = 'none';
  document.getElementById('resultsBody').innerHTML = '';
  document.getElementById('resultsSummary').innerHTML = '';
}

// Render scan results
function renderScanResults(scanType, result) {
  const panel = document.getElementById('scanResultsPanel');
  const title = document.getElementById('resultsTitle');
  const summary = document.getElementById('resultsSummary');
  const body = document.getElementById('resultsBody');

  panel.style.display = 'block';
  document.getElementById('scanLoading').style.display = 'none';

  // Enable button again
  enableScanButtons();

  // Store results
  lastResults = { scanType, result, timestamp: new Date().toISOString() };

  if (scanType === 'fullScan') {
    title.innerHTML = '🔍 Full Scan Results';
    const issues = result.issues || [];
    const critical = issues.filter(i => i.severity === 'CRITICAL').length;
    const high = issues.filter(i => i.severity === 'HIGH').length;
    const medium = issues.filter(i => i.severity === 'MEDIUM').length;
    const low = issues.filter(i => i.severity === 'LOW').length;

    summary.innerHTML = 
      '<div class="issue-count critical">🔴 ' + critical + ' Critical</div>' +
      '<div class="issue-count high">🟠 ' + high + ' High</div>' +
      '<div class="issue-count medium">🟡 ' + medium + ' Medium</div>' +
      '<div class="issue-count low">🟢 ' + low + ' Low</div>' +
      '<div class="issue-count">Total: ' + issues.length + '</div>';

    body.innerHTML = issues.slice(0, 100).map(i => renderIssueRow(i)).join('');
  } 
  else if (scanType === 'security') {
    title.innerHTML = '🛡️ Security Scan Results';
    const findings = result.findings || result.issues || [];
    const critical = findings.filter(i => i.severity === 'CRITICAL' || i.severity === 'critical').length;
    const high = findings.filter(i => i.severity === 'HIGH' || i.severity === 'high').length;
    const medium = findings.filter(i => i.severity === 'MEDIUM' || i.severity === 'medium').length;

    summary.innerHTML = 
      '<div class="issue-count critical">🔴 ' + critical + ' Critical</div>' +
      '<div class="issue-count high">🟠 ' + high + ' High</div>' +
      '<div class="issue-count medium">🟡 ' + medium + ' Medium</div>' +
      '<div class="issue-count">Total: ' + findings.length + '</div>';

    body.innerHTML = findings.slice(0, 100).map(i => renderIssueRow(i)).join('');
  }
  else if (scanType === 'contracts') {
    title.innerHTML = '📋 Contract Validation Results';
    const violations = result.violations || [];
    summary.innerHTML = '<div class="issue-count">' + violations.length + ' violations found</div>';
    body.innerHTML = violations.length ? violations.map(v => 
      '<div class="result-row">' +
        '<span class="result-icon">⚠️</span>' +
        '<div class="result-content">' +
          '<div class="result-msg">' + esc(v.message || v.rule) + '</div>' +
          '<div class="result-meta">' + esc(v.endpoint || v.file_path || '') + '</div>' +
        '</div>' +
      '</div>'
    ).join('') : '<div class="empty-state" style="padding:20px"><div class="desc">✅ All contracts valid!</div></div>';
  }
  else if (scanType === 'git') {
    title.innerHTML = '📊 Git Analysis Results';
    const changes = result.changes || [];
    const risk = result.risk_score || 0;
    summary.innerHTML = 
      '<div class="issue-count">Risk Score: ' + risk + '/10</div>' +
      '<div class="issue-count">' + changes.length + ' changed files</div>';
    body.innerHTML = changes.length ? changes.map(c => 
      '<div class="result-row" onclick="send(\'openFile\', {filePath: \'' + esc(c.file) + '\'})">' +
        '<span class="result-icon">' + (c.risk_level === 'high' ? '🔴' : c.risk_level === 'medium' ? '🟡' : '🟢') + '</span>' +
        '<div class="result-content">' +
          '<div class="result-msg">' + esc(c.file) + '</div>' +
          '<div class="result-meta">' + esc(c.change_type) + '</div>' +
        '</div>' +
      '</div>'
    ).join('') : '<div class="empty-state" style="padding:20px"><div class="desc">No changes detected</div></div>';
  }
  else if (scanType === 'endpoints') {
    title.innerHTML = '🌐 Detected Endpoints';
    const endpoints = result.endpoints || [];
    summary.innerHTML = '<div class="issue-count">' + endpoints.length + ' endpoints found</div>';
    body.innerHTML = endpoints.length ? endpoints.map(e => 
      '<div class="result-row" onclick="send(\'openFile\', {filePath: \'' + esc(e.file) + '\', line: ' + (e.line||1) + '})">' +
        '<span class="result-icon">🔗</span>' +
        '<div class="result-content">' +
          '<div class="result-msg"><strong>' + esc(e.method) + '</strong> ' + esc(e.route) + '</div>' +
          '<div class="result-meta">' + basename(e.file) + ':' + (e.line||'?') + '</div>' +
        '</div>' +
      '</div>'
    ).join('') : '<div class="empty-state" style="padding:20px"><div class="desc">No endpoints detected</div></div>';
  }
  else if (scanType === 'stack') {
    title.innerHTML = '🔧 Stack Detection Results';
    summary.innerHTML = '';
    body.innerHTML = 
      '<div style="padding:16px">' +
        '<div style="margin-bottom:12px"><strong>Languages:</strong> ' + esc((result.languages || []).join(', ') || 'Unknown') + '</div>' +
        '<div style="margin-bottom:12px"><strong>Frameworks:</strong> ' + esc((result.frameworks || []).join(', ') || 'Unknown') + '</div>' +
        '<div style="margin-bottom:12px"><strong>ORM:</strong> ' + esc(result.orm || 'None detected') + '</div>' +
        '<div><strong>API Style:</strong> ' + esc(result.api_style || 'Unknown') + '</div>' +
      '</div>';
  }
  else if (scanType === 'initialize') {
    title.innerHTML = '🚀 Initialization Results';
    const steps = result.steps || {};
    summary.innerHTML = result.initialized || result.already_initialized ? 
      '<div class="issue-count" style="color:#4ade80">✅ Workspace initialized</div>' : 
      '<div class="issue-count critical">❌ Initialization failed</div>';
    body.innerHTML = 
      '<div style="padding:16px">' +
        (steps.index ? '<div style="margin-bottom:8px">📁 Indexed ' + (steps.index.indexed || 0) + ' files, ' + (steps.index.entities_found || 0) + ' entities</div>' : '') +
        (steps.graph ? '<div style="margin-bottom:8px">🔗 Built graph: ' + (steps.graph.file_edges || 0) + ' dependencies</div>' : '') +
        (steps.snapshots ? '<div style="margin-bottom:8px">📸 Created ' + steps.snapshots + ' AST snapshots</div>' : '') +
        (result.already_initialized ? '<div style="opacity:.6">Already initialized previously</div>' : '') +
      '</div>';
  }

  // Update last results tab
  document.getElementById('lastResults').innerHTML = body.innerHTML;
}

function renderIssueRow(issue) {
  const sev = (issue.severity || 'medium').toUpperCase();
  const icon = sev === 'CRITICAL' ? '🔴' : sev === 'HIGH' ? '🟠' : sev === 'MEDIUM' ? '🟡' : '🟢';
  const badgeClass = sev === 'CRITICAL' ? 'badge-critical' : sev === 'HIGH' ? 'badge-high' : sev === 'MEDIUM' ? 'badge-medium' : 'badge-low';
  const filePath = issue.file_path || issue.file || '';
  const line = issue.line_number || issue.line || '';

  return '<div class="result-row" onclick="send(\'openFile\', {filePath: \'' + esc(filePath) + '\', line: ' + (line||1) + '})">' +
    '<span class="result-icon">' + icon + '</span>' +
    '<div class="result-content">' +
      '<div class="result-msg">' + esc(issue.message || issue.category) + '</div>' +
      '<div class="result-meta">' + basename(filePath) + (line ? ':' + line : '') + ' • ' + esc(issue.category || issue.pillar || '') + '</div>' +
    '</div>' +
    '<span class="result-badge ' + badgeClass + '">' + sev + '</span>' +
  '</div>';
}

function enableScanButtons() {
  document.querySelectorAll('.scan-btn').forEach(btn => btn.classList.remove('loading'));
}

// Render dashboard data (from autonomous engine)
function renderDashboard(data) {
  const health = data.health || {};
  const risk = health.risk_scores || {};
  const worker = health.worker || {};
  const graph = health.graph || {};

  // Update status bar
  document.getElementById('workerStatus').textContent = worker.started_at ? 'Running' : 'Stopped';
  document.getElementById('eventCount').textContent = worker.events_processed || 0;

  // Update health tab
  const healthContent = document.getElementById('healthContent');
  if (graph.total_files > 0 || Object.keys(risk).length > 0) {
    healthContent.innerHTML = 
      '<div class="stats-grid">' +
        '<div class="stat-card"><div class="stat-value">' + (graph.total_files || 0) + '</div><div class="stat-label">Files Indexed</div></div>' +
        '<div class="stat-card"><div class="stat-value">' + (graph.file_edges || 0) + '</div><div class="stat-label">Dependencies</div></div>' +
        '<div class="stat-card"><div class="stat-value">' + (graph.entity_edges || 0) + '</div><div class="stat-label">Entity Edges</div></div>' +
        '<div class="stat-card ' + (graph.circular_count > 0 ? 'warning' : 'success') + '"><div class="stat-value">' + (graph.circular_count || 0) + '</div><div class="stat-label">Circular Deps</div></div>' +
        '<div class="stat-card ' + (graph.dead_code_files > 0 ? 'warning' : 'success') + '"><div class="stat-value">' + (graph.dead_code_files || 0) + '</div><div class="stat-label">Dead Code</div></div>' +
        '<div class="stat-card"><div class="stat-value">' + (worker.fast_path_runs || 0) + '</div><div class="stat-label">Fast Scans</div></div>' +
        '<div class="stat-card"><div class="stat-value">' + (worker.idle_runs || 0) + '</div><div class="stat-label">Deep Scans</div></div>' +
        '<div class="stat-card ' + (worker.errors > 0 ? 'danger' : 'success') + '"><div class="stat-value">' + (worker.errors || 0) + '</div><div class="stat-label">Errors</div></div>' +
      '</div>';
  }

  // Circular deps
  const circularList = document.getElementById('circularList');
  const circular = data.circular_dependencies || [];
  document.getElementById('circularCount').textContent = circular.length;
  if (circular.length > 0) {
    circularList.innerHTML = circular.map(c =>
      '<div class="result-row"><span class="result-icon">🔄</span><div class="result-content"><div class="result-msg">' + c.map(basename).join(' → ') + '</div></div></div>'
    ).join('');
  }

  // Dead code
  const deadCodeList = document.getElementById('deadCodeList');
  const deadCode = data.dead_code_files || [];
  document.getElementById('deadCodeCount').textContent = deadCode.length;
  if (deadCode.length > 0) {
    deadCodeList.innerHTML = deadCode.map(f =>
      '<div class="result-row" onclick="send(\'openFile\', {filePath: \'' + esc(f) + '\'})"><span class="result-icon">📄</span><div class="result-content"><div class="result-msg">' + basename(f) + '</div><div class="result-meta">' + esc(f) + '</div></div></div>'
    ).join('');
  }
}

// Render backend status
function renderBackendStatus(status) {
  const dot = document.getElementById('backendDot');
  const label = document.getElementById('backendLabel');
  const state = document.getElementById('backendState');
  const meta = document.getElementById('backendMeta');
  const btnStart = document.getElementById('btnStart');
  const btnStop = document.getElementById('btnStop');
  const btnRestart = document.getElementById('btnRestart');

  if (status.health === 'healthy') {
    dot.className = 'status-dot green';
    label.textContent = 'Backend: Running';
    state.textContent = 'Running';
    state.style.color = '#4ade80';
  } else if (status.health === 'starting') {
    dot.className = 'status-dot yellow';
    label.textContent = 'Backend: Starting...';
    state.textContent = 'Starting...';
    state.style.color = '#facc15';
  } else if (status.health === 'unhealthy') {
    dot.className = 'status-dot red';
    label.textContent = 'Backend: Error';
    state.textContent = 'Unhealthy';
    state.style.color = '#ef4444';
  } else {
    dot.className = 'status-dot gray';
    label.textContent = 'Backend: Stopped';
    state.textContent = 'Stopped';
    state.style.color = '#6b7280';
  }

  const uptimeStr = status.uptime > 0 ? (status.uptime < 60 ? status.uptime + 's' : Math.floor(status.uptime / 60) + 'm') : '—';
  meta.textContent = 'Port: ' + (status.port || 7779) + ' | PID: ' + (status.pid || '—') + ' | Uptime: ' + uptimeStr;
  document.getElementById('portNum').textContent = status.port || 7779;

  btnStart.disabled = status.running;
  btnStop.disabled = !status.running;
  btnRestart.disabled = !status.running;
}

function renderBackendLogs(logs) {
  const content = document.getElementById('logsContent');
  content.innerHTML = (logs || []).map(l => '<div>' + esc(l) + '</div>').join('');
  content.scrollTop = content.scrollHeight;
}

// Message handler
window.addEventListener('message', (event) => {
  const msg = event.data;
  
  switch (msg.command) {
    case 'dashboard':
      renderDashboard(msg.data);
      break;
    case 'backendStatus':
      renderBackendStatus(msg.status);
      break;
    case 'backendLogs':
      renderBackendLogs(msg.logs);
      break;
    case 'scanStarted':
      document.getElementById('scanLoading').style.display = 'block';
      document.getElementById('scanResultsPanel').style.display = 'none';
      document.getElementById('loadingText').textContent = 'Running scan...';
      // Disable all scan buttons
      document.querySelectorAll('.scan-btn').forEach(btn => btn.classList.add('loading'));
      break;
    case 'scanResults':
      renderScanResults(msg.scanType, msg.result);
      break;
    case 'scanComplete':
      document.getElementById('scanLoading').style.display = 'none';
      enableScanButtons();
      if (!msg.success) {
        const panel = document.getElementById('scanResultsPanel');
        panel.style.display = 'block';
        document.getElementById('resultsTitle').innerHTML = '❌ Scan Failed';
        document.getElementById('resultsSummary').innerHTML = '';
        document.getElementById('resultsBody').innerHTML = '<div class="empty-state" style="padding:20px"><div class="desc">Error: ' + esc(msg.error) + '</div></div>';
      }
      break;
    case 'refreshing':
      document.getElementById('btnRefresh').disabled = true;
      document.getElementById('btnRefresh').textContent = '↻ ...';
      break;
    case 'refreshComplete':
      document.getElementById('btnRefresh').disabled = false;
      document.getElementById('btnRefresh').textContent = '↻ Refresh';
      break;
  }
});

  // Signal ready
  debug('Signaling webviewReady...');
  vscode.postMessage({ command: 'webviewReady' });
  debug('Initialization complete!');
  
} catch (err) {
  // Show error visibly
  debug('ERROR: ' + err.message);
  const errDiv = document.createElement('div');
  errDiv.style.cssText = 'position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:#dc2626;color:white;padding:20px;border-radius:8px;z-index:10000;max-width:80%;';
  errDiv.innerHTML = '<h3>Script Error</h3><pre>' + err.message + '\\n' + err.stack + '</pre>';
  document.body.appendChild(errDiv);
}
</script>
</body>
</html>`;
    }
}
