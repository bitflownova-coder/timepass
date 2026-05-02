/**
 * Copilot Engine - VS Code Extension Entry Point
 * Main activation/deactivation logic. Wires all modules together.
 */
import * as vscode from 'vscode';
import { EngineClient } from './engineClient';
import { OutputManager } from './outputChannel';
import { StatusBarManager } from './statusBar';
import { TerminalCapture } from './terminalCapture';
import { CopilotCodeLensProvider, registerCodeLensCommands } from './codeLensProvider';
import { SecurityDiagnosticsProvider } from './securityDiagnostics';
import { GitIntegration } from './gitIntegration';
import { PromptInjector } from './promptInjector';
import { BehaviorTracker } from './behaviorTracker';
import { registerCommands } from './commands';
import { getConfig } from './config';
import { AutonomousEngine } from './autonomousEngine';
import { PreCommitInterceptor } from './preCommitInterceptor';
import { BackendManager } from './backendManager';

let client: EngineClient;
let output: OutputManager;
let statusBar: StatusBarManager;
let terminalCapture: TerminalCapture;
let codeLensProvider: CopilotCodeLensProvider;
let securityDiag: SecurityDiagnosticsProvider;
let gitIntegration: GitIntegration;
let promptInjector: PromptInjector;
let behaviorTracker: BehaviorTracker;
let autonomousEngine: AutonomousEngine;
let preCommitInterceptor: PreCommitInterceptor;
let backendManager: BackendManager;

/**
 * Extension activation
 */
