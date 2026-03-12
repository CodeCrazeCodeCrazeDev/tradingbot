# Trading Bot Monitoring Dashboard
# Run this script to get a real-time view of bot status

param(
    [int]$RefreshSeconds = 10,
    [switch]$Continuous
)

function Show-BotStatus {
    Clear-Host
    Write-Host "=" -NoNewline -ForegroundColor Cyan
    Write-Host ("=" * 78) -ForegroundColor Cyan
    Write-Host "  TRADING BOT MONITORING DASHBOARD" -ForegroundColor Yellow
    Write-Host "=" -NoNewline -ForegroundColor Cyan
    Write-Host ("=" * 78) -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
    Write-Host ""

    # Check if bot is running
    $pythonProcesses = Get-Process | Where-Object {$_.ProcessName -like '*python*'}
    
    if ($pythonProcesses) {
        Write-Host "  BOT STATUS: " -NoNewline
        Write-Host "RUNNING" -ForegroundColor Green
        Write-Host ""
        
        foreach ($proc in $pythonProcesses) {
            Write-Host "  Process Details:" -ForegroundColor Cyan
            Write-Host "    PID:        $($proc.Id)"
            Write-Host "    Name:       $($proc.ProcessName)"
            Write-Host "    CPU:        $([math]::Round($proc.CPU, 2))%"
            Write-Host "    Memory:     $([math]::Round($proc.PM / 1MB, 2)) MB"
            Write-Host "    Start Time: $($proc.StartTime)"
            
            if ($proc.StartTime) {
                $uptime = (Get-Date) - $proc.StartTime
                Write-Host "    Uptime:     $($uptime.Hours)h $($uptime.Minutes)m $($uptime.Seconds)s"
            }
            Write-Host ""
        }
    } else {
        Write-Host "  BOT STATUS: " -NoNewline
        Write-Host "NOT RUNNING" -ForegroundColor Red
        Write-Host ""
        Write-Host "  To start the bot, run:" -ForegroundColor Yellow
        Write-Host "    py main.py --mode paper --symbol EURUSD --timeframe H1 --bars 200"
        Write-Host ""
    }

    # Recent trades
    Write-Host "  RECENT TRADES:" -ForegroundColor Cyan
    if (Test-Path "logs\stderr_correct.log") {
        $recentTrades = Get-Content "logs\stderr_correct.log" -Tail 100 | 
                        Select-String "Paper trade executed" | 
                        Select-Object -Last 5
        
        if ($recentTrades) {
            foreach ($trade in $recentTrades) {
                $tradeLine = $trade.Line
                if ($tradeLine -match "(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}).*Paper trade executed: (\w+) (\w+) ([\d.]+) lots") {
                    $time = $matches[1]
                    $symbol = $matches[2]
                    $direction = $matches[3]
                    $size = $matches[4]
                    
                    $dirColor = if ($direction -eq "BUY") { "Green" } else { "Red" }
                    Write-Host "    [$time] " -NoNewline
                    Write-Host "$symbol " -NoNewline -ForegroundColor Yellow
                    Write-Host "$direction " -NoNewline -ForegroundColor $dirColor
                    Write-Host "$size lots"
                }
            }
        } else {
            Write-Host "    No trades found in recent logs" -ForegroundColor Gray
        }
    } else {
        Write-Host "    Log file not found" -ForegroundColor Gray
    }
    Write-Host ""

    # Recent errors
    Write-Host "  RECENT ERRORS:" -ForegroundColor Cyan
    if (Test-Path "logs\stderr_correct.log") {
        $recentErrors = Get-Content "logs\stderr_correct.log" -Tail 200 | 
                        Select-String "ERROR" | 
                        Select-Object -Last 3
        
        if ($recentErrors) {
            foreach ($error in $recentErrors) {
                Write-Host "    $($error.Line)" -ForegroundColor Red
            }
        } else {
            Write-Host "    No errors detected" -ForegroundColor Green
        }
    } else {
        Write-Host "    Log file not found" -ForegroundColor Gray
    }
    Write-Host ""

    # Statistics
    Write-Host "  STATISTICS:" -ForegroundColor Cyan
    if (Test-Path "logs\stderr_correct.log") {
        $totalTrades = (Get-Content "logs\stderr_correct.log" | 
                       Select-String "Paper trade executed" | 
                       Measure-Object).Count
        
        $totalErrors = (Get-Content "logs\stderr_correct.log" | 
                       Select-String "ERROR" | 
                       Measure-Object).Count
        
        Write-Host "    Total Trades: $totalTrades"
        Write-Host "    Total Errors: $totalErrors"
        
        if ($totalTrades -gt 0) {
            $errorRate = [math]::Round(($totalErrors / $totalTrades) * 100, 2)
            Write-Host "    Error Rate:   $errorRate%"
        }
    }
    Write-Host ""

    # Health indicators
    Write-Host "  HEALTH INDICATORS:" -ForegroundColor Cyan
    
    $healthChecks = @()
    
    # Check 1: Bot running
    if ($pythonProcesses) {
        $healthChecks += @{Status="OK"; Message="Bot process running"}
    } else {
        $healthChecks += @{Status="FAIL"; Message="Bot not running"}
    }
    
    # Check 2: Recent activity
    if (Test-Path "logs\stderr_correct.log") {
        $lastWrite = (Get-Item "logs\stderr_correct.log").LastWriteTime
        $timeSinceUpdate = (Get-Date) - $lastWrite
        
        if ($timeSinceUpdate.TotalMinutes -lt 1) {
            $healthChecks += @{Status="OK"; Message="Recent log activity"}
        } else {
            $healthChecks += @{Status="WARN"; Message="No recent log activity ($([math]::Round($timeSinceUpdate.TotalMinutes, 1)) min)"}
        }
    }
    
    # Check 3: Error rate
    if ($totalErrors -eq 0) {
        $healthChecks += @{Status="OK"; Message="No errors detected"}
    } elseif ($totalErrors -lt 10) {
        $healthChecks += @{Status="WARN"; Message="$totalErrors errors detected"}
    } else {
        $healthChecks += @{Status="FAIL"; Message="$totalErrors errors detected"}
    }
    
    # Display health checks
    foreach ($check in $healthChecks) {
        $statusColor = switch ($check.Status) {
            "OK" { "Green" }
            "WARN" { "Yellow" }
            "FAIL" { "Red" }
        }
        
        Write-Host "    [$($check.Status)] " -NoNewline -ForegroundColor $statusColor
        Write-Host $check.Message
    }
    
    Write-Host ""
    Write-Host "=" -NoNewline -ForegroundColor Cyan
    Write-Host ("=" * 78) -ForegroundColor Cyan
    
    if ($Continuous) {
        Write-Host ""
        Write-Host "  Refreshing in $RefreshSeconds seconds... (Press Ctrl+C to stop)" -ForegroundColor Gray
    }
}

# Main execution
if ($Continuous) {
    while ($true) {
        Show-BotStatus
        Start-Sleep -Seconds $RefreshSeconds
    }
} else {
    Show-BotStatus
}
