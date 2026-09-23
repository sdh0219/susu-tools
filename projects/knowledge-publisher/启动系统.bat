@echo off
chcp 65001 >nul
title Knowledge Publisher
cd /d "%~dp0"

echo ============================================
echo   Knowledge Publisher - 启动系统
echo   启动后会自动打开浏览器，关闭本窗口即停止
echo ============================================
echo.

rem 系统已经在运行？直接打开浏览器
curl -s -o nul -m 2 http://127.0.0.1:8765/
if %errorlevel%==0 (
    echo 系统已经在运行，正在打开浏览器...
    start http://127.0.0.1:8765/
    pause
    exit /b 0
)

rem 寻找可用的 Python（按优先级：项目内 .venv → PATH 上的 python → 常见 conda 路径）
set "KP_PY="
if exist ".venv\Scripts\python.exe" set "KP_PY=.venv\Scripts\python.exe"
if not defined KP_PY (
    python -c "import fastapi, markdown_it, matplotlib, PIL" >nul 2>&1
    if %errorlevel%==0 set "KP_PY=python"
)
if not defined KP_PY (
    for %%D in ("%USERPROFILE%\anaconda3\envs\kp\python.exe" "D:\environment\anaconda3\envs\kp\python.exe" "C:\ProgramData\anaconda3\envs\kp\python.exe" "%LOCALAPPDATA%\anaconda3\envs\kp\python.exe") do (
        if exist %%D set "KP_PY=%%~D"
    )
)
if not defined KP_PY (
    echo [提示] 找不到可用的 Python 环境。
    echo   第一次使用请先双击「首次安装.bat」自动配置环境。
    pause
    exit /b 1
)

echo 使用环境：%KP_PY%
"%KP_PY%" main.py preview

pause
