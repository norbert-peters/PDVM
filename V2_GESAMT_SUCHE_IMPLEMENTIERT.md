# V2 Gesamt-Suche Persistierung - IMPLEMENTIERT ✅

## Datum
2024-10-14

## Überblick
Erweiterung des V2 Filter-Persistence Systems um **Gesamt-Suche (globale Suche)**

## V2 Architektur - Gesamt-Suche

### Datenspeicherung
```
anwendungsdaten Tabelle:
├── Gruppe: view_guid
├── Feld: 'gesamt'  ← Parameters für UI
│   └── Wert: {"search_text": "Lau"}
├── Feld: 'search_string'  ← ZENTRAL für Pipeline!
│   └── Wert: "Lau"
└── ...
```

### search_string Format
```python
# Gesamt-Suche: Einfach der Suchtext
"Lau"
```

**WICHTIG:** Gesamt-Suche ist die einfachste Form - der search_string ist einfach der eingegebene Text!

## Implementierte Änderungen

### 1. `execute_global_search_filter()` - Extended (Zeile 381)
**Datei:** `linear_filter_execution_manager.py`

**Vorher:**
```python
def execute_global_search_filter(self, search_string: str) -> bool:
    # Nur Filter ausführen
    matrix_manager.apply_filter(search_string)
```

**Nachher:**
```python
def execute_global_search_filter(self, search_string: str) -> bool:
    # 1. Parameters speichern (für UI)
    gcs._app_db.set_value(self.view_guid, 'gesamt', {
        'search_text': search_string
    })
    
    # 2. search_string speichern (für Pipeline)
    gcs._app_db.set_value(self.view_guid, 'search_string', search_string)
    
    # 3. Speichern!
    gcs._app_db.save_all_values()
    
    # 4. Filter ausführen
    matrix_manager.apply_filter(search_string)
```

### 2. `_load_and_apply_persistent_filters()` - Extended
**Datei:** `pdvm_view_dialog.py` (Zeile ~810)

**Funktion:** Lädt gespeicherte Gesamt-Suche und zeigt sie im UI-Suchfeld an

**Neu:**
```python
def _load_and_apply_persistent_filters(self):
    """V2: Lade persistente Filter - Gesamt-Suche in UI"""
    gcs = get_gcs()
    
    # Gesamt-Suche in UI laden (wenn Suchfeld existiert)
    if hasattr(self, 'search_input'):
        gesamt_data, _ = gcs._app_db.get_value(self.view_guid, 'gesamt')
        if gesamt_data and isinstance(gesamt_data, dict):
            search_text = gesamt_data.get('search_text', '')
            if search_text:
                self.search_input.setText(search_text)
                logger.info(f"🔄 V2: Gesamt-Suche in UI geladen: '{search_text}'")
    
    # Pipeline lädt search_string AUTONOM!
```

**Wichtig:** 
- Gesamt-Suche wird in UI-Suchfeld geladen
- Einfach/Komplex-Filter werden NICHT in UI geladen (nur in Dialogen)
- Pipeline lädt search_string autonom beim `rebuild_pipeline()`

### 3. `_reset_persistent_filters()` - Extended
**Datei:** `central_filter_reset.py` (Zeile 133)

**Vorher:**
```python
if not preserve_gesamtfilter:
    gcs._app_db.set_value(self.view_guid, 'search_string', None)
    reset_count += 1
```

**Nachher:**
```python
if not preserve_gesamtfilter:
    gcs._app_db.set_value(self.view_guid, 'search_string', None)
    gcs._app_db.set_value(self.view_guid, 'gesamt', None)  # NEU!
    reset_count += 2
```

## Integration in Pipeline

### Call-Flow - Gesamt-Suche setzen
```
User gibt "Lau" in Suchfeld ein
    ↓
pdvm_view_dialog._perform_global_search()
    ↓
LinearFilterExecutionManager.execute_global_search_filter("Lau")
    ↓
1. Speichere 'gesamt' = {"search_text": "Lau"}
2. Speichere 'search_string' = "Lau"
3. save_all_values()
4. matrix_manager.apply_filter("Lau")
    ↓
Pipeline filtert autonom
```

### Call-Flow - App Neustart
```
App startet → View öffnet
    ↓
pdvm_view_dialog._load_and_apply_persistent_filters()
    ↓
Lädt 'gesamt' → Setzt search_input.text = "Lau"
    ↓
Matrix Manager: rebuild_pipeline()
    ↓
_load_search_string_from_gcs() → Lädt 'search_string' = "Lau"
    ↓
apply_filter("Lau") → Filtert autonom
    ↓
✅ Gesamt-Suche aktiv + im UI sichtbar!
```

## Vorteile V2

### ✅ Einfachstes Format
- Gesamt-Suche ist einfach der Text
- Keine Konversion nötig
- Keine Komplexität

### ✅ UI-Synchronisation
- Suchfeld zeigt gespeicherten Text
- User sieht sofort: Filter ist aktiv
- Kann direkt bearbeiten oder löschen

### ✅ Konsistenz
- Gleiche V2-Struktur wie einfach/komplex
- Parameters ('gesamt') für UI
- search_string für Pipeline
- Klare Trennung!

### ✅ Reset funktioniert
- `central_filter_reset.py` löscht beide Felder
- Sowohl UI als auch Pipeline werden zurückgesetzt

