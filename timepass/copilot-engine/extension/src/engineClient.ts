/**
 * Copilot Engine - HTTP + WebSocket Client
 * Handles all communication with the backend engine
 */
import * as vscode from 'vscode';
import * as http from 'http';
import { getBaseUrl, getWsUrl, getConfig } from './config';
import { OutputManager } from './outputChannel';

export interface ParsedError {
    error_type: string;
    message: string;
    file_path: string | null;
    line_number: number | null;
    suggestions: string[];
    related_files: string[];
    language: string | null;
}

export interface WorkspaceInfo {
    id: number;
    path: string;
    name: string | null;
    language: string | null;
    framework: string | null;
    last_active: string;
}

export interface ContextResponse {
    prompt: string;
    token_estimate: number;
    metadata: Record<string, any>;
}

export interface HealthResponse {
    status: string;
    version: string;
    uptime: number;
    watched_workspaces: string[];
}

export interface GitDiffResponse {
    workspace: string;
    changes: GitChange[];
    risk_score: number;
    warnings: string[];
}

export interface GitChange {
    file: string;
    change_type: string;
    risk_level: string;
    details: string;
}

export interface SecurityFinding {
    file: string;
    line: number;
    severity: string;
    issue: string;
    suggestion: string;
    pattern: string;
}

export interface BehaviorStatus {
    error_count: number;
    repeated_errors: number;
    file_switches: number;
    focus_mode_suggested: boolean;
    message: string;
}

// ========== Enforcement Layer Types ==========

export interface ValidationIssue {
    severity: string;
    category: string;
    message: string;
    file?: string;
    line?: number;
    suggestion?: string;
    model?: string;
    rule?: string;
    endpoint?: string;
}

export interface RiskReport {
    workspace_path: string;
    timestamp: string;
    issues: ValidationIssue[];
    risk_score: number;
    risk_level: string;
    commit_safe?: boolean;
    commit_warnings?: string[];
    summary?: Record<string, any>;
}

export interface PrismaAnalysisResult {
    schema_path: string;
    models: string[];
    issues: ValidationIssue[];
    enums?: string[];
}

export interface ContractMapResult {
    workspace_path: string;
    total_endpoints: number;
    endpoints: Record<string, any>[];
}

export interface ImpactResult {
    changed_file: string;
    risk_score: number;
    risk_level: string;
    impact_radius: string[];
    breaking_changes: string[];
    category: string;
}

export interface StackInfo {
    languages: string[];
    frameworks: string[];
    orm: string | null;
    auth: string | null;
    test_runner: string | null;
    database: string | null;
    package_manager: string | null;
    api_style?: string;
    detected_files?: string[];
}

export class EngineClient {
    private output: OutputManager;
    private ws: any = null; // WebSocket
    private connected: boolean = false;
    private reconnectTimer: NodeJS.Timeout | null = null;
    private wsCallbacks: Map<string, ((data: any) => void)[]> = new Map();
    private inflightRequests: Map<string, AbortController> = new Map();

    constructor(output: OutputManager) {
        this.output = output;
    }

    // ========== HTTP Methods ==========

    private async request<T>(method: string, path: string, body?: any, timeoutMs: number = 10000): Promise<T> {
        const url = `${getBaseUrl()}${path}`;

        // Dedup: abort any inflight request to the same path
        const key = `${method}:${path}`;
        const existing = this.inflightRequests.get(key);
        if (existing) {
            try { existing.abort(); } catch { }
        }

        const controller = new AbortController();
        this.inflightRequests.set(key, controller);

        try {
            return await this._doRequest<T>(method, url, body, timeoutMs);
        } finally {
            this.inflightRequests.delete(key);
        }
    }

