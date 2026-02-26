[System.Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSAvoidUsingPlainTextForPassword', '', Justification = 'Skript verwendet PSCredential/DPAPI und kein Klartext-Passwort-Parameter.')]
param(
    [Parameter(Mandatory = $false)]
    [string]$ContainerName,

    [Parameter(Mandatory = $true)]
    [string]$DbName,

    [Parameter(Mandatory = $false)]
    [string]$DbUser = "postgres",

    [Parameter(Mandatory = $false)]
    [System.Management.Automation.PSCredential]$DbCredential,

    [Parameter(Mandatory = $false)]
    [string]$BackupRoot = "D:\PDVM-System_DB_Backup"
)

$ErrorActionPreference = 'Stop'

function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Write-Ok {
    param([string]$Message)
    Write-Host "[OK]   $Message" -ForegroundColor Green
}

function Write-Err {
    param([string]$Message)
    Write-Host "[ERR]  $Message" -ForegroundColor Red
}

try {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw "Docker CLI wurde nicht gefunden."
    }

    $null = docker version
    if ($LASTEXITCODE -ne 0) {
        throw "Docker Daemon ist nicht erreichbar. Bitte Docker Desktop starten."
    }

    if ([string]::IsNullOrWhiteSpace($ContainerName)) {
        Write-Info "Kein Containername übergeben, suche laufenden PostgreSQL-Container..."
        $runningPg = docker ps --format "{{.Names}}|{{.Image}}" | Where-Object { $_ -match '\|.*postgres' }

        if (-not $runningPg) {
            throw "Kein laufender PostgreSQL-Container gefunden. Bitte -ContainerName angeben."
        }

        $ContainerName = ($runningPg[0] -split '\|')[0]
        Write-Info "Automatisch gewählt: $ContainerName"
    }

    $containerStatus = docker inspect -f "{{.State.Running}}" $ContainerName 2>$null
    if ($LASTEXITCODE -ne 0 -or $containerStatus -ne 'true') {
        throw "Container '$ContainerName' läuft nicht oder existiert nicht."
    }

    if (-not (Test-Path -Path $BackupRoot)) {
        Write-Info "Backup-Ordner wird erstellt: $BackupRoot"
        New-Item -ItemType Directory -Path $BackupRoot -Force | Out-Null
    }

    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $fileName = "${DbName}_${timestamp}.dump"
    $hostBackupPath = Join-Path $BackupRoot $fileName
    $containerBackupPath = "/tmp/$fileName"

    Write-Info "Starte pg_dump aus Container '$ContainerName' für Datenbank '$DbName'..."

    if ($null -eq $DbCredential) {
        docker exec $ContainerName pg_dump -U $DbUser -d $DbName -F c -f $containerBackupPath
    }
    else {
        $credentialUser = $DbCredential.UserName
        if (-not [string]::IsNullOrWhiteSpace($credentialUser)) {
            $DbUser = $credentialUser
        }

        $plainPassword = $DbCredential.GetNetworkCredential().Password
        docker exec -e "PGPASSWORD=$plainPassword" $ContainerName pg_dump -U $DbUser -d $DbName -F c -f $containerBackupPath
    }

    if ($LASTEXITCODE -ne 0) {
        throw "pg_dump im Container ist fehlgeschlagen."
    }

    Write-Info "Kopiere Backup auf Host: $hostBackupPath"
    docker cp "${ContainerName}:${containerBackupPath}" $hostBackupPath

    if ($LASTEXITCODE -ne 0) {
        throw "Kopieren des Backups auf den Host ist fehlgeschlagen."
    }

    docker exec $ContainerName rm -f $containerBackupPath | Out-Null

    $sizeMb = [Math]::Round(((Get-Item $hostBackupPath).Length / 1MB), 2)
    Write-Ok "Backup erfolgreich erstellt."
    Write-Host "      Datei: $hostBackupPath"
    Write-Host "      Größe: $sizeMb MB"

    Write-Host ""
    Write-Host "Restore-Beispiel (in leere DB):"
    Write-Host "  pg_restore -h <host> -p 5432 -U $DbUser -d <ziel_db> `"$hostBackupPath`""
}
catch {
    Write-Err $_.Exception.Message
    exit 1
}
