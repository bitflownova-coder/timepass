/**
 * Backend Manager - Auto-spawn and manage Python backend server
 * Handles process lifecycle, health checks, and auto-restart
 */
import * as vscode from 'vscode';
import * as path from 'path';
import * as fs from 'fs';
import { spawn, ChildProcess } from 'child_process';
import { OutputManager } from './outputChannel';

export interface BackendStatus {
    running: boolean;
    port: number;
    pid: number | null;
    uptime: number; // seconds
    health: 'healthy' | 'starting' | 'unhealthy' | 'stopped';
    lastLog: string;
}

export class BackendManager {
    private process: ChildProcess | null = null;
    private port: number = 7779;
    private startTime: number = 0;
    private output: OutputManager;
    private healthCheckInterval: NodeJS.Timeout | null = null;
    private lastLogLines: string[] = [];
    private maxLogLines: number = 50;
    private onStatusChangeCallback: ((status: BackendStatus) => void) | null = null;
    private onProgressCallback: ((message: string) => void) | null = null;
    private autoRestart: boolean = true;
    private extensionPath: string;
    private connectedToExternal: boolean = false;
    private lastHealthCheck: boolean = false;

    constructor(
        private context: vscode.ExtensionContext,
        output: OutputManager
    ) {
        this.output = output;
        this.extensionPath = context.extensionPath;
        
        // Load port from config
        const config = vscode.workspace.getConfiguration('copilotEngine');
        this.port = config.get('backendPort', 7779);
        this.autoRestart = config.get('autoRestartBackend', true);
    }

    /**
     * Get startup timeout from config (in milliseconds)
     */
    private getStartupTimeout(): number {
        const config = vscode.workspace.getConfiguration('copilotEngine');
        const seconds = config.get('backendStartupTimeout', 600); // default 10 minutes
        return seconds * 1000;
    }

    /**
     * Subscribe to status changes
     */
    public onStatusChange(callback: (status: BackendStatus) => void): void {
        this.onStatusChangeCallback = callback;
    }

    /**
     * Subscribe to progress updates
     */
    public onProgress(callback: (message: string) => void): void {
        this.onProgressCallback = callback;
    }

    /**
     * Get current backend status
     */
    public getStatus(): BackendStatus {
        const isRunning = (this.process !== null && !this.process.killed) || this.connectedToExternal;
        return {
            running: isRunning,
            port: this.port,
            pid: this.process?.pid || null,
            uptime: this.startTime ? Math.floor((Date.now() - this.startTime) / 1000) : 0,
            health: this.determineHealth(),
            lastLog: this.lastLogLines.slice(-1)[0] || ''
        };
    }

    /**
     * Get recent log lines
     */
    public getLogs(): string[] {
        return this.lastLogLines.slice(-20);
    }

    /**
     * Detect if a backend is already running (for Refresh button)
     */
    public async detectExisting(): Promise<boolean> {
        this.output.info(`[DetectExisting] Checking health...`);
        const isHealthy = await this.checkHealth();
        this.output.info(`[DetectExisting] Health result: ${isHealthy}`);
        if (isHealthy) {
            if (!this.connectedToExternal && !this.process) {
                this.connectedToExternal = true;
                this.lastHealthCheck = true;
                if (!this.startTime) {
                    this.startTime = Date.now();
                }
                this.startHealthChecks();
                this.output.success(`Detected running backend on port ${this.port}`);
            }
            this.output.info(`[DetectExisting] Notifying status change, connectedToExternal=${this.connectedToExternal}`);
            this.notifyStatusChange();
            return true;
        } else {
            // Backend is not running
            if (this.connectedToExternal) {
                this.connectedToExternal = false;
                this.lastHealthCheck = false;
            }
            this.output.info(`[DetectExisting] Backend not running, notifying`);
            this.notifyStatusChange();
            return false;
        }
    }

