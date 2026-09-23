# 千瞳 - 一键初始化脚本
# 所有依赖安装在项目目录内，不污染系统环境

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  千瞳 - 视角转换器 环境初始化" -ForegroundColor Cyan
Write-Host "  项目目录: $ProjectRoot" -ForegroundColor Cyan
Write-Host "  所有依赖仅安装在此目录，删除即清" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$localDir = Join-Path $ProjectRoot ".local"
$npmCache = Join-Path $localDir "npm-cache"
$pipCache = Join-Path $localDir "pip-cache"
$nodeDir = Join-Path $localDir "node-v20.18.3-win-x64"
$nodeExe = Join-Path $nodeDir "node.exe"
$npmCmd = Join-Path $nodeDir "npm.cmd"
$frontendDir = Join-Path $ProjectRoot "frontend"
$backendDir = Join-Path $ProjectRoot "backend"
$venvDir = Join-Path $backendDir ".venv"

# ---- 1. 创建本地缓存目录 ----
Write-Host "`n[1/5] 创建本地缓存目录..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path $npmCache, $pipCache | Out-Null
Write-Host "  npm缓存: $npmCache" -ForegroundColor Gray
Write-Host "  pip缓存: $pipCache" -ForegroundColor Gray

# ---- 2. 安装本地 Node.js (便携版) ----
Write-Host "`n[2/5] 检查本地 Node.js..." -ForegroundColor Yellow
if (-not (Test-Path $nodeExe)) {
    Write-Host "  下载 Node.js v20 便携版..." -ForegroundColor Gray
    $nodeZip = Join-Path $localDir "node-v20.18.3-win-x64.zip"
    Invoke-WebRequest -Uri "https://nodejs.org/dist/v20.18.3/node-v20.18.3-win-x64.zip" -OutFile $nodeZip
    Expand-Archive -Path $nodeZip -DestinationPath $localDir -Force
    Remove-Item -Force $nodeZip
    Write-Host "  Node.js v20 安装完成（便携版，仅在项目内）" -ForegroundColor Green
} else {
    Write-Host "  本地 Node.js 已就绪: $(& $nodeExe -v)" -ForegroundColor Green
}

# ---- 3. 初始化前端 (npm) ----
# 强制npm使用项目本地缓存，不写入C盘
Write-Host "`n[3/5] 初始化前端依赖..." -ForegroundColor Yellow
Push-Location $frontendDir
# 设置环境变量强制npm缓存到项目目录
$env:npm_config_cache = $npmCache
& $npmCmd install
Pop-Location
Write-Host "  前端依赖安装完成" -ForegroundColor Green

# ---- 4. 初始化后端 (Python venv) ----
Write-Host "`n[4/5] 初始化后端 Python 环境..." -ForegroundColor Yellow
if (-not (Test-Path $venvDir)) {
    Write-Host "  创建 Python 虚拟环境..." -ForegroundColor Gray
    python -m venv $venvDir
    Write-Host "  虚拟环境创建完成" -ForegroundColor Green
} else {
    Write-Host "  虚拟环境已存在，跳过创建" -ForegroundColor Green
}

$pipPath = Join-Path $venvDir "Scripts\pip.exe"
$reqFile = Join-Path $backendDir "requirements.txt"
# 强制pip缓存到项目目录，不写入C盘
$env:PIP_CACHE_DIR = $pipCache
& $pipPath install --cache-dir $pipCache -r $reqFile
Write-Host "  Python 依赖安装完成" -ForegroundColor Green

# ---- 5. 创建必要目录 ----
Write-Host "`n[5/5] 创建运行时目录..." -ForegroundColor Yellow
$dirs = @(
    (Join-Path $backendDir "checkpoints"),
    (Join-Path $backendDir "uploads"),
    (Join-Path $backendDir "tasks")
)
foreach ($d in $dirs) {
    New-Item -ItemType Directory -Force -Path $d | Out-Null
}
Write-Host "  运行时目录已就绪" -ForegroundColor Green

# ---- 完成 ----
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  初始化完成！" -ForegroundColor Green
Write-Host "  所有依赖均在: $ProjectRoot" -ForegroundColor Gray
Write-Host "  删除此文件夹即可完全清除" -ForegroundColor Gray
Write-Host "  运行 .\scripts\start.ps1 启动服务" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
