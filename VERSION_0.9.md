# PDVM-SYSTEM Version 0.9

**Personal Daten Verwaltungs Management System**

## 🎯 Version Information

- **Version**: 0.9
- **Release-Datum**: 06.11.2025
- **Status**: Produktionsbereit (Beta)
- **Codename**: "Phoenix" (Neuaufbau aus V1)

## 📋 Kernfunktionalität

### Datenverwaltung
- ✅ Personenstammdaten mit Historie
- ✅ Finanzdaten-Verwaltung
- ✅ Stichtagsbezogene Datenabfragen
- ✅ 3-Ebenen Matrix-Struktur (Wert / AB-Datum / Formatiert)

### Benutzeroberfläche
- ✅ Multi-Mandanten-Fähigkeit
- ✅ Rollenbasierte Zugriffskontrolle
- ✅ Dynamisches Menü-System (VERTIKAL, GRUND, ZUSATZ)
- ✅ Template-basierte Menü-Konfiguration
- ✅ V3.2 Lineare Workspace-Pipeline

### Datenverarbeitung
- ✅ Matrix-Pipeline (BASIS → FILTER → SORT → PROJECT)
- ✅ Schnellsuche mit Operator-Unterstützung
- ✅ Einfache + Komplexe Filter
- ✅ Spalten-Verwaltung (Standard / Expert Mode)
- ✅ Sortierung mit AB-Datum-Unterstützung

### Persistierung
- ✅ Duale Datenbank-Architektur (Geschäfts- + Anwendungsdaten)
- ✅ User-spezifische Einstellungen
- ✅ Mandanten-spezifische Konfigurationen
- ✅ Filter-/Sortier-Zustände persistent

## 🏗️ Architektur

### Startup-Ablauf (Linear)
```
1. Login-Dialog (pdvm_login_dialog.py)
2. Mandanten-Auswahl (pdvm_mandanten_dialog.py)
3. GCS-Initialisierung (pdvm_central_systemsteuerung.py)
4. Menü-System Prüfung (pdvm_menu_storage.py)
5. Hauptanwendung (pdvm_systemstart.py)
```

### 3-Ebenen Matrix-Struktur
```python
# EBENE 1: Rohdatum
row_data['geburtsdatum'] = 1980001.0

# EBENE 2: AB-Datum (Änderungs-Zeitstempel)
row_data['geburtsdatum__abdatum'] = 2024310.12500

# EBENE 3: Formatiertes AB-Datum
row_data['geburtsdatum__formatiert'] = "05.11.2024 03:00:00"
```

### View-Pipeline (Vollständig Autonom)
```
START
  ↓
[BASIS] ← matrix_manager.basis_matrix
  ↓
[FILTER] ← BasisMatrix + app_db(s_string, s_source)
  ↓
[SORT] ← FilterMatrix + app_db(sort_column, sort_reverse)
  ↓
[PROJECT] ← SortMatrix + GCS(projection_table)
  ↓
UI-UPDATE
```

### V3.2 Lineare Workspace-Pipeline
```
Handler → Parameter vorbereiten
  ↓
Pipeline → skip_clear?
  ├─ False: Workspace leeren → Handler ausführen → Workspace füllen
  └─ True: Workspace behalten → Handler ausführen → Optional leeren
```

## 📦 Kern-Module

### Datenbank & Systemsteuerung
- `pdvm_datenbank.py` - Datenbank-Basisklasse
- `pdvm_central_datenbank.py` - Zentrale DB-Verwaltung
- `pdvm_central_systemsteuerung.py` - Globale Systemsteuerung (GCS)
- `pdvm_gcs.py` - GCS-Singleton
- `global_gcs.py` - Globale GCS-Instanz

### Menü-System
- `pdvm_menu_handler.py` - Menü-Handler (Linear)
- `pdvm_menu_builder.py` - Menü-Builder
- `pdvm_menu_storage.py` - Menü-Persistierung
- `v3_menu_handler.py` - V3-Menu-System
- `v3_menu_widgets.py` - V3-Menu-Widgets

### View-System
- `pdvm_view_controller.py` - View-Controller mit Matrix-Pipeline
- `pdvm_view_ui.py` - View-UI mit Tooltips
- `pdvm_view_matrix_manager.py` - Matrix-Manager
- `pdvm_pipeline.py` - Autonome Pipeline (BASIS/FILTER/SORT/PROJECT)

### Filter & Suche
- `pdvm_einfach_filter_manager.py` - Einfach-Filter
- `pdvm_komplex_filter_manager.py` - Komplex-Filter
- `pdvm_schnellsuche_manager.py` - Schnellsuche
- `pdvm_filter_reset_manager.py` - Filter-Reset
- `pdvm_search_string_parser_v2.py` - Suchstring-Parser

