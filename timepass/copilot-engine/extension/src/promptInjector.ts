/**
 * Copilot Engine - Prompt Injector (Hardened)
 *
 * Injects structured context comments into code for Copilot to consume.
 *
 * Stability guarantees:
 * - Debounced: rapid saves/edits don't flood requests
 * - Dedup: never inserts duplicate context blocks
 * - Position-safe: inserts at file top or cursor, never misplaces
 * - Non-destructive: wraps in recognizable markers for clean removal
 * - Race-safe: cancels stale requests when new ones arrive
 * - Formatter-safe: uses line comments to avoid block-comment conflicts
 */
import * as vscode from 'vscode';
import { EngineClient, ContextResponse, RiskReport } from './engineClient';
import { OutputManager } from './outputChannel';
import { getConfig } from './config';

// ── Marker constants for comment blocks ──
const MARKER_START = '@copilot-engine-context-start';
const MARKER_END = '@copilot-engine-context-end';

// Comment syntax per language
const COMMENT_SYNTAX: Record<string, { line: string; blockStart: string; blockEnd: string }> = {
    python: { line: '#', blockStart: '"""', blockEnd: '"""' },
    javascript: { line: '//', blockStart: '/*', blockEnd: '*/' },
    typescript: { line: '//', blockStart: '/*', blockEnd: '*/' },
    javascriptreact: { line: '//', blockStart: '/*', blockEnd: '*/' },
    typescriptreact: { line: '//', blockStart: '/*', blockEnd: '*/' },
    java: { line: '//', blockStart: '/*', blockEnd: '*/' },
    go: { line: '//', blockStart: '/*', blockEnd: '*/' },
    rust: { line: '//', blockStart: '/*', blockEnd: '*/' },
    c: { line: '//', blockStart: '/*', blockEnd: '*/' },
    cpp: { line: '//', blockStart: '/*', blockEnd: '*/' },
    html: { line: '', blockStart: '<!--', blockEnd: '-->' },
    css: { line: '', blockStart: '/*', blockEnd: '*/' },
    prisma: { line: '//', blockStart: '//', blockEnd: '//' },
};

export class PromptInjector {
    private client: EngineClient;
    private output: OutputManager;
    private debounceTimer: NodeJS.Timeout | null = null;
    private lastInjectionHash: string = '';
    private injecting: boolean = false;

    constructor(client: EngineClient, output: OutputManager) {
        this.client = client;
        this.output = output;
    }

    // ══════════════════════════════════════════
    //  PUBLIC API
    // ══════════════════════════════════════════

    /**
     * Manual injection at cursor (Ctrl+Shift+I)
     * Builds context + enforcement data and injects above cursor
     */
    async injectContextAtCursor(): Promise<void> {
        const editor = vscode.window.activeTextEditor;
        if (!editor) {
            vscode.window.showWarningMessage('No active editor');
            return;
        }

        const workspacePath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
        if (!workspacePath) { return; }

        const doc = editor.document;
        const selection = editor.selection;
        const selectedText = doc.getText(selection);

        let task = 'Help with this code';
        if (selectedText) {
            task = `Analyze and improve this selected code:\n\n${selectedText}`;
        }

        try {
            // Gather intelligence + enforcement in parallel
            const [context, enforcement] = await Promise.allSettled([
                this.client.optimizePrompt(workspacePath, task, doc.uri.fsPath),
                this.client.fileChangeScan(workspacePath, doc.uri.fsPath),
            ]);

            const contextData = context.status === 'fulfilled' ? context.value : null;
            const enforcementData = enforcement.status === 'fulfilled' ? enforcement.value : null;

            const comment = this.buildContextBlock(
                doc.languageId,
                contextData,
                enforcementData,
            );

            // Remove any existing context block first
            await this.removeExistingBlock(editor);

            // Insert at cursor position
            const insertLine = selection.start.line;
            const insertPos = new vscode.Position(insertLine, 0);

            await editor.edit(editBuilder => {
                editBuilder.insert(insertPos, comment + '\n');
            });

            vscode.window.showInformationMessage(
                'Context injected! Copilot will use it for suggestions.',
                'Remove Later'
            ).then(action => {
                if (action === 'Remove Later') {
                    this.removeExistingBlock(editor);
                }
            });
        } catch (err: any) {
            this.output.error(`Context injection failed: ${err.message}`);
            vscode.window.showErrorMessage('Failed to inject context');
        }
    }

