/**
 * Copilot Engine - EventStream
 * Unified event capture for the autonomous runtime.
 *
 * Captures:
 *  - File saves  (onDidSaveTextDocument)
 *  - File creates/deletes (FileSystemWatcher)
 *  - Active editor changes
 *  - Git branch changes (polling)
 *
 * Produces ChangeEvent objects and forwards them to the AutonomousEngine.
 */
import * as vscode from 'vscode';
import { OutputManager } from './outputChannel';

export interface ChangeEvent {
    file_path: string;
    change_type: 'saved' | 'created' | 'deleted' | 'opened' | 'renamed';
    workspace_path: string;
    timestamp: number;
    git_branch: string;
    metadata: Record<string, any>;
}

export type EventCallback = (event: ChangeEvent) => void;

const IGNORED_DIRS = [
    'node_modules', '.git', '__pycache__', '.next', 'dist',
    'build', '.venv', 'venv', '.turbo', '.cache',
];

const CODE_EXTENSIONS = new Set([
    '.py', '.ts', '.tsx', '.js', '.jsx', '.prisma',
    '.json', '.toml', '.yaml', '.yml', '.sql',
    '.graphql', '.gql', '.env',
]);

export class EventStream {
    private disposables: vscode.Disposable[] = [];
    private callbacks: EventCallback[] = [];
    private output: OutputManager;
    private workspacePath: string = '';
    private gitBranch: string = '';
    private branchPollTimer: NodeJS.Timeout | null = null;
    private running: boolean = false;
    private eventCount: number = 0;

    constructor(output: OutputManager) {
        this.output = output;
    }

    /**
     * Start capturing events for the active workspace.
     */
    start(workspacePath: string): void {
        if (this.running) { return; }
        this.running = true;
        this.workspacePath = workspacePath;

        // ── File save ──
        this.disposables.push(
            vscode.workspace.onDidSaveTextDocument((doc) => {
                this.emit(doc.uri.fsPath, 'saved');
            })
        );

        // ── FileSystemWatcher for creates & deletes ──
        const watcher = vscode.workspace.createFileSystemWatcher('**/*');
        this.disposables.push(
            watcher.onDidCreate((uri) => this.emit(uri.fsPath, 'created')),
            watcher.onDidDelete((uri) => this.emit(uri.fsPath, 'deleted')),
            watcher,
        );

        // ── Active editor change ──
        this.disposables.push(
            vscode.window.onDidChangeActiveTextEditor((editor) => {
                if (editor?.document.uri.scheme === 'file') {
                    this.emit(editor.document.uri.fsPath, 'opened');
                }
            })
        );

        // ── Git branch polling (every 15s) ──
        this.pollGitBranch();
        this.branchPollTimer = setInterval(() => this.pollGitBranch(), 15_000);

        this.output.info('[EventStream] Started - capturing file events');
    }

    /**
     * Stop capturing events.
     */
    stop(): void {
        this.running = false;
        for (const d of this.disposables) {
            try { d.dispose(); } catch { }
        }
        this.disposables = [];
        if (this.branchPollTimer) {
            clearInterval(this.branchPollTimer);
            this.branchPollTimer = null;
        }
    }

    /**
     * Register a callback for change events.
     */
    onEvent(callback: EventCallback): void {
        this.callbacks.push(callback);
    }

    /**
     * Get stats.
     */
    getStats(): { running: boolean; eventCount: number; gitBranch: string } {
        return {
            running: this.running,
            eventCount: this.eventCount,
            gitBranch: this.gitBranch,
        };
    }

    // ═══════════════════════════════════════════
    // Internal
    // ═══════════════════════════════════════════

    private emit(filePath: string, changeType: ChangeEvent['change_type']): void {
        // Filter: only code files
        const ext = filePath.substring(filePath.lastIndexOf('.')).toLowerCase();
        if (!CODE_EXTENSIONS.has(ext)) { return; }

        // Filter: ignore build artifacts and dependencies
        const relative = filePath.replace(/\\/g, '/');
        for (const dir of IGNORED_DIRS) {
            if (relative.includes(`/${dir}/`) || relative.includes(`\\${dir}\\`)) {
                return;
            }
        }

        const event: ChangeEvent = {
            file_path: filePath,
            change_type: changeType,
            workspace_path: this.workspacePath,
            timestamp: Date.now(),
            git_branch: this.gitBranch,
            metadata: {},
        };

        this.eventCount++;

        for (const cb of this.callbacks) {
            try {
                cb(event);
            } catch (e) {
                this.output.warn(`[EventStream] Callback error: ${e}`);
            }
        }
    }

    private async pollGitBranch(): Promise<void> {
        try {
            const gitExt = vscode.extensions.getExtension('vscode.git')?.exports;
            const api = gitExt?.getAPI(1);
            if (api?.repositories?.length) {
                const repo = api.repositories[0];
                const branch = repo.state?.HEAD?.name || '';
                if (branch !== this.gitBranch) {
                    this.gitBranch = branch;
                }
            }
        } catch {
            // Git extension not available — silent
        }
    }

    dispose(): void {
        this.stop();
    }
}
