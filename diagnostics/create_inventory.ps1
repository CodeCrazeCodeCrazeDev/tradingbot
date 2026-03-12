$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$inventory = @{
    timestamp = $timestamp
    os = 'Windows 10 Pro Education'
    shell = 'PowerShell'
    repo_root = 'c:\Users\peterson\trading bot'
    startup_scripts = @(
        'START_BOT_SIMPLE.bat',
        'START_BOT_WITH_WATCHDOG.bat',
        'start_monitored_bot.ps1',
        'RUN_BOT.bat',
        'main.py'
    )
    dependencies = @('requirements.txt', 'requirements-extras.txt')
    config_files = @('config\config.yaml')
    test_files = @('tests\')
    current_status = 'Bot previously running, PID 12140 mentioned in handoff'
    last_operator_session = '2025-10-08 00:28:00'
    position_validator = 'Active - max 1.0 lots'
    trading_mode = 'paper'
    git_available = $false
}

$inventoryJson = $inventory | ConvertTo-Json -Depth 10
$inventoryPath = "diagnostics\inventory-$timestamp.json"
$inventoryJson | Out-File $inventoryPath -Encoding UTF8
Write-Host "Inventory created at: $inventoryPath"
Get-Content $inventoryPath
