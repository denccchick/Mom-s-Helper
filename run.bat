@echo off
chcp 65001 >nul
title DOCX Translator Launcher

echo    MOM'S Helper - Запуск
echo.

echo Запуск бэкенда...
start "DOCX Backend" cmd /k "cd /d "%~dp0\MomsHelperBackend" && .venv\Scripts\activate && uvicorn app.main:app --host 0.0.0.0 --port 8000"

echo Ожидание загрузки бэкенда (8 секунд)...
timeout /t 8 /nobreak >nul

echo Запуск фронтенда...
start "DOCX Frontend" cmd /k "cd /d "%~dp0\MomsHelperFrontend" && npm run dev"

echo Ожидание загрузки фронтенда (3 секунды)...
timeout /t 3 /nobreak >nul

echo Открытие браузера...
start http://localhost:3000

echo.
echo    ЗАПУСК ЗАВЕРШЕН!
echo.
echo Бэкенд:  http://localhost:8000
echo Документация: http://localhost:8000/docs
echo Фронтенд: http://localhost:3000
echo.
echo Для остановки серверов закройте их окна.
echo.
pause
