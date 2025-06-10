# Bytestorm AI - Complete Application Launcher
# This script starts both the main application and the checkout automation server in separate windows

Write-Host "==================================================="
Write-Host "Bytestorm AI - Complete Application Launcher"
Write-Host "==================================================="

# Get the current directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Start the main application in a new PowerShell window
Write-Host "Starting main application in a new window..."
Start-Process powershell.exe -ArgumentList "-NoExit -Command `"& {Set-Location '$scriptDir'; .\run.bat}`""

# Start the checkout automation server in a new PowerShell window
Write-Host "Starting checkout automation server in a new window..."
Start-Process powershell.exe -ArgumentList "-NoExit -Command `"& {Set-Location '$scriptDir\checkout_automation_extension\python-backend'; .\start_server.bat}`""

Write-Host "Both applications have been started in separate windows."
Write-Host "Main application URL: http://localhost:3000"
Write-Host "Checkout automation server URL: http://localhost:5000"
Write-Host ""
Write-Host "You can close this window now."
