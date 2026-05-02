import { ChildProcess, spawn } from 'child_process';
import path from 'path';
import { BrowserWindow } from 'electron';

export interface ServiceConfig {
  id: string;
  name: string;
  command: string;
  args: string[];
  cwd: string;
  port: number;
  healthUrl: string;
  enabled: boolean;
}

export interface ServiceStatus {
  id: string;
  name: string;
  status: 'stopped' | 'starting' | 'running' | 'error' | 'disabled';
  port: number;
  pid?: number;
  uptime?: number;
  lastError?: string;
  startedAt?: number;
}

export class ProcessManager {
  private services: Map<string, ServiceConfig> = new Map();
  private processes: Map<string, ChildProcess> = new Map();
  private statuses: Map<string, ServiceStatus> = new Map();
  private healthIntervals: Map<string, NodeJS.Timeout> = new Map();

  constructor() {
    const baseDir = path.resolve(__dirname, '../../');

    // Copilot Engine
    this.services.set('copilot-engine', {
      id: 'copilot-engine',
      name: 'Copilot Engine',
      command: 'python',
      args: ['run.py'],
      cwd: path.join(baseDir, 'copilot-engine'),
      port: 7779,
      healthUrl: 'http://127.0.0.1:7779/health',
      enabled: true,
    });

    // Website Crawler
    this.services.set('web-crawler', {
      id: 'web-crawler',
      name: 'Web Crawler',
      command: 'python',
      args: ['app.py'],
      cwd: path.join(baseDir, 'website_crawler'),
      port: 5000,
      healthUrl: 'http://127.0.0.1:5000/',
      enabled: true,
    });

    // Initialize statuses
    for (const [id, config] of this.services) {
      this.statuses.set(id, {
        id,
        name: config.name,
        status: config.enabled ? 'stopped' : 'disabled',
        port: config.port,
      });
    }
  }

  async startService(id: string): Promise<void> {
    const config = this.services.get(id);
    if (!config || !config.enabled) return;

    // Skip if already running
    if (this.processes.has(id)) return;

    this.updateStatus(id, { status: 'starting' });
    this.broadcast('service:status', this.getAllStatuses());

    try {
      const proc = spawn(config.command, config.args, {
        cwd: config.cwd,
        stdio: ['pipe', 'pipe', 'pipe'],
        shell: true,
        env: { ...process.env },
      });

      this.processes.set(id, proc);

      proc.stdout?.on('data', (data: Buffer) => {
        const msg = data.toString().trim();
        if (msg) console.log(`[${config.name}] ${msg}`);
      });

      proc.stderr?.on('data', (data: Buffer) => {
        const msg = data.toString().trim();
        if (msg) console.error(`[${config.name}] ${msg}`);
      });

      proc.on('error', (err) => {
        console.error(`[${config.name}] Process error:`, err.message);
        this.updateStatus(id, { status: 'error', lastError: err.message });
        this.processes.delete(id);
        this.broadcast('service:status', this.getAllStatuses());
      });

      proc.on('exit', (code) => {
        console.log(`[${config.name}] Exited with code ${code}`);
        this.processes.delete(id);
        this.updateStatus(id, {
          status: code === 0 ? 'stopped' : 'error',
          lastError: code !== 0 ? `Exited with code ${code}` : undefined,
          pid: undefined,
        });
        this.broadcast('service:status', this.getAllStatuses());
      });

      this.updateStatus(id, {
        status: 'starting',
        pid: proc.pid,
        startedAt: Date.now(),
      });

      // Start health checking
      this.startHealthCheck(id);

    } catch (err: any) {
      this.updateStatus(id, { status: 'error', lastError: err.message });
      this.broadcast('service:status', this.getAllStatuses());
    }
  }

  async stopService(id: string): Promise<void> {
    const proc = this.processes.get(id);
    if (!proc) return;

    this.stopHealthCheck(id);

    return new Promise((resolve) => {
      proc.on('exit', () => {
        this.processes.delete(id);
        this.updateStatus(id, { status: 'stopped', pid: undefined });
        this.broadcast('service:status', this.getAllStatuses());
        resolve();
      });

      // Try graceful kill first
      proc.kill('SIGTERM');
      
      // Force kill after 5s
      setTimeout(() => {
        if (this.processes.has(id)) {
          proc.kill('SIGKILL');
        }
      }, 5000);
    });
  }

  async restartService(id: string): Promise<void> {
    await this.stopService(id);
    await new Promise((r) => setTimeout(r, 1000));
    await this.startService(id);
  }

  async startAll(): Promise<void> {
    const promises = [];
    for (const [id, config] of this.services) {
      if (config.enabled) {
        promises.push(this.startService(id));
      }
    }
    await Promise.all(promises);
  }

  async stopAll(): Promise<void> {
    const promises = [];
    for (const id of this.processes.keys()) {
      promises.push(this.stopService(id));
    }
    await Promise.all(promises);
    
    // Clear all health check intervals
    for (const interval of this.healthIntervals.values()) {
      clearInterval(interval);
    }
    this.healthIntervals.clear();
  }

  getAllStatuses(): ServiceStatus[] {
    return Array.from(this.statuses.values()).map((s) => ({
      ...s,
      uptime: s.startedAt ? Date.now() - s.startedAt : undefined,
    }));
  }

  private startHealthCheck(id: string) {
    const config = this.services.get(id);
    if (!config) return;

    // Check every 10 seconds
    const interval = setInterval(async () => {
      try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 5000);
        
        const response = await fetch(config.healthUrl, {
          signal: controller.signal,
        });
        clearTimeout(timeout);

        if (response.ok) {
          if (this.statuses.get(id)?.status !== 'running') {
            this.updateStatus(id, { status: 'running' });
            this.broadcast('service:status', this.getAllStatuses());
          }
        }
      } catch {
        // Service not ready yet or crashed
        const currentStatus = this.statuses.get(id)?.status;
        if (currentStatus === 'running') {
          this.updateStatus(id, { status: 'error', lastError: 'Health check failed' });
          this.broadcast('service:status', this.getAllStatuses());
        }
      }
    }, 10000);

    this.healthIntervals.set(id, interval);
  }

  private stopHealthCheck(id: string) {
    const interval = this.healthIntervals.get(id);
    if (interval) {
      clearInterval(interval);
      this.healthIntervals.delete(id);
    }
  }

  private updateStatus(id: string, partial: Partial<ServiceStatus>) {
    const current = this.statuses.get(id);
    if (current) {
      this.statuses.set(id, { ...current, ...partial });
    }
  }

  private broadcast(channel: string, data: any) {
    for (const win of BrowserWindow.getAllWindows()) {
      win.webContents.send(channel, data);
    }
  }
}
