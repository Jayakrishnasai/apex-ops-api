# =============================================================================
# rollback.ps1 — Windows PowerShell rollback script
#
# Usage:
#   .\scripts\rollback.ps1 [-TargetTag <tag>]
# =============================================================================
param (
    [string]$TargetTag = ""
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectDir = Split-Path -Parent $scriptDir
Set-Location $projectDir

$rollbackFile = ".last_deployed_tag"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " Apex Operations API — Rollback (Windows)" -ForegroundColor Cyan
Write-Host " $(Get-Date -Format 'yyyy-MM-ddTHH:mm:ssZ')" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

if (-not $TargetTag) {
    if (Test-Path $rollbackFile) {
        $TargetTag = (Get-Content $rollbackFile -Raw).Trim()
        Write-Host "Rolling back to last recorded tag: $TargetTag" -ForegroundColor Yellow
    } else {
        Write-Error "ERROR: No target tag provided and .last_deployed_tag not found."
    }
} else {
    Write-Host "Rolling back to requested tag: $TargetTag" -ForegroundColor Yellow
}

# 1. Stop app container
Write-Host "[1/3] Stopping current app container..." -ForegroundColor Yellow
docker compose stop app

# 2. Start rollback container
Write-Host "[2/3] Restarting app with tag $TargetTag..." -ForegroundColor Yellow
$env:IMAGE_TAG = $TargetTag
docker compose up -d --no-deps app

# 3. Health verification
Write-Host "[3/3] Verifying health on http://localhost:8000/health..." -ForegroundColor Yellow
Start-Sleep -Seconds 5
try {
    $resp = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
    if ($resp.StatusCode -eq 200) {
        Write-Host "✓ Rollback successful! Running version: $TargetTag" -ForegroundColor Green
    } else {
        Write-Warning "Rollback finished with HTTP status $($resp.StatusCode)"
    }
} catch {
    Write-Error "ERROR: Rollback health verification failed. Check logs: docker compose logs app"
}
