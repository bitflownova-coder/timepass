import { app, BrowserWindow, Tray, Menu, globalShortcut, nativeImage, ipcMain } from 'electron';
import path from 'path';
import { ProcessManager } from './processManager';
import { setupIpcHandlers } from './ipc';

// Track quit state
let isQuitting = false;

// Disable GPU acceleration issues on some systems
app.disableHardwareAcceleration();

let mainWindow: BrowserWindow | null = null;
let tray: Tray | null = null;
let processManager: ProcessManager | null = null;

const VITE_DEV_SERVER_URL = process.env.VITE_DEV_SERVER_URL;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 1024,
    minHeight: 700,
    title: 'Bitflow AI OS',
    icon: path.join(__dirname, '../public/icon.png'),
    frame: false, // Custom titlebar
    titleBarStyle: 'hidden',
    titleBarOverlay: {
      color: '#0a0a0f',
      symbolColor: '#9ca3af',
      height: 36,
    },
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
    },
    backgroundColor: '#0a0a0f',
    show: false,
  });

  // Show when ready to prevent flash
  mainWindow.once('ready-to-show', () => {
    mainWindow?.show();
  });

  // Load the app
  if (VITE_DEV_SERVER_URL) {
    mainWindow.loadURL(VITE_DEV_SERVER_URL);
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
  }

  // Minimize to tray instead of closing
  mainWindow.on('close', (event) => {
    if (!isQuitting) {
      event.preventDefault();
      mainWindow?.hide();
    }
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function createTray() {
  // Create a simple 16x16 tray icon
  const icon = nativeImage.createEmpty();
  tray = new Tray(icon);
  
  const contextMenu = Menu.buildFromTemplate([
    {
      label: 'Show Bitflow AI OS',
      click: () => {
        mainWindow?.show();
        mainWindow?.focus();
      },
    },
    { type: 'separator' },
    {
      label: 'Services',
      submenu: [
        {
          label: 'Restart Copilot Engine',
          click: () => processManager?.restartService('copilot-engine'),
        },
        {
          label: 'Restart Web Crawler',
          click: () => processManager?.restartService('web-crawler'),
        },
      ],
    },
    { type: 'separator' },
    {
      label: 'Quit',
      click: () => {
        isQuitting = true;
        app.quit();
      },
    },
  ]);

  tray.setToolTip('Bitflow AI OS');
  tray.setContextMenu(contextMenu);
  tray.on('double-click', () => {
    mainWindow?.show();
    mainWindow?.focus();
  });
}

function registerGlobalShortcuts() {
  // Ctrl+Shift+B to toggle window
  globalShortcut.register('CommandOrControl+Shift+B', () => {
    if (mainWindow?.isVisible()) {
      mainWindow.hide();
    } else {
      mainWindow?.show();
      mainWindow?.focus();
    }
  });
}

app.whenReady().then(async () => {
  // Initialize process manager
  processManager = new ProcessManager();
  
  // Setup IPC handlers
  setupIpcHandlers(processManager);

  createWindow();
  createTray();
  registerGlobalShortcuts();

  // Auto-start backend services
  await processManager.startAll();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  // Don't quit on macOS
  if (process.platform !== 'darwin') {
    // Keep running in tray
  }
});

app.on('before-quit', async () => {
  isQuitting = true;
  globalShortcut.unregisterAll();
  await processManager?.stopAll();
});
