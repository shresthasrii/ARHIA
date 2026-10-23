# ===================================================================
#   ARHIEA - ADAPTIVE ROAD AND HUMAN INTELLIGENCE EMERGENCY SYSTEM (SIH26204)
# ===================================================================

Write-Host "===================================================================" -ForegroundColor Cyan
Write-Host "  ARHIEA - ADAPTIVE ROAD AND HUMAN INTELLIGENCE EMERGENCY SYSTEM   " -ForegroundColor Cyan
Write-Host "===================================================================" -ForegroundColor Cyan
Write-Host "Starting ARHIEA Core Engine on http://127.0.0.1:8000 ..." -ForegroundColor Yellow

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $scriptDir) { $scriptDir = (Get-Location).Path }
Set-Location $scriptDir

$pythonPath = "$scriptDir\.venv\Scripts\python.exe"
if (-not (Test-Path $pythonPath)) {
    $pythonPath = "python"
}

# Start Backend Server with WorkingDirectory explicitly set
$backend = Start-Process -FilePath $pythonPath -ArgumentList "-m uvicorn backend.main:app --host 127.0.0.1 --port 8000" -WorkingDirectory $scriptDir -PassThru

# Health-check polling to ensure server is ready before opening browser
Write-Host "Waiting for ARHIEA backend to bind..." -ForegroundColor Gray
$healthy = $false
for ($i = 0; $i -lt 15; $i++) {
    Start-Sleep -Milliseconds 600
    try {
        $res = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/status" -TimeoutSec 2 -ErrorAction Stop
        if ($res.app_name) {
            $healthy = $true
            break
        }
    } catch {}
}

if ($healthy) {
    Write-Host "ARHIEA Core Engine is live at http://127.0.0.1:8000" -ForegroundColor Green
} else {
    Write-Host "ARHIEA backend started." -ForegroundColor Yellow
}

Start-Process "http://127.0.0.1:8000"

Write-Host "Press any key to stop ARHIEA..." -ForegroundColor Yellow
$null = [System.Console]::ReadKey($true)

Stop-Process -Id $backend.Id -Force -ErrorAction SilentlyContinue
Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*uvicorn*" } | Stop-Process -Force -ErrorAction SilentlyContinue
Write-Host "ARHIEA stopped cleanly." -ForegroundColor Gray