    /**
     * Start backend server
     */
    public async start(): Promise<boolean> {
        if (this.process) {
            this.output.warn('Backend already running');
            return true;
        }

        this.output.section('BACKEND MANAGER');
        this.output.info(`Checking for backend on port ${this.port}...`);
        this.notifyStatusChange();

        // FIRST: Check if there's already a healthy backend running
        const isHealthy = await this.checkHealth();
        if (isHealthy) {
            this.output.success(`Found healthy backend already running on port ${this.port}`);
            // Mark as connected to external backend
            this.connectedToExternal = true;
            this.lastHealthCheck = true;
            this.startTime = Date.now();
            // Start health checks to monitor the existing backend
            this.startHealthChecks();
            vscode.window.showInformationMessage(`Connected to existing Copilot Engine backend on port ${this.port}`);
            this.notifyStatusChange();
            return true;
        }

        this.output.info(`No existing backend found. Attempting to start new backend...`);

        // Find Python executable
        const pythonPath = await this.findPython();
        if (!pythonPath) {
            this.output.error('Python not found. Please install Python 3.8+ or configure python.pythonPath');
            vscode.window.showErrorMessage('Python not found. Cannot start Copilot Engine backend.');
            return false;
        }

        // Find server.py
        const serverPath = this.findServerScript();
        if (!serverPath) {
            this.output.error('server.py not found - cannot start backend locally');
            this.output.separator();
            this.output.warn('WORKAROUND OPTIONS:');
            this.output.info('  1. Start backend manually: cd copilot-engine && python -m uvicorn server:app --port 7779');
            this.output.info('  2. Configure path in settings: copilotEngine.serverPath');
            this.output.info('  3. Open the timepass workspace which contains copilot-engine folder');
            this.output.separator();
            vscode.window.showErrorMessage('Backend server script not found. Start it manually or configure the path.');
            return false;
        }

        // Check if port is available
        const portAvailable = await this.isPortAvailable(this.port);
        if (!portAvailable) {
            // Port is in use but NOT by a healthy backend (we already checked that above)
            // This means it's a hung/crashed process - kill it
            this.output.warn(`Port ${this.port} is occupied by non-responsive process. Killing it...`);
            await this.killProcessOnPort(this.port);
            await this.delay(3000); // Wait for port to be released
            
            // Verify port is now available
            const nowAvailable = await this.isPortAvailable(this.port);
            if (!nowAvailable) {
                this.output.error(`Failed to free port ${this.port}. Please close any process using this port manually.`);
                vscode.window.showErrorMessage(`Port ${this.port} is still in use. Cannot start backend.`);
                return false;
            }
        }

        // Spawn backend process
        const cwd = path.dirname(serverPath);
        this.process = spawn(pythonPath, ['-m', 'uvicorn', 'server:app', '--host', '127.0.0.1', '--port', this.port.toString()], {
            cwd,
            shell: false,
            detached: false,
            stdio: ['ignore', 'pipe', 'pipe']
        });

        this.startTime = Date.now();

        if (this.process.stdout) {
            this.process.stdout.on('data', (data: Buffer) => {
                const lines = data.toString().split('\n').filter(l => l.trim());
                this.lastLogLines.push(...lines);
                if (this.lastLogLines.length > this.maxLogLines) {
                    this.lastLogLines = this.lastLogLines.slice(-this.maxLogLines);
                }
                lines.forEach(line => {
                    this.output.info(`[Backend] ${line}`);
                    // Extract progress messages and notify
                    if (line.includes('Scanning:') || line.includes('Step ') || line.includes('Found ') || line.includes('initialization')) {
                        this.notifyProgress(line);
                    }
                });
                this.notifyStatusChange();
            });
        }

        if (this.process.stderr) {
            this.process.stderr.on('data', (data: Buffer) => {
                const lines = data.toString().split('\n').filter(l => l.trim());
                this.lastLogLines.push(...lines);
                if (this.lastLogLines.length > this.maxLogLines) {
                    this.lastLogLines = this.lastLogLines.slice(-this.maxLogLines);
                }
                lines.forEach(line => {
                    // Highlight errors more prominently
                    if (line.toLowerCase().includes('error') || line.toLowerCase().includes('exception') || line.toLowerCase().includes('traceback')) {
                        this.output.error(`[Backend ERROR] ${line}`);
                    } else if (line.toLowerCase().includes('warning')) {
                        this.output.warn(`[Backend WARN] ${line}`);
                    } else {
                        this.output.warn(`[Backend] ${line}`);
                    }
                });
                this.notifyStatusChange();
            });
        }

        this.process.on('exit', (code, signal) => {
            this.output.warn(`Backend exited (code=${code}, signal=${signal})`);
            this.process = null;
            this.notifyStatusChange();

            // Auto-restart if enabled and not manually stopped
            if (this.autoRestart && code !== 0) {
                this.output.info('Auto-restarting backend in 5 seconds...');
                setTimeout(() => this.start(), 5000);
            }
        });

        this.process.on('error', (err) => {
            this.output.error(`Backend error: ${err.message}`);
            this.process = null;
            this.notifyStatusChange();
        });

        // Wait for backend to be healthy (configurable timeout, default 10 minutes)
        const timeoutMs = this.getStartupTimeout();
        const timeoutMinutes = Math.floor(timeoutMs / 60000);
        this.output.info(`Waiting for backend to initialize (timeout: ${timeoutMinutes} min)...`);
        
        const healthy = await this.waitForHealthy(timeoutMs);
        if (healthy) {
            this.output.success(`Backend started on port ${this.port} (PID ${this.process?.pid})`);
            this.startHealthChecks();
            vscode.window.showInformationMessage(`Copilot Engine backend started on port ${this.port}`);
            return true;
        } else {
            this.output.error(`Backend failed to become healthy within ${timeoutMinutes} minutes`);
            this.output.separator();
            this.output.error('RECENT BACKEND LOGS:');
            // Show last 10 log lines to help debug
            const recentLogs = this.lastLogLines.slice(-10);
            if (recentLogs.length > 0) {
                recentLogs.forEach(line => this.output.info(`  ${line}`));
            } else {
                this.output.warn('  No log output captured - backend may have crashed immediately');
            }
            this.output.separator();
            this.output.error('TROUBLESHOOTING:');
            this.output.info('  1. Check if Python 3.8+ is installed');
            this.output.info('  2. Check if required packages are installed: pip install -r requirements.txt');
            this.output.info(`  3. Check if port ${this.port} is in use: Get-NetTCPConnection -LocalPort ${this.port}`);
            this.output.info('  4. Try starting manually in terminal to see full errors');
            this.output.info('  5. Check server.py exists in copilot-engine folder');
            this.output.separator();
            this.output.warn('Large projects may take longer. Increase copilotEngine.backendStartupTimeout in settings.');
            this.stop();
            vscode.window.showErrorMessage(`Backend startup timeout - check Output panel for error details`);
            return false;
        }
    }

