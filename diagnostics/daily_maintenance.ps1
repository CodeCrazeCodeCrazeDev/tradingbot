# Daily Maintenance Checklist
# Run once daily to maintain bot health

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$dateStamp = Get-Date -Format "yyyyMMdd"

Write-Host "=== DAILY MAINTENANCE - $timestamp ===" -ForegroundColor Cyan
Write-Host ""

$maintenanceLog = @{
    timestamp = $timestamp
    tasks = @()
}

# Task 1: Check for updates (non-destructive)
Write-Host "[1/6] Checking for configuration updates..." -ForegroundColor Yellow
$task1 = @{
    name = "Config Update Check"
    status = "SKIPPED"
    reason = "Automated deploy not configured"
}
Write-Host "  ⏭️ Skipped (manual review recommended)" -ForegroundColor Gray
$maintenanceLog.tasks += $task1

# Task 2: Run quick tests
Write-Host "`n[2/6] Running smoke tests..." -ForegroundColor Yellow
try {
    # Check if pytest is available
    $pytestCheck = py -m pytest --version 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Running quick validation tests..." -ForegroundColor Gray
        $testResult = py -m pytest tests/ -q --tb=no --timeout=30 2>&1
        $task2 = @{
            name = "Smoke Tests"
            status = if ($LASTEXITCODE -eq 0) { "PASS" } else { "FAIL" }
            output = $testResult | Out-String
        }
        Write-Host "  ✅ Tests completed" -ForegroundColor Green
    } else {
        $task2 = @{
            name = "Smoke Tests"
            status = "SKIPPED"
            reason = "pytest not available"
        }
        Write-Host "  ⏭️ Skipped (pytest not available)" -ForegroundColor Gray
    }
} catch {
    $task2 = @{
        name = "Smoke Tests"
        status = "ERROR"
        error = $_.Exception.Message
    }
    Write-Host "  ⚠️ Error running tests" -ForegroundColor Yellow
}
$maintenanceLog.tasks += $task2

# Task 3: Rotate logs
Write-Host "`n[3/6] Rotating logs..." -ForegroundColor Yellow
try {
    $logDir = "logs"
    $archiveDir = "logs\archive"
    
    if (-not (Test-Path $archiveDir)) {
        New-Item -ItemType Directory -Path $archiveDir -Force | Out-Null
    }
    
    # Find logs older than 30 days
    $oldLogs = Get-ChildItem $logDir -Filter *.log | Where-Object { 
        $_.LastWriteTime -lt (Get-Date).AddDays(-30) 
    }
    
    if ($oldLogs) {
        foreach ($log in $oldLogs) {
            Move-Item $log.FullName -Destination $archiveDir -Force
        }
        $task3 = @{
            name = "Log Rotation"
            status = "COMPLETED"
            logs_archived = $oldLogs.Count
        }
        Write-Host "  ✅ Archived $($oldLogs.Count) old log files" -ForegroundColor Green
    } else {
        $task3 = @{
            name = "Log Rotation"
            status = "COMPLETED"
            logs_archived = 0
        }
        Write-Host "  ✅ No old logs to archive" -ForegroundColor Green
    }
} catch {
    $task3 = @{
        name = "Log Rotation"
        status = "ERROR"
        error = $_.Exception.Message
    }
    Write-Host "  ⚠️ Error rotating logs" -ForegroundColor Yellow
}
$maintenanceLog.tasks += $task3

# Task 4: Check disk usage
Write-Host "`n[4/6] Checking disk usage..." -ForegroundColor Yellow
try {
    $drive = Get-PSDrive C
    $usagePct = [math]::Round(($drive.Used / ($drive.Used + $drive.Free)) * 100, 2)
    $freeGB = [math]::Round($drive.Free/1GB, 2)
    
    $task4 = @{
        name = "Disk Usage Check"
        status = if ($usagePct -gt 90) { "CRITICAL" } elseif ($usagePct -gt 80) { "WARNING" } else { "OK" }
        usage_pct = $usagePct
        free_gb = $freeGB
    }
    
    Write-Host "  Disk usage: $usagePct% ($freeGB GB free)" -ForegroundColor $(
        if ($usagePct -gt 90) { "Red" } elseif ($usagePct -gt 80) { "Yellow" } else { "Green" }
    )
} catch {
    $task4 = @{
        name = "Disk Usage Check"
        status = "ERROR"
        error = $_.Exception.Message
    }
}
$maintenanceLog.tasks += $task4

