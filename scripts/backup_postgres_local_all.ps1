param(
    [Parameter(Mandatory = $false)]
    [string]$DbHost = "127.0.0.1",

    [Parameter(Mandatory = $false)]
    [int]$Port = 5432,

    [Parameter(Mandatory = $false)]
    [string]$User = "postgres",

    [Parameter(Mandatory = $false)]
    [string]$PasswordFile = "C:\Users\norbe\OneDrive\Dokumente\MyApplication\scripts\secrets\pg_backup_password.txt",

    [Parameter(Mandatory = $false)]
    [string]$BackupRoot = "D:\PDVM-System_DB_Backup",

    [Parameter(Mandatory = $false)]
    [int]$KeepDays = 14
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path $BackupRoot)) {
    New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null
}

if (-not (Test-Path $PasswordFile)) {
    throw "Passwortdatei nicht gefunden: '$PasswordFile'. Bitte set_pg_backup_secret.ps1 ausführen."
}

$pgBin = "C:\Program Files\PostgreSQL\18\bin"
$pgDump = Join-Path $pgBin "pg_dump.exe"
$psql = Join-Path $pgBin "psql.exe"

if (-not (Test-Path $pgDump) -or -not (Test-Path $psql)) {
    throw "PostgreSQL-Tools nicht gefunden unter '$pgBin'."
}

$securePassword = Get-Content -Path $PasswordFile -ErrorAction Stop | ConvertTo-SecureString
$plainPassword = [System.Net.NetworkCredential]::new('', $securePassword).Password
$env:PGPASSWORD = $plainPassword

$dbQuery = "SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname;"
$dbsRaw = & $psql -h $DbHost -p $Port -U $User -d postgres -t -c $dbQuery
if ($LASTEXITCODE -ne 0) {
    throw "Datenbankliste konnte nicht gelesen werden."
}

$dbs = $dbsRaw | ForEach-Object { $_.Trim() } | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
if (-not $dbs -or $dbs.Count -eq 0) {
    throw "Keine Datenbanken gefunden."
}

$ts = Get-Date -Format "yyyyMMdd_HHmmss"

foreach ($db in $dbs) {
    $file = Join-Path $BackupRoot ("{0}_{1}.dump" -f $db, $ts)
    & $pgDump -h $DbHost -p $Port -U $User -d $db -F c -f $file
    if ($LASTEXITCODE -ne 0) {
        throw "Backup fehlgeschlagen für DB '$db'."
    }
    Write-Host "OK: $file"
}

$cutoff = (Get-Date).AddDays(-1 * $KeepDays)
Get-ChildItem $BackupRoot -File -Filter "*.dump" |
    Where-Object { $_.LastWriteTime -lt $cutoff } |
    Remove-Item -Force

Write-Host "Backup abgeschlossen."

Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