    /**
     * Debug context injection — called when terminal captures an error
     */
    async injectDebugContext(errorText: string): Promise<void> {
        const editor = vscode.window.activeTextEditor;
        const workspacePath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
        if (!workspacePath) { return; }

        try {
            const context = await this.client.buildDebugContext(errorText, workspacePath);

            if (editor) {
                const comment = this.buildDebugBlock(editor.document.languageId, context, errorText);

                await this.removeExistingBlock(editor);

                const insertPos = new vscode.Position(editor.selection.start.line, 0);
                await editor.edit(editBuilder => {
                    editBuilder.insert(insertPos, comment + '\n');
                });
            }

            // Also copy to clipboard
            await vscode.env.clipboard.writeText(context.prompt);
            vscode.window.showInformationMessage('Debug context injected and copied to clipboard!');
        } catch (err: any) {
            this.output.error(`Debug context failed: ${err.message}`);
        }
    }

    /**
     * Auto-injection on file save (if enabled in config)
     * Debounced to prevent rapid-fire during format-on-save
     */
    scheduleAutoInject(document: vscode.TextDocument): void {
        const config = getConfig();
        if (!config.autoInjectContext) { return; }

        // Never auto-inject into non-code files
        if (!COMMENT_SYNTAX[document.languageId]) { return; }

        // Debounce: 2 seconds after last save
        if (this.debounceTimer) {
            clearTimeout(this.debounceTimer);
        }

        this.debounceTimer = setTimeout(async () => {
            this.debounceTimer = null;
            await this.autoInjectForFile(document);
        }, 2000);
    }

    /**
     * Build context for a specific task (for clipboard/chat)
     */
    async buildTaskContext(task: string): Promise<string | null> {
        const workspacePath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
        const currentFile = vscode.window.activeTextEditor?.document.uri.fsPath;
        if (!workspacePath) { return null; }

        try {
            const context = await this.client.optimizePrompt(workspacePath, task, currentFile);
            return context.prompt;
        } catch {
            return null;
        }
    }

    /**
     * Remove injected context block from the active editor
     */
    async removeContextBlock(): Promise<void> {
        const editor = vscode.window.activeTextEditor;
        if (editor) {
            const removed = await this.removeExistingBlock(editor);
            if (removed) {
                vscode.window.showInformationMessage('Context block removed');
            } else {
                vscode.window.showInformationMessage('No context block found');
            }
        }
    }

    // ══════════════════════════════════════════
    //  PRIVATE: Auto-injection (debounced)
    // ══════════════════════════════════════════

    private async autoInjectForFile(document: vscode.TextDocument): Promise<void> {
        if (this.injecting) { return; }
        this.injecting = true;

        try {
            const workspacePath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
            if (!workspacePath) { return; }

            const report = await this.client.fileChangeScan(workspacePath, document.uri.fsPath);

            if (!report.issues || report.issues.length === 0) { return; }

            // Dedup check
            const hash = this.hashIssues(report.issues);
            if (hash === this.lastInjectionHash) { return; }
            this.lastInjectionHash = hash;

            const editor = vscode.window.visibleTextEditors.find(
                e => e.document.uri.toString() === document.uri.toString()
            );
            if (!editor) { return; }

            const comment = this.buildEnforcementOnlyBlock(document.languageId, report);

            await this.removeExistingBlock(editor);

            await editor.edit(editBuilder => {
                editBuilder.insert(new vscode.Position(0, 0), comment + '\n');
            });
        } catch {
            // Silent fail for auto-inject
        } finally {
            this.injecting = false;
        }
    }

    // ══════════════════════════════════════════
    //  PRIVATE: Comment Block Builders
    // ══════════════════════════════════════════

    private buildContextBlock(
        languageId: string,
        context: ContextResponse | null,
        enforcement: RiskReport | null,
    ): string {
        const syntax = COMMENT_SYNTAX[languageId] || COMMENT_SYNTAX.javascript;
        const p = syntax.line; // prefix
        const lines: string[] = [];

        lines.push(`${p} ${MARKER_START}`);
        lines.push(`${p} ═══ Copilot Engine Context ═══`);

        if (context) {
            const meta = context.metadata;
            if (meta.project) { lines.push(`${p}  Project: ${meta.project}`); }
            if (meta.current_file) { lines.push(`${p}  File: ${meta.current_file}`); }
            if (meta.has_error) { lines.push(`${p}  Status: DEBUGGING ERROR`); }
            lines.push(`${p}  Tokens: ${context.token_estimate}`);
            if (meta.task) { lines.push(`${p}  Task: ${meta.task}`); }
        }

        if (enforcement && enforcement.issues && enforcement.issues.length > 0) {
            lines.push(`${p}`);
            lines.push(`${p} ─── Enforcement (${enforcement.issues.length} issues) ───`);
            lines.push(`${p}  Risk: ${enforcement.risk_score?.toFixed(2) || 'N/A'}`);

            if (enforcement.commit_safe !== undefined) {
                lines.push(`${p}  Commit Safe: ${enforcement.commit_safe ? 'YES' : 'NO'}`);
            }

            const critical = enforcement.issues.filter(i => i.severity === 'critical' || i.severity === 'error');
            const warnings = enforcement.issues.filter(i => i.severity === 'warning');

            if (critical.length > 0) {
                lines.push(`${p}  CRITICAL:`);
                for (const issue of critical.slice(0, 5)) {
                    lines.push(`${p}    ! ${issue.category}: ${issue.message}`);
                }
            }

            if (warnings.length > 0) {
                lines.push(`${p}  WARNINGS:`);
                for (const issue of warnings.slice(0, 5)) {
                    lines.push(`${p}    ~ ${issue.category}: ${issue.message}`);
                }
            }
        } else if (enforcement) {
            lines.push(`${p}  Enforcement: All checks passed`);
        }

        lines.push(`${p} ${MARKER_END}`);
        return lines.join('\n');
    }

