Write-Host "Checking for Python processes..."
$pythonProcesses = Get-Process | Where-Object { $_.ProcessName -like '*python*' -or $_.ProcessName -eq 'py' }

if ($pythonProcesses) {
    Write-Host "Found $($pythonProcesses.Count) Python process(es):"
    $pythonProcesses | Select-Object Id, ProcessName, StartTime, CPU, @{Name='MemoryMB';Expression={[math]::Round($_.WorkingSet64/1MB, 2)}} | Format-Table -AutoSize
} else {
    Write-Host "No Python processes currently running"
}

# Check if bot.pid file exists
if (Test-Path "logs\bot.pid") {
    $pid = Get-Content "logs\bot.pid"
    Write-Host "`nPrevious bot PID from logs\bot.pid: $pid"
    try {
        $process = Get-Process -Id $pid -ErrorAction Stop
        Write-Host "✅ Process $pid is still running: $($process.ProcessName)"
    } catch {
        Write-Host "❌ Process $pid is no longer running"
    }
}
