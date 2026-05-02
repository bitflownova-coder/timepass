/**
 * Copilot Engine - Git Integration (VS Code Side)
 * Accesses VS Code's built-in Git API for change tracking
 */
import * as vscode from 'vscode';
import { EngineClient } from './engineClient';
import { OutputManager } from './outputChannel';

interface GitAPI {
    repositories: GitRepository[];
}

interface GitRepository {
    rootUri: vscode.Uri;
    state: {
        HEAD: { name: string; commit: string } | undefined;
        workingTreeChanges: GitChange[];
        indexChanges: GitChange[];
        mergeChanges: GitChange[];
    };
    diffWithHEAD(path?: string): Promise<string>;
    log(options?: { maxEntries?: number }): Promise<GitCommit[]>;
}

interface GitChange {
    uri: vscode.Uri;
    status: number;
}

interface GitCommit {
    hash: string;
    message: string;
    authorName: string;
    authorDate: Date;
}

export class GitIntegration {
    private client: EngineClient;
    private output: OutputManager;
    private gitApi: GitAPI | null = null;
    private disposables: vscode.Disposable[] = [];
    private changeWarnTimer: NodeJS.Timeout | null = null;

    constructor(client: EngineClient, output: OutputManager) {
        this.client = client;
        this.output = output;
    }

    async initialize(): Promise<boolean> {
        try {
            const gitExtension = vscode.extensions.getExtension('vscode.git');
            if (!gitExtension) {
                this.output.warn('Git extension not found');
                return false;
            }

            if (!gitExtension.isActive) {
                await gitExtension.activate();
            }

            const api = gitExtension.exports.getAPI(1);
            this.gitApi = api;

            // Watch for file saves to analyze risk
            const saveWatcher = vscode.workspace.onDidSaveTextDocument((doc) => {
                this.onFileSaved(doc);
            });
            this.disposables.push(saveWatcher);

            this.output.success('Git integration initialized');
            return true;
        } catch (err: any) {
            this.output.error(`Git init failed: ${err.message}`);
            return false;
        }
    }

    getCurrentBranch(): string | undefined {
        if (!this.gitApi || this.gitApi.repositories.length === 0) { return undefined; }
        return this.gitApi.repositories[0].state.HEAD?.name;
    }

    getCurrentCommit(): string | undefined {
        if (!this.gitApi || this.gitApi.repositories.length === 0) { return undefined; }
        return this.gitApi.repositories[0].state.HEAD?.commit;
    }

    getModifiedFiles(): string[] {
        if (!this.gitApi || this.gitApi.repositories.length === 0) { return []; }
        const repo = this.gitApi.repositories[0];
        return [
            ...repo.state.workingTreeChanges.map(c => c.uri.fsPath),
            ...repo.state.indexChanges.map(c => c.uri.fsPath),
        ];
    }

    async getRecentCommits(count: number = 10): Promise<GitCommit[]> {
        if (!this.gitApi || this.gitApi.repositories.length === 0) { return []; }
        try {
            return await this.gitApi.repositories[0].log({ maxEntries: count });
        } catch {
            return [];
        }
    }

    async getDiff(filePath?: string): Promise<string> {
        if (!this.gitApi || this.gitApi.repositories.length === 0) { return ''; }
        try {
            return await this.gitApi.repositories[0].diffWithHEAD(filePath);
        } catch {
            return '';
        }
    }

    private async onFileSaved(doc: vscode.TextDocument): Promise<void> {
        // Debounce
        if (this.changeWarnTimer) {
            clearTimeout(this.changeWarnTimer);
        }

        this.changeWarnTimer = setTimeout(async () => {
            try {
                const workspacePath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
                if (!workspacePath) { return; }

                // Analyze change risk via engine
                const riskResult = await this.client.analyzeChangeRisk(workspacePath, doc.uri.fsPath);

                if (riskResult && riskResult.risk_level === 'high') {
                    const action = await vscode.window.showWarningMessage(
                        `⚠️ High-risk change detected in ${doc.fileName.split(/[/\\]/).pop()}`,
                        'View Details',
                        'Dismiss'
                    );

                    if (action === 'View Details') {
                        this.output.show();
                        this.output.section('CHANGE RISK ANALYSIS');
                        this.output.warn(`File: ${doc.uri.fsPath}`);
                        this.output.warn(`Risk: ${riskResult.risk_level}`);
                        if (riskResult.warnings) {
                            riskResult.warnings.forEach((w: string) => this.output.warn(`  → ${w}`));
                        }
                    }
                }

                // Update session with git info
                await this.client.updateSession(
                    workspacePath,
                    doc.uri.fsPath,
                    undefined,
                    this.getCurrentBranch()
                );
            } catch {
                // Silent fail for background operations
            }
        }, 2000);
    }

    async correlateErrorWithChanges(errorText: string): Promise<void> {
        const workspacePath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
        if (!workspacePath) { return; }

        this.output.section('ROOT CAUSE ANALYSIS');
        this.output.info('Correlating error with recent changes...');

        try {
            const result = await this.client.correlateRootCause(workspacePath, errorText);

            if (result.likely_cause) {
                this.output.warn(`Likely cause: ${result.likely_cause}`);
                this.output.info(`Changed file: ${result.changed_file}`);
                this.output.info(`Time ago: ${result.time_ago}`);

                if (result.commit) {
                    this.output.info(`Commit: ${result.commit.hash} - ${result.commit.message}`);
                }

                vscode.window.showWarningMessage(
                    `🔍 Likely caused by change in ${result.changed_file} (${result.time_ago})`,
                    'View Details',
                    'Open File'
                ).then(async action => {
                    if (action === 'View Details') {
                        this.output.show();
                    } else if (action === 'Open File' && result.changed_file) {
                        const doc = await vscode.workspace.openTextDocument(result.changed_file);
                        await vscode.window.showTextDocument(doc);
                    }
                });
            } else {
                this.output.info('No clear root cause found from recent changes');
            }
        } catch (err: any) {
            this.output.error(`Correlation failed: ${err.message}`);
        }
    }

    dispose(): void {
        if (this.changeWarnTimer) { clearTimeout(this.changeWarnTimer); }
        for (const d of this.disposables) { d.dispose(); }
    }
}
