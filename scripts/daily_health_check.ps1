# Daily Health Check Script
# Run this once per day to track bot progress toward live trading readiness

param(
    [string]$OutputFile = "logs\daily_health_log.txt"
)

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$date = Get-Date -Format "yyyy-MM-dd"

Write-Host "`n===============================================================================" -ForegroundColor Cyan
Write-Host "  DAILY HEALTH CHECK - $date" -ForegroundColor Yellow
Write-Host "===============================================================================`n" -ForegroundColor Cyan

# Initialize report
$report = @"

================================================================================
DAILY HEALTH CHECK REPORT
================================================================================
Date: $timestamp

"@

# Check if bot is running
$pythonProcesses = Get-Process | Where-Object {$_.ProcessName -like '*python*'}

if ($pythonProcesses) {
    $mainBot = $pythonProcesses | Where-Object {$_.PM -gt 500MB} | Select-Object -First 1
    
    if ($mainBot) {
        $uptime = (Get-Date) - $mainBot.StartTime
        $uptimeStr = "$($uptime.Days)d $($uptime.Hours)h $($uptime.Minutes)m"
        
        Write-Host "  BOT STATUS: " -NoNewline
        Write-Host "RUNNING" -ForegroundColor Green
        Write-Host "    PID:        $($mainBot.Id)"
        Write-Host "    Uptime:     $uptimeStr"
        Write-Host "    CPU:        $([math]::Round($mainBot.CPU, 2))%"
        Write-Host "    Memory:     $([math]::Round($mainBot.PM / 1MB, 2)) MB"
        
        $report += @"
BOT STATUS: RUNNING
  Process ID: $($mainBot.Id)
  Uptime: $uptimeStr
  CPU Usage: $([math]::Round($mainBot.CPU, 2))%
  Memory: $([math]::Round($mainBot.PM / 1MB, 2)) MB

"@
    }
} else {
    Write-Host "  BOT STATUS: " -NoNewline
    Write-Host "NOT RUNNING" -ForegroundColor Red
    
    $report += @"
BOT STATUS: NOT RUNNING
  WARNING: Bot should be running for extended testing

"@
}

Write-Host ""

# Check logs
$logFile = "logs\stderr_with_validator.log"
if (Test-Path $logFile) {
    # Count trades
    $totalTrades = (Get-Content $logFile | Select-String "Paper trade executed" | Measure-Object).Count
    
    # Count errors
    $totalErrors = (Get-Content $logFile | Select-String "ERROR" | Measure-Object).Count
    
    # Check position sizes
    $recentTrades = Get-Content $logFile | Select-String "Paper trade executed" | Select-Object -Last 20
    $positionSizes = @()
    
    foreach ($trade in $recentTrades) {
        if ($trade.Line -match "(\d+\.?\d*) lots") {
            $positionSizes += [decimal]$matches[1]
        }
    }
    
    $avgPosition = if ($positionSizes.Count -gt 0) {
        ($positionSizes | Measure-Object -Average).Average
    } else { 0 }
    
    $maxPosition = if ($positionSizes.Count -gt 0) {
        ($positionSizes | Measure-Object -Maximum).Maximum
    } else { 0 }
    
    Write-Host "  TRADING STATISTICS:" -ForegroundColor Cyan
    Write-Host "    Total Trades:    $totalTrades"
    Write-Host "    Total Errors:    $totalErrors"
    Write-Host "    Avg Position:    $([math]::Round($avgPosition, 2)) lots"
    Write-Host "    Max Position:    $maxPosition lots"
    
    if ($totalTrades -gt 0) {
        $errorRate = [math]::Round(($totalErrors / $totalTrades) * 100, 2)
        Write-Host "    Error Rate:      $errorRate%"
        
        $report += @"
TRADING STATISTICS:
  Total Trades: $totalTrades
  Total Errors: $totalErrors
  Error Rate: $errorRate%
  Avg Position Size: $([math]::Round($avgPosition, 2)) lots
  Max Position Size: $maxPosition lots

"@
    }
}

Write-Host ""

# Position Size Validation
Write-Host "  POSITION SIZE VALIDATION:" -ForegroundColor Cyan
if ($maxPosition -le 1.0) {
    Write-Host "    [PASS] All positions <= 1.0 lots" -ForegroundColor Green
    $report += "POSITION SIZE VALIDATION: PASS (max: $maxPosition lots)`n"
} elseif ($maxPosition -le 2.0) {
    Write-Host "    [WARN] Some positions > 1.0 lots (max: $maxPosition)" -ForegroundColor Yellow
    $report += "POSITION SIZE VALIDATION: WARNING (max: $maxPosition lots)`n"
} else {
    Write-Host "    [FAIL] Positions exceed safe limits (max: $maxPosition)" -ForegroundColor Red
    $report += "POSITION SIZE VALIDATION: FAIL (max: $maxPosition lots)`n"
}

