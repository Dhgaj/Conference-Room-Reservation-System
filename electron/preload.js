const { contextBridge } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  getVersions: () => process.versions
});
