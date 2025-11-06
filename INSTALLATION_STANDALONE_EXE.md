# 🚀 PDVM-System v0.9 - Standalone Installation

## Problem behoben: Handler-Verzeichnis
**Status**: ✅ KORRIGIERT in pdvm.spec (06.11.2025 18:56)

Das `handlers/` Verzeichnis wird jetzt **automatisch in die EXE eingebettet**.

---

## 📦 Installation (Standalone EXE)

### Schritt 1: Test-Verzeichnis erstellen
```
C:\Test-PDVM\
```

### Schritt 2: NUR DIE EXE kopieren
```
C:\Test-PDVM\
    └── PDVM-System-v0.9.exe
```

**WICHTIG**: Sie brauchen **KEINE** zusätzlichen Dateien mehr!
- ❌ NICHT: Daten/ Verzeichnis kopieren
- ❌ NICHT: handlers/ Verzeichnis kopieren
- ✅ NUR: Die EXE-Datei

### Schritt 3: Starten
```
C:\Test-PDVM\PDVM-System-v0.9.exe
```

---

## 🔧 Was passiert beim ersten Start?

1. **PyInstaller entpackt** alles nach `%TEMP%\_MEI[random]\`:
   - Alle Python-Module
   - **handlers/** Verzeichnis (NEU!)
   - **Daten/** Verzeichnis mit datenbank.db

2. **Login** → Mandantenauswahl funktioniert

3. **Startmenü** wird geladen

4. **Testbereich** öffnet sich jetzt korrekt (Handler gefunden!)

---

## 📁 Datei-Struktur (intern in EXE)

```
PDVM-System-v0.9.exe [38.12 MB]
├── Python Runtime
├── PyQt5 Libraries
├── PDVM Module (alle pdvm_*.py)
├── handlers/
│   ├── handler_open_app_menu.py      ✅ Jetzt enthalten!
│   ├── handler_open_view.py
│   ├── handler_logout.py
│   └── ... (alle anderen Handler)
├── Daten/
│   └── mandant_001/
│       └── datenbank.db
└── Dokumentation (*.md)
```

---

## 🧪 Test-Ablauf

### Test 1: Kompletter Neustart
1. EXE in neues Verzeichnis kopieren
2. Doppelklick auf EXE
3. Login: `admin` / `admin`
4. Mandant: `Mustermann GmbH`
5. **TESTBEREICH** Button klicken
6. ✅ Sollte jetzt funktionieren!

### Test 2: Handler-Verfügbarkeit prüfen
Logfile wird erstellt unter:
```
C:\Test-PDVM\pdvm_main_1.log
```

**Erwartete Log-Einträge**:
```
✅ HandlerRegistry initialisiert
✅ Handler gefunden: open_app_menu
✅ Handler ausgeführt: open_app_menu
```

**KEINE Fehler mehr** wie:
```
❌ Handler-Datei nicht gefunden: ...\handlers\handler_open_app_menu.py
```

---

## ⚠️ Bekannte Einschränkungen

### Datenbank-Pfad
Die Datenbank liegt im **TEMP-Verzeichnis** nach Entpacken.

**Problem**: Daten gehen nach jedem EXE-Neustart verloren!

**Lösung für v1.0**:
- Datenbank-Pfad konfigurierbar machen
- Option: Datenbank im Benutzerverzeichnis anlegen
- Z.B.: `%APPDATA%\PDVM-System\Daten\datenbank.db`

### Erste Schritte für v1.0
1. Datenbank-Pfad-Manager erstellen
2. Config-Datei im Benutzerverzeichnis
3. Automatische Datenbank-Migration bei Updates

---

## 📊 EXE-Details

- **Datei**: PDVM-System-v0.9.exe
- **Größe**: 38,12 MB
- **Erstellt**: 06.11.2025 18:56:57
- **Python**: 3.12.8
- **PyInstaller**: 6.16.0
- **Modus**: Single-file (--onefile)
- **Console**: Deaktiviert (nur GUI)

---

## 🎯 Nächste Schritte

### Sofort (für Test):
```powershell
# Neue EXE in Download-Ordner kopieren
Copy-Item "dist\PDVM-System-v0.9.exe" "C:\Users\norbe\Downloads\PDVM System\" -Force

# Alte Handler/Daten löschen (nicht mehr nötig!)
Remove-Item "C:\Users\norbe\Downloads\PDVM System\handlers" -Recurse -Force
Remove-Item "C:\Users\norbe\Downloads\PDVM System\Daten" -Recurse -Force

# EXE starten
& "C:\Users\norbe\Downloads\PDVM System\PDVM-System-v0.9.exe"
```

### Für v1.0 (Permanent):
1. Persistente Datenbank außerhalb TEMP
2. Konfigurations-Datei für Pfade
3. Installer mit Deinstallations-Routine
4. Icon für die EXE hinzufügen

---

## 🐛 Troubleshooting

### Handler nicht gefunden
**Symptom**: `Handler 'open_app_menu' nicht registriert`
**Lösung**: Neue EXE verwenden (ab 06.11.2025 18:56)

### Datenbank fehlt
**Symptom**: `Datenbank nicht gefunden`
**Lösung**: Normale Fehlermeldung - Datenbank wird automatisch erstellt

### Login schlägt fehl
**Symptom**: Falscher Benutzername/Passwort
**Standard**: `admin` / `admin`

---

**WICHTIG**: Diese EXE ist **vollständig standalone** - keine zusätzlichen Dateien erforderlich!
