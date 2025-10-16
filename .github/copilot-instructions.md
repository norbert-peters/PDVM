# PDVM-System AI-Assistent Anweisungen

## 🎯 Projektübersicht
PDVM-System v0.9 ist eine **PyQt5-basierte deutsche Enterprise-Anwendung** für Datenverwaltung, Darstellung und kaufmännische Berechnungen. Kernmerkmale:
- **Lineare Datenverarbeitungs-Pipeline** mit strikter Matrix-Hierarchie
- **Duale Datenbank-Architektur** (Geschäftsdaten + Anwendungsdaten)
- **3-Ebenen Matrix-Struktur** für jeden Datenwert
- **Template-basiertes GUID-System** für Mandantentrennung

## 🏗️ Architektur & Kernsysteme

### Startup-Ablauf (STRIKT LINEAR)
Der Start ist **sequenziell und nicht-parallelisierbar**:

1. **`main.py`** → `LinearStartManagerNew` führt 5-Schritte-Ablauf durch
2. **`pdvm_login.py`** → Login-Dialog extrahiert User-GUID aus Datenbank
3. **`pdvm_central_systemsteuerung.py`** → Globale Systemsteuerung (GCS) initialisiert mit User-GUID
   - Template-System ersetzt `!guid!` durch aktuelle User-GUID
   - Initialisiert 3 Datenbank-Instanzen (siehe unten)
4. **`pdvm_systemstart.py`** → `MainAppComplete` Hauptanwendung mit vollständigem Menü
5. **`global_gcs`** → Singleton-Pattern für systemweiten GCS-Zugriff

**KRITISCH**: GCS ist **nur nach erfolgreichem Login verfügbar** - keine GCS-Aufrufe vor Login!

### Duale Datenbank-Architektur (3 SQLite-Instanzen)
GCS verwaltet **3 separate Datenbank-Instanzen** via `PdvmCentralDatenbank`:

```python
# 1. BENUTZERSTAMM-DB: User-spezifische Stammdaten
self._u_db = PdvmCentralDatenbank('benutzerstamm')

# 2. SYSTEMSTEUERUNG-DB: Systemkonfiguration pro User
self._db = PdvmCentralDatenbank('systemsteuerung', user_guid)

# 3. ANWENDUNGSDATEN-DB: Filter, Sortierungen, Spalten-Einstellungen
self._app_db = PdvmCentralDatenbank('anwendungsdaten', user_guid)
```

**WICHTIG**: 
- Hauptdatenbank: `datenbank.db` (SQLite) für Geschäftsdaten (Personen, Finanzen, etc.)
- Anwendungsdaten werden **mandantenspezifisch** in `_app_db` persistiert
- **Stichtag-System**: `gcs.st_inst.PdvmDateTime` für zeitpunktbasierte Datenabfragen

### View-Pipeline-System (✅ VOLLSTÄNDIG GEKAPSELT)
**UPDATE 15.10.2025**: Komplette View-Verwaltung in `PdvmViewPipeline` gekapselt

**PROBLEM VORHER**:
- Projektion extern gesteuert (kompliziert)
- Schnellsuche-Variable mehrfach initialisiert
- Viele manuelle Verbindungen zwischen Komponenten
- Fehleranfällig und unübersichtlich

**LÖSUNG IMPLEMENTIERT**:
```python
# ULTRA EINFACH: Nur 2 Parameter bei Init!
view_pipeline = get_view_pipeline(view_guid, matrix_manager)
view_pipeline.initialize_view(
    view_parent=table_container,        # Parent für Tabelle
    schnellsuche_parent=search_container # Parent für Suchfeld
)

# Nur 3 Methoden für alle Operationen!
view_pipeline.set_schnellsuche('lau')  # Schnellsuche
view_pipeline.reset_filters()          # Filter zurücksetzen
view_pipeline.refresh()                # View aktualisieren
```

**View-Pipeline verwaltet ALLES**:
- Matrix-Pipeline (Datenverarbeitung)
- View-Widget (Tabellenansicht)
- Schnellsuche-Widget (Suchfeld mit Signal-Verbindung)
- Projektion (aus GCS - Standard/Expert Mode)
- Filter-Status (aus app_db)

