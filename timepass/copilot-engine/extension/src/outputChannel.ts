/**
 * Copilot Engine - Output Channel Manager
 */
import * as vscode from 'vscode';

export class OutputManager {
    private outputChannel: vscode.OutputChannel;

    constructor() {
        this.outputChannel = vscode.window.createOutputChannel('Copilot Engine');
    }

    info(message: string): void {
        const ts = new Date().toLocaleTimeString();
        this.outputChannel.appendLine(`[${ts}] ℹ️  ${message}`);
    }

    warn(message: string): void {
        const ts = new Date().toLocaleTimeString();
        this.outputChannel.appendLine(`[${ts}] ⚠️  ${message}`);
    }

    error(message: string): void {
        const ts = new Date().toLocaleTimeString();
        this.outputChannel.appendLine(`[${ts}] ❌ ${message}`);
    }

    success(message: string): void {
        const ts = new Date().toLocaleTimeString();
        this.outputChannel.appendLine(`[${ts}] ✅ ${message}`);
    }

    separator(): void {
        this.outputChannel.appendLine('─'.repeat(60));
    }

    section(title: string): void {
        this.separator();
        this.outputChannel.appendLine(`  ${title}`);
        this.separator();
    }

    json(label: string, data: any): void {
        this.outputChannel.appendLine(`${label}:`);
        this.outputChannel.appendLine(JSON.stringify(data, null, 2));
    }

    show(): void {
        this.outputChannel.show(true);
    }

    clear(): void {
        this.outputChannel.clear();
    }

    dispose(): void {
        this.outputChannel.dispose();
    }
}
