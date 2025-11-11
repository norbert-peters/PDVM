# 🚀 GitHub Release v0.9 erstellen - Schritt-für-Schritt Anleitung

## OPTION 1: Via GitHub Web-Oberfläche (empfohlen)

### Schritt 1: Zu Releases navigieren
1. Öffnen Sie: https://github.com/norbert-peters/PDVM
2. Klicken Sie auf **"Releases"** (rechte Sidebar oder unter "Code")
3. Klicken Sie auf **"Draft a new release"**

### Schritt 2: Tag auswählen
1. Bei "Choose a tag": Wählen Sie **`v0.9`** aus dem Dropdown
2. Target Branch: **`v2.0-neuaufbau`** (sollte automatisch ausgewählt sein)

### Schritt 3: Release-Titel
```
🚀 PDVM-System Version 0.9 - Production Ready Beta
```

### Schritt 4: Release-Beschreibung
Kopieren Sie den folgenden Text in das Beschreibungsfeld:

---

## 🎉 PDVM-System Version 0.9 - Production Ready (Beta)

**Release Date**: 06.11.2025  
**Status**: ✅ Production Ready Beta  
**Branch**: v2.0-neuaufbau

---

## 🌟 RELEASE HIGHLIGHTS

### ✅ Bugfix Rounds 1-6 Complete
Alle kritischen Bugs aus 6 Bugfix-Runden erfolgreich behoben:
- **Round 1**: 7 Kern-Module wiederhergestellt
- **Round 2**: History-Dialog + Dropdown-API korrigiert
- **Round 3**: 6 Widgets + Versions-Zentralisierung
- **Round 4**: Login + Dropdown-Tabelle + Fehlerbehandlung + Pylance
- **Round 5**: Dropdown IC + Autonome View + GUID-API
- **Round 6**: ViewTable-Tabelle + Stichtag-Refresh + Import-Fix + Defaults

### 🏗️ Architektur-Highlights
- **Duale Datenbank**: auth.db + Mandanten-spezifische DBs
- **3-Ebenen Matrix**: Wert + AB-Datum + Formatiertes AB-Datum
- **Matrix-Pipeline V2**: Vollständig autonome Datenverarbeitung
- **View-Pipeline**: Komplett gekapselte View-Verwaltung
- **Template-System**: GUID-basierte Mandantentrennung

### 📦 Code-Cleanup
- ✅ **v2_* → pdvm_*** Umbenennung abgeschlossen
- ✅ **270+ alte Dateien** ins archive_v1 verschoben
- ✅ **Konsistente Namenskonventionen** durchgesetzt

---

## 🐛 BUGFIX ROUND 6 (Final)

### 1. ViewTable: Falscher Tabellenname
**Problem**: Suchte in `viewdaten` statt `sys_viewdaten`  
**Fix**: `pdvm_autonome_view.py` Line 102 korrigiert  
**Impact**: ViewTable-Controls funktionieren nun korrekt

### 2. Stichtag-Refresh: Daten nicht neu geladen
**Problem**: Views luden Daten nicht neu bei Stichtag-Änderung  
**Root Causes**:
- MainApp rief `refresh()` nach Signal auf (überschrieb reload)
- Dialog empfing `stichtag_changed` Signal nicht
- Dialog rief `refresh()` statt `reload_with_stichtag()` auf

**Fixes**:
- `pdvm_systemstart.py`: Direkter `refresh()` Aufruf entfernt
- `pdvm_genereller_dialog.py`: Signal-Verbindung hinzugefügt
- `pdvm_genereller_dialog.py`: `refresh()` Method überarbeitet

**Impact**: Stichtag-System funktioniert nun korrekt

### 3. Import-Fehler: PdvmViewController
**Problem**: `cannot import name 'PdvmViewController'`  
**Fix**: Import zu `V2PdvmViewController` korrigiert  
**Impact**: Autonome Views starten fehlerfrei

### 4. Tabellennamen-Defaults
**Defensive Cleanup**: Alle Default-Parameter auf `sys_*` Präfix migriert  
**Files**: pdvm_systemstart.py, pdvm_datenbank.py, pdvm_central_datenbank.py

---

## 📊 STATISTIKEN

