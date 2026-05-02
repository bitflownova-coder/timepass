/**
 * Copilot Engine - Behavior Tracker (Extension Side)
 * Tracks developer patterns to detect debugging loops and suggest focus mode
 */
import * as vscode from 'vscode';
import { EngineClient, BehaviorStatus } from './engineClient';
import { OutputManager } from './outputChannel';
import { StatusBarManager } from './statusBar';
import { getConfig } from './config';

export class BehaviorTracker {
    private client: EngineClient;
    private output: OutputManager;
    private statusBar: StatusBarManager;
    private disposables: vscode.Disposable[] = [];

    // Tracking metrics
    private fileSwitchCount: number = 0;
    private errorRepeatMap: Map<string, number> = new Map();
    private recentErrors: string[] = [];
    private focusModeActive: boolean = false;
    private sessionStartTime: number = Date.now();
    private lastFileSwitch: number = Date.now();
    private rapidSwitchCount: number = 0;

    constructor(client: EngineClient, output: OutputManager, statusBar: StatusBarManager) {
        this.client = client;
        this.output = output;
        this.statusBar = statusBar;
    }

    start(): void {
        // Track file switches
        const editorChange = vscode.window.onDidChangeActiveTextEditor((editor) => {
            if (editor) {
                this.onFileSwitch(editor.document.uri.fsPath);
            }
        });
        this.disposables.push(editorChange);

        // Track file saves
        const saveHandler = vscode.workspace.onDidSaveTextDocument((doc) => {
            this.trackEvent('file_save', { file: doc.uri.fsPath });
        });
        this.disposables.push(saveHandler);

        this.output.success('Behavior tracking started');
    }

    /**
     * Track an error occurrence
     */
    trackError(errorType: string, message: string): void {
        const sig = `${errorType}:${message.substring(0, 50)}`;

        const count = (this.errorRepeatMap.get(sig) || 0) + 1;
        this.errorRepeatMap.set(sig, count);

        this.recentErrors.push(sig);
        if (this.recentErrors.length > 20) {
            this.recentErrors.shift();
        }

        const config = getConfig();
        if (count >= config.focusModeThreshold && !this.focusModeActive) {
            this.suggestFocusMode(errorType, message, count);
        }

        this.trackEvent('error', { error_type: errorType, count });
    }

    /**
     * Track file switching patterns
     */
    private onFileSwitch(filePath: string): void {
        this.fileSwitchCount++;
        const now = Date.now();
        const timeSinceLastSwitch = now - this.lastFileSwitch;
        this.lastFileSwitch = now;

        // Detect rapid switching (< 3 seconds between switches)
        if (timeSinceLastSwitch < 3000) {
            this.rapidSwitchCount++;
        } else {
            this.rapidSwitchCount = Math.max(0, this.rapidSwitchCount - 1);
        }

        // Warn if switching too rapidly (sign of confusion)
        if (this.rapidSwitchCount >= 10 && !this.focusModeActive) {
            vscode.window.showInformationMessage(
                '🤔 Rapid file switching detected. Need help finding something?',
                'Search Codebase',
                'Build Context',
                'Dismiss'
            ).then(action => {
                if (action === 'Build Context') {
                    vscode.commands.executeCommand('copilotEngine.buildContext');
                }
            });
            this.rapidSwitchCount = 0;
        }

        this.trackEvent('file_switch', { file: filePath });
    }

    /**
     * Suggest activating focus mode
     */
    private async suggestFocusMode(errorType: string, message: string, count: number): Promise<void> {
        const action = await vscode.window.showWarningMessage(
            `🔥 You've hit "${errorType}" ${count} times. Activate Focus Mode for structured debugging?`,
            'Activate Focus Mode',
            'Find Similar Fixes',
            'Not Now'
        );

        switch (action) {
            case 'Activate Focus Mode':
                this.activateFocusMode();
                break;
            case 'Find Similar Fixes':
                const errorText = `${errorType}: ${message}`;
                try {
                    const similar = await this.client.findSimilarErrors(errorText);
                    this.output.show();
                    this.output.section('SIMILAR PAST ERRORS');
                    if (similar.similar_fixes && similar.similar_fixes.length > 0) {
                        for (const fix of similar.similar_fixes) {
                            this.output.info(`Fix: ${fix.description}`);
                            this.output.info(`  How: ${fix.fix}`);
                            this.output.info(`  Used ${fix.success_count} times`);
                            this.output.separator();
                        }
                    } else {
                        this.output.info('No similar fixes found yet. This will improve over time.');
                    }
                } catch {
                    this.output.warn('Could not fetch similar errors');
                }
                break;
        }
    }

    /**
     * Activate focus mode - full debugging support
     */
    activateFocusMode(): void {
        this.focusModeActive = true;
        this.statusBar.setStatus('focus-mode');
        this.output.show();
        this.output.section('🔥 FOCUS MODE ACTIVATED');
        this.output.info('Full context capture enabled');
        this.output.info('All errors will be logged with maximum detail');
        this.output.info('Use Ctrl+Shift+C to build context at any time');
        this.output.separator();

        vscode.window.showInformationMessage(
            '🔥 Focus Mode Active - Enhanced debugging enabled',
            'Deactivate'
        ).then(action => {
            if (action === 'Deactivate') {
                this.deactivateFocusMode();
            }
        });
    }

    /**
     * Deactivate focus mode
     */
    deactivateFocusMode(): void {
        this.focusModeActive = false;
        this.statusBar.setStatus('connected');
        this.errorRepeatMap.clear();
        this.output.success('Focus Mode deactivated');
    }

    isFocusModeActive(): boolean {
        return this.focusModeActive;
    }

    /**
     * Send tracking event to engine
     */
    private async trackEvent(event: string, data: any): Promise<void> {
        try {
            const workspacePath = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
            if (workspacePath) {
                await this.client.trackBehavior(workspacePath, event, data);
            }
        } catch {
            // Silent fail for background tracking
        }
    }

    /**
     * Get session stats
     */
    getStats(): Record<string, any> {
        const sessionMinutes = Math.round((Date.now() - this.sessionStartTime) / 60000);
        return {
            session_duration_minutes: sessionMinutes,
            file_switches: this.fileSwitchCount,
            unique_errors: this.errorRepeatMap.size,
            total_errors: this.recentErrors.length,
            focus_mode: this.focusModeActive,
            rapid_switches: this.rapidSwitchCount,
        };
    }

    dispose(): void {
        for (const d of this.disposables) { d.dispose(); }
    }
}