### Input-Controls
- `pdvm_input_control.py` - Input-Control Basisklasse
- `pdvm_input_controls_manager.py` - Control-Manager
- `pdvm_input_type_text.py` - Text-Input
- `pdvm_input_type_datetime.py` - DateTime-Input
- `pdvm_input_type_dropdown.py` - Dropdown-Input
- `pdvm_input_type_viewtable.py` - ViewTable-Input

### Utilities
- `pd_datetime.py` - Pdvm_DateTime (Formatierung)
- `pd_langtext.py` - Langtext-System
- `pd_util.py` - Utilities
- `allgemeines.py` - Allgemeine Funktionen

## 🔧 Technologie-Stack

- **GUI**: PyQt5
- **Datenbank**: SQLite
- **Sprache**: Python 3.12
- **Passwort-Hashing**: bcrypt
- **Encoding**: UTF-8 (überall)

## 📊 Migration V1 → V2 → 0.9

### V1 (Alte Version)
- Monolithische Struktur
- Einzelne Datenbank
- Hardcodierte Menüs
- 334 Python-Dateien

### V2 (Neuaufbau)
- Modulare Architektur
- Duale Datenbank (Geschäft + Anwendung)
- Dynamisches Menü-System
- Template-basierte GUIDs
- 42 Kern-Module

### 0.9 (Produktionsstand)
- V2 umbenannt zu pdvm_*
- 334 alte Dateien archiviert (archive_v1/)
- V3.2 Lineare Pipeline integriert
- Vollständig getestet

## ⚠️ Bekannte Einschränkungen

### Nicht implementiert in 0.9
- [ ] Dropdown-Übersetzung in Show-Spalten
- [ ] Sortierung nicht persistent
- [ ] Summen-Feature (Dialog vorhanden, Pipeline-Integration fehlt)
- [ ] Drucken/Export-Funktionen
- [ ] Multi-Language Support (nur DEU)

### Geplant für 1.0
- Dropdown-Übersetzung in Projektion
- Sortier-Persistierung
- Summen-Matrix-Integration
- PDF-Export
- Excel-Export
- Englische Übersetzung

## 🚀 Schnellstart

```powershell
# Virtual Environment aktivieren
.\.venv\Scripts\Activate.ps1

# Hauptanwendung starten
python pdvm_main.py

# Login
# Email: admin@super.de
# Passwort: admin

# Mandant wählen: Hauptverwaltung

# Startmenü → TESTBEREICH → Personen-View öffnen
```

## 📚 Dokumentation

- `V3.2_LINEARE_PIPELINE_DOKUMENTATION.md` - Pipeline-Architektur
- `V3.2_MIGRATION_ABGESCHLOSSEN.md` - Migration-Zusammenfassung
- `MATRIX_3_EBENEN_STRUKTUR.md` - Matrix-Dokumentation
- `PIPELINE_V2_VOLLSTÄNDIG_AUTONOM.md` - Pipeline V2 Doku
- `.github/copilot-instructions.md` - Entwickler-Richtlinien

## 🎉 Highlights V0.9

1. **Stabile Basis**: 334 alte Dateien archiviert, nur 42 Produktions-Module
2. **Lineare Pipeline**: V3.2 Widget-Delete-Bug behoben
3. **Autonome View-Pipeline**: Holt ALLE Daten selbst (Matrix, GCS, app_db)
4. **3-Ebenen Matrix**: Rohdatum + AB-Datum + Formatiert (komplett implementiert)
5. **Template-System**: GUID-basierte Mandantentrennung
6. **Duale Datenbank**: Trennung Geschäfts- und Anwendungsdaten

## 📝 Änderungsprotokoll

### [0.9] - 06.11.2025

#### Hinzugefügt
- V3.2 Lineare Workspace-Pipeline mit skip_clear
- Autonome View-Pipeline (BASIS/FILTER/SORT/PROJECT)
- 3-Ebenen Matrix-Struktur (Wert/AB-Datum/Formatiert)
- Log-Rotation System (alle 10 Starts)
- Handler-Metadaten-System (SKIP_CLEAR)
- Welcome-Screen mit App-Namen

#### Geändert
- V2-Präfix durch pdvm_ ersetzt
- 334 alte Dateien nach archive_v1/ verschoben
- Matrix-Pipeline komplett überarbeitet
- Welcome-Widget-Lifecycle (Delete → Neu erstellen)

#### Behoben
- RuntimeError bei Welcome-Widget (V3.2 Fix)
- Stichtagsbar-Dehnung (Workspace-Füllung garantiert)
- Widget-Überlappungen (Lineare Pipeline)
- Filter-Inkonsistenzen (LinearFilterExecutionManager)

## 👥 Team

- **Entwickler**: Norbert Peters
- **System-Architektur**: GitHub Copilot + User
- **Projekt**: PDVM-SYSTEM
- **Repository**: Norbert-Peters/PDVM (v2.0-neuaufbau)

## 📄 Lizenz

Proprietär - Alle Rechte vorbehalten

---

**PDVM-SYSTEM Version 0.9 - Ready for Production** 🚀
