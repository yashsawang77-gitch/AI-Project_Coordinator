Write-Host "========================================================" -ForegroundColor Cyan
Write-Host " Syncora AI - College Hackathon Coordinator Backend" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""
Set-Location -Path "$PSScriptRoot\backend"
py run_server.py
