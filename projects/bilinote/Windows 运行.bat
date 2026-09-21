@echo off
chcp 65001 >nul
echo ========================================
echo   BiliNote
echo ========================================
echo.

set HF_ENDPOINT=https://hf-mirror.com
set PYTHONIOENCODING=utf-8

REM read backend port from .env, default 8000
set BACKEND_PORT=8000
for /f "tokens=1,2 delims==" %%a in (.env) do (
    if "%%a"=="BACKEND_PORT" set BACKEND_PORT=%%b
)

REM kill stale process listening on the port
REM two-stage literal filter to avoid killing unrelated processes
echo checking port %BACKEND_PORT% ...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr /C:":%BACKEND_PORT% " ^| findstr /C:"LISTENING"') do (
    echo port %BACKEND_PORT% is used by PID %%a , killing it ...
    taskkill /PID %%a /F >nul 2>&1
)
ping -n 2 127.0.0.1 >nul
echo port %BACKEND_PORT% is ready
echo.
echo starting BiliNote ...
echo browser will open: http://localhost:%BACKEND_PORT%
echo first run may download the Whisper model, please wait
echo.

call .\python310\python.exe -X utf8 main.py
echo.
echo BiliNote stopped
echo.
pause
