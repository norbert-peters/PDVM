# 🎯 FILTER-PERSISTIERUNG V2 - EINFACH UND ELEGANT

## Problem mit V1
- Zu kompliziert: Konvertierung von Config zu search_string in Pipeline
- Inkonsistent: 3 verschiedene Filter-Arten unterschiedlich behandelt
- Fehleranfällig: Viele Konvertierungs-Schritte

## ✅ Lösung V2: KISS-Prinzip (Keep It Simple, Stupid!)

### Persistierung-Schema
```
gcs._app_db unter view_guid:
├── 'einfach'      → Parameter für Dialog-Anzeige
├── 'komplex'      → Parameter für Dialog-Anzeige
├── 'gesamt'       → Parameter für Suchfeld-Anzeige (NEU!)
└── 'search_string' → Der AKTIVE Filter für Pipeline (NEU!)
```

### Workflow

#### 1. Filter setzen (Einfach-Dialog)
```python
# search_parameter_dialog.py: on_apply()
def on_apply():
    # 1. Erstelle search_string aus Parametern
    search_string = f"{field_name}_show:{search_value}"
    
    # 2. Speichere BEIDE in GCS
    gcs._app_db.set_value(view_guid, 'einfach', {
        'field_name': field_name,
        'search_value': search_value,
        'operator': operator
    })
    gcs._app_db.set_value(view_guid, 'search_string', search_string)
    gcs._app_db.save_all_values()  # 💾 CRITICAL!
    
    # 3. Pipeline neu durchlaufen
    matrix_manager.rebuild_pipeline()  # Lädt search_string autonom!
```

#### 2. Filter setzen (Komplex-Dialog)
```python
# extended_filter_engine.py: on_apply()
def on_apply():
    # 1. Erstelle search_string aus Bedingungen
    search_string = self._build_search_string_from_conditions(conditions)
    
    # 2. Speichere BEIDE in GCS
    gcs._app_db.set_value(view_guid, 'komplex', {
        'conditions': conditions,
        'logic': logic
    })
    gcs._app_db.set_value(view_guid, 'search_string', search_string)
    gcs._app_db.save_all_values()  # 💾 CRITICAL!
    
    # 3. Pipeline neu durchlaufen
    matrix_manager.rebuild_pipeline()
```

#### 3. Filter setzen (Gesamt-Suchfeld auf View)
```python
# pdvm_view_controller.py: on_global_search()
def on_global_search(search_text):
    # 1. Erstelle search_string (global = alle Felder)
    search_string = search_text  # Einfach der Text
    
    # 2. Speichere BEIDE in GCS
    gcs._app_db.set_value(view_guid, 'gesamt', {
        'search_text': search_text
    })
    gcs._app_db.set_value(view_guid, 'search_string', search_string)
    gcs._app_db.save_all_values()  # 💾 CRITICAL!
    
    # 3. Pipeline neu durchlaufen
    matrix_manager.rebuild_pipeline()
```

#### 4. Pipeline lädt Filter autonom
```python
# pdvm_view_matrix_manager.py: rebuild_pipeline()
def rebuild_pipeline(self, search_string=None):
    # Filter AUTONOM aus GCS holen
    if search_string is None:
        search_string = self._load_search_string_from_gcs()
    
    # Filter direkt anwenden
    self.apply_filter(search_string)
    
    # Sort autonom aus GCS
    sort_config = self._load_sort_config_from_gcs()
    self.apply_sort(sort_config)

def _load_search_string_from_gcs(self):
    """Lädt search_string DIREKT - KEINE Konvertierung!"""
    gcs = get_gcs()
    search_string, _ = gcs._app_db.get_value(self.view_guid, 'search_string')
    return search_string
```

#### 5. Dialog lädt Parameter
```python
# search_parameter_dialog.py: load_from_gcs()
def load_from_gcs():
    """Lädt Parameter für Dialog-Anzeige"""
    gcs = get_gcs()
    params, _ = gcs._app_db.get_value(view_guid, 'einfach')
    
    if params:
        self.field_combo.setCurrentText(params['field_name'])
        self.search_input.setText(params['search_value'])
        self.operator_combo.setCurrentText(params['operator'])
```

