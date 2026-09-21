@echo off
chcp 65001 >nul
echo ========================================
echo   BiliNote 打包分发版（自动排除敏感文件）
echo ========================================
echo.

setlocal EnableDelayedExpansion
set "OUT=..\BiliNote_win_v1.1.1_dist"
set "FLAGS="

:parse
if "%~1"=="" goto run
if /I "%~1"=="--force" (
  set "FLAGS=!FLAGS! --force"
  shift
  goto parse
)
if /I "%~1"=="--slim" (
  set "FLAGS=!FLAGS! --slim"
  shift
  goto parse
)
set "OUT=%~1"
shift
goto parse

:run
echo 输出目录: %OUT%
echo 参数: %FLAGS%（可为空；覆盖已存在目录需 --force；精简包加 --slim）
echo.

call .\python310\python.exe -X utf8 pack_dist.py --out "%OUT%" %FLAGS%
if errorlevel 1 (
    echo.
    echo 打包失败。若目录已存在请加 --force，或换输出路径。
    pause
    exit /b 1
)

echo.
echo 完成。可将输出目录整体发给使用者（勿再手动拷入 cookies.txt / .env / db / logs）。
pause
