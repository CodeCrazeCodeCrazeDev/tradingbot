# Bot Monitoring and Startup Script
# Created by System Operator AI - 2025-10-07

$ErrorActionPreference = "Continue"
$logFile = "logs\runtime.log"
$summaryLog = "logs\operator_summary.log"

# Function to log with timestamp
function Write-Log {
    param($Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] $Message"
    Write-Host $logMessage
    Add-Content -Path $logFile -Value $logMessage
    Add-Content -Path $summaryLog -Value $logMessage
}

# Clear previous runtime log
if (Test-Path $logFile) {
    Remove-Item $logFile -Force
}

Write-Log "=== BOT STARTUP INITIATED ==="
Write-Log "Mode: Paper Trading (SAFE)"
Write-Log "Command: py main.py --mode paper --symbol EURUSD --timeframe H1 --bars 200"
Write-Log ""

# Start the bot and capture output
Write-Log "Starting bot process..."
$process = Start-Process -FilePath "py" -ArgumentList "main.py --mode paper --symbol EURUSD --timeframe H1 --bars 200" -PassThru -NoNewWindow -RedirectStandardOutput "logs\stdout.log" -RedirectStandardError "logs\stderr.log"

if ($process) {
    Write-Log "✅ Bot started successfully"
    Write-Log "Process ID: $($process.Id)"
    Write-Log "Process Name: $($process.ProcessName)"
    
    # Save PID for monitoring
    $process.Id | Out-File -FilePath "logs\bot.pid" -Force
    
    Write-Log ""
    Write-Log "Bot is now running. Monitor logs at:"
    Write-Log "  - Runtime: logs\runtime.log"
    Write-Log "  - Stdout: logs\stdout.log"
    Write-Log "  - Stderr: logs\stderr.log"
    Write-Log ""
    Write-Log "Process will be monitored for 30 minutes..."
    
} else {
    Write-Log "❌ Failed to start bot process"
    exit 1
}
