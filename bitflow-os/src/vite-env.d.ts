/// <reference types="vite/client" />

declare interface ElectronAPI {
  getServiceStatuses: () => Promise<ServiceStatus[]>;
  startService: (id: string) => Promise<ServiceStatus[]>;
  stopService: (id: string) => Promise<ServiceStatus[]>;
  restartService: (id: string) => Promise<ServiceStatus[]>;
  onServiceStatus: (callback: (statuses: ServiceStatus[]) => void) => () => void;
  getVersion: () => Promise<string>;
  minimize: () => void;
  maximize: () => void;
  close: () => void;
}

declare interface ServiceStatus {
  id: string;
  name: string;
  status: 'stopped' | 'starting' | 'running' | 'error' | 'disabled';
  port: number;
  pid?: number;
  uptime?: number;
  lastError?: string;
  startedAt?: number;
}

interface Window {
  electronAPI: ElectronAPI;
}
