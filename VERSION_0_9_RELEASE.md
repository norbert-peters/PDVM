# 🚀 PDVM-System Version 0.9 - Release Notes

**Release-Datum**: 06.11.2025  
**Codename**: "Stabilisierung"  
**Status**: ✅ Release Ready

---

## 📋 Executive Summary

Version 0.9 ist eine **Stabilisierungs-Release** nach der umfangreichen V2→PDVM-Migration. Der Fokus lag auf:
- **Bugfixing**: 6 Bugfix-Runden mit 15+ Fixes
- **Code-Qualität**: Konsistente Namenskonventionen
- **Architektur**: Signal-basierte Stichtag-Verwaltung
- **Migration**: Vollständige Umbenennung von v2_* → pdvm_*

---

## 🎯 Highlights

### ✅ Architektur-Verbesserungen

**1. Duale Datenbank-Architektur stabilisiert**
- 3 SQLite-Instanzen in GCS (Benutzerstamm, Systemsteuerung, Anwendungsdaten)
- Mandantentrennung über User-GUID
- Template-System für !guid!-Ersetzung

**2. Signal-basierte Stichtag-Verwaltung**
- Automatische Propagation über `stichtag_changed` Signal
- Views und Input Controls aktualisieren sich automatisch
- Korrekte Daten-Neuladung mit `reload_with_stichtag()`

**3. Tabellen-Namenskonvention V0.9**
```python
# System-Tabellen (von Anwendung verwaltet)
sys_viewdaten
sys_dropdowndaten
sys_framedaten
sys_dialogdaten
sys_menudaten

# Geschäftsdaten (von User verwaltet)
personen
finanzdaten
konto
```

### ✅ Matrix-Pipeline V2

**Vollständig autonome Pipeline**:
```
START → BASIS → FILTER → SORT → PROJECT → UI
```

**Features**:
- Holt alle Daten selbst (Matrix, GCS, app_db)
- Single Source of Truth für jeden Parameter
- Linear ohne If-Then-Verschachtelungen
- Ein Aufruf pro Ablauf: `pipeline.run('BASIS')`

### ✅ 3-Ebenen Matrix-Struktur

**Für jeden Datenwert**:
```python
row_data[control_key]                      # EBENE 1: Rohdatum
row_data[f"{control_key}__abdatum"]        # EBENE 2: AB-Datum (roh)
row_data[f"{control_key}__formatiert"]     # EBENE 3: Formatiertes AB-Datum
```

**Vorteile**:
- Maximale Flexibilität
- Länderspezifische Formatierung
- Historische Nachverfolgbarkeit

---

## 🔧 Behobene Bugs

### Bugfix Round 1 (Initiale V2-Migration)
- ✅ 7 Kern-Module wiederhergestellt
- ✅ Import-Pfade korrigiert

### Bugfix Round 2
- ✅ History-Dialog Funktionalität
- ✅ Dropdown API-Konsistenz

### Bugfix Round 3
- ✅ 6 Widget-Module + Viewtable Selection Dialog
- ✅ Version-Management zentralisiert in GCS

### Bugfix Round 4
- ✅ Login-Titel korrigiert
- ✅ Dropdown Tabelle: `dropdowndaten` → `sys_dropdowndaten`
- ✅ History-Dialog Errors behoben
- ✅ Pylance Warnings eliminiert

### Bugfix Round 5
- ✅ Dropdown Input Controls zeigen Auswahl
- ✅ `pdvm_autonome_view` Modul wiederhergestellt
- ✅ GUID-Auswahl API-Konsistenz (`get_value` ↔ `set_value`)

### Bugfix Round 6 (Final)
- ✅ ViewTable Tabelle: `viewdaten` → `sys_viewdaten`
- ✅ Stichtag-Refresh lädt Daten neu (View + Input Controls)
- ✅ Import-Fix: `PdvmViewController` → `V2PdvmViewController`

---

## 📊 Statistiken

### Code-Migration
- **334 Dateien** ins archive_v1/ verschoben
- **42 Dateien** umbenannt (v2_* → pdvm_*)
- **87 Imports** aktualisiert über 37 Dateien
- **0 Breaking Changes** für Endbenutzer

