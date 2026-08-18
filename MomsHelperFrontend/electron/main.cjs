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

function findBackendPath() {
    const resourcesPath = process.resourcesPath;

    const possiblePaths = [
        resourcesPath,
        path.join(resourcesPath, 'backend'),
        path.join(path.dirname(app.getPath('exe')), 'resources', 'backend'),
    ];

    for (const p of possiblePaths) {
        const mainPy = path.join(p, 'app', 'main.py');
        if (fs.existsSync(mainPy)) {
            return p;
        }
    }

    return null;
}

function setupVenv(backendPath) {
    const venvPath = path.join(backendPath, 'venv');
    const pythonExe = path.join(venvPath, 'Scripts', 'python.exe');

    if (fs.existsSync(pythonExe)) {
        console.log('Python environment found: ' + pythonExe);
        return pythonExe;
    }

    console.log('Python environment not found. Creating venv...');

    const result = require('child_process').spawnSync('python', ['-m', 'venv', 'venv'], {
        cwd: backendPath,
        shell: true,
        stdio: 'pipe'
    });

    if (result.status !== 0) {
        console.log('Failed to create virtual environment');
        return null;
    }

    console.log('Virtual environment created');

    const pipExe = path.join(venvPath, 'Scripts', 'pip.exe');
    const requirementsPath = path.join(backendPath, 'requirements.txt');

    if (fs.existsSync(requirementsPath)) {
        console.log('Installing dependencies...');
        const pipResult = require('child_process').spawnSync(pipExe, ['install', '--no-cache-dir', '-r', 'requirements.txt'], {
            cwd: backendPath,
            shell: true,
            stdio: 'pipe'
        });

        if (pipResult.status !== 0) {
            console.log('Failed to install dependencies');
            return null;
        }

        console.log('All dependencies installed');
    }

    return pythonExe;
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

    if (!isPortAvailable(8000)) {
        console.log('Port 8000 is busy, trying to free it...');
        killProcessOnPort(8000);
    }

    const backendPath = findBackendPath();

    if (!backendPath) {
        dialog.showErrorBox('Error', 'Application files not found. Please reinstall.');
        app.quit();
        return;
    }

    console.log('Backend path:', backendPath);

    const pythonExe = setupVenv(backendPath);

    if (!pythonExe) {
        dialog.showErrorBox(
            'Setup Failed',
            'Failed to setup Python environment.\n\nMake sure Python 3.8+ is installed and added to PATH.\n\nDownload Python: https://python.org'
        );
        app.quit();
        return;
    }

    console.log('Starting uvicorn...');

    backendProcess = spawn(pythonExe, ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000'], {
        cwd: backendPath,
        shell: true,
        stdio: 'pipe',
        env: {
            ...process.env,
            PYTHONPATH: backendPath,
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
