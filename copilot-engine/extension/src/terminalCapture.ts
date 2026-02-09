/**
 * Copilot Engine - Terminal Output Capture & Error Detection
 * Monitors terminal output for errors and auto-triggers analysis
 */
import * as vscode from 'vscode';
import { EngineClient, ParsedError } from './engineClient';
import { OutputManager } from './outputChannel';
import { StatusBarManager } from './statusBar';
import { getConfig } from './config';

// Error patterns for different languages
const ERROR_PATTERNS: { lang: string; pattern: RegExp }[] = [
    // Python
    { lang: 'python', pattern: /Traceback \(most recent call last\):/m },
    { lang: 'python', pattern: /^\w+Error: .+$/m },
    { lang: 'python', pattern: /^\w+Exception: .+$/m },
    { lang: 'python', pattern: /^SyntaxError: /m },
    // JavaScript / Node.js
    { lang: 'javascript', pattern: /^\w+Error: .+\n\s+at /m },
    { lang: 'javascript', pattern: /^(TypeError|ReferenceError|SyntaxError|RangeError): /m },
    { lang: 'javascript', pattern: /UnhandledPromiseRejection/m },
    // TypeScript
    { lang: 'typescript', pattern: /error TS\d+: /m },
    { lang: 'typescript', pattern: /\.tsx?:\d+:\d+/m },
    // Java
    { lang: 'java', pattern: /Exception in thread "/m },
    { lang: 'java', pattern: /^\w+\.(\w+Exception|\w+Error): .+$/m },
    // Go
    { lang: 'go', pattern: /^panic: /m },
    { lang: 'go', pattern: /^goroutine \d+ \[/m },
    // Rust
    { lang: 'rust', pattern: /^error\[E\d+\]: /m },
    { lang: 'rust', pattern: /^error: /m },
    // Generic
    { lang: 'generic', pattern: /^FATAL:/m },
    { lang: 'generic', pattern: /^ERROR:/im },
    { lang: 'generic', pattern: /^FAILED/m },
    { lang: 'generic', pattern: /exit code: [1-9]/im },
];

export class TerminalCapture {
    private client: EngineClient;
    private output: OutputManager;
    private statusBar: StatusBarManager;
    private disposables: vscode.Disposable[] = [];
    private terminalBuffers: Map<string, string> = new Map();
    private debounceTimers: Map<string, NodeJS.Timeout> = new Map();
    private errorHistory: ParsedError[] = [];
    private errorCount: number = 0;
    private errorCallbacks: ((error: ParsedError, raw: string) => void)[] = [];

    constructor(client: EngineClient, output: OutputManager, statusBar: StatusBarManager) {
        this.client = client;
        this.output = output;
        this.statusBar = statusBar;
    }

    start(): void {
        const config = getConfig();
        if (!config.terminalCapture) {
            this.output.info('Terminal capture disabled in settings');
            return;
        }

        // Listen for terminal shell execution end (modern API)
        try {
            const endHandler = vscode.window.onDidEndTerminalShellExecution(async (e) => {
                if (e.exitCode !== undefined && e.exitCode !== 0) {
                    // Command failed - try to read output
                    await this.handleFailedExecution(e);
                }
            });
            this.disposables.push(endHandler);
        } catch {
            this.output.warn('Terminal shell integration API not available, using fallback');
        }

        // Listen for terminal data write (capture raw output)
        try {
            const writeHandler = (vscode.window as any).onDidWriteTerminalData((e: any) => {
                this.handleTerminalData(e.terminal, e.data);
            });
            this.disposables.push(writeHandler);
        } catch {
            this.output.warn('onDidWriteTerminalData not available');
        }

        // Listen for terminal close to cleanup
        const closeHandler = vscode.window.onDidCloseTerminal((terminal) => {
            const key = terminal.name;
            this.terminalBuffers.delete(key);
            const timer = this.debounceTimers.get(key);
            if (timer) {
                clearTimeout(timer);
                this.debounceTimers.delete(key);
            }
        });
        this.disposables.push(closeHandler);

        this.output.success('Terminal capture started');
    }

    onError(callback: (error: ParsedError, raw: string) => void): void {
        this.errorCallbacks.push(callback);
    }

    private handleTerminalData(terminal: vscode.Terminal, data: string): void {
        const key = terminal.name;

        // Append to buffer
        let buffer = this.terminalBuffers.get(key) || '';
        buffer += data;

        // Keep only last 5000 chars
        if (buffer.length > 5000) {
            buffer = buffer.substring(buffer.length - 5000);
        }
        this.terminalBuffers.set(key, buffer);

        // Debounce error checking (wait for full output)
        const existingTimer = this.debounceTimers.get(key);
        if (existingTimer) {
            clearTimeout(existingTimer);
        }

        this.debounceTimers.set(key, setTimeout(() => {
            this.checkForErrors(key, buffer);
            this.debounceTimers.delete(key);
        }, 800));
    }

    private async handleFailedExecution(e: vscode.TerminalShellExecutionEndEvent): Promise<void> {
        const execution = e.execution;
        try {
            // Try to read the output stream
            let output = '';
            if (execution && typeof (execution as any).read === 'function') {
                const stream = (execution as any).read();
                for await (const chunk of stream) {
                    output += chunk;
                }
            }

            if (output) {
                this.checkForErrors(`shell-${Date.now()}`, output);
            }
        } catch {
            // Shell integration may not provide readable output
        }
    }

    private async checkForErrors(key: string, buffer: string): Promise<void> {
        // Check against all error patterns
        let matchedPattern: { lang: string; pattern: RegExp } | null = null;

        for (const ep of ERROR_PATTERNS) {
            if (ep.pattern.test(buffer)) {
                matchedPattern = ep;
                break;
            }
        }

        if (!matchedPattern) {
            return;
        }

        // Extract the error portion from the buffer
        const errorText = this.extractErrorBlock(buffer, matchedPattern.lang);
        if (!errorText || errorText.length < 10) {
            return;
        }

        // Avoid duplicate errors (check last 5 seconds)
        const errorSig = errorText.substring(0, 100);
        if (this.errorHistory.some(e =>
            (e.error_type + e.message).substring(0, 100) === errorSig
        )) {
            return;
        }

        this.output.section('ERROR DETECTED');
        this.output.info(`Language: ${matchedPattern.lang}`);

        try {
            const workspacePath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
            const parsed = await this.client.parseError(errorText, workspacePath);

            this.errorHistory.push(parsed);
            if (this.errorHistory.length > 50) {
                this.errorHistory.shift();
            }

            this.errorCount++;
            this.statusBar.setErrorCount(this.errorCount);

            this.output.info(`Type: ${parsed.error_type}`);
            this.output.info(`Message: ${parsed.message}`);
            if (parsed.file_path) {
                this.output.info(`File: ${parsed.file_path}:${parsed.line_number}`);
            }
            if (parsed.suggestions.length > 0) {
                this.output.info('Suggestions:');
                parsed.suggestions.forEach(s => this.output.info(`  → ${s}`));
            }

            // Notify callbacks
            for (const cb of this.errorCallbacks) {
                try { cb(parsed, errorText); } catch { }
            }

            // Show notification
            this.showErrorNotification(parsed, errorText);

        } catch (err: any) {
            this.output.error(`Failed to parse error: ${err.message}`);
        }

        // Clear buffer after processing
        this.terminalBuffers.set(key, '');
    }

    private extractErrorBlock(buffer: string, lang: string): string {
        const lines = buffer.split('\n');

        if (lang === 'python') {
            // Find the Traceback block
            const traceStart = lines.findIndex(l => l.includes('Traceback (most recent call last):'));
            if (traceStart >= 0) {
                // Find the end (the error line)
                let end = traceStart + 1;
                for (let i = traceStart + 1; i < lines.length; i++) {
                    end = i;
                    if (/^\w+Error:|\w+Exception:/.test(lines[i].trim())) {
                        end = i + 1;
                        break;
                    }
                }
                return lines.slice(traceStart, end).join('\n');
            }

            // Single error line
            const errorLine = lines.find(l => /^\w+(Error|Exception): /.test(l.trim()));
            if (errorLine) { return errorLine.trim(); }
        }

        if (lang === 'javascript' || lang === 'typescript') {
            const errorIdx = lines.findIndex(l => /^\w+Error: /.test(l.trim()));
            if (errorIdx >= 0) {
                let end = errorIdx + 1;
                for (let i = errorIdx + 1; i < lines.length && i < errorIdx + 20; i++) {
                    if (lines[i].trim().startsWith('at ')) {
                        end = i + 1;
                    } else {
                        break;
                    }
                }
                return lines.slice(errorIdx, end).join('\n');
            }
        }

        // Generic: return last 30 lines
        return lines.slice(-30).join('\n');
    }

    private async showErrorNotification(error: ParsedError, rawError: string): Promise<void> {
        const config = getConfig();
        if (config.notificationLevel === 'none') { return; }

        const title = `${error.error_type}: ${error.message.substring(0, 80)}`;

        const action = await vscode.window.showErrorMessage(
            `⚡ ${title}`,
            'View Suggestions',
            'Build Context',
            'Go to Error',
            'Dismiss'
        );

        switch (action) {
            case 'View Suggestions':
                this.output.show();
                this.output.section('SUGGESTIONS');
                error.suggestions.forEach(s => this.output.info(`→ ${s}`));
                if (error.related_files.length > 0) {
                    this.output.info('Related files:');
                    error.related_files.forEach(f => this.output.info(`  📄 ${f}`));
                }
                break;

            case 'Build Context':
                const workspacePath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
                if (workspacePath) {
                    try {
                        const context = await this.client.buildDebugContext(rawError, workspacePath);
                        this.output.show();
                        this.output.section('DEBUG CONTEXT (copy for Copilot)');
                        this.output.info(context.prompt);
                        this.output.info(`\nToken estimate: ${context.token_estimate}`);

                        // Copy to clipboard
                        await vscode.env.clipboard.writeText(context.prompt);
                        vscode.window.showInformationMessage('Debug context copied to clipboard!');
                    } catch (err: any) {
                        this.output.error(`Failed to build context: ${err.message}`);
                    }
                }
                break;

            case 'Go to Error':
                if (error.file_path && error.line_number) {
                    const doc = await vscode.workspace.openTextDocument(error.file_path);
                    const editor = await vscode.window.showTextDocument(doc);
                    const pos = new vscode.Position(error.line_number - 1, 0);
                    editor.selection = new vscode.Selection(pos, pos);
                    editor.revealRange(new vscode.Range(pos, pos), vscode.TextEditorRevealType.InCenter);
                }
                break;
        }
    }

    getErrorHistory(): ParsedError[] {
        return [...this.errorHistory];
    }

    getErrorCount(): number {
        return this.errorCount;
    }

    clearHistory(): void {
        this.errorHistory = [];
        this.errorCount = 0;
        this.statusBar.setErrorCount(0);
    }

    stop(): void {
        this.dispose();
    }

    dispose(): void {
        for (const d of this.disposables) { d.dispose(); }
        for (const t of this.debounceTimers.values()) { clearTimeout(t); }
        this.terminalBuffers.clear();
        this.debounceTimers.clear();
    }
}
