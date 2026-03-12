$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$backupPath = "diagnostics\backups\backup-$timestamp.zip"

Write-Host "Creating backup..."
Compress-Archive -Path 'config\*', 'main.py', 'requirements.txt', 'trading_bot\*' -DestinationPath $backupPath -Force -ErrorAction SilentlyContinue

if (Test-Path $backupPath) {
    $size = (Get-Item $backupPath).Length
    $sizeMB = [math]::Round($size/1MB, 2)
    Write-Host "✅ Backup created: $backupPath"
    Write-Host "Backup size: $sizeMB MB"
    
    # Calculate checksum
    $hash = Get-FileHash $backupPath -Algorithm SHA256
    Write-Host "SHA256: $($hash.Hash)"
    
    # Log to changes log
    $logEntry = "[$timestamp] BACKUP CREATED: $backupPath (Size: $sizeMB MB, SHA256: $($hash.Hash))"
    Add-Content -Path "diagnostics\changes-log.txt" -Value $logEntry
    Write-Host "Logged to changes-log.txt"
} else {
    Write-Host "❌ Backup failed"
    exit 1
}