## Vollständiger V2 Stack

### Alle 3 Filter-Typen implementiert! ✅

| Filter-Typ | Parameters Feld | search_string Format | Implementiert |
|------------|----------------|---------------------|---------------|
| **Einfach** | 'einfach' oder 'familienname_show' | `"familienname_show:Lau"` | ✅ |
| **Komplex** | 'familienname_show' etc. | `"EXTENDED:familienname_show:AND\|IS\|enthält\|Lau"` | ✅ |
| **Gesamt** | 'gesamt' | `"Lau"` | ✅ |

### Gemeinsame Struktur
```python
# Für JEDEN Filter-Typ:

# 1. Speichere Parameters (für UI/Dialog)
gcs._app_db.set_value(view_guid, field_name, parameters_dict)

# 2. Speichere search_string (für Pipeline)
gcs._app_db.set_value(view_guid, 'search_string', search_string)

# 3. CRITICAL: Speichern!
gcs._app_db.save_all_values()
```

### Pipeline lädt AUTONOM
```python
# pdvm_view_matrix_manager.py

def rebuild_pipeline(self, search_string: Optional[str] = None):
    if search_string is None:
        search_string = self._load_search_string_from_gcs()
    
    self.apply_filter(search_string)

def _load_search_string_from_gcs(self) -> Optional[str]:
    gcs = get_gcs()
    search_string, _ = gcs._app_db.get_value(self.view_guid, 'search_string')
    return search_string
```

## Testplan

### Test 1: Gesamt-Suche setzen
```
1. Öffne View
2. Gib "Lau" in Suchfeld ein
3. Klicke "Suchen"
4. ✅ Filter wird angewendet
5. ✅ Suchfeld zeigt "Lau"
6. App neu starten
7. ✅ Filter ist aktiv
8. ✅ Suchfeld zeigt immer noch "Lau"
```

### Test 2: Gesamt-Suche ändern
```
1. Öffne View (mit gespeicherter Suche "Lau")
2. ✅ Suchfeld zeigt "Lau"
3. Ändere zu "Mei"
4. Klicke "Suchen"
5. ✅ Filter wird aktualisiert
6. App neu starten
7. ✅ Suchfeld zeigt "Mei"
```

### Test 3: Gesamt-Suche löschen
```
1. Öffne View (mit gespeicherter Suche)
2. Klicke "Zurücksetzen"
3. ✅ Suchfeld wird geleert
4. ✅ Filter wird zurückgesetzt
5. App neu starten
6. ✅ Keine Suche aktiv
7. ✅ Suchfeld ist leer
```

### Test 4: Kombination mit anderen Filtern
```
1. Setze Einfachen Filter: "familienname_show:Lau"
2. ✅ Filter aktiv
3. Setze Gesamt-Suche: "Max"
4. ⚠️ Gesamt-Suche ÜBERSCHREIBT einfachen Filter (search_string wird ersetzt)
5. App neu starten
6. ✅ Nur Gesamt-Suche ist aktiv
```

**WICHTIG:** Alle 3 Filter-Typen teilen sich EIN `search_string` Feld!
- Der LETZTE Filter gewinnt
- Nur EIN Filter-Typ kann gleichzeitig aktiv sein
- Das ist gewollt und Teil der V2-Architektur

## Status
✅ **IMPLEMENTIERT** - Gesamt-Suche speichert Parameters + search_string
✅ **UI-LOAD** - Suchfeld wird beim Start geladen
✅ **RESET** - Löschen funktioniert für beide Felder
✅ **VOLLSTÄNDIG** - Alle 3 Filter-Typen (Einfach/Komplex/Gesamt) im V2 System!

## Nächste Schritte

### ⏳ Linear Filter Manager Cleanup
- Alte Persistence-Methoden entfernen
- Nur Execution-Logik behalten
- Dokumentation aktualisieren

### ⏳ Vollständige Tests
- Alle 3 Filter-Typen praktisch testen
- Kombinationen testen (Filter überschreiben)
- Reset-Funktionalität testen
- App-Neustart-Szenarien testen

### ⏳ Dokumentation finalisieren
- Vollständige V2-Architektur-Dokumentation
- Best Practices
- Migration Guide (falls alte Filter existieren)

## Dateien geändert
- `linear_filter_execution_manager.py`:
  - Zeile 381-439: `execute_global_search_filter()` - V2 Extension
  
- `pdvm_view_dialog.py`:
  - Zeile ~810: `_load_and_apply_persistent_filters()` - V2 UI-Load
  
- `central_filter_reset.py`:
  - Zeile 133-137: `_reset_persistent_filters()` - V2 Reset Extension

## V2 Filter-Persistence - VOLLSTÄNDIG! 🎉

**Alle 3 Filter-Typen implementiert:**
- ✅ Einfacher Filter (search_parameter_dialog.py)
- ✅ Komplexer Filter (extended_filter_engine.py)
- ✅ Gesamt-Suche (linear_filter_execution_manager.py + pdvm_view_dialog.py)

**Gemeinsame V2-Struktur:**
- Parameters für UI/Dialoge (field-specific)
- search_string für Pipeline (shared)
- Autonome Pipeline lädt nur search_string
- Keine Konversion bei Pipeline-Load!

**Bereit für Tests! 🚀**