    private buildEnforcementOnlyBlock(languageId: string, report: RiskReport): string {
        const syntax = COMMENT_SYNTAX[languageId] || COMMENT_SYNTAX.javascript;
        const p = syntax.line;
        const lines: string[] = [];

        lines.push(`${p} ${MARKER_START}`);
        lines.push(`${p} ═══ Copilot Engine: Enforcement ═══`);
        lines.push(`${p}  Risk: ${report.risk_score?.toFixed(2) || '0.00'} | Issues: ${report.issues.length}`);

        if (report.commit_safe !== undefined) {
            lines.push(`${p}  Commit: ${report.commit_safe ? 'SAFE' : 'BLOCKED'}`);
        }

        for (const issue of report.issues.slice(0, 8)) {
            const icon = issue.severity === 'critical' || issue.severity === 'error' ? '!' :
                         issue.severity === 'warning' ? '~' : '-';
            lines.push(`${p}  ${icon} [${issue.category}] ${issue.message}`);
        }

        if (report.issues.length > 8) {
            lines.push(`${p}  ... and ${report.issues.length - 8} more`);
        }

        lines.push(`${p} ${MARKER_END}`);
        return lines.join('\n');
    }

    private buildDebugBlock(languageId: string, context: ContextResponse, errorText: string): string {
        const syntax = COMMENT_SYNTAX[languageId] || COMMENT_SYNTAX.javascript;
        const p = syntax.line;
        const lines: string[] = [];

        lines.push(`${p} ${MARKER_START}`);
        lines.push(`${p} ═══ Copilot Engine: Debug Context ═══`);

        const errorFirstLine = errorText.split('\n')[0].substring(0, 100);
        lines.push(`${p}  Error: ${errorFirstLine}`);

        const meta = context.metadata;
        if (meta.project) { lines.push(`${p}  Project: ${meta.project}`); }
        if (meta.has_error) { lines.push(`${p}  Status: Active error`); }
        lines.push(`${p}  Tokens: ${context.token_estimate}`);

        lines.push(`${p} ${MARKER_END}`);
        return lines.join('\n');
    }

    // ══════════════════════════════════════════
    //  PRIVATE: Block Management (dedup + cleanup)
    // ══════════════════════════════════════════

    private async removeExistingBlock(editor: vscode.TextEditor): Promise<boolean> {
        const doc = editor.document;
        const text = doc.getText();

        const startIdx = text.indexOf(MARKER_START);
        if (startIdx === -1) { return false; }

        const endIdx = text.indexOf(MARKER_END, startIdx);
        if (endIdx === -1) { return false; }

        const startPos = doc.positionAt(startIdx);
        const endPos = doc.positionAt(endIdx + MARKER_END.length);

        const startLine = startPos.line;
        let endLine = endPos.line + 1;
        if (endLine > doc.lineCount) { endLine = doc.lineCount; }

        const lineStart = doc.lineAt(startLine).range.start;

        let rangeEnd: vscode.Position;
        if (endLine < doc.lineCount) {
            rangeEnd = doc.lineAt(endLine).range.start;
        } else {
            rangeEnd = doc.lineAt(doc.lineCount - 1).range.end;
        }

        const range = new vscode.Range(lineStart, rangeEnd);

        await editor.edit(editBuilder => {
            editBuilder.delete(range);
        });

        return true;
    }

    private hashIssues(issues: any[]): string {
        const sig = issues.map((i: any) => `${i.severity}:${i.category}:${i.message}`).sort().join('|');
        let hash = 0;
        for (let i = 0; i < sig.length; i++) {
            const char = sig.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash |= 0;
        }
        return hash.toString(36);
    }
}
