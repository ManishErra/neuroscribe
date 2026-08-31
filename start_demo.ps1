# NeuroScribe Local Demo Startup (Windows PowerShell)
# Run: .\start_demo.ps1

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  NeuroScribe Local Demo Startup" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Ensure client\.env points to local backend
$clientEnvPath = "client\.env"
if (Test-Path $clientEnvPath) {
    $clientContent = Get-Content $clientEnvPath -Raw
    $clientContent = $clientContent -replace "(?m)^VITE_API_URL=.*", "VITE_API_URL=http://localhost:8000"
    $clientContent | Set-Content $clientEnvPath -Encoding UTF8
    Write-Host "[OK] Frontend API URL set to http://localhost:8000" -ForegroundColor Green
}

# Ensure backend\.env uses local CORS
$backendEnvPath = "backend\.env"
if (Test-Path $backendEnvPath) {
    $backendContent = Get-Content $backendEnvPath -Raw
    $backendContent = $backendContent -replace "(?m)^CORS_ALLOWED_ORIGINS=.*", "CORS_ALLOWED_ORIGINS="
    $backendContent | Set-Content $backendEnvPath -Encoding UTF8
    Write-Host "[OK] Backend CORS set to local defaults (http://localhost:5173)" -ForegroundColor Green
}

Write-Host ""
Write-Host "STARTUP COMMANDS:" -ForegroundColor Yellow
Write-Host ""
Write-Host "  TERMINAL 1 (Backend):" -ForegroundColor Cyan
Write-Host "  cd backend" -ForegroundColor White
Write-Host "  python -m uvicorn main:app --host 0.0.0.0 --port 8000" -ForegroundColor White
Write-Host ""
Write-Host "  TERMINAL 2 (Frontend):" -ForegroundColor Cyan
Write-Host "  cd client" -ForegroundColor White
Write-Host "  npm run dev" -ForegroundColor White
Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "  LOCAL DEMO URL:" -ForegroundColor Cyan
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor White
Write-Host "  Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
