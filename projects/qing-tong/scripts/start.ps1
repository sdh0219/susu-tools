# 千瞳 - 一键启动脚本
# 使用项目内本地 Node.js 和 Python 虚拟环境
# 所有缓存和运行时均在项目目录内，不污染C盘

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  千瞳 - 视角转换器 启动" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$localDir = Join-Path $ProjectRoot ".local"
$npmCache = Join-Path $localDir "npm-cache"
$pipCache = Join-Path $localDir "pip-cache"
$nodeDir = Join-Path $localDir "node-v20.18.3-win-x64"
$nodeExe = Join-Path $nodeDir "node.exe"
$backendDir = Join-Path $ProjectRoot "backend"
$frontendDir = Join-Path $ProjectRoot "frontend"
$venvDir = Join-Path $backendDir ".venv"
$pythonPath = Join-Path $venvDir "Scripts\python.exe"

# 检查环境
if (-not (Test-Path $nodeExe)) {
    Write-Host "未检测到本地 Node.js，请先运行 .\scripts\setup.ps1" -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $pythonPath)) {
    Write-Host "未检测到 Python 虚拟环境，请先运行 .\scripts\setup.ps1" -ForegroundColor Red
    exit 1
}
if (-not (Test-Path (Join-Path $frontendDir "node_modules"))) {
    Write-Host "未检测到前端依赖，请先运行 .\scripts\setup.ps1" -ForegroundColor Red
    exit 1
}

# 设置环境变量：强制缓存到项目目录，不写入C盘
$env:npm_config_cache = $npmCache
$env:PIP_CACHE_DIR = $pipCache

# 启动后端
Write-Host "`n[1/2] 启动后端服务 (FastAPI on port 8000)..." -ForegroundColor Yellow
Start-Process -FilePath $pythonPath -ArgumentList "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000" -WorkingDirectory $backendDir -NoNewWindow

Start-Sleep -Seconds 3

# 启动前端
Write-Host "`n[2/2] 启动前端服务 (Vite on port 3000)..." -ForegroundColor Yellow
$vitePath = Join-Path $frontendDir "node_modules\vite\bin\vite.js"
Start-Process -FilePath $nodeExe -ArgumentList $vitePath -WorkingDirectory $frontendDir -NoNewWindow

Start-Sleep -Seconds 3

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  服务已启动！" -ForegroundColor Green
Write-Host "  前端: http://localhost:3000" -ForegroundColor White
Write-Host "  后端: http://localhost:8000" -ForegroundColor White
Write-Host "  API文档: http://localhost:8000/docs" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Cyan
