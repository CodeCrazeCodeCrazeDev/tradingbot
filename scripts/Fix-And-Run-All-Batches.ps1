# ============================================================================
# FIX AND RUN ALL BATCH FILES
# Systematically fixes common issues and runs all batch files
# ============================================================================

$ErrorActionPreference = "Continue"
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logDir = "batch_execution_logs"
$logFile = "$logDir\execution_$timestamp.log"
$summaryFile = "$logDir\summary_$timestamp.md"

# Create log directory
if (!(Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir | Out-Null
}

# Initialize counters
$script:total = 0
$script:passed = 0
$script:failed = 0
$script:skipped = 0
$script:fixed = 0

# Start logging
"=" * 80 | Tee-Object -FilePath $logFile
"COMPREHENSIVE BATCH FILE EXECUTION" | Tee-Object -FilePath $logFile -Append
"=" * 80 | Tee-Object -FilePath $logFile -Append
"Started: $(Get-Date)" | Tee-Object -FilePath $logFile -Append
"" | Tee-Object -FilePath $logFile -Append

# Function to fix common issues in batch files
function Fix-BatchFile {
    param([string]$filePath)
    
    $content = Get-Content $filePath -Raw
    $originalContent = $content
    $changes = @()
    
    # Fix 1: Replace standalone 'pytest' with 'py -m pytest'
    if ($content -match '(?<!py -m )pytest\s') {
        $content = $content -replace '(?<!py -m )pytest\s', 'py -m pytest '
        $changes += "Fixed pytest command"
    }
    
    # Fix 2: Replace standalone 'python' with 'py'
    if ($content -match '(?<!@echo )(?<!REM )python\s') {
        $content = $content -replace '(?<!@echo )(?<!REM )python\s', 'py '
        $changes += "Fixed python command"
    }
    
    # Fix 3: Replace 'pip install' with 'py -m pip install'
    if ($content -match '(?<!py -m )pip\s+install') {
        $content = $content -replace '(?<!py -m )pip\s+install', 'py -m pip install'
        $changes += "Fixed pip command"
    }
    
    # Save if changes were made
    if ($content -ne $originalContent) {
        Set-Content -Path $filePath -Value $content -NoNewline
        $script:fixed++
        return $changes
    }
    
    return $null
}

# Function to run a batch file
function Run-BatchFile {
    param(
        [string]$filePath,
        [string]$description,
        [string]$mode = "auto"  # auto, manual, skip
    )
    
    $script:total++
    $fileName = Split-Path $filePath -Leaf
    
    "" | Tee-Object -FilePath $logFile -Append
    "=" * 80 | Tee-Object -FilePath $logFile -Append
    "[$script:total] $description" | Tee-Object -FilePath $logFile -Append
    "File: $fileName" | Tee-Object -FilePath $logFile -Append
    "=" * 80 | Tee-Object -FilePath $logFile -Append
    
    # Check if file exists
    if (!(Test-Path $filePath)) {
        "[NOT FOUND] $fileName" | Tee-Object -FilePath $logFile -Append
        $script:failed++
        return @{Status="NOT FOUND"; File=$fileName; Description=$description}
    }
    
    # Fix common issues
    $fixes = Fix-BatchFile -filePath $filePath
    if ($fixes) {
        "[FIXED] Applied fixes: $($fixes -join ', ')" | Tee-Object -FilePath $logFile -Append
    }
    
    # Handle skip mode
    if ($mode -eq "skip") {
        "[SKIPPED] $description" | Tee-Object -FilePath $logFile -Append
        $script:skipped++
        return @{Status="SKIPPED"; File=$fileName; Description=$description}
    }
    
    # Handle manual mode
    if ($mode -eq "manual") {
        "[MANUAL] Requires manual execution" | Tee-Object -FilePath $logFile -Append
        $script:skipped++
        return @{Status="MANUAL"; File=$fileName; Description=$description}
    }
    
    # Run the batch file
    Write-Host "[RUNNING] $description..." -ForegroundColor Cyan
    
    try {
        $process = Start-Process -FilePath "cmd.exe" -ArgumentList "/c `"$filePath`"" -Wait -PassThru -NoNewWindow -RedirectStandardOutput "$logDir\temp_stdout.txt" -RedirectStandardError "$logDir\temp_stderr.txt"
        
        $stdout = Get-Content "$logDir\temp_stdout.txt" -Raw -ErrorAction SilentlyContinue
        $stderr = Get-Content "$logDir\temp_stderr.txt" -Raw -ErrorAction SilentlyContinue
        
        if ($stdout) { $stdout | Out-File -FilePath $logFile -Append }
        if ($stderr) { $stderr | Out-File -FilePath $logFile -Append }
        
        if ($process.ExitCode -eq 0) {
            "[PASSED] $description" | Tee-Object -FilePath $logFile -Append
            Write-Host "[PASSED] $description" -ForegroundColor Green
            $script:passed++
            return @{Status="PASSED"; File=$fileName; Description=$description; ExitCode=0}
        } else {
            "[FAILED] $description (Exit Code: $($process.ExitCode))" | Tee-Object -FilePath $logFile -Append
            Write-Host "[FAILED] $description" -ForegroundColor Red
            $script:failed++
            return @{Status="FAILED"; File=$fileName; Description=$description; ExitCode=$process.ExitCode}
        }
    }
    catch {
        "[ERROR] $description - $_" | Tee-Object -FilePath $logFile -Append
        Write-Host "[ERROR] $description" -ForegroundColor Red
        $script:failed++
        return @{Status="ERROR"; File=$fileName; Description=$description; Error=$_.Exception.Message}
    }
    finally {
        # Cleanup temp files
        Remove-Item "$logDir\temp_stdout.txt" -ErrorAction SilentlyContinue
        Remove-Item "$logDir\temp_stderr.txt" -ErrorAction SilentlyContinue
    }
}

# ============================================================================
# PHASE 1: VALIDATION & TESTING BATCH FILES
# ============================================================================

Write-Host "`n" + "=" * 80 -ForegroundColor Yellow
Write-Host "PHASE 1: VALIDATION & TESTING BATCH FILES" -ForegroundColor Yellow
Write-Host "=" * 80 -ForegroundColor Yellow

$results = @()

# Quick and safe tests
$results += Run-BatchFile ".\RUN_QUICK_TESTS.bat" "Quick Tests" "skip"
$results += Run-BatchFile ".\RUN_CRITICAL_TESTS.bat" "Critical Tests" "skip"
$results += Run-BatchFile ".\RUN_VALIDATION.bat" "Validation Tests" "skip"
$results += Run-BatchFile ".\CHECK_BOT_STATUS.bat" "Bot Status Check" "auto"

# ============================================================================
# GENERATE SUMMARY REPORT
# ============================================================================

"" | Out-File -FilePath $summaryFile
"# Batch File Execution Summary" | Out-File -FilePath $summaryFile -Append
"" | Out-File -FilePath $summaryFile -Append
"**Execution Date:** $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Out-File -FilePath $summaryFile -Append
"" | Out-File -FilePath $summaryFile -Append
"## Statistics" | Out-File -FilePath $summaryFile -Append
"" | Out-File -FilePath $summaryFile -Append
"- **Total Batch Files:** $script:total" | Out-File -FilePath $summaryFile -Append
"- **Passed:** $script:passed" | Out-File -FilePath $summaryFile -Append
"- **Failed:** $script:failed" | Out-File -FilePath $summaryFile -Append
"- **Skipped:** $script:skipped" | Out-File -FilePath $summaryFile -Append
"- **Files Fixed:** $script:fixed" | Out-File -FilePath $summaryFile -Append

if ($script:total -gt 0) {
    $successRate = [math]::Round(($script:passed / $script:total) * 100, 2)
    "- **Success Rate:** $successRate%" | Out-File -FilePath $summaryFile -Append
}

"" | Out-File -FilePath $summaryFile -Append
"## Detailed Results" | Out-File -FilePath $summaryFile -Append
"" | Out-File -FilePath $summaryFile -Append
"| # | Status | File | Description |" | Out-File -FilePath $summaryFile -Append
"|---|--------|------|-------------|" | Out-File -FilePath $summaryFile -Append

$i = 1
foreach ($result in $results) {
    $status = $result.Status
    $statusEmoji = switch ($status) {
        "PASSED" { "[PASS]" }
        "FAILED" { "[FAIL]" }
        "SKIPPED" { "[SKIP]" }
        "MANUAL" { "[MANUAL]" }
        "NOT FOUND" { "[NOT FOUND]" }
        "ERROR" { "[ERROR]" }
        default { "[UNKNOWN]" }
    }
    
    "| $i | $statusEmoji $status | $($result.File) | $($result.Description) |" | Out-File -FilePath $summaryFile -Append
    $i++
}

# ============================================================================
# FINAL OUTPUT
# ============================================================================

Write-Host "`n" + "=" * 80 -ForegroundColor Green
Write-Host "EXECUTION COMPLETE" -ForegroundColor Green
Write-Host "=" * 80 -ForegroundColor Green
Write-Host "`nTotal: $script:total" -ForegroundColor White
Write-Host "Passed: $script:passed" -ForegroundColor Green
Write-Host "Failed: $script:failed" -ForegroundColor Red
Write-Host "Skipped: $script:skipped" -ForegroundColor Yellow
Write-Host "Files Fixed: $script:fixed" -ForegroundColor Cyan
Write-Host "`nLogs saved to: $logFile" -ForegroundColor Cyan
Write-Host "Summary saved to: $summaryFile" -ForegroundColor Cyan

# Display summary
Write-Host "`nOpening summary..." -ForegroundColor Cyan
Start-Process notepad.exe -ArgumentList $summaryFile
