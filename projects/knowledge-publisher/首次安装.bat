@echo off
chcp 65001 >nul
title Knowledge Publisher - 首次安装
cd /d "%~dp0"

echo ============================================
echo   Knowledge Publisher - 首次安装
echo   自动创建运行环境（约 2-5 分钟）
echo   前提：电脑上已安装 Python 3.9+ 或 Anaconda
echo ============================================
echo.

rem 寻找真实的 Python（排除 Windows 商店的占位符）
set "BASE_PY="
for %%D in ("%USERPROFILE%\anaconda3\python.exe" "D:\environment\anaconda3\python.exe" "C:\ProgramData\anaconda3\python.exe" "%LOCALAPPDATA%\anaconda3\python.exe" "C:\Program Files\Python311\python.exe" "C:\Program Files\Python312\python.exe" "C:\Python311\python.exe" "C:\Python312\python.exe") do (
    if exist %%D set "BASE_PY=%%~D"
)
if not defined BASE_PY (
    for /f "delims=" %%P in ('where python 2^>nul') do (
        echo %%P | findstr /i "WindowsApps" >nul
        if errorlevel 1 set "BASE_PY=%%P"
    )
)
if not defined BASE_PY (
    echo [错误] 没有检测到 Python。
    echo.
    echo 请先安装 Anaconda（https://www.anaconda.com/download）或 Python 3.11，
    echo 然后重新双击本脚本。
    echo.
    pause
    exit /b 1
)

echo 使用 Python：%BASE_PY%
echo.
echo [1/2] 创建虚拟环境 .venv ...
"%BASE_PY%" -m venv .venv
if errorlevel 1 (
    echo [错误] 创建虚拟环境失败，请安装 Python 3.9+ 后重试
    pause
    exit /b 1
)

echo [2/2] 安装依赖库（需要联网，请稍候）...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo [错误] 依赖安装失败，请检查网络后重试
    pause
    exit /b 1
)

echo.
echo ============================================
echo   安装完成！
echo   以后双击「启动系统.bat」即可使用。
echo ============================================
pause
