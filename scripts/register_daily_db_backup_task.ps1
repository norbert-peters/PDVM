param(
    [Parameter(Mandatory = $false)]
    [string]$TaskName = "PDVM_Daily_Postgres_Backup",

    [Parameter(Mandatory = $false)]
    [string]$Time = "02:00",

    [Parameter(Mandatory = $false)]
    [string]$PasswordFile = "C:\Users\norbe\OneDrive\Dokumente\MyApplication\scripts\secrets\pg_backup_password.txt"
)

$scriptPath = "C:\Users\norbe\OneDrive\Dokumente\MyApplication\scripts\backup_postgres_local_all.ps1"

if (-not (Test-Path $scriptPath)) {
    throw "Backup-Skript nicht gefunden: $scriptPath"
}

if (-not (Test-Path $PasswordFile)) {
    throw "Passwortdatei nicht gefunden: $PasswordFile"
}

$cmd = "powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`" -PasswordFile `"$PasswordFile`""

schtasks /Create /F /SC DAILY /TN $TaskName /TR $cmd /ST $Time /RL LIMITED
if ($LASTEXITCODE -ne 0) {
    throw "Task konnte nicht erstellt werden."
}

schtasks /Query /TN $TaskName /V /FO LIST
