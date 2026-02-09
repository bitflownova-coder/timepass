/**
 * Copilot Engine - Configuration Manager
 */
import * as vscode from 'vscode';

export interface EngineConfig {
    host: string;
    port: number;
    autoStart: boolean;
    terminalCapture: boolean;
    codeLensEnabled: boolean;
    securityWarnings: boolean;
    notificationLevel: 'all' | 'errors' | 'critical' | 'none';
    debugMode: boolean;
    autoInjectContext: boolean;
    focusModeThreshold: number;
    enginePath: string;
}

export function getConfig(): EngineConfig {
    const config = vscode.workspace.getConfiguration('copilotEngine');
    return {
        host: config.get<string>('host', '127.0.0.1'),
        port: config.get<number>('port', 7779),
        autoStart: config.get<boolean>('autoStart', true),
        terminalCapture: config.get<boolean>('terminalCapture', true),
        codeLensEnabled: config.get<boolean>('codeLensEnabled', true),
        securityWarnings: config.get<boolean>('securityWarnings', true),
        notificationLevel: config.get<string>('notificationLevel', 'errors') as EngineConfig['notificationLevel'],
        debugMode: config.get<boolean>('debugMode', false),
        autoInjectContext: config.get<boolean>('autoInjectContext', false),
        focusModeThreshold: config.get<number>('focusModeThreshold', 5),
        enginePath: config.get<string>('enginePath', ''),
    };
}

export function getBaseUrl(): string {
    const config = getConfig();
    return `http://${config.host}:${config.port}`;
}

export function getWsUrl(): string {
    const config = getConfig();
    return `ws://${config.host}:${config.port}`;
}
