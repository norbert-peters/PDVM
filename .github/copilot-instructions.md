# PDVM-System AI-Assistent Anweisungen

## Projektübersicht
PDVM-System v0.9 ist eine PyQt5-basierte deutsche Anwendung für Datenverwaltung, Darstellung und kaufmännische Berechnungen mit einem komplexen Filter-System und dualer Datenbank-Architektur.

## Architektur & Kernsysteme

### Startup-Ablauf (Linear)
1. `main.py` → `LinearStartManagerNew` führt linearen 5-Schritte Startablauf durch
2. `pdvm_login.py` → Login-Dialog mit User-GUID Extraktion  
3. `pdvm_central_systemsteuerung.py` → Globale Systemsteuerung (GCS) mit Template-System (!guid! Referenzen)
4. `pdvm_systemstart.py` → MainAppComplete Hauptanwendung
5. Persistierung über `global_gcs` Modul für systemweiten Zugriff

### Duale Datenbank-Architektur
- **Haupt-DB**: `datenbank.db` SQLite für Geschäftsdaten
- **App-DB**: Anwendungsdaten/Einstellungen über `gcs._app_db`
- **Stichtag-System**: Persistente Datumskontrolle mit `st_inst.FormTimeStamp`

### Filter-System (KRITISCHES PROBLEM)
**AKTUELLER ZUSTAND**: Nicht-lineare Pipeline verursacht inkonsistente Ergebnisse
- Komplexer Filter → 3 Zeilen → Einfacher Filter "Lau" → 2 Treffer (FALSCH)
- Filter löschen → Einfacher Filter "Lau" → 3 Treffer (KORREKT)

**LÖSUNG IMPLEMENTIERT**:
- `linear_filter_execution_manager.py` - Zentrale lineare Pipeline
- `linear_filter_integration_example.py` - Integration in bestehende Dialoge
- Automatischer kompletter Reset vor jeder Filterung
- Nur EIN aktiver Filter, immer komplette Datenbasis als Ausgangspunkt

**Filter-Components**:
- `extended_filter_engine.py` - 4-Positionen Struktur (FIRST/AND/OR | IS/NOT | Operator | Wert)
- `central_filter_reset.py` - Multi-Ebenen Reset-System
- `search_parameter_dialog.py` - Parametrische Filter
- Gesamtfilter - Direkte Datenbank-Anwendung

## Template-System & GUID-Management
- **Template-Pattern**: `!guid!` in Konfiguration wird durch aktuelle User-GUID ersetzt
- **View-GUIDs**: Eindeutige Identifikation für Persistierung/Filter pro Ansicht  
- **User-GUIDs**: Mandantentrennung und personalisierte Einstellungen

## Entwicklungsrichtlinien

### Filter-System verwenden
```python
# NIEMALS direkte Filter-Aufrufe verwenden:
self.apply_search_filter('familienname', 'Lau')  # ❌

# IMMER LinearFilterExecutionManager verwenden:
from linear_filter_execution_manager import get_linear_filter_manager
manager = get_linear_filter_manager(view_guid)
manager.execute_filter_linear('parametric', {
    'field_name': 'familienname', 
    'search_value': 'Lau',
    'operator': 'enthält'
})  # ✅
```

### GCS-Zugriff Pattern
```python
from pdvm_central_systemsteuerung import get_gcs
gcs = get_gcs()
if not gcs:
    logger.error("GCS nicht initialisiert!")
    return
    
# Template-GUID Zugriff
user_guid = gcs.user_guid
country = gcs.field_value('country')
stichtag = gcs.stichtag
```

### Persistierung Pattern  
```python
# Anwendungsdaten speichern
gcs._app_db.set_value(view_guid, key, value)
data, _ = gcs._app_db.get_value(view_guid, key)
```

## Datei-Konventionen
- **Analyse-Dateien**: `analyze_*.py` - Systemanalyse und Debugging
- **PDVM-Module**: `pdvm_*.py` - Kernfunctionalität  
- **Cleanup-Logs**: `CLEANUP_*.md`, `*_ZUSAMMENFASSUNG.md` - Dokumentation
- **Deutsche Kommentare**: Verwende deutsche Sprache in Kommentaren und Logs
- **Logging Pattern**: Emojis in Logs (`🎯`, `✅`, `❌`, `📂`, `🔧`)

## Häufige Fallstricke
1. **Filter-Inkonsistenz**: Verwende NIEMALS direkte Filter ohne LinearFilterExecutionManager
2. **GCS vor Login**: GCS ist nur nach erfolgreichem Login verfügbar
3. **GUID-Template vergessen**: Verwende `!guid!` für benutzerspezifische Konfigurationen
4. **Circular Imports**: GCS lokal importieren in Funktionen, nicht module-level
5. **Encoding**: Dateien sind UTF-8, verwende `encoding='utf-8'` für Dateioperationen

## Debugging & Analyse
- `analyze_filter_pipeline.py` - Filter-Pipeline Debugging
- `architecture_analysis.py` - System-Architektur Analyse  
- `check_database_raw.py` - Datenbank-Strukturprüfung
- Logs in `main.log` mit strukturiertem Format

## Build & Ausführung
```bash
# Abhängigkeiten
pip install PyQt5

# Start  
python main.py

# Filter-Tests
python linear_filter_integration_example.py
```

Arbeite IMMER mit dem LinearFilterExecutionManager für Filter-Operationen und beachte die duale Datenbank-Architektur mit GCS-Template-System.