    /**
     * Stop backend server
     */
    public stop(): void {
        // Stop health checks
        if (this.healthCheckInterval) {
            clearInterval(this.healthCheckInterval);
            this.healthCheckInterval = null;
        }

        // If connected to external backend, just disconnect
        if (this.connectedToExternal) {
            this.output.info('Disconnecting from external backend...');
            this.connectedToExternal = false;
            this.lastHealthCheck = false;
            this.notifyStatusChange();
            this.output.success('Disconnected from backend');
            vscode.window.showInformationMessage('Disconnected from Copilot Engine backend');
            return;
        }

        if (!this.process) {
            this.output.info('Backend not running');
            return;
        }

        this.output.info('Stopping backend...');
        this.autoRestart = false; // Disable auto-restart for manual stop

        try {
            // Try graceful shutdown first
            this.process.kill('SIGTERM');
            
            // Force kill after 5 seconds
            setTimeout(() => {
                if (this.process && !this.process.killed) {
                    this.process.kill('SIGKILL');
                }
            }, 5000);
        } catch (err: any) {
            this.output.error(`Error stopping backend: ${err.message}`);
        }

        this.process = null;
        this.lastHealthCheck = false;
        this.notifyStatusChange();
        this.output.success('Backend stopped');
        vscode.window.showInformationMessage('Copilot Engine backend stopped');
    }

