@echo off
REM Bytestorm AI - Complete Application Launcher
REM This script starts both the main application and the checkout automation server

echo ===================================================
echo Bytestorm AI - Complete Application Launcher
echo ===================================================

REM Start the PowerShell script with execution policy bypass to ensure it runs
powershell.exe -ExecutionPolicy Bypass -File "%~dp0start_all.ps1"

REM Keep this window open until the user closes it
pause
