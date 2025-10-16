# ✅ EINFACH + KOMPLEX Filter FIX

## 🎯 Problem

**Symptom**: Einfach und Komplex Filter funktionieren **nur** bis View-Neuaufruf
- ❌ Parameter **nicht** in DB
- ❌ `s_string` und `s_source` **nicht** gesetzt
- ❌ Nach App-Restart: Filter **weg**

**Root Cause**: SearchParameterDialog wird **OHNE `matrix_manager`** aufgerufen!

```python
# VORHER (FALSCH):
dialog = SearchParameterDialog(self, view_guid, self.view_dialog.controls_config, current_filters)
#                                                                                   ^^^^^^^^^^^^
#                                                                    matrix_manager FEHLT!
```

**Konsequenz**:
- `self.matrix_manager = None` im Dialog
- `self.einfach_filter_manager = None` (Check schlägt fehl)
- `self.komplex_filter_manager = None` (Check schlägt fehl)
- Manager werden **NICHT** ausgeführt → **KEINE** Persistierung!

## 🔧 Fix Details

### 1. pdvm_view_dialog.py ✅

**Problem**: Dialog-Aufruf ohne `matrix_manager` Parameter

**Zeile 3371 (ALT)**:
```python
dialog = SearchParameterDialog(self, view_guid, self.view_dialog.controls_config, current_filters)
```

**Zeile 3363-3377 (NEU)**:
```python
# Matrix Manager für V3 Filter-Manager holen
matrix_manager = None
if hasattr(self.view_dialog, 'controller') and self.view_dialog.controller:
    if hasattr(self.view_dialog.controller, 'matrix_manager'):
        matrix_manager = self.view_dialog.controller.matrix_manager
        logger.info(f"✅ Matrix Manager für SearchParameterDialog geholt")

# Modal-Dialog öffnen mit controls_config direkt übergeben (V3: MIT matrix_manager!)
dialog = SearchParameterDialog(self, view_guid, self.view_dialog.controls_config, current_filters, matrix_manager)
```

**Resultat**: Manager werden initialisiert ✅

### 2. einfach_filter_manager.py ✅

**Problem**: `apply_filter()` ohne `filter_source` aufgerufen

**Zeile 75 (ALT)**:
```python
self.matrix_manager.apply_filter(search_string)
```

**Zeile 75 (NEU)**:
```python
self.matrix_manager.apply_filter(search_string, filter_source='einfach')
```

**Resultat**: Parser kann source-basiert interpretieren ✅

### 3. komplex_filter_manager.py ✅

**Problem**: `apply_filter()` ohne `filter_source` aufgerufen

**Zeile 86 (ALT)**:
```python
self.matrix_manager.apply_filter(search_string)
```

**Zeile 86 (NEU)**:
```python
self.matrix_manager.apply_filter(search_string, filter_source='komplex')
```

**Resultat**: Parser kann source-basiert interpretieren ✅

## 🔄 Workflow nach Fix

### EINFACH-Filter (z.B. Familienname = "Müller")

```
User: Öffnet Suchparameter-Dialog
    ↓
pdvm_view_dialog.py:
    matrix_manager = controller.matrix_manager  ✅ GEHOLT!
    dialog = SearchParameterDialog(..., matrix_manager)
    ↓
SearchParameterDialog.__init__():
    self.matrix_manager = matrix_manager  ✅ GESETZT!
    self.einfach_filter_manager = EinfachFilterManager(view_guid, matrix_manager)  ✅
    ↓
User: Gibt "Müller" ein → Übernehmen
    ↓
SearchParameterDialog.accept_changes():
    clean_filters = {"familienname_show": "Müller"}
    self.einfach_filter_manager.execute_einfach_filter(clean_filters)  ✅
    ↓
EinfachFilterManager.execute_einfach_filter():
    1. ✅ gcs._app_db.set_value(view_guid, 'familienname_show', {
           'simple_search': 'Müller',
           'conditions': []
       })
    2. ✅ search_string = "familienname_show:contains:Müller"
    3. ✅ gcs._app_db.set_value(view_guid, 's_string', search_string)
    4. ✅ gcs._app_db.set_value(view_guid, 's_source', 'einfach')
    5. ✅ gcs._app_db.save_all_values()  ← IN DB GESCHRIEBEN!
    6. ✅ matrix_manager.apply_filter(search_string, filter_source='einfach')
```

### KOMPLEX-Filter (z.B. Familienname AND IS enthält "Müller")

