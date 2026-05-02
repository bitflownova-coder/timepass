/**
 * Copilot Engine - Status Bar Manager
 */
import * as vscode from 'vscode';

export type EngineStatus = 'disconnected' | 'connecting' | 'connected' | 'error' | 'focus-mode';

export class StatusBarManager {
    private statusBarItem: vscode.StatusBarItem;
    private currentStatus: EngineStatus = 'disconnected';

    constructor() {
        this.statusBarItem = vscode.window.createStatusBarItem(
            vscode.StatusBarAlignment.Left,
            100
        );
        this.statusBarItem.command = 'copilotEngine.showStatus';
        this.setStatus('disconnected');
        this.statusBarItem.show();
    }

    setStatus(status: EngineStatus, detail?: string): void {
        this.currentStatus = status;

        switch (status) {
            case 'disconnected':
                this.statusBarItem.text = '$(circle-slash) Engine Off';
                this.statusBarItem.backgroundColor = undefined;
                this.statusBarItem.tooltip = 'Copilot Engine: Disconnected. Click to start.';
                break;
            case 'connecting':
                this.statusBarItem.text = '$(sync~spin) Engine...';
                this.statusBarItem.backgroundColor = undefined;
                this.statusBarItem.tooltip = 'Copilot Engine: Connecting...';
                break;
            case 'connected':
                this.statusBarItem.text = '$(zap) Engine';
                this.statusBarItem.backgroundColor = undefined;
                this.statusBarItem.tooltip = `Copilot Engine: Connected${detail ? ' - ' + detail : ''}`;
                break;
            case 'error':
                this.statusBarItem.text = '$(warning) Engine Error';
                this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.warningBackground');
                this.statusBarItem.tooltip = `Copilot Engine: Error${detail ? ' - ' + detail : ''}`;
                break;
            case 'focus-mode':
                this.statusBarItem.text = '$(flame) Focus Mode';
                this.statusBarItem.backgroundColor = new vscode.ThemeColor('statusBarItem.errorBackground');
                this.statusBarItem.tooltip = 'Copilot Engine: Focus Mode Active';
                break;
        }
    }

    getStatus(): EngineStatus {
        return this.currentStatus;
    }

    setErrorCount(count: number): void {
        if (count > 0 && this.currentStatus === 'connected') {
            this.statusBarItem.text = `$(zap) Engine (${count} errors)`;
        }
    }

    dispose(): void {
        this.statusBarItem.dispose();
    }
}