### Dokumentation
- **15 Dokumentations-Dateien** erstellt
- Vollständige Architektur-Dokumentation
- Pattern-Libraries für Entwickler
- Bugfix-Historie lückenlos dokumentiert

### Test-Abdeckung
- ✅ Alle Core-Features getestet
- ✅ Stichtag-Wechsel (View + Input Controls)
- ✅ ViewTable Input Control
- ✅ Dropdown Input Control
- ✅ Historische Daten-Verwaltung
- ✅ Filter-System (Schnellsuche, Parametric, Expert)

---

## 🚧 Bekannte Einschränkungen

### Deferred Issues
**1. Gruppierte Daten GUID-Problem**
- **Status**: Bekanntes Edge-Case, nicht kritisch
- **Beschreibung**: Bei gruppierten Daten wird falscher GUID verwendet
- **Workaround**: Keine Gruppen verwenden beim Editieren
- **Geplant für**: Version 0.10

---

## 🔄 Migration von älteren Versionen

### Von V2.0 → V0.9

**Automatisch migriert**:
- Tabellennamen (alte Namen werden automatisch erkannt)
- Import-Pfade (v2_* → pdvm_*)
- API-Calls (Legacy API wird unterstützt)

**Manuell zu prüfen**:
- Custom Code mit direkten DB-Zugriffen
- Hardcoded Tabellennamen in User-Scripts

**Migrations-Tool**:
```powershell
python pdvm_migrate_data.py
```

---

## 📚 Wichtige Dateien

### Kern-Module
- `pdvm_central_systemsteuerung.py` - Global Central System (GCS)
- `pdvm_central_datenbank.py` - Business-Logic-Schicht
- `pdvm_view_controller.py` - View-Management
- `pdvm_matrix_pipeline.py` - Datenverarbeitungs-Pipeline
- `pdvm_input_controls_manager.py` - Input Controls Management

### Dokumentation
- `ARCHITEKTUR_V3_LÖSUNG_ZUSAMMENFASSUNG.md` - System-Architektur
- `MATRIX_3_EBENEN_STRUKTUR.md` - Matrix-Design
- `PIPELINE_V2_VOLLSTÄNDIG_AUTONOM.md` - Pipeline-Dokumentation
- `BUGFIX_ROUND_*.md` - Bugfix-Historie (Rounds 1-6)

---

## 🎓 Entwickler-Guide

### Neue Features entwickeln

**1. View erstellen**:
```python
from pdvm_view_controller import V2PdvmViewController

call_daten = {
    'view_guid': 'your-view-guid',
    'root_table': 'personen',
    'title': 'Meine View'
}

controller = V2PdvmViewController(call_daten, parent=parent_widget)
controller.initialize()
widget = controller.get_widget()
```

**2. Input Controls verwenden**:
```python
from pdvm_input_controls_manager import PdvmInputControlsManager

manager = PdvmInputControlsManager(
    framedaten_db=frame_db,
    selected_guid=guid,
    main_app=main_app,
    gcs=gcs
)

widget = manager.get_widget()
```

**3. Stichtag-Signal empfangen**:
```python
# In __init__:
if hasattr(self.gcs, 'stichtag_changed'):
    self.gcs.stichtag_changed.connect(self.reload_with_stichtag)

# Handler:
def reload_with_stichtag(self, new_stichtag):
    self._load_data()              # Daten NEU laden
    self._build_basis_matrix()     # Matrix NEU aufbauen
    self._run_matrix_pipeline()    # Pipeline durchlaufen
```

### Best Practices

**1. GCS-Zugriff**:
```python
from pdvm_central_systemsteuerung import get_gcs
gcs = get_gcs()
if not gcs or not gcs.is_initialized:
    raise RuntimeError("GCS nicht verfügbar!")
```