- **Dateien geändert**: 396
- **Einfügungen**: 11.587 Zeilen
- **Löschungen**: 7.273 Zeilen
- **Archiviert**: 270+ alte Dateien
- **Neue Dokumentation**: 4 MD-Dateien
- **Bugfix-Dokumentation**: 6 Complete-Dokumente

---

## 🎯 KERN-FUNKTIONEN

### Datenbank-Architektur
```
auth.db (Authentifizierung)
├── sys_benutzer (User-Daten)
└── sys_mandanten (Mandanten-Info)

mandant_XXX/datenbank.db (Pro Mandant)
├── sys_viewdaten (View-Definitionen)
├── sys_dropdowndaten (Dropdown-Listen)
├── sys_menudaten (Menü-Strukturen)
├── sys_dialogdaten (Dialog-Konfigurationen)
├── sys_framedaten (Frame-Layouts)
├── sys_anwendungsdaten (App-Settings)
├── sys_systemsteuerung (System-Config)
└── personen, finanzdaten, etc. (Business-Daten)
```

### Matrix-Pipeline V2
```
START → BasisMatrix → FilterMatrix → SortMatrix → ProjectionMatrix → UI
```
- **Vollständig autonom**: Pipeline holt ALLE Daten selbst
- **Single Source of Truth**: Jeder Parameter eine zentrale Quelle
- **Linear**: Keine Verschachtelungen, nur sequenziell

### 3-Ebenen Struktur
Jeder Datenwert existiert in 3 Ebenen:
```python
row_data['geburtsdatum']                    # EBENE 1: Rohdatum
row_data['geburtsdatum__abdatum']           # EBENE 2: Änderungszeitpunkt
row_data['geburtsdatum__formatiert']        # EBENE 3: Formatiertes Datum
```

---

## 🚀 INSTALLATION & SETUP

### Voraussetzungen
- Python 3.8+
- PyQt5
- bcrypt (optional, für Passwort-Hashing)

### Installation
```powershell
# Repository klonen
git clone https://github.com/norbert-peters/PDVM.git
cd PDVM
git checkout v0.9

# Virtual Environment (optional)
python -m venv .venv
.venv\Scripts\Activate.ps1

# Dependencies installieren
pip install PyQt5 bcrypt

# Datenbank initialisieren
python pdvm_init_auth_database.py
python pdvm_init_mandanten_databases.py

# Optional: Daten migrieren (falls alte PdvmManager.db vorhanden)
python pdvm_migrate_data.py

# Anwendung starten
python pdvm_main.py
```

### Test-Zugänge
- **Admin**: admin@super.de / admin
- **User**: user@super.de / user

---

## ⚠️ BEKANNTE EINSCHRÄNKUNGEN

### 1. Grouped Data GUID Issue
**Status**: Deferred to V0.10  
**Problem**: Gruppen-Header-Daten verwenden falsche GUID  
**Workaround**: Manuelle GUID-Korrektur in Dialogen  
**User-Entscheidung**: "das Problem lassen wir offen und lösen es dann nach der Versionierung"

### 2. Menü-Editor nicht implementiert
**Status**: Geplant für V0.10+  
**Workaround**: Manuelle JSON-Bearbeitung in `sys_menudaten`  
**Dokumentation**: POST_V09_MENU_EDITOR_TODO.md

---

## 📚 MIGRATION VON V2.0

### Automatische Umbenennung
Alle `v2_*` Module wurden automatisch zu `pdvm_*` umbenannt:
```python
# Alt (V2.0)
from v2_pdvm_view_controller import V2PdvmViewController

# Neu (V0.9)
from pdvm_view_controller import V2PdvmViewController
```

### Archivierte Dateien
270+ alte Dateien wurden nach `archive_v1/` verschoben:
- Alle Analyse-Tools (`analyze_*.py`)
- Alle Fix-Scripts (`fix_*.py`)
- Alte Versionen von Kern-Modulen
- Test- und Debug-Dateien

### Datenbank-Migration
Falls Sie von einer älteren Version upgraden:
```powershell
# 1. Backup erstellen
Copy-Item -Path "Daten" -Destination "Daten_backup" -Recurse

# 2. Auth-DB neu initialisieren
python pdvm_init_auth_database.py

# 3. Mandanten-DBs erstellen
python pdvm_init_mandanten_databases.py

# 4. Daten migrieren (falls vorhanden)
python pdvm_migrate_data.py
```

