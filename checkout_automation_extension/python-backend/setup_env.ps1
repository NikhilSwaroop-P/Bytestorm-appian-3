# AI Checkout Automation - Environment Setup Script
# This script helps set up the required environment variables

param(
    [Parameter(Mandatory=$false)]
    [string]$ApiKey
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AI Checkout Automation Environment Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if API key was provided as parameter
if (-not $ApiKey) {
    Write-Host "Please enter your Google AI API Key:" -ForegroundColor Yellow
    Write-Host "(Get one from: https://makersuite.google.com/app/apikey)"
    Write-Host ""
    $ApiKey = Read-Host "API Key"
}

if (-not $ApiKey) {
    Write-Host "❌ No API key provided. Exiting." -ForegroundColor Red
    exit 1
}

# Validate API key format (basic check)
if ($ApiKey.Length -lt 20) {
    Write-Host "⚠️  Warning: API key seems too short. Please verify it's correct." -ForegroundColor Yellow
}

try {
    # Set environment variable for current session
    $env:GOOGLE_API_KEY = $ApiKey
    Write-Host "✅ Environment variable set for current session" -ForegroundColor Green
    
    # Set environment variable persistently for user
    [Environment]::SetEnvironmentVariable("GOOGLE_API_KEY", $ApiKey, "User")
    Write-Host "✅ Environment variable set persistently for user account" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "✅ Setup completed successfully!" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Your Google AI API key has been configured." -ForegroundColor White
    Write-Host "You can now run the server with: .\start_server.bat" -ForegroundColor White
    Write-Host ""
    Write-Host "⚠️  Note: You may need to restart PowerShell for" -ForegroundColor Yellow
    Write-Host "   the persistent environment variable to take effect." -ForegroundColor Yellow
    
} catch {
    Write-Host "❌ Error setting environment variable: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
    Write-Host "You can manually set it with:" -ForegroundColor Yellow
    Write-Host "`$env:GOOGLE_API_KEY = '$ApiKey'" -ForegroundColor White
    exit 1
}

Write-Host ""
Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