**2. Datenbank-Zugriff**:
```python
from pdvm_central_datenbank import PdvmCentralDatenbank

# IMMER expliziten Tabellennamen angeben
db = PdvmCentralDatenbank('sys_viewdaten', view_guid)

# V0.9 API verwenden
wert, abdatum = db.get_value('ROOT', 'FIELD', stichtag)
db.set_value('ROOT', 'FIELD', wert, abdatum)
db.save_all_values()
```

**3. Matrix-Pipeline**:
```python
from pdvm_matrix_pipeline import get_pipeline

pipeline = get_pipeline(view_guid, matrix_manager)

# Komplett neu (mit Daten-Neuladung)
pipeline.run('BASIS')

# Nur Filter neu
pipeline.run('FILTER')

# UI-Update
matrix_project, visible_columns = pipeline.get_projected_data()
```

---

## 🔐 Sicherheit & Performance

### Sicherheit
- ✅ Mandantentrennung über User-GUID
- ✅ Template-System verhindert GUID-Leaks
- ✅ Kein SQL-Injection-Risk (SQLite Prepared Statements)

### Performance
- ✅ Instance-Cache in Input Controls
- ✅ Matrix-Pipeline mit incrementellen Updates
- ✅ Lazy-Loading von Dropdown-Daten
- ✅ get_all_records() mit Performance-Optimierung

### Speicherbedarf
- **Datenbank**: ~5-50 MB (abhängig von Datenmenge)
- **Runtime**: ~50-100 MB (Python + PyQt5)
- **Cache**: ~10-20 MB (Matrix + Instanzen)

---

## 🛠️ Installation & Setup

### Voraussetzungen
```
Python 3.8+
PyQt5 5.15+
SQLite 3.35+
```

### Installation
```powershell
# Virtual Environment aktivieren
.\.venv\Scripts\Activate.ps1

# Dependencies installieren
pip install PyQt5

# Anwendung starten
python pdvm_main.py
```

### Erste Schritte
1. Login mit Benutzer-Credentials
2. Stichtag überprüfen (standardmäßig aktuelles Datum)
3. Menü explorieren
4. View öffnen und testen

---

## 📞 Support & Feedback

### Bug-Reports
- Detaillierte Fehlerbeschreibung
- Log-Ausgabe (`main.log`)
- Reproduktions-Schritte

### Feature-Requests
- Use-Case beschreiben
- Erwartetes Verhalten
- Alternativen erwägen

---

## 🗺️ Roadmap

### Version 0.10 (geplant)
- 🔧 Gruppierte Daten GUID-Fix
- 🚀 Performance-Optimierungen (große Datenmengen)
- 📊 Erweiterte Filter-Optionen
- 🎨 UI-Modernisierung

### Version 1.0 (geplant)
- 🔐 Multi-User-Unterstützung
- 🌐 Netzwerk-Datenbank Support
- 📱 Responsive UI
- 🔌 Plugin-System

---

## 🙏 Danksagung

Diese Version wäre nicht möglich ohne:
- Umfangreiche User-Tests und Feedback
- Systematische Bug-Reports
- Geduldige Entwicklungs-Iterationen

---

## 📜 Changelog (Detailliert)

### [0.9.0] - 2025-11-06

#### Added
- Signal-basierte Stichtag-Verwaltung
- 3-Ebenen Matrix-Struktur
- Autonome Matrix-Pipeline V2
- Version-Management in GCS
- Umfassende Logging-Infrastruktur

#### Changed
- Tabellen-Namenskonvention (sys_ Prefix für System-Tabellen)
- Import-Pfade (v2_* → pdvm_*)
- API-Konsistenz (get_value ↔ set_value)
- refresh() vs reload_with_stichtag() Semantik

#### Fixed
- Stichtag-Refresh lädt Daten neu
- ViewTable Input Control verwendet korrekte Tabelle
- Dropdown Input Control zeigt Auswahl
- GUID-Auswahl API-Konsistenz
- History-Dialog Errors
- Diverse Import-Fehler

#### Removed
- Legacy v2_* Module (archiviert)
- Veraltete API-Calls (get_static_value)
- Redundante Code-Duplikationen

---

**PDVM-System Version 0.9** - Stabil, getestet, produktionsbereit! 🎯
