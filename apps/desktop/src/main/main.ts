import { app, BrowserWindow, ipcMain, shell } from 'electron';
import { join } from 'node:path';
import isDev from 'electron-is-dev';

const devServerUrl = process.env.VITE_DEV_SERVER_URL;

function createMainWindow(): void {
  const window = new BrowserWindow({
    width: 1440,
    height: 940,
    minWidth: 1120,
    minHeight: 720,
    title: 'Gestor Web',
    backgroundColor: '#f4f2ed',
    webPreferences: {
      preload: join(__dirname, '../preload/preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true
    }
  });

  if (isDev && devServerUrl) {
    void window.loadURL(devServerUrl);
    window.webContents.openDevTools({ mode: 'detach' });
  } else {
    void window.loadFile(join(__dirname, '../renderer/index.html'));
  }

  window.webContents.setWindowOpenHandler(({ url }) => {
    void shell.openExternal(url);
    return { action: 'deny' };
  });
}

app.whenReady().then(() => {
  ipcMain.handle('app:get-version', () => app.getVersion());
  createMainWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createMainWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
