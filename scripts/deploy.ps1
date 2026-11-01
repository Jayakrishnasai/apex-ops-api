# =============================================================================
# deploy.ps1 — Windows PowerShell deploy script
#
# Usage:
#   .\scripts\deploy.ps1 [-Version <tag>]
# =============================================================================
param (
    [string]$Version = ""
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectDir = Split-Path -Parent $scriptDir
Set-Location $projectDir

if (-not $Version) {
    try {
        $Version = (git rev-parse --short HEAD 2>$null)
    } catch {
        $Version = "local"
    }
    if (-not $Version) { $Version = "local" }
}

$env:IMAGE_TAG = $Version

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " Apex Operations API — Deploy (Windows)" -ForegroundColor Cyan
Write-Host " Version: $env:IMAGE_TAG" -ForegroundColor Cyan
Write-Host " $(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ')" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Pre-flight check
if (-not (Test-Path ".env")) {
    Write-Error "ERROR: .env file not found. Copy .env.example to .env and configure secrets."
}

# 1. Build Docker image
Write-Host "`n[1/4] Building Docker image apex-ops-api:$env:IMAGE_TAG ..." -ForegroundColor Yellow
docker build --target runtime -t "apex-ops-api:$env:IMAGE_TAG" -t "apex-ops-api:latest" .
if ($LASTEXITCODE -ne 0) { Write-Error "Docker build failed" }

# 2. Record previous tag for rollback
$rollbackFile = ".last_deployed_tag"
if (Test-Path $rollbackFile) {
    $prev = Get-Content $rollbackFile -Raw
    Write-Host "[2/4] Previous tag recorded for rollback: $($prev.Trim())" -ForegroundColor Gray
}
$env:IMAGE_TAG | Out-File -FilePath $rollbackFile -NoNewline

# 3. Start services
Write-Host "[3/4] Starting stack with docker compose ..." -ForegroundColor Yellow
docker compose up -d --no-deps --build app
docker compose up -d db prometheus

# 4. Health gate
Write-Host "[4/4] Polling health check on http://localhost:8000/health ..." -ForegroundColor Yellow
$maxRetries = 15
$retryInterval = 5
$healthy = $false

for ($i = 1; $i -le $maxRetries; $i++) {
    try {
        $resp = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 3 -ErrorAction SilentlyContinue
        if ($resp.StatusCode -eq 200) {
            Write-Host "✓ Health check passed (HTTP 200) after $($i * $retryInterval)s" -ForegroundColor Green
            $healthy = $true
            break
        }
    } catch {
        # Retry
    }
    Write-Host "  Attempt $i/$maxRetries — waiting ${retryInterval}s..." -ForegroundColor Gray
    Start-Sleep -Seconds $retryInterval
}

if (-not $healthy) {
    Write-Host "ERROR: Health check failed. Triggering automatic rollback..." -ForegroundColor Red
    & "$scriptDir\rollback.ps1"
    exit 1
}

Write-Host "`n✓ Deployment complete." -ForegroundColor Green
Write-Host "  API:        http://localhost:8000" -ForegroundColor Cyan
Write-Host "  Docs:       http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "  Metrics:    http://localhost:8000/metrics" -ForegroundColor Cyan
Write-Host "  Prometheus: http://localhost:9090" -ForegroundColor Cyan
