/**
 * Copilot Engine - Autonomous Monitoring Dashboard
 * Live structural health monitor + backend management controls.
 * Receives data from AutonomousEngine and renders real-time state.
 */
import * as vscode from 'vscode';
import { EngineClient, HealthResponse } from './engineClient';
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

        // Send initial data if available
        const latest = this.autonomousEngine.getLatestDashboard();
        if (latest) {
            this.pushDashboardData(latest);
        }

        // Subscribe to backend status changes
        this.backendManager.onStatusChange((status) => {
            this.pushBackendStatus(status);
            // Also push logs during startup
            if (status.health === 'starting') {
                this.panel.webview.postMessage({ 
                    command: 'backendLogs', 
                    logs: this.backendManager.getLogs() 
                });
            }
        });

        // Initial status will be sent when webview signals ready via 'webviewReady' message
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
            '⚡ Copilot Engine — Monitor',
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
        switch (msg.command) {
            case 'openSettings':
                await vscode.commands.executeCommand('workbench.action.openSettings', 'copilotEngine');
                break;
            case 'webviewReady': {
                // Webview is ready to receive messages - send all initial data
                await this.backendManager.detectExisting();
                this.pushBackendStatus(this.backendManager.getStatus());
                this.panel.webview.postMessage({ 
                    command: 'backendLogs', 
                    logs: this.backendManager.getLogs() 
                });
                // Send latest dashboard data or force poll
                const workspacePath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
                let dashData = this.autonomousEngine.getLatestDashboard();
                if (!dashData && workspacePath) {
                    // No cached data - force poll with workspace path
                    dashData = await this.autonomousEngine.refreshDashboard(workspacePath);
                }
                if (dashData) {
                    this.pushDashboardData(dashData);
                }
                break;
            }
            case 'toggleFocus':
                await vscode.commands.executeCommand('copilotEngine.toggleFocusMode');
                break;
            case 'openFile': {
                if (msg.filePath) {
                    const doc = await vscode.workspace.openTextDocument(msg.filePath);
                    await vscode.window.showTextDocument(doc, {
                        selection: msg.line ? new vscode.Range(msg.line - 1, 0, msg.line - 1, 0) : undefined,
                    });
                }
                break;
            }
            case 'startBackend':
                await this.backendManager.start();
                break;
            case 'stopBackend':
                this.backendManager.stop();
                break;
            case 'restartBackend':
                await this.backendManager.restart();
                break;
            case 'refreshBackend': {
                // Try to detect if backend is already running externally
                await this.backendManager.detectExisting();
                this.pushBackendStatus(this.backendManager.getStatus());
                this.panel.webview.postMessage({ 
                    command: 'backendLogs', 
                    logs: this.backendManager.getLogs() 
                });
                // Also refresh dashboard data
                const wsPath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
                const refreshedData = await this.autonomousEngine.refreshDashboard(wsPath);
                if (refreshedData) {
                    this.pushDashboardData(refreshedData);
                }
                break;
            }
            // Quick Actions
            case 'fullScan':
                await vscode.commands.executeCommand('copilotEngine.fullScan');
                break;
            case 'securityScan':
                await vscode.commands.executeCommand('copilotEngine.checkSecurity');
                break;
            case 'gitAnalysis':
                await vscode.commands.executeCommand('copilotEngine.analyzeGitChanges');
                break;
            case 'preCommit':
                await vscode.commands.executeCommand('copilotEngine.preCommitCheck');
                break;
            case 'validateContracts':
                await vscode.commands.executeCommand('copilotEngine.validateContracts');
                break;
            case 'validateSchema':
                await vscode.commands.executeCommand('copilotEngine.validateSchema');
                break;
            case 'detectStack':
                await vscode.commands.executeCommand('copilotEngine.detectStack');
                break;
            case 'detectEndpoints':
                await vscode.commands.executeCommand('copilotEngine.detectEndpoints');
                break;
            case 'analyzeCode':
                await vscode.commands.executeCommand('copilotEngine.analyzeCode');
                break;
            case 'buildContext':
                await vscode.commands.executeCommand('copilotEngine.buildContext');
                break;
            case 'showOutput':
                await vscode.commands.executeCommand('copilotEngine.showStatus');
                break;
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

.shell{max-width:1000px;margin:0 auto;padding:24px 20px 60px}

/* ── Header ── */
.header{display:flex;align-items:center;justify-content:space-between;margin-bottom:24px;padding-bottom:14px;border-bottom:1px solid var(--vscode-panel-border)}
.header h1{font-size:20px;font-weight:700;letter-spacing:-.3px}
.header h1 span{opacity:.4;font-weight:400;font-size:12px;margin-left:6px}
.header-right{display:flex;align-items:center;gap:10px}
.pill{display:inline-flex;align-items:center;gap:5px;padding:3px 12px;border-radius:16px;font-size:11px;font-weight:600}
.pill-dot{width:7px;height:7px;border-radius:50%}
.pill-healthy{background:#22c55e18;color:#4ade80}.pill-healthy .pill-dot{background:#4ade80;box-shadow:0 0 6px #4ade80}
.pill-caution{background:#eab30818;color:#facc15}.pill-caution .pill-dot{background:#facc15}
.pill-atrisk{background:#f9731618;color:#fb923c}.pill-atrisk .pill-dot{background:#fb923c}
.pill-degraded{background:#ef444418;color:#f87171}.pill-degraded .pill-dot{background:#f87171}
.pill-critical{background:#dc262618;color:#ef4444}.pill-critical .pill-dot{background:#ef4444;box-shadow:0 0 6px #ef4444}

/* ── Health Gauge ── */
.gauge-wrap{display:flex;align-items:center;gap:20px;margin-bottom:24px;padding:20px;background:var(--vscode-editor-inactiveSelectionBackground);border:1px solid var(--vscode-panel-border);border-radius:12px}
.gauge{width:120px;height:120px;position:relative;flex-shrink:0}
.gauge svg{width:100%;height:100%;transform:rotate(-90deg)}
.gauge-bg{fill:none;stroke:var(--vscode-panel-border);stroke-width:8}
.gauge-fill{fill:none;stroke-width:8;stroke-linecap:round;transition:stroke-dashoffset .8s ease,stroke .5s}
.gauge-text{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center}
.gauge-score{font-size:28px;font-weight:800;line-height:1}
.gauge-label{font-size:10px;opacity:.5;text-transform:uppercase;letter-spacing:.5px;margin-top:2px}
.gauge-info{flex:1}
.gauge-level{font-size:18px;font-weight:700;margin-bottom:6px}
.gauge-meta{font-size:12px;opacity:.55;line-height:1.7}

/* ── Risk Category Grid ── */
.categories{display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));gap:10px;margin-bottom:24px}
.cat-card{background:var(--vscode-editor-inactiveSelectionBackground);border:1px solid var(--vscode-panel-border);border-radius:10px;padding:12px 14px;text-align:center;transition:border-color .3s}
.cat-card.warn{border-color:#eab30866}
.cat-card.danger{border-color:#ef444466}
.cat-val{font-size:22px;font-weight:700}
.cat-lbl{font-size:10px;opacity:.5;text-transform:uppercase;letter-spacing:.4px;margin-top:2px}
.c-green{color:#4ade80}.c-yellow{color:#facc15}.c-orange{color:#fb923c}.c-red{color:#ef4444}

/* ── Section ── */
.section{margin-bottom:24px}
.section-title{font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.8px;opacity:.5;margin-bottom:10px;display:flex;align-items:center;gap:8px}
.section-title::after{content:'';flex:1;height:1px;background:var(--vscode-panel-border)}
.section-title .count{background:var(--vscode-badge-background);color:var(--vscode-badge-foreground);padding:1px 7px;border-radius:10px;font-size:10px;font-weight:700}

/* ── Panels ── */
.panel{background:var(--vscode-editor-inactiveSelectionBackground);border:1px solid var(--vscode-panel-border);border-radius:10px;overflow:hidden;max-height:280px;overflow-y:auto}
.panel-empty{padding:24px;text-align:center;opacity:.4;font-size:12px}

/* ── Issue rows ── */
.row{display:flex;align-items:flex-start;gap:8px;padding:8px 14px;border-bottom:1px solid var(--vscode-panel-border);font-size:12px;cursor:pointer;transition:background .1s}
.row:hover{background:var(--vscode-list-hoverBackground)}
.row:last-child{border-bottom:none}
.row-icon{flex-shrink:0;font-size:13px;margin-top:1px}
.row-body{flex:1;min-width:0}
.row-msg{font-size:12px}
.row-meta{font-size:11px;opacity:.45;margin-top:1px}
.sev-crit{color:#ef4444}.sev-high{color:#fb923c}.sev-med{color:#facc15}.sev-low{color:#4ade80}

/* ── Trend sparkline ── */
.trend-wrap{background:var(--vscode-editor-inactiveSelectionBackground);border:1px solid var(--vscode-panel-border);border-radius:10px;padding:14px;height:100px;position:relative;overflow:hidden}
.trend-label{position:absolute;top:10px;left:14px;font-size:10px;opacity:.4;text-transform:uppercase;letter-spacing:.5px}
.trend-svg{width:100%;height:100%}

/* ── Worker stats bar ── */
.worker-bar{display:flex;gap:14px;flex-wrap:wrap;margin-bottom:24px;font-size:11px;opacity:.55}
.worker-bar span{display:inline-flex;align-items:center;gap:4px}
.wdot{width:6px;height:6px;border-radius:50%;background:#4ade80}
.wdot.off{background:#f87171}

/* ── Minimal controls ── */
.controls{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:24px}
.cbtn{
  padding:5px 12px;border-radius:5px;font-size:11px;font-weight:500;
  border:1px solid var(--vscode-panel-border);
  background:transparent;color:var(--vscode-foreground);
  cursor:pointer;transition:all .12s;opacity:.7
}
.cbtn:hover{opacity:1;border-color:var(--vscode-focusBorder)}

/* ── Quick Actions Grid ── */
.actions-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:8px;margin-bottom:16px}
.action-btn{
  display:flex;align-items:center;gap:8px;padding:10px 14px;border-radius:8px;
  background:var(--vscode-editor-inactiveSelectionBackground);
  border:1px solid var(--vscode-panel-border);
  color:var(--vscode-foreground);cursor:pointer;transition:all .15s;
  font-size:12px;font-weight:500;text-align:left
}
.action-btn:hover{background:var(--vscode-list-hoverBackground);border-color:var(--vscode-focusBorder);transform:translateY(-1px)}
.action-btn .icon{font-size:16px;flex-shrink:0}
.action-btn .label{flex:1;line-height:1.3}
.action-btn .label small{display:block;font-size:10px;opacity:.5;font-weight:400}
.action-btn.primary{background:var(--vscode-button-background);color:var(--vscode-button-foreground);border-color:var(--vscode-button-background)}
.action-btn.primary:hover{background:var(--vscode-button-hoverBackground)}
.action-btn.warning{border-color:#eab308;background:#eab30815}
.action-btn.danger{border-color:#ef4444;background:#ef444415}

.footer{text-align:center;opacity:.25;font-size:10px;margin-top:28px}

/* ── Backend Management ── */
.backend-panel{background:var(--vscode-editor-inactiveSelectionBackground);border:1px solid var(--vscode-panel-border);border-radius:10px;padding:16px;margin-bottom:24px}
.backend-status{display:flex;align-items:center;justify-content:space-between;gap:16px;margin-bottom:16px;flex-wrap:wrap}
.backend-indicator{display:flex;align-items:center;gap:12px;flex:1;min-width:220px}
.status-dot{width:12px;height:12px;border-radius:50%;flex-shrink:0}
.status-dot.status-stopped{background:#6b7280;box-shadow:0 0 0 2px #6b72804d}
.status-dot.status-starting{background:#facc15;box-shadow:0 0 8px #facc15;animation:pulse 1.5s ease-in-out infinite}
.status-dot.status-healthy{background:#4ade80;box-shadow:0 0 8px #4ade80}
.status-dot.status-unhealthy{background:#ef4444;box-shadow:0 0 8px #ef4444;animation:pulse 1s ease-in-out infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.5}}
.backend-info{flex:1}
.backend-state{font-size:14px;font-weight:600;margin-bottom:2px}
.backend-meta{font-size:11px;opacity:.5}
.backend-controls{display:flex;gap:6px;flex-wrap:wrap}
.bbtn{padding:6px 14px;border-radius:6px;font-size:11px;font-weight:600;border:1px solid var(--vscode-panel-border);background:var(--vscode-button-secondaryBackground);color:var(--vscode-button-secondaryForeground);cursor:pointer;transition:all .15s;opacity:.9}
.bbtn:hover:not(:disabled){opacity:1;transform:translateY(-1px);background:var(--vscode-button-secondaryHoverBackground)}
.bbtn:disabled{opacity:.3;cursor:not-allowed}
.bbtn-primary{background:var(--vscode-button-background);color:var(--vscode-button-foreground)}
.bbtn-primary:hover:not(:disabled){background:var(--vscode-button-hoverBackground)}
.bbtn-danger{background:#dc262626;color:#ef4444;border-color:#dc2626}
.bbtn-danger:hover:not(:disabled){background:#dc26264d}
.bbtn-warning{background:#eab30826;color:#facc15;border-color:#eab308}
.bbtn-warning:hover:not(:disabled){background:#eab3084d}
.backend-logs{border-top:1px solid var(--vscode-panel-border);padding-top:12px;margin-top:4px}
.logs-header{font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.5px;opacity:.5;margin-bottom:8px}
.logs-content{background:var(--vscode-editor-background);border:1px solid var(--vscode-panel-border);border-radius:6px;padding:10px;font-family:var(--vscode-editor-font-family);font-size:10px;line-height:1.6;max-height:180px;overflow-y:auto;color:#a1a1aa}
.logs-content.empty{opacity:.4;font-style:italic}
.log-line{margin-bottom:2px}
</style>
</head>
<body>
<div class="shell">

  <!-- ── Header ── -->
  <div class="header">
    <h1>⚡ Copilot Engine <span>Autonomous Monitor</span></h1>
    <div class="header-right">
      <div id="healthPill" class="pill pill-healthy">
        <span class="pill-dot"></span>
        <span id="healthText">Initializing...</span>
      </div>
    </div>
  </div>

  <!-- ── Worker Status ── -->
  <div class="worker-bar">
    <span><span id="wdot" class="wdot off"></span> <span id="workerLabel">Worker starting...</span></span>
    <span>Events: <strong id="evtCount">0</strong></span>
    <span>Fast runs: <strong id="fastCount">0</strong></span>
    <span>Idle scans: <strong id="idleCount">0</strong></span>
    <span>Errors: <strong id="errCount">0</strong></span>
    <span>Last: <strong id="lastEvt">—</strong></span>
  </div>

  <!-- ── Health Gauge ── -->
  <div class="gauge-wrap">
    <div class="gauge">
      <svg viewBox="0 0 36 36">
        <path class="gauge-bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"/>
        <path id="gaugeFill" class="gauge-fill" stroke="#4ade80" stroke-dasharray="0, 100" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"/>
      </svg>
      <div class="gauge-text">
        <div id="scoreVal" class="gauge-score">—</div>
        <div class="gauge-label">/ 10</div>
      </div>
    </div>
    <div class="gauge-info">
      <div id="levelText" class="gauge-level">Waiting for data...</div>
      <div id="gaugeMeta" class="gauge-meta"></div>
    </div>
  </div>

  <!-- ── Risk Categories ── -->
  <div class="categories">
    <div class="cat-card" id="cat-schema"><div id="v-schema" class="cat-val c-green">—</div><div class="cat-lbl">Schema</div></div>
    <div class="cat-card" id="cat-contract"><div id="v-contract" class="cat-val c-green">—</div><div class="cat-lbl">Contracts</div></div>
    <div class="cat-card" id="cat-drift"><div id="v-drift" class="cat-val c-green">—</div><div class="cat-lbl">Drift</div></div>
    <div class="cat-card" id="cat-security"><div id="v-security" class="cat-val c-green">—</div><div class="cat-lbl">Security</div></div>
    <div class="cat-card" id="cat-dependency"><div id="v-dependency" class="cat-val c-green">—</div><div class="cat-lbl">Deps</div></div>
    <div class="cat-card" id="cat-migration"><div id="v-migration" class="cat-val c-green">—</div><div class="cat-lbl">Migration</div></div>
    <div class="cat-card" id="cat-naming"><div id="v-naming" class="cat-val c-green">—</div><div class="cat-lbl">Naming</div></div>
  </div>

  <!-- ── Risk Trend ── -->
  <div class="section">
    <div class="section-title">Risk Trend</div>
    <div class="trend-wrap">
      <div class="trend-label">Score / time</div>
      <svg id="trendSvg" class="trend-svg" preserveAspectRatio="none" viewBox="0 0 400 60"></svg>
    </div>
  </div>

  <!-- ── Structural Drift ── -->
  <div class="section">
    <div class="section-title">Structural Drift <span id="driftCount" class="count">0</span></div>
    <div id="driftPanel" class="panel">
      <div class="panel-empty">No drift events detected</div>
    </div>
  </div>

  <!-- ── Circular Dependencies ── -->
  <div class="section">
    <div class="section-title">Circular Dependencies <span id="circCount" class="count">0</span></div>
    <div id="circPanel" class="panel">
      <div class="panel-empty">No circular dependencies</div>
    </div>
  </div>

  <!-- ── Dead Code ── -->
  <div class="section">
    <div class="section-title">Dead Code (Never Imported) <span id="deadCount" class="count">0</span></div>
    <div id="deadPanel" class="panel">
      <div class="panel-empty">No dead code files detected</div>
    </div>
  </div>

  <!-- ── Backend Management ── -->
  <div class="section">
    <div class="section-title">Backend Server</div>
    <div class="backend-panel">
      <div class="backend-status">
        <div class="backend-indicator">
          <div id="backendDot" class="status-dot status-stopped"></div>
          <div class="backend-info">
            <div id="backendState" class="backend-state">Stopped</div>
            <div id="backendMeta" class="backend-meta">Port: — | PID: — | Uptime: —</div>
          </div>
        </div>
        <div class="backend-controls">
          <button id="btnStart" class="bbtn bbtn-primary" onclick="send('startBackend')">▶ Start</button>
          <button id="btnStop" class="bbtn bbtn-danger" onclick="send('stopBackend')" disabled>⏹ Stop</button>
          <button id="btnRestart" class="bbtn bbtn-warning" onclick="send('restartBackend')" disabled>🔄 Restart</button>
          <button class="bbtn" onclick="send('refreshBackend')">↻ Refresh</button>
        </div>
      </div>
      <div class="backend-logs">
        <div class="logs-header">Recent Logs</div>
        <div id="logsContent" class="logs-content">Waiting for backend status...</div>
      </div>
    </div>
  </div>

  <!-- ── Quick Actions ── -->
  <div class="section">
    <div class="section-title">Quick Actions</div>
    <div class="actions-grid">
      <button class="action-btn primary" onclick="send('fullScan')">
        <span class="icon">🔍</span>
        <span class="label">Full Scan<small>Complete analysis</small></span>
      </button>
      <button class="action-btn warning" onclick="send('securityScan')">
        <span class="icon">🛡️</span>
        <span class="label">Security<small>Find vulnerabilities</small></span>
      </button>
      <button class="action-btn" onclick="send('gitAnalysis')">
        <span class="icon">📊</span>
        <span class="label">Git Analysis<small>Review changes</small></span>
      </button>
      <button class="action-btn" onclick="send('preCommit')">
        <span class="icon">✅</span>
        <span class="label">Pre-Commit<small>Validate before commit</small></span>
      </button>
      <button class="action-btn" onclick="send('validateContracts')">
        <span class="icon">📋</span>
        <span class="label">Contracts<small>API validation</small></span>
      </button>
      <button class="action-btn" onclick="send('validateSchema')">
        <span class="icon">🗄️</span>
        <span class="label">Schema<small>Prisma / DB</small></span>
      </button>
      <button class="action-btn" onclick="send('detectStack')">
        <span class="icon">🔧</span>
        <span class="label">Detect Stack<small>Languages & frameworks</small></span>
      </button>
      <button class="action-btn" onclick="send('detectEndpoints')">
        <span class="icon">🌐</span>
        <span class="label">Endpoints<small>API routes</small></span>
      </button>
      <button class="action-btn" onclick="send('analyzeCode')">
        <span class="icon">📝</span>
        <span class="label">Analyze Code<small>Current selection</small></span>
      </button>
      <button class="action-btn" onclick="send('buildContext')">
        <span class="icon">🧠</span>
        <span class="label">Build Context<small>For Copilot</small></span>
      </button>
    </div>
  </div>

  <!-- ── Minimal Controls ── -->
  <div class="controls">
    <button class="cbtn" onclick="send('toggleFocus')">Toggle Focus Mode</button>
    <button class="cbtn" onclick="send('showOutput')">Show Output</button>
    <button class="cbtn" onclick="send('openSettings')">Settings</button>
  </div>

  <div class="footer">Copilot Engine — Autonomous Structural Auditor + Backend Manager</div>
</div>

<script>
const vscode = acquireVsCodeApi();
function send(cmd, payload) { vscode.postMessage({ command: cmd, ...(payload||{}) }); }
function esc(s) { return (s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }

function scoreColor(v) {
  if (v <= 2) return '#4ade80';
  if (v <= 4) return '#facc15';
  if (v <= 6) return '#fb923c';
  return '#ef4444';
}
function scoreClass(v) {
  if (v <= 2) return 'c-green';
  if (v <= 4) return 'c-yellow';
  if (v <= 6) return 'c-orange';
  return 'c-red';
}
function cardClass(v) {
  if (v <= 3) return '';
  if (v <= 6) return 'warn';
  return 'danger';
}
function pillClass(level) {
  const l = (level||'').toLowerCase();
  if (l === 'healthy') return 'pill-healthy';
  if (l === 'caution') return 'pill-caution';
  if (l === 'at_risk' || l === 'at-risk') return 'pill-atrisk';
  if (l === 'degraded') return 'pill-degraded';
  if (l === 'critical') return 'pill-critical';
  return 'pill-healthy';
}
function sevIcon(s) {
  const l = (s||'').toLowerCase();
  if (l === 'critical') return '🔴';
  if (l === 'high') return '🟠';
  if (l === 'medium') return '🟡';
  return '🟢';
}

function basename(p) { return (p||'').replace(/\\\\/g,'/').split('/').pop() || p; }

// ── Render dashboard data ──
function renderDashboard(data) {
  const risk = data.health?.risk_scores || {};
  const worker = data.health?.worker || {};
  const graph = data.health?.graph || {};
  const drift = data.health?.drift || {};

  // Health pill
  const pill = document.getElementById('healthPill');
  pill.className = 'pill ' + pillClass(risk.health_level);
  document.getElementById('healthText').textContent = (risk.health_level || 'UNKNOWN').replace('_', ' ');

  // Worker bar
  document.getElementById('wdot').className = 'wdot' + (worker.started_at ? '' : ' off');
  document.getElementById('workerLabel').textContent = worker.started_at ? 'Worker running' : 'Worker stopped';
  document.getElementById('evtCount').textContent = worker.events_processed || 0;
  document.getElementById('fastCount').textContent = worker.fast_path_runs || 0;
  document.getElementById('idleCount').textContent = worker.idle_runs || 0;
  document.getElementById('errCount').textContent = worker.errors || 0;
  document.getElementById('lastEvt').textContent = worker.last_event ? basename(worker.last_event) : '—';

  // Gauge
  const score = risk.overall_score ?? 0;
  const pct = Math.min(score * 10, 100);
  const color = scoreColor(score);
  const fill = document.getElementById('gaugeFill');
  fill.setAttribute('stroke-dasharray', pct + ', 100');
  fill.setAttribute('stroke', color);
  document.getElementById('scoreVal').textContent = score.toFixed(1);
  document.getElementById('scoreVal').style.color = color;
  document.getElementById('levelText').textContent = (risk.health_level || 'UNKNOWN').replace('_', ' ');
  document.getElementById('levelText').style.color = color;

  const meta = [];
  if (graph.total_files) meta.push(graph.total_files + ' files indexed');
  if (graph.file_edges) meta.push(graph.file_edges + ' dependencies');
  if (graph.circular_count) meta.push(graph.circular_count + ' cycles');
  if (drift.affected_files) meta.push(drift.affected_files + ' drifted files');
  document.getElementById('gaugeMeta').innerHTML = meta.join(' &middot; ');

  // Category cards
  const cats = ['schema','contract','drift','security','dependency','migration','naming'];
  for (const c of cats) {
    const v = risk[c + '_risk'] ?? 0;
    const el = document.getElementById('v-' + c);
    el.textContent = v.toFixed(1);
    el.className = 'cat-val ' + scoreClass(v);
    document.getElementById('cat-' + c).className = 'cat-card ' + cardClass(v);
  }

  // Trend sparkline
  renderTrend(data.risk_trend || []);

  // Drift events
  renderDrifts(data.unresolved_drifts || []);

  // Circular dependencies
  renderCircular(data.circular_dependencies || []);

  // Dead code
  renderDeadCode(data.dead_code_files || []);
}

function renderTrend(trend) {
  const svg = document.getElementById('trendSvg');
  if (!trend.length) {
    svg.innerHTML = '<text x="200" y="35" text-anchor="middle" fill="currentColor" opacity="0.3" font-size="8">No trend data yet</text>';
    return;
  }
  const w = 400, h = 60, pad = 4;
  const maxVal = Math.max(...trend.map(t => t.overall_score || 0), 10);
  const points = trend.map((t, i) => {
    const x = pad + (i / Math.max(trend.length - 1, 1)) * (w - pad * 2);
    const y = h - pad - ((t.overall_score || 0) / maxVal) * (h - pad * 2);
    return x + ',' + y;
  });
  const last = trend[trend.length - 1]?.overall_score || 0;
  const col = scoreColor(last);
  svg.innerHTML = '<polyline points="' + points.join(' ') + '" fill="none" stroke="' + col + '" stroke-width="1.5" stroke-linejoin="round"/>'
    + '<circle cx="' + points[points.length-1].split(',')[0] + '" cy="' + points[points.length-1].split(',')[1] + '" r="3" fill="' + col + '"/>';
}

function renderDrifts(drifts) {
  document.getElementById('driftCount').textContent = drifts.length;
  const panel = document.getElementById('driftPanel');
  if (!drifts.length) {
    panel.innerHTML = '<div class="panel-empty">No drift events — structure is stable</div>';
    return;
  }
  panel.innerHTML = drifts.slice(0, 50).map(d =>
    '<div class="row" onclick="send(\'openFile\',{filePath:\'' + esc(d.file_path||'') + '\'})">'
    + '<span class="row-icon">' + sevIcon(d.severity) + '</span>'
    + '<div class="row-body">'
    + '<div class="row-msg sev-' + (d.severity||'low').toLowerCase() + '"><strong>' + esc(d.drift_type||'') + '</strong> on ' + esc(d.entity_name||'?') + '</div>'
    + '<div class="row-meta">' + basename(d.file_path) + (d.old_value && d.new_value ? ' — ' + esc(d.old_value) + ' → ' + esc(d.new_value) : '') + '</div>'
    + '</div></div>'
  ).join('');
}

function renderCircular(cycles) {
  document.getElementById('circCount').textContent = cycles.length;
  const panel = document.getElementById('circPanel');
  if (!cycles.length) {
    panel.innerHTML = '<div class="panel-empty">No circular dependencies — graph is clean</div>';
    return;
  }
  panel.innerHTML = cycles.slice(0, 20).map(c =>
    '<div class="row">'
    + '<span class="row-icon">🔄</span>'
    + '<div class="row-body"><div class="row-msg">' + c.map(f => basename(f)).join(' → ') + '</div></div>'
    + '</div>'
  ).join('');
}

function renderDeadCode(files) {
  document.getElementById('deadCount').textContent = files.length;
  const panel = document.getElementById('deadPanel');
  if (!files.length) {
    panel.innerHTML = '<div class="panel-empty">All files are imported somewhere</div>';
    return;
  }
  panel.innerHTML = files.slice(0, 30).map(f =>
    '<div class="row" onclick="send(\'openFile\',{filePath:\'' + esc(f) + '\'})">'
    + '<span class="row-icon">📄</span>'
    + '<div class="row-body"><div class="row-msg">' + basename(f) + '</div>'
    + '<div class="row-meta">' + esc(f) + '</div>'
    + '</div></div>'
  ).join('');
}

// ── Render backend status ──
function renderBackendStatus(status) {
  const dot = document.getElementById('backendDot');
  const state = document.getElementById('backendState');
  const meta = document.getElementById('backendMeta');
  const btnStart = document.getElementById('btnStart');
  const btnStop = document.getElementById('btnStop');
  const btnRestart = document.getElementById('btnRestart');

  // Update dot and state
  dot.className = 'status-dot status-' + status.health;
  state.textContent = status.running ? (status.health === 'starting' ? 'Starting...' : 'Running') : 'Stopped';
  state.style.color = status.health === 'healthy' ? '#4ade80' : status.health === 'starting' ? '#facc15' : status.health === 'unhealthy' ? '#ef4444' : '#6b7280';

  // Update metadata
  const uptimeStr = status.uptime > 0 ? (status.uptime < 60 ? status.uptime + 's' : Math.floor(status.uptime / 60) + 'm ' + (status.uptime % 60) + 's') : '—';
  meta.textContent = 'Port: ' + (status.port || '—') + ' | PID: ' + (status.pid || '—') + ' | Uptime: ' + uptimeStr;

  // Update button states
  btnStart.disabled = status.running;
  btnStop.disabled = !status.running;
  btnRestart.disabled = !status.running;
}

function renderBackendLogs(logs) {
  const content = document.getElementById('logsContent');
  if (!logs || !logs.length) {
    content.className = 'logs-content empty';
    content.textContent = 'No logs available';
    return;
  }
  content.className = 'logs-content';
  content.innerHTML = logs.map(line => '<div class="log-line">' + esc(line) + '</div>').join('');
  content.scrollTop = content.scrollHeight;
}

// ── Message handler ──
window.addEventListener('message', (event) => {
  const msg = event.data;
  if (msg.command === 'dashboard') {
    renderDashboard(msg.data);
  } else if (msg.command === 'backendStatus') {
    renderBackendStatus(msg.status);
  } else if (msg.command === 'backendLogs') {
    renderBackendLogs(msg.logs);
  }
});

// Signal that webview is ready to receive messages
vscode.postMessage({ command: 'webviewReady' });
</script>
</body>
</html>`;
    }
}
