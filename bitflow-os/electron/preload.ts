import { contextBridge, ipcRenderer } from 'electron';

// Expose protected methods to the renderer process
contextBridge.exposeInMainWorld('electronAPI', {
  // Service management
  getServiceStatuses: () => ipcRenderer.invoke('services:status'),
  startService: (id: string) => ipcRenderer.invoke('services:start', id),
  stopService: (id: string) => ipcRenderer.invoke('services:stop', id),
  restartService: (id: string) => ipcRenderer.invoke('services:restart', id),
  onServiceStatus: (callback: (statuses: any[]) => void) => {
    const handler = (_event: any, statuses: any[]) => callback(statuses);
    ipcRenderer.on('service:status', handler);
    return () => ipcRenderer.removeListener('service:status', handler);
  },

  // App
  getVersion: () => ipcRenderer.invoke('app:version'),

  // Window controls
  minimize: () => ipcRenderer.invoke('window:minimize'),
  maximize: () => ipcRenderer.invoke('window:maximize'),
  close: () => ipcRenderer.invoke('window:close'),
});