## Template-System & GUID-Management
- **Template-Pattern**: `!guid!` in Konfiguration wird durch aktuelle User-GUID ersetzt
- **View-GUIDs**: Eindeutige Identifikation für Persistierung/Filter pro Ansicht  
- **User-GUIDs**: Mandantentrennung und personalisierte Einstellungen

## 3-Ebenen Matrix-Struktur (KRITISCH)
**KONZEPT**: Jeder Datenwert in der Matrix hat 3 separate Ebenen für maximale Flexibilität:

```python
# EBENE 1: Rohdatum aus DB
row_data['geburtsdatum_original'] = 1980001.0

# EBENE 2: AB-Datum (Änderungs-Zeitstempel, roh)
row_data['geburtsdatum_original_abdatum'] = 2024310.12500

# EBENE 3: Formatiertes AB-Datum (länderspezifisch via pdvm_DateTime)
row_data['geburtsdatum_original_formatiertes_abdatum'] = "05.11.2024 03:00:00"
```

**IMPLEMENTIERUNGS-PATTERN** (✅ IMPLEMENTIERT):
```python
# 1. Wert und AB-Datum aus DB holen
result = temp_instance.get_value(gruppe, feld, gcs.st_inst.PdvmDateTime)
wert, abdatum = result[0], result[1] if isinstance(result, tuple) else (result, None)

# 2. Alle 3 Ebenen befüllen (IMMER zusammen!)
row_data[control_key] = wert  # EBENE 1
row_data[f"{control_key}__abdatum"] = abdatum  # EBENE 2
row_data[f"{control_key}__formatiert"] = temp_dt.FormTimeStamp  # EBENE 3
```

**FORMATIERUNGS-FUNKTION**:
```python
def _format_abdatum(self, abdatum_value):
    """Formatiert AB-Datum länderspezifisch"""
    if abdatum_value is None:
        return None
    if float(abdatum_value) == 1001.0:
        return "01.01.0001 (Default)"
    
    dt = self.gcs.temp_dt_inst
    dt.PdvmDateTime = float(abdatum_value)
    return dt.FormTimeStamp  # Länderspezifisch (DEU/ENG/USA)
```

**WICHTIGE DATEIEN**:
- `MATRIX_3_EBENEN_STRUKTUR.md` - Vollständige Dokumentation
- `MIGRATION_ABGESCHLOSSEN_3EBENEN.md` - ✅ Migration Complete Summary
- `MATRIX_PIPELINE_KOMPLETT_IMPLEMENTIERT.md` - ✅ Pipeline Implementation Complete
- `matrix_3_ebenen_example.py` - Praktische Beispiele
- `pdvm_matrix_pipeline.py` - ✅ BasisMatrix/FilterMatrix/SortMatrix/ProjectionMatrix
- `pdvm_view_daten_manager.py` - ✅ Korrekte 3-Ebenen Implementation + Pipeline Integration
- `pdvm_view_widget_with_tooltips.py` - ✅ Widget mit Tooltip-Unterstützung
- `pd_datetime.py` - Pdvm_DateTime Formatierung

**KRITISCHE REGELN**:
- ✅ IMMER alle 3 Ebenen zusammen befüllen
- ✅ Show-Spalten kopieren ALLE 3 Ebenen von Original-Spalten
- ❌ NIEMALS nur einzelne Ebenen formatieren
- ❌ NIEMALS nachträgliche Formatierung

## Matrix-Pipeline-Architektur V2 (✅ VOLLSTÄNDIG AUTONOM)
**UPDATE 15.10.2025**: Pipeline komplett überarbeitet nach Benutzer-Vorgabe

### Architektur-Prinzipien
1. ✅ **Vollständige Autonomie**: Pipeline holt ALLE Daten selbst (Matrix, GCS, app_db)
2. ✅ **Single Source of Truth**: Jeder Parameter hat EINE zentrale Quelle
3. ✅ **Linear ohne Verschachtelungen**: Keine If-Then-Logik, nur sequenzielle Ausführung
4. ✅ **Ein Aufruf pro Ablauf**: Manager setzen nur DB → `pipeline.run()` → fertig

