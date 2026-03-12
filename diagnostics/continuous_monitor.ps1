# Continuous Bot Monitoring Script
# Monitors bot for 30 minutes with health checks every 3 minutes

param(
    [int]$ProcessId = 12140,
    [int]$DurationMinutes = 30,
    [int]$CheckIntervalSeconds = 180
)

$startTime = Get-Date
$endTime = $startTime.AddMinutes($DurationMinutes)
$checkCount = 0
$healthHistory = @()

Write-Host "=== CONTINUOUS MONITORING STARTED ===" -ForegroundColor Cyan
Write-Host "Process ID: $ProcessId" -ForegroundColor Gray
Write-Host "Duration: $DurationMinutes minutes" -ForegroundColor Gray
Write-Host "Check Interval: $CheckIntervalSeconds seconds" -ForegroundColor Gray
Write-Host "Start Time: $($startTime.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Gray
Write-Host "End Time: $($endTime.ToString('yyyy-MM-dd HH:mm:ss'))" -ForegroundColor Gray
Write-Host ""

while ((Get-Date) -lt $endTime) {
    $checkCount++
    $currentTime = Get-Date
    $elapsed = ($currentTime - $startTime).TotalMinutes
    
    Write-Host "[$checkCount] Health Check at $($currentTime.ToString('HH:mm:ss')) (Elapsed: $([math]::Round($elapsed, 1)) min)" -ForegroundColor Yellow
    
    # Quick health check
    $healthStatus = @{
        timestamp = $currentTime.ToString('yyyy-MM-dd HH:mm:ss')
        check_number = $checkCount
        process_alive = $false
        cpu_pct = 0
        memory_mb = 0
        recent_trades = 0
        errors_in_last_check = 0
    }
    
    # Check if process is alive
    try {
        $process = Get-Process -Id $ProcessId -ErrorAction Stop
        $healthStatus.process_alive = $true
        $healthStatus.cpu_pct = [math]::Round($process.CPU, 2)
        $healthStatus.memory_mb = [math]::Round($process.WorkingSet64/1MB, 2)
        
        Write-Host "  ✅ Process alive - CPU: $($healthStatus.cpu_pct)s, Memory: $($healthStatus.memory_mb) MB" -ForegroundColor Green
    } catch {
        Write-Host "  ❌ CRITICAL: Process $ProcessId has stopped!" -ForegroundColor Red
        $healthStatus.process_alive = $false
        
        # Log critical failure
        $criticalMsg = "[$($currentTime.ToString('yyyy-MM-dd HH:mm:ss'))] CRITICAL: Bot process $ProcessId stopped unexpectedly"
        Add-Content -Path "diagnostics\CRITICAL-ISSUE-$($currentTime.ToString('yyyyMMdd-HHmmss')).md" -Value $criticalMsg
        
        Write-Host "`n=== MONITORING STOPPED DUE TO PROCESS FAILURE ===" -ForegroundColor Red
        break
    }
    
    # Check recent trades
    if (Test-Path "logs\stderr_with_validator.log") {
        $recentLog = Get-Content "logs\stderr_with_validator.log" -Tail 50 -ErrorAction SilentlyContinue
        $tradeLines = $recentLog | Select-String "Paper trade executed" -CaseSensitive:$false
        $healthStatus.recent_trades = $tradeLines.Count
        
        # Check for errors
        $errorLines = $recentLog | Select-String "error|exception|fail" -CaseSensitive:$false
        $healthStatus.errors_in_last_check = $errorLines.Count
        
        Write-Host "  Recent trades: $($healthStatus.recent_trades)" -ForegroundColor Gray
        if ($healthStatus.errors_in_last_check -gt 0) {
            Write-Host "  ⚠️ Errors detected: $($healthStatus.errors_in_last_check)" -ForegroundColor Yellow
        }
    }
    
    $healthHistory += $healthStatus
    
    # Wait for next check (unless this is the last iteration)
    $remaining = ($endTime - (Get-Date)).TotalSeconds
    if ($remaining -gt 0) {
        $waitTime = [math]::Min($CheckIntervalSeconds, $remaining)
        if ($waitTime -gt 0) {
            Write-Host "  Next check in $([math]::Round($waitTime, 0)) seconds..." -ForegroundColor Gray
            Write-Host ""
            Start-Sleep -Seconds $waitTime
        }
    }
}

# Final summary
Write-Host "`n=== MONITORING COMPLETE ===" -ForegroundColor Cyan
Write-Host "Total Checks: $checkCount" -ForegroundColor Gray
Write-Host "Duration: $([math]::Round(((Get-Date) - $startTime).TotalMinutes, 1)) minutes" -ForegroundColor Gray

$aliveChecks = ($healthHistory | Where-Object { $_.process_alive -eq $true }).Count
$totalTrades = ($healthHistory | Measure-Object -Property recent_trades -Sum).Sum
$totalErrors = ($healthHistory | Measure-Object -Property errors_in_last_check -Sum).Sum

Write-Host "`nSummary:" -ForegroundColor Yellow
Write-Host "  Process Alive: $aliveChecks/$checkCount checks" -ForegroundColor $(if ($aliveChecks -eq $checkCount) { "Green" } else { "Red" })
Write-Host "  Total Trades Observed: $totalTrades" -ForegroundColor Gray
Write-Host "  Total Errors: $totalErrors" -ForegroundColor $(if ($totalErrors -gt 10) { "Yellow" } else { "Green" })

# Save history
$historyJson = $healthHistory | ConvertTo-Json -Depth 5
$historyPath = "diagnostics\monitoring-history-$($startTime.ToString('yyyyMMdd-HHmmss')).json"
$historyJson | Out-File $historyPath -Encoding UTF8
Write-Host "`nMonitoring history saved to: $historyPath" -ForegroundColor Cyan

# Update changes log
$logEntry = "[$($startTime.ToString('yyyy-MM-dd HH:mm:ss'))] MONITORING: Completed $checkCount health checks over $([math]::Round(((Get-Date) - $startTime).TotalMinutes, 1)) minutes. Process alive: $aliveChecks/$checkCount"
Add-Content -Path "diagnostics\changes-log.txt" -Value $logEntry
