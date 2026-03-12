Write-Host "=== INTERNET CONNECTIVITY DIAGNOSIS ===" -ForegroundColor Cyan
Write-Host ""

$results = @{
    dns = $false
    ping = $false
    https = $false
    api = $false
    issues = @()
}

# Test 1: DNS Resolution
Write-Host "[1/5] Testing DNS Resolution..." -ForegroundColor Yellow
try {
    $null = Resolve-DnsName google.com -ErrorAction Stop
    Write-Host "  OK: DNS Working" -ForegroundColor Green
    $results.dns = $true
} catch {
    Write-Host "  FAIL: DNS Failed" -ForegroundColor Red
    Write-Host "     Error: $($_.Exception.Message)" -ForegroundColor Gray
    $results.issues += "DNS resolution failed"
}

Write-Host ""

# Test 2: Basic Connectivity (Ping)
Write-Host "[2/5] Testing Basic Internet Connectivity..." -ForegroundColor Yellow
try {
    $ping = Test-Connection -ComputerName 8.8.8.8 -Count 2 -Quiet -ErrorAction Stop
    if ($ping) {
        Write-Host "  OK: Ping Working (Google DNS reachable)" -ForegroundColor Green
        $results.ping = $true
    } else {
        Write-Host "  FAIL: Ping Failed" -ForegroundColor Red
        $results.issues += "Ping test failed"
    }
} catch {
    Write-Host "  WARNING: Ping Error" -ForegroundColor Yellow
    Write-Host "     Error: $($_.Exception.Message)" -ForegroundColor Gray
    $results.issues += "Ping error"
}

Write-Host ""

# Test 3: HTTPS Connectivity
Write-Host "[3/5] Testing HTTPS Connectivity..." -ForegroundColor Yellow
try {
    $web = Invoke-WebRequest -Uri "https://www.google.com" -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
    Write-Host "  OK: HTTPS Working (Status: $($web.StatusCode))" -ForegroundColor Green
    $results.https = $true
} catch {
    Write-Host "  FAIL: HTTPS Failed" -ForegroundColor Red
    Write-Host "     Error: $($_.Exception.Message)" -ForegroundColor Gray
    $results.issues += "HTTPS connectivity failed"
}

Write-Host ""

# Test 4: Financial API Endpoints
Write-Host "[4/5] Testing Financial API Endpoints..." -ForegroundColor Yellow

# Test Alpha Vantage
try {
    $av = Invoke-WebRequest -Uri "https://www.alphavantage.co" -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
    Write-Host "  OK: Alpha Vantage Reachable (Status: $($av.StatusCode))" -ForegroundColor Green
    $results.api = $true
} catch {
    Write-Host "  WARNING: Alpha Vantage Issue" -ForegroundColor Yellow
    Write-Host "     Error: $($_.Exception.Message)" -ForegroundColor Gray
    $results.issues += "Alpha Vantage unreachable"
}

# Test Yahoo Finance
try {
    $yf = Invoke-WebRequest -Uri "https://finance.yahoo.com" -TimeoutSec 10 -UseBasicParsing -ErrorAction Stop
    Write-Host "  OK: Yahoo Finance Reachable (Status: $($yf.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "  WARNING: Yahoo Finance Issue" -ForegroundColor Yellow
}

Write-Host ""

# Test 5: Proxy/Firewall Settings
Write-Host "[5/5] Testing Proxy/Firewall Settings..." -ForegroundColor Yellow
try {
    $proxy = [System.Net.WebRequest]::GetSystemWebProxy()
    $proxyUri = $proxy.GetProxy([System.Uri]"https://www.google.com")
    
    if ($proxyUri.ToString() -eq "https://www.google.com/") {
        Write-Host "  OK: No proxy configured (direct connection)" -ForegroundColor Green
    } else {
        Write-Host "  WARNING: Proxy detected: $proxyUri" -ForegroundColor Yellow
        $results.issues += "Proxy configured"
    }
} catch {
    Write-Host "  WARNING: Could not check proxy settings" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== DIAGNOSIS SUMMARY ===" -ForegroundColor Cyan

$passedTests = 0
if ($results.dns) { $passedTests++ }
if ($results.ping) { $passedTests++ }
if ($results.https) { $passedTests++ }
if ($results.api) { $passedTests++ }

Write-Host "Tests Passed: $passedTests/4" -ForegroundColor $(if ($passedTests -ge 3) { "Green" } elseif ($passedTests -ge 2) { "Yellow" } else { "Red" })

if ($results.issues.Count -eq 0) {
    Write-Host ""
    Write-Host "CONNECTIVITY: EXCELLENT" -ForegroundColor Green
    Write-Host "   All connectivity tests passed" -ForegroundColor Gray
    Write-Host "   No issues detected" -ForegroundColor Gray
} elseif ($passedTests -ge 2) {
    Write-Host ""
    Write-Host "CONNECTIVITY: PARTIAL" -ForegroundColor Yellow
    Write-Host "   Basic connectivity working" -ForegroundColor Gray
    Write-Host "   Some services may be unreachable" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Issues detected:" -ForegroundColor Yellow
    foreach ($issue in $results.issues) {
        Write-Host "   - $issue" -ForegroundColor Gray
    }
} else {
    Write-Host ""
    Write-Host "CONNECTIVITY: POOR" -ForegroundColor Red
    Write-Host "   Multiple connectivity issues detected" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Issues detected:" -ForegroundColor Red
    foreach ($issue in $results.issues) {
        Write-Host "   - $issue" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "RECOMMENDATIONS:" -ForegroundColor Cyan

if ($results.https -and $results.dns) {
    Write-Host "   OK: Core connectivity is working" -ForegroundColor Green
    Write-Host "   OK: Bot can operate normally in paper mode" -ForegroundColor Green
    if (-not $results.api) {
        Write-Host "   WARNING: External API access may be limited" -ForegroundColor Yellow
        Write-Host "   - This is non-critical for paper trading" -ForegroundColor Gray
        Write-Host "   - Bot uses MT5 data primarily" -ForegroundColor Gray
    }
} else {
    Write-Host "   - Check your internet connection" -ForegroundColor Yellow
    Write-Host "   - Check firewall/antivirus settings" -ForegroundColor Yellow
    Write-Host "   - Try disabling VPN if active" -ForegroundColor Yellow
}

Write-Host ""

# Save results
$resultsJson = $results | ConvertTo-Json -Depth 5
$resultsJson | Out-File "diagnostics\connectivity-test-results.json" -Encoding UTF8
Write-Host "Results saved to: diagnostics\connectivity-test-results.json" -ForegroundColor Gray
Write-Host ""
