param(
    [int]$ProcessId = 12140,
    [string]$OutputFile = "diagnostics\health-20251008-003941.json"
)

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Write-Host "=== HEALTH CHECK STARTED: $timestamp ===" -ForegroundColor Cyan

$healthData = @{
    timestamp = $timestamp
    process_check = @{}
    resource_check = @{}
    log_check = @{}
    disk_check = @{}
    connectivity_check = @{}
    trading_check = @{}
    overall_status = "UNKNOWN"
}

# 1. Process Check
Write-Host "`n[1/7] Checking process health..." -ForegroundColor Yellow
try {
    $process = Get-Process -Id $ProcessId -ErrorAction Stop
    $uptime = (Get-Date) - $process.StartTime
    $healthData.process_check = @{
        status = "RUNNING"
        pid = $ProcessId
        name = $process.ProcessName
        start_time = $process.StartTime.ToString("yyyy-MM-dd HH:mm:ss")
        uptime_minutes = [math]::Round($uptime.TotalMinutes, 2)
        cpu_seconds = [math]::Round($process.CPU, 2)
        memory_mb = [math]::Round($process.WorkingSet64/1MB, 2)
        threads = $process.Threads.Count
    }
    Write-Host "  ✅ Process $ProcessId is running" -ForegroundColor Green
    Write-Host "  Uptime: $([math]::Round($uptime.TotalMinutes, 1)) minutes" -ForegroundColor Gray
    Write-Host "  Memory: $([math]::Round($process.WorkingSet64/1MB, 2)) MB" -ForegroundColor Gray
} catch {
    $healthData.process_check = @{
        status = "NOT_RUNNING"
        error = $_.Exception.Message
    }
    Write-Host "  ❌ Process $ProcessId is not running" -ForegroundColor Red
}

# 2. Resource Check
Write-Host "`n[2/7] Checking resource usage..." -ForegroundColor Yellow
try {
    $cpu = Get-Counter '\Processor(_Total)\% Processor Time' -ErrorAction Stop
    $cpuUsage = [math]::Round($cpu.CounterSamples[0].CookedValue, 2)
    
    $mem = Get-CimInstance Win32_OperatingSystem
    $totalMemGB = [math]::Round($mem.TotalVisibleMemorySize/1MB, 2)
    $freeMemGB = [math]::Round($mem.FreePhysicalMemory/1MB, 2)
    $usedMemGB = $totalMemGB - $freeMemGB
    $memUsagePct = [math]::Round(($usedMemGB / $totalMemGB) * 100, 2)
    
    $healthData.resource_check = @{
        cpu_usage_pct = $cpuUsage
        memory_total_gb = $totalMemGB
        memory_used_gb = $usedMemGB
        memory_usage_pct = $memUsagePct
        status = if ($cpuUsage -gt 90 -or $memUsagePct -gt 90) { "WARNING" } else { "OK" }
    }
    
    Write-Host "  CPU: $cpuUsage%" -ForegroundColor $(if ($cpuUsage -gt 80) { "Yellow" } else { "Green" })
    Write-Host "  Memory: $memUsagePct% ($usedMemGB GB / $totalMemGB GB)" -ForegroundColor $(if ($memUsagePct -gt 80) { "Yellow" } else { "Green" })
} catch {
    $healthData.resource_check = @{ status = "ERROR"; error = $_.Exception.Message }
    Write-Host "  ⚠️ Could not check resources" -ForegroundColor Yellow
}

# 3. Disk Check
Write-Host "`n[3/7] Checking disk usage..." -ForegroundColor Yellow
try {
    $drive = Get-PSDrive C
    $totalGB = [math]::Round($drive.Used/1GB + $drive.Free/1GB, 2)
    $usedGB = [math]::Round($drive.Used/1GB, 2)
    $freeGB = [math]::Round($drive.Free/1GB, 2)
    $usagePct = [math]::Round(($usedGB / $totalGB) * 100, 2)
    
    $healthData.disk_check = @{
        drive = "C:"
        total_gb = $totalGB
        used_gb = $usedGB
        free_gb = $freeGB
        usage_pct = $usagePct
        status = if ($usagePct -gt 90) { "CRITICAL" } elseif ($usagePct -gt 80) { "WARNING" } else { "OK" }
    }
    
    Write-Host "  Disk C: $usagePct% used ($freeGB GB free)" -ForegroundColor $(if ($usagePct -gt 80) { "Yellow" } else { "Green" })
} catch {
    $healthData.disk_check = @{ status = "ERROR"; error = $_.Exception.Message }
}

# 4. Log Check
Write-Host "`n[4/7] Checking logs..." -ForegroundColor Yellow
$logFiles = @("logs\stderr_with_validator.log", "logs\stderr.log", "logs\stdout.log", "logs\runtime.log")
$logErrors = @()
$logWarnings = @()

foreach ($logFile in $logFiles) {
    if (Test-Path $logFile) {
        $recentLines = Get-Content $logFile -Tail 100 -ErrorAction SilentlyContinue
        if ($recentLines) {
            $errors = $recentLines | Select-String -Pattern "error|exception|traceback|fail|fatal" -CaseSensitive:$false
            $warnings = $recentLines | Select-String -Pattern "warning|warn" -CaseSensitive:$false
            
            if ($errors) { $logErrors += @{ file = $logFile; count = $errors.Count } }
            if ($warnings) { $logWarnings += @{ file = $logFile; count = $warnings.Count } }
        }
    }
}

