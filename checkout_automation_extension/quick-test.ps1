# Troubleshooting Quick Test

Use the commands below to quickly test the different components of the AI Checkout Extension.

```powershell
# 1. Test the server health
Invoke-WebRequest -Uri http://localhost:5000/health -Method GET

# 2. Create a simple health check file for debugging
$healthContent = Invoke-WebRequest -Uri http://localhost:5000/health -Method GET | Select-Object -ExpandProperty Content
$healthContent | Out-File -FilePath "$PWD\server-health-test.json" -Encoding utf8

# 3. Start the server if it's not running
$serverProcess = Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*server.py*" }
if (-not $serverProcess) {
    Write-Host "Server not running. Starting server..."
    Start-Process -FilePath "powershell.exe" -ArgumentList "-NoProfile -ExecutionPolicy Bypass -File .\python-backend\start_server.bat" -WindowStyle Normal
    Start-Sleep -Seconds 3
    Write-Host "Server started. Checking health again..."
    Invoke-WebRequest -Uri http://localhost:5000/health -Method GET
}

# 4. Test the process-checkout endpoint with a minimal payload
$testPayload = @{
    html = "<html><body><form><input type='text' id='name'></form></body></html>"
    url = "http://example.com/checkout"
    user_profile = @{
        name = "Test User"
        email = "test@example.com"
    }
} | ConvertTo-Json

$processResult = Invoke-WebRequest -Uri http://localhost:5000/process-checkout -Method POST -Body $testPayload -ContentType "application/json" -ErrorAction SilentlyContinue
if ($processResult) {
    Write-Host "Process-checkout endpoint test: SUCCESS"
    $processResult.Content | Out-File -FilePath "$PWD\process-checkout-test.json" -Encoding utf8
} else {
    Write-Host "Process-checkout endpoint test: FAILED"
}

Write-Host "Test complete. Check the JSON files for results."
```

Save this to a file named `quick-test.ps1` and run it to verify the server is working correctly.
