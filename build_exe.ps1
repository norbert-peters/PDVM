# PDVM-System v0.9 - Build Script
# Erstellt eine standalone EXE-Datei

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "PDVM-System v0.9 - Build Process" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

# 1. Virtual Environment aktivieren (falls vorhanden)
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "Aktiviere Virtual Environment..." -ForegroundColor Green
    & .\.venv\Scripts\Activate.ps1
} else {
    Write-Host "Kein Virtual Environment gefunden - verwende globales Python" -ForegroundColor Yellow
}

# 2. PyInstaller installieren (falls nicht vorhanden)
Write-Host ""
Write-Host "Pruefe PyInstaller..." -ForegroundColor Cyan
$pyinstaller = pip list | Select-String "pyinstaller"
if (-not $pyinstaller) {
    Write-Host "Installiere PyInstaller..." -ForegroundColor Yellow
    pip install pyinstaller
} else {
    Write-Host "PyInstaller bereits installiert" -ForegroundColor Green
}

# 3. Alte Build-Dateien löschen
Write-Host ""
Write-Host "Raeume alte Build-Dateien auf..." -ForegroundColor Cyan
if (Test-Path "build") {
    Remove-Item -Path "build" -Recurse -Force
    Write-Host "build/ geloescht" -ForegroundColor Green
}
if (Test-Path "dist") {
    Remove-Item -Path "dist" -Recurse -Force
    Write-Host "dist/ geloescht" -ForegroundColor Green
}

# 4. EXE erstellen
Write-Host ""
Write-Host "Erstelle EXE-Datei..." -ForegroundColor Cyan
Write-Host "Dies kann einige Minuten dauern..." -ForegroundColor Yellow
Write-Host ""

try {
    pyinstaller pdvm.spec
    
    if (Test-Path "dist\PDVM-System-v0.9.exe") {
        Write-Host ""
        Write-Host "======================================================================" -ForegroundColor Green
        Write-Host "BUILD ERFOLGREICH!" -ForegroundColor Green
        Write-Host "======================================================================" -ForegroundColor Green
        
        # Dateigröße ermitteln
        $exeFile = Get-Item "dist\PDVM-System-v0.9.exe"
        $sizeMB = [math]::Round($exeFile.Length / 1MB, 2)
        
        Write-Host ""
        Write-Host "Build-Informationen:" -ForegroundColor Cyan
        Write-Host "Datei: dist\PDVM-System-v0.9.exe"
        Write-Host "Groesse: $sizeMB MB"
        Write-Host "Erstellt: $($exeFile.LastWriteTime)"
        
        Write-Host ""
        Write-Host "Naechste Schritte:" -ForegroundColor Cyan
        Write-Host "1. Teste die EXE: .\dist\PDVM-System-v0.9.exe"
        Write-Host "2. Erstelle Installer (optional): innosetup setup.iss"
        Write-Host "3. Lade zum GitHub Release hoch"
        
    } else {
        Write-Host ""
        Write-Host "BUILD FEHLGESCHLAGEN!" -ForegroundColor Red
        Write-Host "EXE-Datei wurde nicht erstellt" -ForegroundColor Red
    }
    
} catch {
    Write-Host ""
    Write-Host "FEHLER BEIM BUILD!" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

# 5. Optional: Test ausführen
Write-Host ""
Write-Host "Test-Optionen:" -ForegroundColor Cyan
Write-Host "a) EXE direkt testen: .\dist\PDVM-System-v0.9.exe"
Write-Host "b) Installer erstellen: .\build_installer.ps1"
Write-Host ""

# Frage ob Test ausgeführt werden soll
$response = Read-Host "Moechten Sie die EXE jetzt testen? (j/n)"
if ($response -eq "j" -or $response -eq "J") {
    Write-Host ""
    Write-Host "Starte PDVM-System..." -ForegroundColor Cyan
    Start-Process ".\dist\PDVM-System-v0.9.exe"
}