$healthData.log_check = @{
    files_checked = $logFiles.Count
    errors_found = ($logErrors | Measure-Object -Property count -Sum).Sum
    warnings_found = ($logWarnings | Measure-Object -Property count -Sum).Sum
    status = if (($logErrors | Measure-Object -Property count -Sum).Sum -gt 10) { "WARNING" } else { "OK" }
}

Write-Host "  Errors in logs: $(($logErrors | Measure-Object -Property count -Sum).Sum)" -ForegroundColor $(if (($logErrors | Measure-Object -Property count -Sum).Sum -gt 10) { "Yellow" } else { "Green" })
Write-Host "  Warnings in logs: $(($logWarnings | Measure-Object -Property count -Sum).Sum)" -ForegroundColor Gray

# 5. Connectivity Check
Write-Host "`n[5/7] Checking connectivity..." -ForegroundColor Yellow
$connectivityTests = @()

# DNS test
try {
    $dns = Resolve-DnsName google.com -ErrorAction Stop
    $connectivityTests += @{ test = "DNS"; status = "OK" }
    Write-Host "  ✅ DNS resolution working" -ForegroundColor Green
} catch {
    $connectivityTests += @{ test = "DNS"; status = "FAIL"; error = $_.Exception.Message }
    Write-Host "  ❌ DNS resolution failed" -ForegroundColor Red
}

# Internet connectivity test
try {
    $response = Invoke-WebRequest -Uri "https://www.google.com" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
    $connectivityTests += @{ test = "Internet"; status = "OK"; response_code = $response.StatusCode }
    Write-Host "  ✅ Internet connectivity OK" -ForegroundColor Green
} catch {
    $connectivityTests += @{ test = "Internet"; status = "FAIL"; error = $_.Exception.Message }
    Write-Host "  ⚠️ Internet connectivity issue" -ForegroundColor Yellow
}

$healthData.connectivity_check = @{
    tests = $connectivityTests
    status = if ($connectivityTests | Where-Object { $_.status -eq "FAIL" }) { "WARNING" } else { "OK" }
}

# 6. Trading Check
Write-Host "`n[6/7] Checking trading activity..." -ForegroundColor Yellow
$tradingData = @{
    position_validator = "Unknown"
    recent_trades = 0
    position_sizes = @()
    status = "UNKNOWN"
}

if (Test-Path "logs\stderr_with_validator.log") {
    $recentLog = Get-Content "logs\stderr_with_validator.log" -Tail 200 -ErrorAction SilentlyContinue
    
    # Check for validator
    $validatorLines = $recentLog | Select-String "validator|VALIDATOR" -CaseSensitive:$false
    if ($validatorLines) {
        $tradingData.position_validator = "ACTIVE"
        Write-Host "  ✅ Position validator: ACTIVE" -ForegroundColor Green
    }
    
    # Check for recent trades
    $tradeLines = $recentLog | Select-String "Paper trade executed|trade executed" -CaseSensitive:$false
    if ($tradeLines) {
        $tradingData.recent_trades = $tradeLines.Count
        Write-Host "  Recent trades: $($tradeLines.Count)" -ForegroundColor Gray
    }
    
    # Check position sizes
    $positionLines = $recentLog | Select-String "position.*size|lots" -CaseSensitive:$false | Select-Object -First 10
    if ($positionLines) {
        $tradingData.position_sizes = @($positionLines | ForEach-Object { $_.Line })
    }
    
    $tradingData.status = "OK"
}

$healthData.trading_check = $tradingData

# 7. Overall Status
Write-Host "`n[7/7] Computing overall status..." -ForegroundColor Yellow

$criticalIssues = 0
$warnings = 0

if ($healthData.process_check.status -ne "RUNNING") { $criticalIssues++ }
if ($healthData.resource_check.status -eq "WARNING") { $warnings++ }
if ($healthData.disk_check.status -eq "CRITICAL") { $criticalIssues++ }
if ($healthData.disk_check.status -eq "WARNING") { $warnings++ }
if ($healthData.log_check.status -eq "WARNING") { $warnings++ }
if ($healthData.connectivity_check.status -eq "WARNING") { $warnings++ }

if ($criticalIssues -gt 0) {
    $healthData.overall_status = "CRITICAL"
    $statusColor = "Red"
} elseif ($warnings -gt 0) {
    $healthData.overall_status = "WARNING"
    $statusColor = "Yellow"
} else {
    $healthData.overall_status = "OK"
    $statusColor = "Green"
}

$healthData.summary = @{
    critical_issues = $criticalIssues
    warnings = $warnings
    checks_passed = 7 - $criticalIssues - $warnings
    total_checks = 7
}

# Save to JSON
$healthJson = $healthData | ConvertTo-Json -Depth 10
$healthJson | Out-File $OutputFile -Encoding UTF8

Write-Host "`n=== OVERALL STATUS: $($healthData.overall_status) ===" -ForegroundColor $statusColor
Write-Host "Critical Issues: $criticalIssues" -ForegroundColor $(if ($criticalIssues -gt 0) { "Red" } else { "Green" })
Write-Host "Warnings: $warnings" -ForegroundColor $(if ($warnings -gt 0) { "Yellow" } else { "Green" })
Write-Host "Checks Passed: $($healthData.summary.checks_passed)/7" -ForegroundColor Green
Write-Host "`nHealth report saved to: $OutputFile" -ForegroundColor Cyan