#### 6. Filter zurücksetzen
```python
# pdvm_view_controller.py: reset_filter()
def reset_filter():
    # Lösche ALLE Filter-Daten
    gcs._app_db.set_value(view_guid, 'einfach', None)
    gcs._app_db.set_value(view_guid, 'komplex', None)
    gcs._app_db.set_value(view_guid, 'gesamt', None)
    gcs._app_db.set_value(view_guid, 'search_string', None)
    gcs._app_db.save_all_values()  # 💾 CRITICAL!
    
    # Pipeline neu (ohne Filter)
    matrix_manager.rebuild_pipeline()
```

## 📝 Implementierungs-Checkliste

### Matrix Manager (pdvm_view_matrix_manager.py)
- [x] ✅ `rebuild_pipeline()` - Parameter zu `search_string` ändern
- [x] ✅ `_load_search_string_from_gcs()` - Neue einfache Methode
- [ ] ❌ ENTFERNEN: `_apply_filter_from_gcs()`
- [ ] ❌ ENTFERNEN: `_convert_filter_config_to_search_string()`
- [ ] ❌ ENTFERNEN: `_load_filter_config_from_gcs()`

### Einfacher Filter-Dialog (search_parameter_dialog.py)
- [ ] `on_apply()` - Speichert Parameter + search_string
- [ ] `load_from_gcs()` - Lädt Parameter (nicht search_string!)
- [ ] Konvertierungs-Methode: Parameter → search_string

### Komplexer Filter-Dialog (extended_filter_engine.py)
- [ ] `on_apply()` - Speichert Bedingungen + search_string
- [ ] `load_from_gcs()` - Lädt Bedingungen
- [ ] Konvertierungs-Methode: Bedingungen → search_string

### View Controller (pdvm_view_controller.py)
- [ ] `on_global_search()` - Speichert Text + search_string unter 'gesamt'
- [ ] `reset_filter()` - Löscht alle 4 Felder
- [ ] `load_last_search()` - Lädt Suchfeld-Text aus 'gesamt'

### Linear Filter Manager (linear_filter_execution_manager.py)
- [ ] ❌ ENTFERNEN: Alle Persistierung-Methoden (werden in Dialogen gemacht!)
- [ ] ❌ ENTFERNEN: `load_filter_from_gcs()`
- [ ] ❌ ENTFERNEN: `_save_filter_to_gcs()`
- [ ] ❌ ENTFERNEN: `_clear_filters_from_gcs()`

## 🎯 Vorteile

✅ **Einfach**: Nur 1 Feld für Filter (`search_string`), 3 Felder für Dialog-Anzeige
✅ **Konsistent**: Alle 3 Filterarten gleich behandelt
✅ **Autonom**: Pipeline lädt nur `search_string`, keine Konvertierung
✅ **Transparent**: Parameter für UI, search_string für Logik
✅ **Wartbar**: Jeder Dialog verantwortlich für seine Parameter
✅ **Testbar**: Klare Trennung zwischen UI und Logik

## 📊 Datenbank-Struktur

```sql
-- Nach Einfach-Filter "Lau" auf "Familienname":
gruppe: "0d10a0d0-..."
feld: "einfach"
wert: '{"field_name": "familienname_show", "search_value": "Lau", "operator": "enthält"}'

gruppe: "0d10a0d0-..."
feld: "search_string"
wert: "familienname_show:Lau"

-- Nach Komplex-Filter:
gruppe: "0d10a0d0-..."
feld: "komplex"
wert: '{"conditions": [...], "logic": "AND"}'

gruppe: "0d10a0d0-..."
feld: "search_string"
wert: "familienname_show:Lau AND ort_show:Berlin"

-- Nach Gesamt-Suche "li":
gruppe: "0d10a0d0-..."
feld: "gesamt"
wert: '{"search_text": "li"}'

gruppe: "0d10a0d0-..."
feld: "search_string"
wert: "li"  # Global search = einfach der Text
```

## 🚀 Nächste Schritte

1. ✅ Matrix Manager vereinfachen (NUR search_string laden)
2. ⏳ Dialoge erweitern (Parameter + search_string speichern)
3. ⏳ View Controller erweitern (Gesamt-Filter)
4. ⏳ Linear Filter Manager bereinigen (Persistierung raus!)
5. ⏳ Testen mit allen 3 Filterarten

**Status**: Matrix Manager-Änderungen IN PROGRESS
