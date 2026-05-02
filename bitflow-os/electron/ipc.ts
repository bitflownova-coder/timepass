import { ipcMain, BrowserWindow } from 'electron';
import { ProcessManager } from './processManager';

export function setupIpcHandlers(processManager: ProcessManager) {
  // Service management
  ipcMain.handle('services:status', () => {
    return processManager.getAllStatuses();
  });

  ipcMain.handle('services:start', async (_, serviceId: string) => {
    await processManager.startService(serviceId);
    return processManager.getAllStatuses();
  });

  ipcMain.handle('services:stop', async (_, serviceId: string) => {
    await processManager.stopService(serviceId);
    return processManager.getAllStatuses();
  });

  ipcMain.handle('services:restart', async (_, serviceId: string) => {
    await processManager.restartService(serviceId);
    return processManager.getAllStatuses();
  });

  // App info
  ipcMain.handle('app:version', () => {
    return '0.1.0';
  });

  // Window controls
  ipcMain.handle('window:minimize', (event) => {
    BrowserWindow.fromWebContents(event.sender)?.minimize();
  });

  ipcMain.handle('window:maximize', (event) => {
    const win = BrowserWindow.fromWebContents(event.sender);
    if (win?.isMaximized()) {
      win.unmaximize();
    } else {
      win?.maximize();
    }
  });

  ipcMain.handle('window:close', (event) => {
    BrowserWindow.fromWebContents(event.sender)?.close();
  });
}
