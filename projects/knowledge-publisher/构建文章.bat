@echo off
chcp 65001 >nul
title Knowledge Publisher - 构建
cd /d "%~dp0"

echo ============================================
echo   Knowledge Publisher - 一键构建
echo   输入文章名（如 bayes），生成知乎 + 抖音
echo ============================================
echo.
set /p NAME=请输入文章名：

if "%NAME%"=="" (
    echo 未输入文章名，退出。
    pause
    exit /b 1
)

rem 寻找可用的 Python（与启动脚本相同逻辑）
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
    echo [提示] 找不到可用的 Python 环境，请先运行「首次安装.bat」。
    pause
    exit /b 1
)

"%KP_PY%" main.py build %NAME% --all

echo.
echo 构建完成！打开 output\%NAME%\ 查看成品。
pause