```
User: Erweitert → Bedingung hinzufügen
    ↓
SearchParameterDialog.accept_changes():
    field_conditions = {
        "familienname_show": [{
            'position_1': 'AND',
            'position_2': 'IS',
            'position_3': 'enthält',
            'position_4': 'Müller'
        }]
    }
    self.komplex_filter_manager.execute_komplex_filter(field_conditions)  ✅
    ↓
KomplexFilterManager.execute_komplex_filter():
    1. ✅ gcs._app_db.set_value(view_guid, 'familienname_show', {
           'simple_search': '',
           'conditions': [condition_dict]
       })
    2. ✅ search_string = "familienname_show:AND|IS|enthält|Müller"
    3. ✅ gcs._app_db.set_value(view_guid, 's_string', search_string)
    4. ✅ gcs._app_db.set_value(view_guid, 's_source', 'komplex')
    5. ✅ gcs._app_db.save_all_values()  ← IN DB GESCHRIEBEN!
    6. ✅ matrix_manager.apply_filter(search_string, filter_source='komplex')
```

## 📊 Datenbank nach Fix

**Anwendungsdaten Table**:

```sql
-- EINFACH-Filter "Müller":
gruppe          | feld                | wert
----------------|---------------------|------------------------------------------
view_guid       | familienname_show   | {"simple_search": "Müller", "conditions": []}
view_guid       | s_string            | "familienname_show:contains:Müller"
view_guid       | s_source            | "einfach"

-- KOMPLEX-Filter:
gruppe          | feld                | wert
----------------|---------------------|------------------------------------------
view_guid       | familienname_show   | {"simple_search": "", "conditions": [{"position_1": "AND", ...}]}
view_guid       | s_string            | "familienname_show:AND|IS|enthält|Müller"
view_guid       | s_source            | "komplex"
```

## 🧪 Test-Szenario

### Test 1: EINFACH-Filter Persistierung

```
1. App starten → View öffnen
2. Suchparameter → Familienname = "Müller" → Übernehmen
3. Prüfe Ergebnis: 2 Treffer (z.B.)
4. Prüfe Log:
   ✅ "V3 EINFACH-Filter angewendet: 1 Felder"
   ✅ "save_all_values() aufgerufen - Daten in DB"
5. Prüfe DB (python check_filter_db.py):
   ✅ familienname_show → {"simple_search": "Müller", "conditions": []}
   ✅ s_string → "familienname_show:contains:Müller"
   ✅ s_source → "einfach"
6. App schließen
7. App NEU starten → View öffnen
8. Erwartung: Filter AKTIV, 2 Treffer, Suchfeld LEER (kein Global)
```

### Test 2: KOMPLEX-Filter Persistierung

```
1. App starten → View öffnen
2. Suchparameter → Erweitert → Familienname: enthält "Müller" → Übernehmen
3. Prüfe Ergebnis: 2 Treffer
4. Prüfe Log:
   ✅ "V3 KOMPLEX-Filter angewendet: 1 Felder"
   ✅ "save_all_values() aufgerufen - Daten in DB"
5. Prüfe DB:
   ✅ familienname_show → {"simple_search": "", "conditions": [...]}
   ✅ s_string → "familienname_show:AND|IS|enthält|Müller"
   ✅ s_source → "komplex"
6. App schließen
7. App NEU starten → View öffnen
8. Erwartung: Filter AKTIV, 2 Treffer, Suchfeld LEER
```

### Test 3: Filter-Wechsel

```
1. EINFACH-Filter: Familienname = "Müller" → 2 Treffer
2. Prüfe DB: s_source = "einfach"
3. KOMPLEX-Filter: Familienname enthält "Schmidt" → 3 Treffer
4. Prüfe DB: s_source = "komplex" (überschrieben!)
5. Restart → Erwartung: KOMPLEX aktiv, 3 Treffer
```

## ✅ Zusammenfassung

**3 Dateien geändert**:
1. ✅ `pdvm_view_dialog.py`: matrix_manager wird an Dialog übergeben
2. ✅ `einfach_filter_manager.py`: apply_filter() mit filter_source='einfach'
3. ✅ `komplex_filter_manager.py`: apply_filter() mit filter_source='komplex'

**Resultat**:
- ✅ Manager werden initialisiert
- ✅ Parameter werden in DB geschrieben
- ✅ s_string wird gesetzt
- ✅ s_source wird gesetzt
- ✅ save_all_values() wird aufgerufen
- ✅ Filter überleben App-Restart

**Next**: Test mit echten Daten! 🚀
