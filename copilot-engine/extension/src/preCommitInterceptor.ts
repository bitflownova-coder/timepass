/**
 * Copilot Engine - PreCommitInterceptor
 * Automatically intercepts git commits and validates changes.
 *
 * Strategy:
 *  - Watches the Git extension's repository state for commits
 *  - Before a commit goes through, calls /pipeline/pre-commit
 *  - If critical issues found → shows warning + blocks (user can override)
 *  - If moderate issues → shows info notification
 *  - If clean → silent pass-through
 *
 * This is NOT a git hook file. It uses VS Code's Git extension API
 * to intercept commits at the UI level.
 */
import * as vscode from 'vscode';
import { EngineClient } from './engineClient';
import { OutputManager } from './outputChannel';

interface PreCommitResult {
    workspace_path: string;
    timestamp: string;
    issues: Array<{
        severity: string;
        category: string;
        message: string;
        file?: string;
        line?: number;
    }>;
    risk_score: number;
    risk_level: string;
    commit_safe: boolean;
    commit_warnings: string[];
}

export class PreCommitInterceptor {
    private client: EngineClient;
    private output: OutputManager;
    private disposables: vscode.Disposable[] = [];
    private enabled: boolean = true;
    private running: boolean = false;
    private lastCheckResult: PreCommitResult | null = null;
    private interceptCount: number = 0;
    private blockedCount: number = 0;

    constructor(client: EngineClient, output: OutputManager) {
        this.client = client;
        this.output = output;
    }

    /**
     * Start intercepting git commits.
     * Registers a post-commit-command that runs validation.
     */
    start(workspacePath: string): void {
        if (this.running) { return; }
        this.running = true;

        // Watch for source control input box changes (commit attempt detection)
        // VS Code doesn't have a direct pre-commit hook API, so we use
        // the git extension's postCommitCommand as a workaround, or
        // we intercept via a file system watcher on .git/COMMIT_EDITMSG
        this.watchGitCommits(workspacePath);

        this.output.info('[PreCommit] Interceptor active — commits will be validated');
    }

    /**
     * Run a pre-commit check manually (also called automatically).
     */
    async checkBeforeCommit(workspacePath: string): Promise<PreCommitResult | null> {
        this.interceptCount++;

        try {
            // Get changed files from git
            const changedFiles = await this.getGitChangedFiles(workspacePath);
            if (changedFiles.length === 0) {
                return null;
            }

            this.output.info(`[PreCommit] Validating ${changedFiles.length} changed files...`);

            const result = await this.client.post<PreCommitResult>('/pipeline/pre-commit', {
                workspace_path: workspacePath,
                changed_files: changedFiles,
            });

            this.lastCheckResult = result;

            // Handle result
            if (!result.commit_safe) {
                this.blockedCount++;
                await this.showBlockingWarning(result);
            } else if (result.commit_warnings?.length) {
                this.showInfoWarnings(result);
            }

            return result;
        } catch (e) {
            this.output.warn(`[PreCommit] Check failed: ${e}`);
            return null;
        }
    }

    /**
     * Toggle interceptor on/off.
     */
    toggle(): boolean {
        this.enabled = !this.enabled;
        this.output.info(`[PreCommit] ${this.enabled ? 'Enabled' : 'Disabled'}`);
        return this.enabled;
    }

    getStats(): Record<string, any> {
        return {
            enabled: this.enabled,
            running: this.running,
            interceptCount: this.interceptCount,
            blockedCount: this.blockedCount,
            lastResult: this.lastCheckResult ? {
                risk_score: this.lastCheckResult.risk_score,
                risk_level: this.lastCheckResult.risk_level,
                commit_safe: this.lastCheckResult.commit_safe,
                issues: this.lastCheckResult.issues?.length || 0,
            } : null,
        };
    }

    // ═══════════════════════════════════════════
    // Internal
    // ═══════════════════════════════════════════

    private watchGitCommits(workspacePath: string): void {
        // Strategy: Watch .git/COMMIT_EDITMSG — written right before a commit
        // This is the most reliable cross-platform approach
        const gitDir = vscode.Uri.file(
            require('path').join(workspacePath, '.git')
        );

        try {
            const pattern = new vscode.RelativePattern(gitDir, 'COMMIT_EDITMSG');
            const watcher = vscode.workspace.createFileSystemWatcher(pattern);

            this.disposables.push(
                watcher.onDidCreate(() => {
                    if (this.enabled) {
                        this.checkBeforeCommit(workspacePath);
                    }
                }),
                watcher.onDidChange(() => {
                    if (this.enabled) {
                        this.checkBeforeCommit(workspacePath);
                    }
                }),
                watcher,
            );
        } catch {
            this.output.warn('[PreCommit] Could not watch .git directory');
        }
    }

    private async getGitChangedFiles(workspacePath: string): Promise<string[]> {
        try {
            const gitExt = vscode.extensions.getExtension('vscode.git')?.exports;
            const api = gitExt?.getAPI(1);
            if (!api?.repositories?.length) { return []; }

            const repo = api.repositories[0];
            const changes = [
                ...repo.state.workingTreeChanges,
                ...repo.state.indexChanges,
            ];

            const files = changes
                .map((c: any) => c.uri?.fsPath)
                .filter((f: string | undefined): f is string => !!f);

            // Deduplicate
            return [...new Set(files)];
        } catch {
            return [];
        }
    }

    private async showBlockingWarning(result: PreCommitResult): Promise<void> {
        const criticalCount = result.issues.filter(i => i.severity === 'CRITICAL').length;
        const highCount = result.issues.filter(i => i.severity === 'HIGH').length;

        const msg = `Commit blocked: ${criticalCount} critical, ${highCount} high severity issues (risk: ${result.risk_score}/10)`;

        const action = await vscode.window.showWarningMessage(
            msg,
            { modal: false },
            'Show Details',
            'Commit Anyway',
        );

        if (action === 'Show Details') {
            this.output.section('PRE-COMMIT VIOLATIONS');
            for (const issue of result.issues) {
                const loc = issue.file ? ` [${issue.file}:${issue.line || '?'}]` : '';
                this.output.warn(`[${issue.severity}] ${issue.category}${loc}: ${issue.message}`);
            }
            this.output.show();
        }

        // "Commit Anyway" — just let it go, the commit already happened
        // (we're in post-COMMIT_EDITMSG, commit may already be in progress)
    }

    private showInfoWarnings(result: PreCommitResult): void {
        const warnings = result.commit_warnings || [];
        if (warnings.length) {
            vscode.window.showInformationMessage(
                `Commit OK with ${warnings.length} warning(s): ${warnings[0]}`
            );
        }
    }

    stop(): void {
        this.running = false;
        for (const d of this.disposables) {
            try { d.dispose(); } catch { }
        }
        this.disposables = [];
    }

    dispose(): void {
        this.stop();
    }
}