Write-Host ""

# Calculate testing progress
$startDate = Get-Date "2025-10-08"
$currentDate = Get-Date
$daysRunning = ($currentDate - $startDate).Days
$targetDays = 14  # 2 weeks

$testingProgress = [math]::Min(100, [math]::Round(($daysRunning / $targetDays) * 100, 0))

Write-Host "  TESTING PROGRESS:" -ForegroundColor Cyan
Write-Host "    Days Running:    $daysRunning / $targetDays"
Write-Host "    Progress:        $testingProgress%"

$progressBar = ""
$filled = [math]::Floor($testingProgress / 5)
for ($i = 0; $i -lt 20; $i++) {
    if ($i -lt $filled) {
        $progressBar += "█"
    } else {
        $progressBar += "░"
    }
}
Write-Host "    [$progressBar] $testingProgress%" -ForegroundColor $(if ($testingProgress -ge 100) { "Green" } elseif ($testingProgress -ge 50) { "Yellow" } else { "Red" })

$report += @"
TESTING PROGRESS:
  Days Running: $daysRunning / $targetDays
  Progress: $testingProgress%

"@

Write-Host ""

# Live Trading Readiness Checklist
Write-Host "  LIVE TRADING READINESS:" -ForegroundColor Cyan

$checklist = @{
    "Technical Fixes" = 100
    "Position Validation" = 100
    "Paper Trading (2 weeks)" = $testingProgress
    "Broker Connection Test" = 0
    "Safety Mechanisms" = 0
    "Gradual Rollout Plan" = 0
}

$totalProgress = 0
foreach ($item in $checklist.GetEnumerator()) {
    $totalProgress += $item.Value
    $status = if ($item.Value -eq 100) { "[OK]" } elseif ($item.Value -gt 0) { "[..]" } else { "[ ]" }
    $color = if ($item.Value -eq 100) { "Green" } elseif ($item.Value -gt 0) { "Yellow" } else { "Red" }
    
    Write-Host "    [$status] " -NoNewline -ForegroundColor $color
    Write-Host "$($item.Key): $($item.Value)%"
}

$overallReadiness = [math]::Round($totalProgress / $checklist.Count, 0)
Write-Host "`n    Overall Readiness: $overallReadiness%" -ForegroundColor $(if ($overallReadiness -ge 80) { "Green" } elseif ($overallReadiness -ge 50) { "Yellow" } else { "Red" })

$report += @"
LIVE TRADING READINESS: $overallReadiness%
  Technical Fixes: 100%
  Position Validation: 100%
  Paper Trading: $testingProgress%
  Broker Connection: 0%
  Safety Mechanisms: 0%
  Gradual Rollout: 0%

"@

Write-Host ""

# Recommendations
Write-Host "  RECOMMENDATIONS:" -ForegroundColor Cyan

if ($daysRunning -lt 7) {
    Write-Host "    - Continue paper trading ($(7 - $daysRunning) days until week 1 complete)" -ForegroundColor Yellow
} elseif ($daysRunning -lt 14) {
    Write-Host "    - Continue paper trading ($(14 - $daysRunning) days until week 2 complete)" -ForegroundColor Yellow
    Write-Host "    - Begin testing real broker connection" -ForegroundColor Yellow
} else {
    Write-Host "    - Paper trading period complete!" -ForegroundColor Green
    Write-Host "    - Ready to implement safety mechanisms" -ForegroundColor Green
    Write-Host "    - Prepare for Phase 1 micro testing (0.01 lots)" -ForegroundColor Green
}

if ($totalErrors -gt 10) {
    Write-Host "    - WARNING: High error count - investigate logs" -ForegroundColor Red
}

if ($maxPosition -gt 1.0) {
    Write-Host "    - WARNING: Position sizes exceeding 1.0 lots - check validator" -ForegroundColor Red
}

$report += @"
RECOMMENDATIONS:
"@

if ($daysRunning -lt 14) {
    $report += "  - Continue paper trading ($(14 - $daysRunning) days remaining)`n"
} else {
    $report += "  - Paper trading complete - ready for next phase`n"
}

Write-Host ""
Write-Host "===============================================================================`n" -ForegroundColor Cyan

# Save report
$report += @"

================================================================================
Report saved: $timestamp
================================================================================

"@

Add-Content -Path $OutputFile -Value $report

Write-Host "  Report saved to: $OutputFile" -ForegroundColor Gray
Write-Host ""