### Pipeline-Struktur (AUTONOM)
```
START (View-Initialisierung)
  ↓
[1] BASIS ← matrix_manager.basis_matrix
    Wird NUR bei START oder Stichtag-Refresh geladen
  ↓
[2] FILTER ← BasisMatrix + app_db(s_string, s_source)
    Baut FilterMatrix aus BasisMatrix
    Steuert Schnellsuche-Feld automatisch (current_search_text)
  ↓
[3] SORT ← FilterMatrix + app_db(sort_column, sort_reverse)
    Baut SortMatrix aus FilterMatrix
  ↓
[4] PROJECT ← SortMatrix + GCS(projection_table)
    Projiziert View aus SortMatrix
    row_type in versteckter Spalte verfügbar
  ↓
UI-UPDATE (außerhalb Pipeline)
```

### Pipeline-Aufrufe
```python
# Import
from pdvm_pipeline import get_pipeline

# Pipeline holen (Singleton pro View)
pipeline = get_pipeline(view_guid, matrix_manager)

# AUFRUFE (linear ab Status)
pipeline.run('BASIS')    # Kompletter Neustart (BASIS→FILTER→SORT→PROJECT)
pipeline.run('FILTER')   # Ab Filter neu (FILTER→SORT→PROJECT)
pipeline.run('SORT')     # Ab Sort neu (SORT→PROJECT)
pipeline.run('PROJECT')  # Nur Projektion neu

# UI-Update (holt ALLE Daten aus Pipeline)
matrix_project, visible_columns = pipeline.get_projected_data()
search_text = pipeline.get_search_text()  # Für Schnellsuche-Feld
```

### Manager-Integration (ULTRA EINFACH)
```python
# Schnellsuche aktivieren
def execute_schnellsuche(self, search_text):
    # 1. Parameter in app_db speichern
    self.gcs._app_db.set_value(self.view_guid, 's_string', search_text)
    self.gcs._app_db.set_value(self.view_guid, 's_source', 'schnell')
    self.gcs._app_db.save_all_values()
    
    # 2. Pipeline läuft - FERTIG!
    self.pipeline.run('FILTER')

# Filter zurücksetzen
def reset_all_filters(self):
    # 1. Parameter löschen
    self.gcs._app_db.set_value(self.view_guid, 's_string', None)
    self.gcs._app_db.set_value(self.view_guid, 's_source', None)
    self.gcs._app_db.save_all_values()
    
    # 2. Pipeline läuft - FERTIG!
    self.pipeline.run('FILTER')
```

### UI-Controller Integration
```python
def refresh_ui_from_pipeline(self):
    """Pipeline liefert ALLES für UI-Update"""
    pipeline = get_pipeline(self.view_guid, self.matrix_manager)
    
    # Alle Daten aus Pipeline holen
    matrix_project, visible_columns = pipeline.get_projected_data()
    search_text = pipeline.get_search_text()
    
    # Schnellsuche-Feld aktualisieren (AUTONOM!)
    if search_text:
        self.ui.search_field.setText(search_text)
    else:
        self.ui.search_field.clear()
    
    # Matrix-Daten anzeigen
    self.ui.set_data_from_matrix(matrix_project, visible_columns, self.all_controls)
```

### Datenfluss-Diagramm
```
Matrix Manager (BasisMatrix)
    ↓ [NUR bei START/Stichtag]
Pipeline.matrix_base
    ↓ + app_db(s_string, s_source)
Pipeline.matrix_filter
    ↓ + app_db(sort_column, sort_reverse)
Pipeline.matrix_sort
    ↓ + GCS(projection_table)
Pipeline.matrix_project
    ↓
UI (View + Schnellsuche-Feld)
```

### Wichtige Dateien
- `pdvm_pipeline.py` - ✅ V2 Vollständig autonom
- `schnellsuche_manager.py` - ✅ Integriert mit Pipeline
- `filter_reset_manager.py` - ✅ Integriert mit Pipeline
- `pdvm_view_controller.py` - ✅ `refresh_ui_from_pipeline()`
- `PIPELINE_V2_VOLLSTÄNDIG_AUTONOM.md` - ✅ Komplette Dokumentation

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

## 📂 Projektstruktur & Datei-Konventionen