    /**
     * Restart backend server
     */
    public async restart(): Promise<boolean> {
        this.output.info('Restarting backend...');
        this.stop();
        await this.delay(3000);
        return await this.start();
    }

    /**
     * Dispose - cleanup on extension deactivate
     */
    public dispose(): void {
        if (this.healthCheckInterval) {
            clearInterval(this.healthCheckInterval);
        }
        if (this.process) {
            this.process.kill('SIGKILL');
        }
    }

    // ────────────────────────────────────────────────────────────
    // Private helpers
    // ────────────────────────────────────────────────────────────

    private determineHealth(): 'healthy' | 'starting' | 'unhealthy' | 'stopped' {
        // Connected to external backend
        if (this.connectedToExternal) {
            return this.lastHealthCheck ? 'healthy' : 'unhealthy';
        }
        // No process and not connected externally
        if (!this.process) {
            return 'stopped';
        }
        const uptime = Math.floor((Date.now() - this.startTime) / 1000);
        if (uptime < 10) {
            return 'starting';
        }
        // Check if process is responsive (simple heuristic)
        return this.lastHealthCheck ? 'healthy' : 'starting';
    }

    private async findPython(): Promise<string | null> {
        // 1. Check workspace venv
        const workspaceFolder = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
        if (workspaceFolder) {
            const venvPaths = [
                path.join(workspaceFolder, '.venv', 'Scripts', 'python.exe'),
                path.join(workspaceFolder, 'venv', 'Scripts', 'python.exe'),
                path.join(workspaceFolder, '.venv', 'bin', 'python'),
                path.join(workspaceFolder, 'venv', 'bin', 'python')
            ];
            for (const p of venvPaths) {
                if (fs.existsSync(p)) {
                    this.output.info(`Using venv: ${p}`);
                    return p;
                }
            }
        }

        // 2. Check Python extension setting
        const pythonExt = vscode.extensions.getExtension('ms-python.python');
        if (pythonExt) {
            const config = vscode.workspace.getConfiguration('python');
            const pythonPath = config.get<string>('defaultInterpreterPath') || config.get<string>('pythonPath');
            if (pythonPath && fs.existsSync(pythonPath)) {
                this.output.info(`Using Python extension: ${pythonPath}`);
                return pythonPath;
            }
        }

        // 3. Check system PATH
        const systemPaths = ['python', 'python3', 'python.exe', 'python3.exe'];
        for (const cmd of systemPaths) {
            try {
                // Try to find in PATH
                const { execSync } = require('child_process');
                const result = execSync(`where ${cmd}`, { encoding: 'utf-8', stdio: 'pipe' });
                const pythonPath = result.split('\n')[0].trim();
                if (pythonPath && fs.existsSync(pythonPath)) {
                    this.output.info(`Using system Python: ${pythonPath}`);
                    return pythonPath;
                }
            } catch {
                // Continue to next
            }
        }

        return null;
    }