export async function activate(context: vscode.ExtensionContext): Promise<void> {
    // ── Core Components ──
    output = new OutputManager();
    client = new EngineClient(output);
    statusBar = new StatusBarManager();
    backendManager = new BackendManager(context, output);
    context.subscriptions.push(statusBar);

    // Subscribe to backend progress updates
    backendManager.onProgress((message) => {
        // Extract key info for status bar
        if (message.includes('Scanning:')) {
            const match = message.match(/(\d+)\/(\d+)/);
            if (match) {
                statusBar.setStatus('connecting', `Scanning ${match[1]}/${match[2]} files`);
            }
        } else if (message.includes('Step ')) {
            statusBar.setStatus('connecting', message.replace(/[^\x00-\x7F]/g, '').trim());
        } else if (message.includes('Waiting')) {
            statusBar.setStatus('connecting', 'Starting backend...');
        }
    });

    output.section('COPILOT ENGINE');
    output.info('Initializing...');

    // ── Feature Modules ──
    terminalCapture = new TerminalCapture(client, output, statusBar);
    codeLensProvider = new CopilotCodeLensProvider(client, output);
    securityDiag = new SecurityDiagnosticsProvider(client, output);
    gitIntegration = new GitIntegration(client, output);
    promptInjector = new PromptInjector(client, output);
    behaviorTracker = new BehaviorTracker(client, output, statusBar);
    autonomousEngine = new AutonomousEngine(client, output);
    preCommitInterceptor = new PreCommitInterceptor(client, output);

    // ── Register Commands ──
    registerCommands(
        context, client, output, statusBar,
        promptInjector, securityDiag, behaviorTracker,
        gitIntegration, terminalCapture, autonomousEngine, backendManager
    );
    registerCodeLensCommands(context, client, output);

    // ── Register CodeLens Provider ──
    const codeLensLanguages = [
        'python', 'javascript', 'typescript',
        'javascriptreact', 'typescriptreact',
        'java', 'go', 'rust'
    ];

    for (const lang of codeLensLanguages) {
        context.subscriptions.push(
            vscode.languages.registerCodeLensProvider(
                { language: lang, scheme: 'file' },
                codeLensProvider
            )
        );
    }

    // ── Register Disposables ──
    context.subscriptions.push(
        { dispose: () => terminalCapture.stop() },
        { dispose: () => securityDiag.dispose() },
        { dispose: () => gitIntegration.dispose() },
        { dispose: () => behaviorTracker.dispose() },
        { dispose: () => autonomousEngine.dispose() },
        { dispose: () => preCommitInterceptor.dispose() },
        { dispose: () => client.disconnect() }
    );

    // ── WebSocket Event Handlers ──
    client.on('connected', () => {
        statusBar.setStatus('connected');
    });

    client.on('disconnected', () => {
        if (!behaviorTracker.isFocusModeActive()) {
            statusBar.setStatus('disconnected');
        }
    });

    client.on('error', (data: any) => {
        output.warn(`Engine event: ${JSON.stringify(data)}`);
    });

    client.on('file_changed', (data: any) => {
        // Refresh CodeLens when files change
        codeLensProvider.refresh();
    });

    // ── File Save Handler: auto-inject + enforcement ──
    context.subscriptions.push(
        vscode.workspace.onDidSaveTextDocument((doc) => {
            // Trigger debounced auto-inject (no-op if disabled in config)
            promptInjector.scheduleAutoInject(doc);
        })
    );

    // ── Config Change Handler ──
    context.subscriptions.push(
        vscode.workspace.onDidChangeConfiguration((e) => {
            if (e.affectsConfiguration('copilotEngine')) {
                const newConfig = getConfig();

                // Toggle terminal capture
                if (newConfig.terminalCapture) {
                    terminalCapture.start();
                } else {
                    terminalCapture.stop();
                }

                // Refresh CodeLens
                codeLensProvider.refresh();

                output.info('Configuration updated');
            }
        })
    );

    output.success('Copilot Engine extension activated!');
    output.info('Use Ctrl+Shift+P → "Copilot Engine" to see available commands');

    // ── Auto-Start Backend ──
    const config = getConfig();
    if (config.autoStart) {
        output.info('Auto-starting backend server...');
        statusBar.setStatus('connecting');
        
        const started = await backendManager.start();
        if (started) {
            statusBar.setStatus('connected');
            output.success('Backend auto-started successfully!');
            
            // Register workspace
            const workspacePath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
            if (workspacePath) {
                try {
                    await client.registerWorkspace(workspacePath, vscode.workspace.name);
                    client.connectWebSocket(workspacePath);
                } catch { }
            }

            // Start feature modules
            if (config.terminalCapture) {
                terminalCapture.start();
            }
            if (config.securityWarnings) {
                securityDiag.start();
            }
            behaviorTracker.start();
            await gitIntegration.initialize();

            // ── Start autonomous runtime ──
            if (workspacePath) {
                autonomousEngine.start(workspacePath);
                preCommitInterceptor.start(workspacePath);
            }
        } else {
            statusBar.setStatus('disconnected');
            output.warn('Backend failed to start. Use dashboard to manage backend.');
        }
    } else {
        // Check if backend is already running
        const running = await client.isRunning();
        if (running) {
            statusBar.setStatus('connected');
            output.info('Backend is already running');
            
            // Register workspace and start modules
            const workspacePath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
            if (workspacePath) {
                try {
                    await client.registerWorkspace(workspacePath, vscode.workspace.name);
                    client.connectWebSocket(workspacePath);
                } catch { }
                
                const config = getConfig();
                if (config.terminalCapture) terminalCapture.start();
                if (config.securityWarnings) securityDiag.start();
                behaviorTracker.start();
                await gitIntegration.initialize();
                autonomousEngine.start(workspacePath);
                preCommitInterceptor.start(workspacePath);
            }
        } else {
            statusBar.setStatus('disconnected');
            output.info('Backend not running. Use dashboard or "Start Engine" command.');
        }
    }
}

/**
 * Extension deactivation
 */
export function deactivate(): void {
    client?.disconnect();
    terminalCapture?.stop();
    securityDiag?.dispose();
    gitIntegration?.dispose();
    behaviorTracker?.dispose();
    autonomousEngine?.dispose();
    preCommitInterceptor?.dispose();
    backendManager?.dispose();
}
