import { contextBridge, ipcRenderer } from 'electron';

contextBridge.exposeInMainWorld('gestorWeb', {
  getAppVersion: () => ipcRenderer.invoke('app:get-version') as Promise<string>
});
