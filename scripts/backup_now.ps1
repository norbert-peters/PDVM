[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$target = Join-Path $scriptDir 'backup_postgres_local_all.ps1'

if (-not (Test-Path -Path $target)) {
    Write-Host "❌ Backup-Skript nicht gefunden: $target" -ForegroundColor Red
    exit 1
}

Write-Host "🚀 Starte manuelles Datenbank-Backup..." -ForegroundColor Cyan

try {
    & $target
    if ($LASTEXITCODE -ne 0) {
        throw "Backup-Skript meldete ExitCode $LASTEXITCODE"
    }

    Write-Host "✅ Backup abgeschlossen." -ForegroundColor Green
}
catch {
    Write-Host "❌ Backup fehlgeschlagen: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