    private _doRequest<T>(method: string, url: string, body: any, timeoutMs: number): Promise<T> {

        return new Promise<T>((resolve, reject) => {
            const urlObj = new URL(url);
            const options: http.RequestOptions = {
                hostname: urlObj.hostname,
                port: urlObj.port,
                path: urlObj.pathname + urlObj.search,
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                },
                timeout: timeoutMs,
            };

            const req = http.request(options, (res) => {
                let data = '';
                res.on('data', (chunk: Buffer) => { data += chunk.toString(); });
                res.on('end', () => {
                    try {
                        const parsed = JSON.parse(data);
                        if (res.statusCode && res.statusCode >= 400) {
                            reject(new Error(parsed.detail || `HTTP ${res.statusCode}`));
                        } else {
                            resolve(parsed as T);
                        }
                    } catch {
                        reject(new Error(`Invalid JSON response: ${data.substring(0, 200)}`));
                    }
                });
            });

            req.on('error', (err: Error) => reject(err));
            req.on('timeout', () => {
                req.destroy();
                reject(new Error('Request timeout'));
            });

            if (body) {
                req.write(JSON.stringify(body));
            }
            req.end();
        });
    }

    async get<T>(path: string): Promise<T> {
        return this.request<T>('GET', path);
    }

    async post<T>(path: string, body: any): Promise<T> {
        return this.request<T>('POST', path, body);
    }

    private async del<T>(path: string): Promise<T> {
        return this.request<T>('DELETE', path);
    }

    // ========== Health ==========

    async checkHealth(): Promise<HealthResponse | null> {
        try {
            return await this.get<HealthResponse>('/health');
        } catch {
            return null;
        }
    }

    async isRunning(): Promise<boolean> {
        const health = await this.checkHealth();
        return health !== null && health.status === 'healthy';
    }

    // ========== Workspace ==========

    async registerWorkspace(path: string, name?: string): Promise<WorkspaceInfo> {
        return this.post<WorkspaceInfo>('/workspace/register', { path, name });
    }

    async listWorkspaces(): Promise<WorkspaceInfo[]> {
        return this.get<WorkspaceInfo[]>('/workspaces');
    }

    async unregisterWorkspace(id: number): Promise<any> {
        return this.del(`/workspace/${id}`);
    }

    // ========== Error Parsing ==========

    async parseError(errorText: string, workspacePath?: string): Promise<ParsedError> {
        return this.post<ParsedError>('/error/parse', {
            error_text: errorText,
            workspace_path: workspacePath,
        });
    }

    async findSimilarErrors(errorText: string): Promise<any> {
        return this.post('/error/find-similar', {
            error_text: errorText,
        });
    }

    // ========== Context Building ==========

    async buildContext(workspacePath: string, task: string, currentFile?: string, errorText?: string): Promise<ContextResponse> {
        return this.post<ContextResponse>('/context/build', {
            workspace_path: workspacePath,
            task,
            current_file: currentFile,
            error_text: errorText,
        });
    }

    async buildDebugContext(errorText: string, workspacePath: string): Promise<ContextResponse> {
        return this.post<ContextResponse>('/context/debug', {
            error_text: errorText,
            workspace_path: workspacePath,
        });
    }

    // ========== Session ==========

    async updateSession(workspacePath: string, currentFile?: string, terminalOutput?: string, gitBranch?: string): Promise<any> {
        return this.post('/session/update', {
            workspace_path: workspacePath,
            current_file: currentFile,
            terminal_output: terminalOutput,
            git_branch: gitBranch,
        });
    }

    // ========== Git Integration ==========

    async analyzeGitDiff(workspacePath: string): Promise<GitDiffResponse> {
        return this.post<GitDiffResponse>('/git/diff', { workspace_path: workspacePath });
    }

    async getRecentCommits(workspacePath: string, limit?: number): Promise<any> {
        const limitParam = limit ? `?limit=${limit}` : '';
        return this.get(`/git/recent-commits/${encodeURIComponent(workspacePath)}${limitParam}`);
    }

    async analyzeChangeRisk(workspacePath: string, filePath: string): Promise<any> {
        return this.post('/git/analyze-change', {
            workspace_path: workspacePath,
            file_path: filePath,
        });
    }

    async correlateRootCause(workspacePath: string, errorText: string): Promise<any> {
        return this.post('/git/correlate', {
            workspace_path: workspacePath,
            error_text: errorText,
        });
    }

    // ========== Security ==========

    async scanSecurity(filePath: string): Promise<SecurityFinding[]> {
        return this.post<SecurityFinding[]>('/security/scan', { file_path: filePath });
    }

    async scanWorkspaceSecurity(workspacePath: string): Promise<any> {
        return this.post('/security/scan-workspace', { workspace_path: workspacePath });
    }

    // ========== Behavior Tracking ==========

    async trackBehavior(workspacePath: string, event: string, data: any): Promise<BehaviorStatus> {
        return this.post<BehaviorStatus>('/behavior/track', {
            workspace_path: workspacePath,
            event,
            data,
        });
    }

    // ========== Prompt Optimization ==========

    async optimizePrompt(workspacePath: string, task: string, currentFile?: string, errorText?: string): Promise<ContextResponse> {
        return this.post<ContextResponse>('/prompt/optimize', {
            workspace_path: workspacePath,
            task,
            current_file: currentFile,
            error_text: errorText,
        });
    }

    // ========== API Detection ==========

    async detectEndpoints(workspacePath: string): Promise<any> {
        return this.post('/api/detect', { workspace_path: workspacePath });
    }

    async validateApiCall(workspacePath: string, method: string, route: string): Promise<any> {
        return this.post('/api/validate', {
            workspace_path: workspacePath,
            method,
            route,
        });
    }

    // ========== SQL Analysis ==========

    async analyzeSQL(query: string, workspacePath?: string): Promise<any> {
        return this.post('/sql/analyze', {
            query,
            workspace_path: workspacePath,
        });
    }

    // ========== Enforcement: Prisma/ORM Intelligence ==========

    async analyzePrisma(workspacePath: string): Promise<PrismaAnalysisResult> {
        return this.post<PrismaAnalysisResult>('/prisma/analyze', {
            workspace_path: workspacePath,
        });
    }

    async validatePrisma(workspacePath: string): Promise<any> {
        return this.post('/prisma/validate', {
            workspace_path: workspacePath,
        });
    }

    async parsePrismaSchema(schemaPath: string): Promise<any> {
        return this.post('/prisma/schema', { schema_path: schemaPath });
    }

    async validateDTO(workspacePath: string, dtoPath: string): Promise<any> {
        return this.post('/prisma/validate-dto', {
            workspace_path: workspacePath,
            dto_path: dtoPath,
        });
    }

    async checkPrismaInclude(workspacePath: string, filePath: string): Promise<any> {
        return this.post('/prisma/check-include', {
            workspace_path: workspacePath,
            file_path: filePath,
        });
    }

    // ========== Enforcement: API Contract ==========

    async analyzeContracts(workspacePath: string): Promise<ContractMapResult> {
        return this.post<ContractMapResult>('/contracts/analyze', {
            workspace_path: workspacePath,
        });
    }

    async validateContracts(workspacePath: string): Promise<any> {
        return this.post('/contracts/validate', {
            workspace_path: workspacePath,
        });
    }

    async checkContract(method: string, path: string, workspacePath: string): Promise<any> {
        return this.post('/contracts/check', {
            method, path, workspace_path: workspacePath,
        });
    }

    async getContractMap(workspacePath: string): Promise<ContractMapResult> {
        return this.post<ContractMapResult>('/contracts/map', {
            workspace_path: workspacePath,
        });
    }

    // ========== Enforcement: Impact Analysis ==========

    async buildDependencyGraph(workspacePath: string): Promise<any> {
        return this.post('/impact/build-graph', {
            workspace_path: workspacePath,
        });
    }

    async analyzeImpact(workspacePath: string, filePath: string, oldContent?: string, newContent?: string): Promise<ImpactResult> {
        return this.post<ImpactResult>('/impact/analyze', {
            workspace_path: workspacePath,
            file_path: filePath,
            old_content: oldContent,
            new_content: newContent,
        });
    }

    async analyzeMultiImpact(workspacePath: string, filePaths: string[]): Promise<any> {
        return this.post('/impact/analyze-multi', {
            workspace_path: workspacePath,
            file_paths: filePaths,
        });
    }

    async getFileInfo(workspacePath: string, filePath: string): Promise<any> {
        return this.post('/impact/file-info', {
            workspace_path: workspacePath,
            file_path: filePath,
        });
    }

    async getDependencyMap(workspacePath: string): Promise<any> {
        return this.post('/impact/dependency-map', {
            workspace_path: workspacePath,
        });
    }

    // ========== Enforcement: Validation Pipeline ==========

    async fullScan(workspacePath: string): Promise<RiskReport> {
        return this.post<RiskReport>('/pipeline/full-scan', {
            workspace_path: workspacePath,
        });
    }

    async fileChangeScan(workspacePath: string, filePath: string, content?: string): Promise<RiskReport> {
        return this.post<RiskReport>('/pipeline/file-change', {
            workspace_path: workspacePath,
            file_path: filePath,
            content,
        });
    }

    async preCommitValidation(workspacePath: string, changedFiles: string[]): Promise<RiskReport> {
        return this.post<RiskReport>('/pipeline/pre-commit', {
            workspace_path: workspacePath,
            changed_files: changedFiles,
        });
    }

    async detectStack(workspacePath: string): Promise<StackInfo> {
        return this.post<StackInfo>('/stack/detect', {
            workspace_path: workspacePath,
        });
    }

    // ========== WebSocket ==========

    connectWebSocket(workspacePath: string): void {
        if (this.ws) {
            try { this.ws.close(); } catch { }
        }

        const wsUrl = `${getWsUrl()}/ws/${encodeURIComponent(workspacePath)}`;
        this.output.info(`Connecting WebSocket: ${wsUrl}`);

        try {
            const WebSocket = require('ws');
            this.ws = new WebSocket(wsUrl);

            this.ws.on('open', () => {
                this.connected = true;
                this.output.success('WebSocket connected');
                this.emit('connected', {});
            });

            this.ws.on('message', (data: any) => {
                try {
                    const message = JSON.parse(data.toString());
                    this.emit(message.type, message.data || message);
                } catch { }
            });

            this.ws.on('close', () => {
                this.connected = false;
                this.output.warn('WebSocket disconnected');
                this.emit('disconnected', {});
                this.scheduleReconnect(workspacePath);
            });

            this.ws.on('error', (err: Error) => {
                this.output.error(`WebSocket error: ${err.message}`);
            });
        } catch (err: any) {
            this.output.error(`WebSocket connection failed: ${err.message}`);
            this.scheduleReconnect(workspacePath);
        }
    }

    private scheduleReconnect(workspacePath: string): void {
        if (this.reconnectTimer) { return; }
        this.reconnectTimer = setTimeout(() => {
            this.reconnectTimer = null;
            this.connectWebSocket(workspacePath);
        }, 5000);
    }

    sendWs(type: string, data: any): void {
        if (this.ws && this.connected) {
            this.ws.send(JSON.stringify({ type, ...data }));
        }
    }

    on(event: string, callback: (data: any) => void): void {
        if (!this.wsCallbacks.has(event)) {
            this.wsCallbacks.set(event, []);
        }
        this.wsCallbacks.get(event)!.push(callback);
    }

    private emit(event: string, data: any): void {
        const callbacks = this.wsCallbacks.get(event) || [];
        for (const cb of callbacks) {
            try { cb(data); } catch { }
        }
    }

    isConnected(): boolean {
        return this.connected;
    }

    disconnect(): void {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
            this.reconnectTimer = null;
        }
        if (this.ws) {
            try { this.ws.close(); } catch { }
            this.ws = null;
        }
        this.connected = false;
    }
}