---

## 🔧 ENTWICKLER-GUIDE

### Best Practices
1. **GCS-Zugriff**: Immer `get_gcs()` verwenden, nie direkt importieren
2. **3-Ebenen-Struktur**: ALLE 3 Ebenen zusammen befüllen
3. **Pipeline**: Verwende `pipeline.run()` für Datenverarbeitung
4. **Filter**: Nutze `LinearFilterExecutionManager`, nie direkte Filter

### Code-Beispiele
```python
# ✅ RICHTIG: GCS-Zugriff
from pdvm_central_systemsteuerung import get_gcs
gcs = get_gcs()
if not gcs:
    logger.error("GCS nicht initialisiert!")
    return

# ✅ RICHTIG: 3-Ebenen befüllen
row_data[control_key] = wert
row_data[f"{control_key}__abdatum"] = abdatum
row_data[f"{control_key}__formatiert"] = formatiert

# ✅ RICHTIG: Pipeline verwenden
pipeline = get_pipeline(view_guid, matrix_manager)
pipeline.run('FILTER')
```

---

## 📝 ROADMAP

### Version 0.10 (Geplant)
- ✅ Grouped Data GUID Issue beheben
- ✅ Performance-Optimierungen
- ✅ Erweiterte Filter-Optionen

### Version 1.0 (Ziel)
- ✅ Menü-Editor GUI
- ✅ Erweiterte Berechtigungssystem
- ✅ Export/Import-Funktionen
- ✅ Reporting-System
- ✅ Vollständige Dokumentation
- ✅ Produktionsreife

---

## 🤝 CONTRIBUTING

Beiträge sind willkommen! Bitte beachten Sie:
1. Branch von `v2.0-neuaufbau` erstellen
2. Commits mit aussagekräftigen Messages
3. Deutsche Kommentare im Code
4. Pull Request erstellen

---

## 📄 LIZENZ

Copyright © 2025 Norbert Peters  
Alle Rechte vorbehalten.

---

## 📞 KONTAKT & SUPPORT

- **Repository**: https://github.com/norbert-peters/PDVM
- **Issues**: https://github.com/norbert-peters/PDVM/issues
- **Branch**: v2.0-neuaufbau

---

## 📖 DOKUMENTATION

Vollständige Dokumentation im Repository:
- `VERSION_0_9_RELEASE.md` - Vollständige Release Notes
- `BUGFIX_ROUND_6_COMPLETE.md` - Letzte Bugfix-Details
- `MIGRATION_ABGESCHLOSSEN_3EBENEN.md` - Matrix-Migration
- `PIPELINE_V2_VOLLSTÄNDIG_AUTONOM.md` - Pipeline-Dokumentation

---

**🎉 Vielen Dank an alle Contributors und Tester!**

---

### Schritt 5: Release-Optionen
- ✅ Setzen Sie **"Set as the latest release"**
- ⚠️ **"This is a pre-release"** aktivieren (da Beta)
- Optional: **"Create a discussion for this release"** aktivieren

### Schritt 6: Veröffentlichen
Klicken Sie auf **"Publish release"** 🚀

---

## OPTION 2: Via GitHub CLI (Alternative)

Falls Sie GitHub CLI installiert haben:

```powershell
# GitHub CLI installieren (falls noch nicht vorhanden)
# winget install GitHub.cli

# Anmelden
gh auth login

# Release erstellen
gh release create v0.9 `
  --title "🚀 PDVM-System Version 0.9 - Production Ready Beta" `
  --notes-file VERSION_0_9_RELEASE.md `
  --prerelease `
  --target v2.0-neuaufbau
```

---

## ✅ NACH DEM RELEASE

### Verifikation
1. Prüfen Sie: https://github.com/norbert-peters/PDVM/releases
2. Release sollte als "Pre-release" markiert sein
3. Tag `v0.9` sollte verlinkt sein

### Nächste Schritte
1. Release-Ankündigung schreiben (optional)
2. Changelog in README.md einfügen
3. Mit Version 0.10 Entwicklung beginnen

---

**Status**: ⏳ Warten auf manuelle Erstellung via GitHub Web-Oberfläche
