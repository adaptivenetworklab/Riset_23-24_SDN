const { app, BrowserWindow, ipcMain, dialog } = require('electron');
const path = require('path');
const { spawn, exec } = require('child_process');
const fs = require('fs');

let mainWindow;
let dockerProcess = null;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false
    }
  });

  mainWindow.loadFile('index.html');

  // Open DevTools for development
  // mainWindow.webContents.openDevTools();

  mainWindow.on('closed', function () {
    mainWindow = null;
  });
}

app.on('ready', createWindow);

app.on('window-all-closed', function () {
  if (process.platform !== 'darwin') app.quit();
});

app.on('activate', function () {
  if (mainWindow === null) createWindow();
});

// IPC handlers for Docker management
ipcMain.on('start-docker-compose', (event) => {
  try {
    const projectDir = path.join(__dirname, '..');

    // Check if docker-compose.yml exists
    if (!fs.existsSync(path.join(projectDir, 'docker-compose.yml'))) {
      event.reply('docker-output', 'Error: docker-compose.yml not found');
      return;
    }

    dockerProcess = spawn('docker-compose', ['up'], { cwd: projectDir });

    dockerProcess.stdout.on('data', (data) => {
      event.reply('docker-output', data.toString());
    });

    dockerProcess.stderr.on('data', (data) => {
      event.reply('docker-output', data.toString());
    });

    dockerProcess.on('close', (code) => {
      event.reply('docker-output', `Docker process exited with code ${code}`);
      dockerProcess = null;
    });

    event.reply('docker-status', 'running');
  } catch (error) {
    event.reply('docker-output', `Error starting Docker: ${error.message}`);
    event.reply('docker-status', 'error');
  }
});

ipcMain.on('stop-docker-compose', (event) => {
  try {
    const projectDir = path.join(__dirname, '..');

    const stopProcess = spawn('docker-compose', ['down'], { cwd: projectDir });

    stopProcess.stdout.on('data', (data) => {
      event.reply('docker-output', data.toString());
    });

    stopProcess.stderr.on('data', (data) => {
      event.reply('docker-output', data.toString());
    });

    stopProcess.on('close', (code) => {
      event.reply('docker-output', `Docker-compose down exited with code ${code}`);
      event.reply('docker-status', 'stopped');

      if (dockerProcess) {
        dockerProcess.kill();
        dockerProcess = null;
      }
    });
  } catch (error) {
    event.reply('docker-output', `Error stopping Docker: ${error.message}`);
  }
});

ipcMain.on('check-docker-status', (event) => {
  exec('docker ps', (error, stdout, stderr) => {
    if (error) {
      event.reply('docker-status', 'error');
      event.reply('docker-output', `Error checking Docker status: ${error.message}`);
      return;
    }

    if (dockerProcess) {
      event.reply('docker-status', 'running');
    } else {
      // Check if our containers are already running
      exec('docker-compose ps', { cwd: path.join(__dirname, '..') }, (err, out) => {
        if (err) {
          event.reply('docker-status', 'stopped');
        } else if (out.toLowerCase().includes('up')) {
          event.reply('docker-status', 'running');
        } else {
          event.reply('docker-status', 'stopped');
        }
      });
    }
  });
});
