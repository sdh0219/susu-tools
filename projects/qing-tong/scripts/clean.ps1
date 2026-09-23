# 千瞳 - 彻底清理脚本
# 删除所有本地依赖和缓存，恢复到纯净状态
# 删除整个 QianTong 文件夹即可完全清除，此脚本用于只清理依赖保留源码

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

Write-Host "========================================" -ForegroundColor Red
Write-Host "  千瞳 - 清理本地依赖和缓存" -ForegroundColor Red
Write-Host "  项目目录: $ProjectRoot" -ForegroundColor Red
Write-Host "========================================" -ForegroundColor Red

$confirm = Read-Host "确认清理所有本地依赖？(y/N)"
if ($confirm -ne 'y') {
    Write-Host "已取消" -ForegroundColor Yellow
    exit 0
}

# 清理 .local 目录（包含 Node.js 便携版、npm 缓存、pip 缓存）
$localDir = Join-Path $ProjectRoot ".local"
if (Test-Path $localDir) {
    Write-Host "删除本地 Node.js 和所有缓存..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $localDir
}

# 清理前端 node_modules
$frontendNM = Join-Path $ProjectRoot "frontend\node_modules"
if (Test-Path $frontendNM) {
    Write-Host "删除前端 node_modules..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $frontendNM
}

# 清理前端 package-lock.json
$lockFile = Join-Path $ProjectRoot "frontend\package-lock.json"
if (Test-Path $lockFile) {
    Remove-Item -Force $lockFile
}

# 清理 Python 虚拟环境
$venvDir = Join-Path $ProjectRoot "backend\.venv"
if (Test-Path $venvDir) {
    Write-Host "删除 Python 虚拟环境..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $venvDir
}

# 清理临时文件
$uploadsDir = Join-Path $ProjectRoot "backend\uploads"
$tasksDir = Join-Path $ProjectRoot "backend\tasks"
if (Test-Path $uploadsDir) { Remove-Item -Recurse -Force $uploadsDir }
if (Test-Path $tasksDir) { Remove-Item -Recurse -Force $tasksDir }

Write-Host "`n清理完成！项目已恢复到纯净状态（仅保留源码）。" -ForegroundColor Green
Write-Host "如需重新初始化，运行 .\scripts\setup.ps1" -ForegroundColor Cyan
Write-Host "如需彻底删除，直接删除整个 QianTong 文件夹即可。" -ForegroundColor DarkGray
