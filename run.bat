@echo off
chcp 65001 >nul
title DOCX Translator Launcher

echo ========================================
echo    DOCX TRANSLATOR - АВТОЗАПУСК
echo ========================================
echo.

:: Запуск бэкенда
echo Запуск бэкенда...
start "DOCX Backend" cmd /k "cd /d "%~dp0\MomsHelperBackend" && .venv\Scripts\activate && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

:: Ожидание загрузки бэкенда
echo Ожидание загрузки бэкенда (8 секунд)...
timeout /t 8 /nobreak >nul

:: Запуск фронтенда
echo Запуск фронтенда...
start "DOCX Frontend" cmd /k "cd /d "%~dp0\MomsHelperFrontend" && npm run dev"

:: Ожидание загрузки фронтенда
echo Ожидание загрузки фронтенда (3 секунды)...
timeout /t 3 /nobreak >nul

:: Открытие браузера
echo Открытие браузера...
start http://localhost:3000

echo.
echo ========================================
echo    ЗАПУСК ЗАВЕРШЕН!
echo ========================================
echo.
echo Бэкенд:  http://localhost:8000
echo Документация: http://localhost:8000/docs
echo Фронтенд: http://localhost:3000
echo.
echo Для остановки серверов закройте их окна.
echo.
pause