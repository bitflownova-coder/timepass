/**
 * Copilot Engine - Command Implementations
 * All user-facing commands registered in package.json
 */
import * as vscode from 'vscode';
import { EngineClient } from './engineClient';
import { OutputManager } from './outputChannel';
import { StatusBarManager } from './statusBar';
import { PromptInjector } from './promptInjector';
import { SecurityDiagnosticsProvider } from './securityDiagnostics';
import { BehaviorTracker } from './behaviorTracker';
import { GitIntegration } from './gitIntegration';
import { DashboardPanel } from './webviewPanel';
import { TerminalCapture } from './terminalCapture';
import { AutonomousEngine } from './autonomousEngine';
import { BackendManager } from './backendManager';

export function registerCommands(
    context: vscode.ExtensionContext,
    client: EngineClient,
    output: OutputManager,
    statusBar: StatusBarManager,
    promptInjector: PromptInjector,
    securityDiag: SecurityDiagnosticsProvider,
    behaviorTracker: BehaviorTracker,
    gitIntegration: GitIntegration,
    terminalCapture: TerminalCapture,
    autonomousEngine: AutonomousEngine,
    backendManager: BackendManager
): void {
    // ====== START ENGINE ======
    context.subscriptions.push(
        vscode.commands.registerCommand('copilotEngine.start', async () => {
            statusBar.setStatus('connecting');
            output.section('ENGINE START');

            const running = await client.isRunning();
            if (running) {
                statusBar.setStatus('connected');
                output.success('Engine already running!');
                vscode.window.showInformationMessage('⚡ Copilot Engine is running');

                // Register workspace
                const workspacePath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
                if (workspacePath) {
                    try {
                        const ws = await client.registerWorkspace(
                            workspacePath,
                            vscode.workspace.name
                        );
                        output.success(`Workspace registered: ${ws.name || ws.path} (${ws.language || 'unknown'})`);
                        client.connectWebSocket(workspacePath);
                    } catch (err: any) {
                        output.warn(`Workspace registration failed: ${err.message}`);
                    }
                }
                return;
            }

            // Use BackendManager to start (handles existing backends, multiple paths, etc)
            const started = await backendManager.start();
            
            if (started) {
                // Verify connection and get version
                const health = await client.checkHealth();
                if (health) {
                    statusBar.setStatus('connected');
                    output.success(`Engine connected! Version ${health.version}`);

                    // Register workspace
                    const workspacePath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
                    if (workspacePath) {
                        try {
                            await client.registerWorkspace(workspacePath, vscode.workspace.name);
                            client.connectWebSocket(workspacePath);
                        } catch (err: any) {
                            output.warn(`Workspace registration: ${err.message}`);
                        }
                    }

                    vscode.window.showInformationMessage('⚡ Copilot Engine started');
                } else {
                    statusBar.setStatus('connected');
                    output.success('Engine started (health check pending)');
                }
            } else {
                statusBar.setStatus('error');
                // BackendManager already logged detailed errors
            }
        })
    );

    // ====== STOP ENGINE ======
    context.subscriptions.push(
        vscode.commands.registerCommand('copilotEngine.stop', async () => {
            client.disconnect();
            terminalCapture.stop();
            statusBar.setStatus('disconnected');
            output.info('Engine disconnected');
            vscode.window.showInformationMessage('Copilot Engine stopped');
        })
    );

    // ====== SHOW STATUS ======
    context.subscriptions.push(
        vscode.commands.registerCommand('copilotEngine.showStatus', async () => {
            output.show();
            output.section('ENGINE STATUS');

            const health = await client.checkHealth();
            if (health) {
                output.success(`Status: ${health.status}`);
                output.info(`Version: ${health.version}`);
                output.info(`Uptime: ${Math.round(health.uptime)}s`);
                output.info(`Watched Workspaces: ${health.watched_workspaces.join(', ') || 'none'}`);
            } else {
                output.error('Engine is not running');
            }

            // Show behavior stats
            const stats = behaviorTracker.getStats();
            output.separator();
            output.info(`Session Duration: ${stats.session_duration_minutes} min`);
            output.info(`File Switches: ${stats.file_switches}`);
            output.info(`Errors Tracked: ${stats.total_errors}`);
            output.info(`Focus Mode: ${stats.focus_mode ? 'ACTIVE' : 'Off'}`);
        })
    );

    // ====== CLEAR HISTORY ======
    context.subscriptions.push(
        vscode.commands.registerCommand('copilotEngine.clearHistory', () => {
            securityDiag.clearDiagnostics();
            output.info('Error history and diagnostics cleared');
            vscode.window.showInformationMessage('History cleared');
        })
    );

    // ====== ANALYZE CODE ======
    context.subscriptions.push(
        vscode.commands.registerCommand('copilotEngine.analyzeCode', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showWarningMessage('No active editor');
                return;
            }

            const selection = editor.selection;
            let code: string;

            if (selection.isEmpty) {
                code = editor.document.getText();
            } else {
                code = editor.document.getText(selection);
            }

            const workspacePath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
            if (!workspacePath) { return; }

            output.show();
            output.section('CODE ANALYSIS');
            output.info('Building analysis context...');

            try {
                const result = await client.buildContext(
                    workspacePath,
                    `Analyze this code for:\n1. Bugs and potential issues\n2. Performance problems\n3. Security vulnerabilities\n4. Code style improvements\n5. Best practice violations\n\nCode:\n\`\`\`\n${code}\n\`\`\``,
                    editor.document.uri.fsPath
                );

                output.separator();
                output.info(result.prompt);
                output.info(`\nToken estimate: ${result.token_estimate}`);

                await vscode.env.clipboard.writeText(result.prompt);
                vscode.window.showInformationMessage('Analysis context copied to clipboard!');
            } catch (err: any) {
                output.error(`Analysis failed: ${err.message}`);
            }
        })
    );

    // ====== BUILD CONTEXT ======
    context.subscriptions.push(
        vscode.commands.registerCommand('copilotEngine.buildContext', async () => {
            const task = await vscode.window.showInputBox({
                prompt: 'What are you trying to do?',
                placeHolder: 'e.g., Fix the authentication bug, Add pagination to the API',
            });

            if (!task) { return; }

            const workspacePath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
            const currentFile = vscode.window.activeTextEditor?.document.uri.fsPath;
            if (!workspacePath) { return; }

            output.show();
            output.section('CONTEXT BUILD');
            output.info(`Task: ${task}`);

            try {
                const result = await client.buildContext(
                    workspacePath,
                    task,
                    currentFile
                );

                output.separator();
                output.info(result.prompt);
                output.info(`\nTokens: ${result.token_estimate}`);

                await vscode.env.clipboard.writeText(result.prompt);
                vscode.window.showInformationMessage('Context copied to clipboard! Paste into Copilot Chat.');
            } catch (err: any) {
                output.error(`Context build failed: ${err.message}`);
            }
        })
    );

    // ====== CHECK SECURITY ======
    context.subscriptions.push(
        vscode.commands.registerCommand('copilotEngine.checkSecurity', async () => {
            output.show();
            await securityDiag.scanWorkspace();
        })
    );

    // ====== FIND SIMILAR ERRORS ======
    context.subscriptions.push(
        vscode.commands.registerCommand('copilotEngine.findSimilarErrors', async () => {
            const errorText = await vscode.window.showInputBox({
                prompt: 'Paste the error message',
                placeHolder: 'TypeError: Cannot read property...',
            });

            if (!errorText) { return; }

            output.show();
            output.section('SIMILAR ERROR SEARCH');

            try {
                const parsed = await client.parseError(errorText);
                output.info(`Error Type: ${parsed.error_type}`);
                output.info(`Message: ${parsed.message}`);

                if (parsed.suggestions.length > 0) {
                    output.separator();
                    output.info('Suggestions:');
                    for (const s of parsed.suggestions) {
                        output.info(`  → ${s}`);
                    }
                }

                const similar = await client.findSimilarErrors(errorText);
                if (similar?.similar_fixes?.length > 0) {
                    output.separator();
                    output.info('Past Fixes:');
                    for (const fix of similar.similar_fixes) {
                        output.info(`  ✅ ${fix.description} (used ${fix.success_count}x)`);
                    }
                }
            } catch (err: any) {
                output.error(`Search failed: ${err.message}`);
            }
        })
    );

    // ====== INJECT CONTEXT ======
    context.subscriptions.push(
        vscode.commands.registerCommand('copilotEngine.injectContext', async () => {
            await promptInjector.injectContextAtCursor();
        })
    );

    // ====== SHOW DASHBOARD ======
    context.subscriptions.push(
        vscode.commands.registerCommand('copilotEngine.showDashboard', () => {
            DashboardPanel.show(context, client, autonomousEngine, backendManager);
        })
    );

    // ====== BACKEND MANAGEMENT ======
    context.subscriptions.push(
        vscode.commands.registerCommand('copilotEngine.startBackend', async () => {
            await backendManager.start();
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('copilotEngine.stopBackend', () => {
            backendManager.stop();
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('copilotEngine.restartBackend', async () => {
            await backendManager.restart();
        })
    );

    // ====== FOCUS MODE ======
    context.subscriptions.push(
        vscode.commands.registerCommand('copilotEngine.toggleFocusMode', () => {
            if (behaviorTracker.isFocusModeActive()) {
                behaviorTracker.deactivateFocusMode();
            } else {
                behaviorTracker.activateFocusMode();
            }
        })
    );

    // ====== GIT ANALYZE ======
    context.subscriptions.push(
        vscode.commands.registerCommand('copilotEngine.analyzeGitChanges', async () => {
            const workspacePath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
            if (!workspacePath) { return; }

            output.show();
            output.section('GIT CHANGE ANALYSIS');

            try {
                const diff = await client.analyzeGitDiff(workspacePath);
                output.info(`Risk Score: ${diff.risk_score}/10`);

                if (diff.warnings.length > 0) {
                    output.separator();
                    output.warn('Warnings:');
                    for (const w of diff.warnings) {
                        output.warn(`  ⚠️ ${w}`);
                    }
                }

                output.separator();
                output.info(`Changed Files (${diff.changes.length}):`);
                for (const c of diff.changes) {
                    const icon = c.risk_level === 'high' ? '🔴' : c.risk_level === 'medium' ? '🟡' : '🟢';
                    output.info(`  ${icon} ${c.file} [${c.change_type}]`);
                }
            } catch (err: any) {
                output.error(`Git analysis failed: ${err.message}`);
            }
        })
    );

    // ====== DETECT API ENDPOINTS ======
    context.subscriptions.push(
        vscode.commands.registerCommand('copilotEngine.detectEndpoints', async () => {
            const workspacePath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
            if (!workspacePath) { return; }

            output.show();
            output.section('API ENDPOINT DETECTION');

            try {
                const result = await client.detectEndpoints(workspacePath);
                if (result.endpoints && result.endpoints.length > 0) {
                    for (const ep of result.endpoints) {
                        output.info(`  ${ep.method} ${ep.route} → ${ep.file}:${ep.line}`);
                    }
                } else {
                    output.info('No API endpoints detected');
                }
            } catch (err: any) {
                output.error(`Detection failed: ${err.message}`);
            }
        })
    );

    // ====== FULL SCAN (Enforcement) ======
    context.subscriptions.push(
        vscode.commands.registerCommand('copilotEngine.fullScan', async () => {
            const workspacePath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
            if (!workspacePath) { return; }

            output.show();
            output.section('FULL ENFORCEMENT SCAN');
            statusBar.setStatus('connecting'); // indicate busy

            try {
                const report = await client.fullScan(workspacePath);
                const riskIcon = report.risk_level === 'critical' ? '🔴'
                    : report.risk_level === 'high' ? '🟠'
                    : report.risk_level === 'medium' ? '🟡' : '🟢';

                output.info(`${riskIcon} Risk: ${report.risk_level.toUpperCase()} (score ${report.risk_score}/100)`);
                output.separator();

                if (report.issues.length > 0) {
                    output.warn(`Found ${report.issues.length} issue(s):`);
                    for (const issue of report.issues) {
                        const icon = issue.severity === 'error' ? '❌' : issue.severity === 'warning' ? '⚠️' : 'ℹ️';
                        output.info(`  ${icon} [${issue.category}] ${issue.message}`);
                        if (issue.file) { output.info(`     → ${issue.file}${issue.line ? ':' + issue.line : ''}`); }
                    }
                } else {
                    output.success('No issues found — codebase is clean!');
                }

                if (report.summary) {
                    output.separator();
                    for (const [key, val] of Object.entries(report.summary)) {
                        output.info(`  ${key}: ${val}`);
                    }
                }

                statusBar.setStatus('connected');
                vscode.window.showInformationMessage(
                    `${riskIcon} Scan complete: ${report.issues.length} issue(s), risk ${report.risk_level}`
                );
            } catch (err: any) {
                statusBar.setStatus('connected');
                output.error(`Full scan failed: ${err.message}`);
            }
        })
    );

    // ====== PRE-COMMIT CHECK (Enforcement) ======
    context.subscriptions.push(
        vscode.commands.registerCommand('copilotEngine.preCommitCheck', async () => {
            const workspacePath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
            if (!workspacePath) { return; }

            output.show();
            output.section('PRE-COMMIT VALIDATION');

            try {
                // Get git changed files first
                let changedFiles: string[] = [];
                try {
                    const diff = await client.analyzeGitDiff(workspacePath);
                    changedFiles = diff.changes?.map((c: any) => c.file) || [];
                } catch {
                    // Fallback: validate all files
                    output.warn('Could not detect git changes, scanning workspace...');
                }

                const report = await client.preCommitValidation(workspacePath, changedFiles);
                const riskIcon = report.risk_level === 'critical' ? '🔴'
                    : report.risk_level === 'high' ? '🟠'
                    : report.risk_level === 'medium' ? '🟡' : '🟢';

                if (report.issues.length === 0) {
                    output.success('✅ Commit is SAFE — no enforcement violations');
                    vscode.window.showInformationMessage('✅ Pre-commit: All clear!');
                } else {
                    const errors = report.issues.filter((i: any) => i.severity === 'error');
                    const warnings = report.issues.filter((i: any) => i.severity === 'warning');

                    output.warn(`${riskIcon} Found ${errors.length} error(s), ${warnings.length} warning(s)`);
                    output.separator();

                    for (const issue of report.issues) {
                        const icon = issue.severity === 'error' ? '❌' : '⚠️';
                        output.info(`  ${icon} [${issue.category}] ${issue.message}`);
                        if (issue.file) { output.info(`     → ${issue.file}`); }
                    }

                    if (errors.length > 0) {
                        const proceed = await vscode.window.showWarningMessage(
                            `⚠️ ${errors.length} error(s) found. Commit anyway?`,
                            'Commit Anyway', 'Cancel'
                        );
                        if (proceed !== 'Commit Anyway') {
                            output.info('Commit aborted by user');
                        }
                    } else {
                        vscode.window.showInformationMessage(
                            `${riskIcon} Pre-commit: ${warnings.length} warning(s), no blocking errors`
                        );
                    }
                }
            } catch (err: any) {
                output.error(`Pre-commit check failed: ${err.message}`);
            }
        })
    );

    // ====== VALIDATE CONTRACTS (Enforcement) ======
    context.subscriptions.push(
        vscode.commands.registerCommand('copilotEngine.validateContracts', async () => {
            const workspacePath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
            if (!workspacePath) { return; }

            output.show();
            output.section('API CONTRACT VALIDATION');

            try {
                const result = await client.validateContracts(workspacePath);
                const violations = result.violations || [];

                if (violations.length === 0) {
                    output.success('✅ All API contracts valid');
                    vscode.window.showInformationMessage('✅ API contracts: No violations');
                } else {
                    output.warn(`Found ${violations.length} contract violation(s):`);
                    for (const v of violations) {
                        output.info(`  ❌ ${v.rule}: ${v.message}`);
                        if (v.endpoint) { output.info(`     → ${v.endpoint}`); }
                        if (v.suggestion) { output.info(`     💡 ${v.suggestion}`); }
                    }
                    vscode.window.showWarningMessage(
                        `⚠️ ${violations.length} API contract violation(s) found`
                    );
                }
            } catch (err: any) {
                output.error(`Contract validation failed: ${err.message}`);
            }
        })
    );

    // ====== VALIDATE SCHEMA (Enforcement) ======
    context.subscriptions.push(
        vscode.commands.registerCommand('copilotEngine.validateSchema', async () => {
            const workspacePath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
            if (!workspacePath) { return; }

            output.show();
            output.section('SCHEMA / PRISMA VALIDATION');

            try {
                const result = await client.analyzePrisma(workspacePath);
                const issues = result.issues || [];

                if (issues.length === 0) {
                    output.success('✅ Schema is clean — no issues found');
                    vscode.window.showInformationMessage('✅ Schema validation passed');
                } else {
                    output.warn(`Found ${issues.length} schema issue(s):`);
                    for (const issue of issues) {
                        const icon = issue.severity === 'error' ? '❌' : '⚠️';
                        output.info(`  ${icon} [${issue.category}] ${issue.message}`);
                        if (issue.model) { output.info(`     → Model: ${issue.model}`); }
                    }
                    vscode.window.showWarningMessage(
                        `⚠️ ${issues.length} schema issue(s) found`
                    );
                }
            } catch (err: any) {
                output.error(`Schema validation failed: ${err.message}`);
            }
        })
    );

    // ====== REMOVE CONTEXT BLOCK ======
    context.subscriptions.push(
        vscode.commands.registerCommand('copilotEngine.removeContext', async () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showWarningMessage('No active editor');
                return;
            }
            await promptInjector.removeContextBlock();
        })
    );

    // ====== DETECT STACK ======
    context.subscriptions.push(
        vscode.commands.registerCommand('copilotEngine.detectStack', async () => {
            const workspacePath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
            if (!workspacePath) { return; }

            output.show();
            output.section('STACK DETECTION');

            try {
                const stack = await client.detectStack(workspacePath);
                output.info(`Language:  ${stack.languages?.join(', ') || 'unknown'}`);
                output.info(`Framework: ${stack.frameworks?.join(', ') || 'unknown'}`);
                output.info(`ORM:       ${stack.orm || 'none'}`);
                output.info(`API Style: ${stack.api_style || 'unknown'}`);
                if (stack.detected_files && stack.detected_files.length > 0) {
                    output.separator();
                    output.info('Key files detected:');
                    for (const f of stack.detected_files) {
                        output.info(`  📄 ${f}`);
                    }
                }
                vscode.window.showInformationMessage(
                    `Stack: ${stack.languages?.[0] || '?'} / ${stack.frameworks?.[0] || '?'} / ${stack.orm || 'no ORM'}`
                );
            } catch (err: any) {
                output.error(`Stack detection failed: ${err.message}`);
            }
        })
    );
}

// ====== Helpers ======

function getCopilotEnginePath(): string {
    // Try to detect copilot-engine path relative to workspace
    const workspaceFolders = vscode.workspace.workspaceFolders;
    if (workspaceFolders) {
        for (const folder of workspaceFolders) {
            const enginePath = vscode.Uri.joinPath(folder.uri, 'copilot-engine').fsPath;
            return enginePath;
        }
    }
    return '';
}

function sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
}