    private findServerScript(): string | null {
        // Check config first
        const config = vscode.workspace.getConfiguration('copilotEngine');
        const configuredPath = config.get<string>('serverPath', '');
        if (configuredPath && fs.existsSync(configuredPath)) {
            this.output.info(`Using configured server path: ${configuredPath}`);
            return configuredPath;
        }

        // Build search paths - try multiple locations
        const searchPaths: string[] = [];
        
        // 1. Relative to extension installation
        searchPaths.push(path.join(this.extensionPath, '..', 'server.py'));
        searchPaths.push(path.join(this.extensionPath, '..', '..', 'server.py'));
        
        // 2. In current workspace's copilot-engine folder
        const workspaceFolders = vscode.workspace.workspaceFolders || [];
        for (const folder of workspaceFolders) {
            searchPaths.push(path.join(folder.uri.fsPath, 'copilot-engine', 'server.py'));
            searchPaths.push(path.join(folder.uri.fsPath, 'server.py'));
        }
        
        // 3. Common development locations
        const homeDir = process.env.USERPROFILE || process.env.HOME || '';
        searchPaths.push(path.join(homeDir, 'copilot-engine', 'server.py'));
        searchPaths.push(path.join(homeDir, 'projects', 'copilot-engine', 'server.py'));
        
        // 4. Check parent directories of any workspace folder
        for (const folder of workspaceFolders) {
            let dir = folder.uri.fsPath;
            for (let i = 0; i < 5; i++) { // Go up 5 levels
                const parent = path.dirname(dir);
                if (parent === dir) break;
                dir = parent;
                searchPaths.push(path.join(dir, 'copilot-engine', 'server.py'));
            }
        }
        
        // 5. Known development paths (add your common paths)
        searchPaths.push('D:\\Bitflow_softwares\\timepass\\copilot-engine\\server.py');
        searchPaths.push('C:\\Users\\prati\\copilot-engine\\server.py');

        // Remove duplicates
        const uniquePaths = [...new Set(searchPaths)];
        
        this.output.info(`Searching for server.py in ${uniquePaths.length} locations...`);

        for (const p of uniquePaths) {
            if (fs.existsSync(p)) {
                this.output.success(`Found server.py: ${p}`);
                return p;
            }
        }

        // Log all tried paths for debugging
        this.output.error('server.py not found! Searched in:');
        uniquePaths.forEach((p, i) => {
            this.output.info(`  ${i + 1}. ${p}`);
        });
        this.output.separator();
        this.output.warn('TIP: Configure the path in settings: copilotEngine.serverPath');

        return null;
    }

    /**
     * Quick health check without waiting
     */
    private async checkHealth(): Promise<boolean> {
        try {
            const http = require('http');
            return await new Promise<boolean>((resolve) => {
                const req = http.get(`http://127.0.0.1:${this.port}/health`, (res: any) => {
                    // Consume response data to prevent memory leak
                    res.resume();
                    resolve(res.statusCode === 200);
                });
                req.on('error', (err: Error) => {
                    this.output.warn(`Health check error: ${err.message}`);
                    resolve(false);
                });
                req.setTimeout(5000, () => {
                    this.output.warn('Health check timeout');
                    req.destroy();
                    resolve(false);
                });
            });
        } catch (err) {
            this.output.warn(`Health check exception: ${err}`);
            return false;
        }
    }

    private async isPortAvailable(port: number): Promise<boolean> {
        try {
            const http = require('http');
            const server = http.createServer();
            
            return new Promise<boolean>((resolve) => {
                server.once('error', () => resolve(false));
                server.once('listening', () => {
                    server.close();
                    resolve(true);
                });
                server.listen(port, '127.0.0.1');
            });
        } catch {
            return false;
        }
    }

    private async killProcessOnPort(port: number): Promise<void> {
        try {
            const { execSync } = require('child_process');
            if (process.platform === 'win32') {
                // Use PowerShell for reliable process killing on Windows
                const cmd = `powershell -Command "$conns = Get-NetTCPConnection -LocalPort ${port} -ErrorAction SilentlyContinue; $conns.OwningProcess | ForEach-Object { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }"`;
                execSync(cmd, { stdio: 'ignore' });
                this.output.info(`Killed existing process on port ${port}`);
            } else {
                execSync(`lsof -ti:${port} | xargs kill -9`, { stdio: 'ignore' });
            }
        } catch (error) {
            this.output.warn(`Could not kill process on port ${port}: ${error}`);
        }
    }

