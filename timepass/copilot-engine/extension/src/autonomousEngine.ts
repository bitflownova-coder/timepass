/**
 * Copilot Engine - AutonomousEngine
 * Client-side orchestration for the autonomous runtime.
 *
 * Responsibilities:
 *  - Forwards ChangeEvents from EventStream to backend /autonomous/event
 *  - Initializes workspace on first connect (/autonomous/initialize)
 *  - Polls dashboard data on a timer for webview updates
 *  - Listens for WebSocket push updates from backend
 *  - Exposes current health state for StatusBar & Webview
 */
import * as vscode from 'vscode';
import { EngineClient } from './engineClient';
import { OutputManager } from './outputChannel';
import { EventStream, ChangeEvent } from './eventStream';

export interface RiskScores {
    overall_score: number;
    health_level: string;
    schema_risk: number;
    contract_risk: number;
    migration_risk: number;
    dependency_risk: number;
    security_risk: number;
    naming_risk: number;
    drift_risk: number;
}

export interface DashboardData {
    health: {
        workspace: string;
        risk_scores: RiskScores;
        graph: Record<string, any>;
        drift: Record<string, any>;
        worker: Record<string, any>;
    };
    risk_trend: Array<{ timestamp: string; overall_score: number }>;
    unresolved_drifts: Array<Record<string, any>>;
    circular_dependencies: string[][];
    dead_code_files: string[];
    timestamp: string;
}

type DashboardListener = (data: DashboardData) => void;

export class AutonomousEngine {
    private client: EngineClient;
    private output: OutputManager;
    private eventStream: EventStream;
    private workspacePath: string = '';

    private pollTimer: NodeJS.Timeout | null = null;
    private dashboardListeners: DashboardListener[] = [];
    private latestDashboard: DashboardData | null = null;

    private initialized: boolean = false;
    private running: boolean = false;

    // Configurable
    private pollIntervalMs: number = 15_000; // 15 seconds

    constructor(client: EngineClient, output: OutputManager) {
        this.client = client;
        this.output = output;
        this.eventStream = new EventStream(output);
    }

    /**
     * Start the autonomous runtime for a workspace.
     * Called once during extension activation after engine is confirmed running.
     */
    async start(workspacePath: string): Promise<void> {
        if (this.running) { return; }
        this.running = true;
        this.workspacePath = workspacePath;

        // 1. Start event stream
        this.eventStream.start(workspacePath);
        this.eventStream.onEvent((event) => this.onChangeEvent(event));

        // 2. Initialize workspace in backend (full index + graph build)
        try {
            this.output.info('[Autonomous] Initializing workspace analysis...');
            const result = await this.client.post<any>('/autonomous/initialize', {
                workspace_path: workspacePath,
            });
            this.initialized = true;

            const steps = result?.steps || {};
            const entities = steps.index?.entities_found || 0;
            const edges = steps.graph?.file_edges || 0;
            this.output.success(
                `[Autonomous] Workspace initialized: ${entities} entities, ${edges} graph edges`
            );
        } catch (e) {
            this.output.warn(`[Autonomous] Init failed (engine may be starting): ${e}`);
        }

        // 3. Start dashboard polling
        this.pollTimer = setInterval(() => this.pollDashboard(), this.pollIntervalMs);
        // Immediate first poll
        this.pollDashboard();

        this.output.info('[Autonomous] Runtime started — all events are being captured');
    }

    /**
     * Stop the autonomous runtime.
     */
    stop(): void {
        this.running = false;
        this.eventStream.stop();
        if (this.pollTimer) {
            clearInterval(this.pollTimer);
            this.pollTimer = null;
        }
    }

    /**
     * Register a listener for dashboard data updates.
     */
    onDashboardUpdate(listener: DashboardListener): void {
        this.dashboardListeners.push(listener);
        // Immediately send latest if available
        if (this.latestDashboard) {
            listener(this.latestDashboard);
        }
    }

    /**
     * Get latest dashboard data synchronously.
     */
    getLatestDashboard(): DashboardData | null {
        return this.latestDashboard;
    }

    /**
     * Get event stream stats.
     */
    getStats(): Record<string, any> {
        return {
            running: this.running,
            initialized: this.initialized,
            eventStream: this.eventStream.getStats(),
            latestRisk: this.latestDashboard?.health?.risk_scores?.overall_score ?? null,
            healthLevel: this.latestDashboard?.health?.risk_scores?.health_level ?? 'UNKNOWN',
        };
    }

    /**
     * Expose the EventStream for extension wiring.
     */
    getEventStream(): EventStream {
        return this.eventStream;
    }

    // ═══════════════════════════════════════════
    // Internal
    // ═══════════════════════════════════════════

    private async onChangeEvent(event: ChangeEvent): Promise<void> {
        if (!this.running) { return; }

        try {
            await this.client.post<any>('/autonomous/event', {
                file_path: event.file_path,
                workspace_path: event.workspace_path,
                change_type: event.change_type,
                git_branch: event.git_branch,
            });
        } catch {
            // Backend may be temporarily unavailable — silent
        }
    }

    /**
     * Force refresh dashboard data (public for manual refresh button).
     * Can work even if autonomous engine hasn't started yet.
     */
    async refreshDashboard(workspacePathOverride?: string): Promise<DashboardData | null> {
        const wsPath = workspacePathOverride || this.workspacePath;
        
        // If we have a workspace path, fetch directly (don't require running state)
        if (wsPath) {
            try {
                const encodedPath = encodeURIComponent(wsPath);
                const data = await this.client.get<DashboardData>(
                    `/autonomous/dashboard/${encodedPath}`
                );

                if (data) {
                    this.latestDashboard = data;
                    // Notify listeners
                    for (const listener of this.dashboardListeners) {
                        try {
                            listener(data);
                        } catch (e) {
                            this.output.warn(`[Autonomous] Dashboard listener error: ${e}`);
                        }
                    }
                    return data;
                }
            } catch (e) {
                this.output.warn(`[Autonomous] Dashboard refresh failed: ${e}`);
            }
        }
        
        return this.latestDashboard;
    }

    private async pollDashboard(): Promise<void> {
        if (!this.running || !this.workspacePath) { return; }

        try {
            const encodedPath = encodeURIComponent(this.workspacePath);
            const data = await this.client.get<DashboardData>(
                `/autonomous/dashboard/${encodedPath}`
            );

            if (data) {
                this.latestDashboard = data;
                for (const listener of this.dashboardListeners) {
                    try {
                        listener(data);
                    } catch (e) {
                        this.output.warn(`[Autonomous] Dashboard listener error: ${e}`);
                    }
                }
            }
        } catch {
            // Silent — backend may be restarting
        }
    }

    dispose(): void {
        this.stop();
    }
}