### Namenskonventionen
- **Kern-Module**: `pdvm_*.py` - Kernfunktionalität (z.B. `pdvm_view_controller.py`, `pdvm_matrix_pipeline.py`)
- **Analyse-Tools**: `analyze_*.py` - Systemanalyse und Debugging (z.B. `analyze_filter_pipeline.py`)
- **Test-Dateien**: `test_*.py` - Unit- und Integrationstests
- **Fix-Skripte**: `fix_*.py` - Temporäre Reparatur-Skripte (können nach Erfolg gelöscht werden)
- **Dokumentation**: `*.md` - Markdown-Dokumentation (z.B. `MATRIX_3_EBENEN_STRUKTUR.md`)
  - `*_ZUSAMMENFASSUNG.md` - Projekt-Meilenstein Zusammenfassungen
  - `CLEANUP_*.md` - Refactoring-Dokumentation

### Wichtige Verzeichnisse
- `/Daten/` - Produktionsdatenbank (`datenbank.db`)
- `/.github/` - Repository-Konfiguration
- `/datasets/` - Test- und Beispieldaten
- `/__pycache__/`, `/env/`, `/venv/` - Generierte Dateien (nicht bearbeiten)

### Code-Stil
- **Sprache**: Deutsche Kommentare, Variablen und Log-Nachrichten
- **Logging**: Strukturierte Logs mit Emojis (`🎯`, `✅`, `❌`, `📂`, `🔧`, `🔍`, `⚠️`)
- **Encoding**: UTF-8 überall, explizit `encoding='utf-8'` bei Dateioperationen

## ⚠️ Häufige Fallstricke

### KRITISCHE Fehler vermeiden
1. **Filter-Inkonsistenz**: Verwende NIEMALS direkte Filter ohne `LinearFilterExecutionManager`
   ```python
   # ❌ FALSCH
   self.apply_search_filter('familienname', 'Lau')
   
   # ✅ RICHTIG
   from linear_filter_execution_manager import get_linear_filter_manager
   manager = get_linear_filter_manager(view_guid)
   manager.execute_filter_linear('parametric', {'field_name': 'familienname', ...})
   ```

2. **GCS vor Login**: GCS ist **nur nach erfolgreichem Login verfügbar**
   ```python
   # ✅ IMMER prüfen
   from pdvm_central_systemsteuerung import get_gcs
   gcs = get_gcs()
   if not gcs:
       logger.error("GCS nicht initialisiert!")
       return
   ```

3. **Matrix 3-Ebenen vergessen**: NIEMALS nur einzelne Ebenen befüllen
   ```python
   # ❌ FALSCH - nur eine Ebene
   row_data[control_key] = wert
   
   # ✅ RICHTIG - alle 3 Ebenen zusammen
   row_data[control_key] = wert  # EBENE 1
   row_data[f"{control_key}_abdatum"] = abdatum  # EBENE 2
   row_data[f"{control_key}_formatiertes_abdatum"] = formatiert  # EBENE 3
   ```

4. **Circular Imports**: GCS lokal in Funktionen importieren, nicht module-level
5. **GUID-Template vergessen**: Verwende `!guid!` für benutzerspezifische Konfigurationen
6. **Nachträgliche Formatierung**: Formatierung passiert bei Matrix-Erstellung, NICHT später!

## Debugging & Analyse
- `analyze_filter_pipeline.py` - Filter-Pipeline Debugging
- `architecture_analysis.py` - System-Architektur Analyse  
- `check_database_raw.py` - Datenbank-Strukturprüfung
- Logs in `main.log` mit strukturiertem Format

## 🚀 Build & Ausführung

### Entwicklungsumgebung starten
```powershell
# Virtual Environment aktivieren (falls verwendet)
.\venv\Scripts\Activate.ps1

# Abhängigkeiten installieren
pip install PyQt5

# Hauptanwendung starten
python main.py

# Filter-System testen
python linear_filter_integration_example.py

# Matrix-Pipeline testen
python test_matrix_pipeline.py
```

### Debugging & Analyse
```powershell
# Filter-Pipeline analysieren
python analyze_filter_pipeline.py

# Datenbank-Struktur prüfen
python check_database_raw.py

# System-Architektur analysieren
python architecture_analysis.py
```

### Logs & Monitoring
- **Haupt-Log**: `main.log` - Strukturierte Produktions-Logs
- **Debug-Logs**: `pdvm_*.log` - Modul-spezifische Debug-Ausgaben
- **Log-Format**: `%(asctime)s - %(levelname)s - %(message)s` mit UTF-8 Encoding

---

**WICHTIG**: Arbeite IMMER mit dem `LinearFilterExecutionManager` für Filter-Operationen und beachte die duale Datenbank-Architektur mit GCS-Template-System.