    private async waitForHealthy(timeout: number): Promise<boolean> {
        const startTime = Date.now();
        let lastProgressLog = 0;
        const progressInterval = 5000; // Log progress every 5 seconds
        const timeoutMinutes = Math.floor(timeout / 60000);

        while (Date.now() - startTime < timeout) {
            try {
                const http = require('http');
                const healthCheck = await new Promise<boolean>((resolve) => {
                    const req = http.get(`http://127.0.0.1:${this.port}/health`, (res: any) => {
                        resolve(res.statusCode === 200);
                    });
                    req.on('error', () => resolve(false));
                    req.setTimeout(2000, () => {
                        req.destroy();
                        resolve(false);
                    });
                });

                if (healthCheck) {
                    return true;
                }
            } catch {
                // Continue waiting
            }

            // Show progress updates
            const elapsed = Date.now() - startTime;
            if (elapsed - lastProgressLog >= progressInterval) {
                const seconds = Math.floor(elapsed / 1000);
                const msg = `Waiting for backend... (${seconds}s / ${timeoutMinutes}min)`;
                this.output.info(`⏳ ${msg}`);
                this.notifyProgress(msg);
                if (seconds > 60 && seconds % 30 === 0) {
                    const scanMsg = `Large projects (1000+ files) may take ${timeoutMinutes} minutes to scan all files...`;
                    this.output.info(`   ${scanMsg}`);
                    this.notifyProgress(scanMsg);
                }
                lastProgressLog = elapsed;
            }

            await this.delay(1000);
        }
        return false;
    }

    private startHealthChecks(): void {
        if (this.healthCheckInterval) {
            clearInterval(this.healthCheckInterval);
        }

        let consecutiveFailures = 0;

        this.healthCheckInterval = setInterval(async () => {
            // Check health for both spawned and external backends
            if (!this.process && !this.connectedToExternal) {
                return;
            }

            try {
                const http = require('http');
                const startTime = Date.now();
                const healthy = await new Promise<boolean>((resolve) => {
                    const req = http.get(`http://127.0.0.1:${this.port}/health`, (res: any) => {
                        res.resume(); // Consume response data
                        this.output.info(`[HealthCheck] Response status=${res.statusCode} in ${Date.now() - startTime}ms`);
                        resolve(res.statusCode === 200);
                    });
                    req.on('error', (err: Error) => {
                        this.output.warn(`[HealthCheck] Error: ${err.message}`);
                        resolve(false);
                    });
                    req.setTimeout(10000, () => {
                        this.output.warn(`[HealthCheck] Timeout after 10s`);
                        req.destroy();
                        resolve(false);
                    });
                });

                this.lastHealthCheck = healthy;

                if (!healthy) {
                    consecutiveFailures++;
                    if (this.connectedToExternal) {
                        if (consecutiveFailures >= 3) {
                            this.output.warn(`External backend unresponsive after ${consecutiveFailures} failed checks`);
                            this.connectedToExternal = false;
                            consecutiveFailures = 0;
                        } else {
                            this.output.warn(`External backend health check failed (${consecutiveFailures}/3)`);
                        }
                    } else if (this.autoRestart && consecutiveFailures >= 3) {
                        this.output.warn(`Backend health check failed ${consecutiveFailures} times. Restarting...`);
                        consecutiveFailures = 0;
                        await this.restart();
                    } else if (consecutiveFailures < 3) {
                        this.output.warn(`Backend health check failed (${consecutiveFailures}/3 before restart)`);
                    }
                } else {
                    consecutiveFailures = 0;
                }

                this.notifyStatusChange();
            } catch {
                this.lastHealthCheck = false;
                this.notifyStatusChange();
            }
        }, 15000); // Check every 15 seconds
    }

    private notifyStatusChange(): void {
        const status = this.getStatus();
        this.output.info(`[NotifyStatus] running=${status.running}, health=${status.health}, hasCallback=${!!this.onStatusChangeCallback}`);
        if (this.onStatusChangeCallback) {
            this.onStatusChangeCallback(status);
        }
    }

    private notifyProgress(message: string): void {
        if (this.onProgressCallback) {
            this.onProgressCallback(message);
        }
    }

    private delay(ms: number): Promise<void> {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}
