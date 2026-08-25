const { app, BrowserWindow, dialog } = require('electron');
const { spawn, exec } = require('child_process');
const path = require('path');
const fs = require('fs');

let mainWindow;
let backendProcess;

function killProcessOnPort(port) {
    try {
        if (process.platform === 'win32') {
            exec(`for /f "tokens=5" %a in ('netstat -ano ^| findstr :${port}') do taskkill /F /PID %a 2>nul`, (error) => {
                if (!error) console.log(`Freed port ${port}`);
            });
        } else {
            exec(`lsof -ti :${port} | xargs kill -9`, (error) => {
                if (!error) console.log(`Freed port ${port}`);
            });
        }
    } catch (error) {
        console.error('Error killing process on port:', error);
    }
}

function killBackend() {
    if (backendProcess && backendProcess.pid) {
        console.log(`Killing backend process (PID: ${backendProcess.pid})...`);

        if (process.platform === 'win32') {
            exec(`taskkill /PID ${backendProcess.pid} /F /T`, (error) => {
                if (error) {
                    console.error('Error killing backend process:', error);
                } else {
                    console.log('Backend process killed');
                }
            });
        } else {
            try {
                process.kill(-backendProcess.pid, 'SIGKILL');
            } catch (e) {
                backendProcess.kill('SIGKILL');
            }
        }

        backendProcess = null;
    }

    setTimeout(() => {
        killProcessOnPort(8000);
    }, 500);
}

function isPortAvailable(port) {
    try {
        const result = require('child_process').execSync(`netstat -ano | findstr :${port}`, { stdio: 'pipe' });
        return !result.toString().trim();
    } catch {
        return true;
    }
}

function createMainWindow() {
    mainWindow = new BrowserWindow({
        width: 1400,
        height: 900,
        webPreferences: {
            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, 'preload.cjs')
        },
        icon: path.join(__dirname, 'icon.ico')
    });

    mainWindow.on('closed', () => {
        mainWindow = null;
        killBackend();
    });

    const isDev = process.env.NODE_ENV === 'development';

    if (isDev) {
        mainWindow.loadURL('http://localhost:3000');
        mainWindow.webContents.openDevTools();
    } else {
        const paths = [
            path.join(__dirname, '../dist/index.html'),
            path.join(process.resourcesPath, 'app', 'dist', 'index.html'),
            path.join(__dirname, '..', 'resources', 'app', 'dist', 'index.html'),
            path.join(__dirname, 'dist', 'index.html')
        ];

        let loaded = false;
        for (const p of paths) {
            if (fs.existsSync(p)) {
                console.log('Loading index from:', p);
                mainWindow.loadFile(p);
                loaded = true;
                break;
            }
        }

        if (!loaded) {
            console.error('index.html not found in any path');
            mainWindow.loadURL('data:text/html,<h1>Error: index.html not found</h1>');
        }
    }
}

function startBackend() {
    const isDev = process.env.NODE_ENV === 'development';

    if (isDev) {
        const backendPath = path.join(__dirname, '../../MomsHelperBackend');
        console.log('Starting backend from:', backendPath);

        backendProcess = spawn('python', ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000', '--reload'], {
            cwd: backendPath,
            shell: true,
            stdio: 'pipe'
        });

        backendProcess.stdout.on('data', (data) => {
            console.log('[Backend]: ' + data);
        });

        backendProcess.stderr.on('data', (data) => {
            console.error('[Backend Error]: ' + data);
        });

        backendProcess.on('close', (code) => {
            console.log('Backend exited with code ' + code);
        });

        createMainWindow();
        return;
    }

    // ========== ПРОДАКШЕН ==========

    if (!isPortAvailable(8000)) {
        console.log('Port 8000 is busy, trying to free it...');
        killProcessOnPort(8000);
    }

    const resourcesPath = process.resourcesPath;
    const exePath = path.join(resourcesPath, 'backend', 'backend.exe');

    if (!fs.existsSync(exePath)) {
        console.error('Backend executable not found at:', exePath);
        dialog.showErrorBox(
            'Error',
            'Backend executable not found.\n\n' +
            'Expected: ' + exePath
        );
        app.quit();
        return;
    }

    console.log('Starting backend from:', exePath);

    backendProcess = spawn(exePath, [], {
        detached: false,
        stdio: 'pipe',
        env: {
            ...process.env,
            PYTHONUNBUFFERED: '1'
        }
    });

    let backendReady = false;

    backendProcess.stdout.on('data', (data) => {
        const output = data.toString();
        console.log('[Backend]: ' + output);

        if (output.includes('Application startup complete') || output.includes('Uvicorn running')) {
            backendReady = true;
            console.log('Backend started successfully');
            if (!mainWindow) {
                createMainWindow();
            }
        }
    });

    backendProcess.stderr.on('data', (data) => {
        const output = data.toString();
        console.error('[Backend Error]: ' + output);
    });

    backendProcess.on('close', (code) => {
        console.log('Backend exited with code ' + code);
        if (code !== 0 && code !== null && !mainWindow) {
            dialog.showErrorBox('Error', 'Failed to start backend server.');
            app.quit();
        }
    });

    setTimeout(() => {
        if (!mainWindow) {
            createMainWindow();
        }
    }, 15000);
}

app.whenReady().then(() => {
    startBackend();
});

app.on('window-all-closed', () => {
    killBackend();
    if (process.platform !== 'darwin') {
        app.quit();
    }
});

app.on('before-quit', () => {
    killBackend();
});

app.on('will-quit', () => {
    killBackend();
});