# Task 5: Dependency audit
Write-Host "`n[5/6] Auditing dependencies..." -ForegroundColor Yellow
try {
    $outdated = py -m pip list --outdated --format=json 2>&1 | ConvertFrom-Json
    $outdatedCount = $outdated.Count
    
    $task5 = @{
        name = "Dependency Audit"
        status = "COMPLETED"
        outdated_packages = $outdatedCount
        audit_file = "diagnostics\deps-audit-$dateStamp.json"
    }
    
    # Save audit results
    $outdated | ConvertTo-Json -Depth 5 | Out-File "diagnostics\deps-audit-$dateStamp.json" -Encoding UTF8
    
    Write-Host "  ✅ Found $outdatedCount outdated packages" -ForegroundColor $(if ($outdatedCount -gt 20) { "Yellow" } else { "Green" })
    Write-Host "  Audit saved to: diagnostics\deps-audit-$dateStamp.json" -ForegroundColor Gray
} catch {
    $task5 = @{
        name = "Dependency Audit"
        status = "ERROR"
        error = $_.Exception.Message
    }
    Write-Host "  ⚠️ Error auditing dependencies" -ForegroundColor Yellow
}
$maintenanceLog.tasks += $task5

# Task 6: Backup critical configs
Write-Host "`n[6/6] Backing up configurations..." -ForegroundColor Yellow
try {
    $backupPath = "diagnostics\backups\daily-backup-$dateStamp.zip"
    
    # Only backup if not already done today
    if (-not (Test-Path $backupPath)) {
        Compress-Archive -Path "config\*", "main.py" -DestinationPath $backupPath -Force
        $size = [math]::Round((Get-Item $backupPath).Length/1MB, 2)
        
        $task6 = @{
            name = "Config Backup"
            status = "COMPLETED"
            backup_path = $backupPath
            size_mb = $size
        }
        Write-Host "  ✅ Backup created: $size MB" -ForegroundColor Green
    } else {
        $task6 = @{
            name = "Config Backup"
            status = "SKIPPED"
            reason = "Backup already exists for today"
        }
        Write-Host "  ⏭️ Backup already exists for today" -ForegroundColor Gray
    }
} catch {
    $task6 = @{
        name = "Config Backup"
        status = "ERROR"
        error = $_.Exception.Message
    }
    Write-Host "  ⚠️ Error creating backup" -ForegroundColor Yellow
}
$maintenanceLog.tasks += $task6

# Run health check
Write-Host "`n[7/6] Running health check..." -ForegroundColor Yellow
& "diagnostics\health_monitor.ps1" -OutputFile "diagnostics\health-daily-$dateStamp.json"

# Save maintenance log
$maintenanceJson = $maintenanceLog | ConvertTo-Json -Depth 10
$maintenanceJson | Out-File "diagnostics\maintenance-$dateStamp.json" -Encoding UTF8

# Generate summary
Write-Host "`n=== DAILY MAINTENANCE COMPLETE ===" -ForegroundColor Cyan
$completedTasks = ($maintenanceLog.tasks | Where-Object { $_.status -eq "COMPLETED" -or $_.status -eq "PASS" -or $_.status -eq "OK" }).Count
$totalTasks = $maintenanceLog.tasks.Count
Write-Host "Tasks Completed: $completedTasks/$totalTasks" -ForegroundColor Green
Write-Host "Maintenance log: diagnostics\maintenance-$dateStamp.json" -ForegroundColor Gray
Write-Host ""

# Update changes log
$logEntry = "[$timestamp] DAILY_MAINTENANCE: Completed $completedTasks/$totalTasks tasks"
Add-Content -Path "diagnostics\changes-log.txt" -Value $logEntry
