const { app, BrowserWindow, session } = require('electron');
const path = require('path');

const gotTheLock = app.requestSingleInstanceLock();

if (!gotTheLock) {
  app.quit();
} else {
  app.on('second-instance', (event, commandLine, workingDirectory) => {
    const mainWindow = BrowserWindow.getAllWindows()[0];
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });

  function createWindow() {
    const persistentSession = session.fromPartition('persist:main');

    persistentSession.webRequest.onHeadersReceived(
      (details, callback) => {
        const headers = details.responseHeaders || {};

        Object.keys(headers).forEach((key) => {
          headers[key] = headers[key].map((value) =>
            value.replace(/SameSite=None/gi, 'SameSite=None; Secure')
          );
        });

        callback({ responseHeaders: headers });
      }
    );

    const baseUrl = process.env.APP_URL;

    if (!baseUrl) {
      console.error('Error: APP_URL environment variable is not set');
      app.quit();
      return;
    }

    const win = new BrowserWindow({
      width: 1200,
      height: 800,
      webPreferences: {
        session: persistentSession,
        contextIsolation: true,
        nodeIntegration: false,
        webSecurity: true,
        preload: path.join(__dirname, 'preload.js')
      }
    });

    persistentSession.cookies
      .get({ domain: new URL(baseUrl).hostname })
      .then((cookies) => {
        const isLoggedIn = cookies.some(
          (cookie) => cookie.name === 'sessionid'
        );

        if (isLoggedIn) {
          win.loadURL(baseUrl);
        } else {
          win.loadURL(`${baseUrl}/login`);
        }
      })
      .catch((err) => {
        console.error('Failed to read cookies:', err);
        win.loadURL(`${baseUrl}/login`);
      });
  }

  app.whenReady().then(() => {
    createWindow();
  });

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });

  app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
      app.quit();
    }
  });
}
