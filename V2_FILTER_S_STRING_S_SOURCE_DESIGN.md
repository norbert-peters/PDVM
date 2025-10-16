# V2 Filter: s_string + s_source Design ✅

## Problem (User-Beschreibung)

**Schnellsuche**:
- Text wird eingegeben & Filter funktioniert
- Nach App-Restart: Filter ist aktiv, aber **Text wird nicht angezeigt**
- Nach Einfach/Komplex-Filter: Schnellsuche-Text **bleibt stehen**, obwohl anderer Filter aktiv ist

**Root Cause**: 
- Wir wussten nicht, **welcher Filter** gerade aktiv ist
- Schnellsuche-Feld wurde immer befüllt, egal welcher Filter aktiv war

---

## Lösung (User-Vorgabe)

Statt nur `search_string`, speichern wir **zwei Werte ZUSAMMEN**:

| Feld | Typ | Beschreibung |
|------|-----|--------------|
| `s_string` | String | Der eigentliche search_string (z.B. `"lau"` oder `"familienname_show:Müller"`) |
| `s_source` | String | Die Quelle des Filters (`'schnell'`, `'einfach'`, `'komplex'`) |

**Regel**: Diese zwei Werte werden **IMMER ZUSAMMEN** gesetzt!

---

## Implementierung

### 1. Schnellsuche speichert s_string + s_source

**Datei**: `pdvm_view_controller.py`
**Methode**: `execute_search()`

```python
def execute_search(self):
    search_text = 'lau'
    
    # 1. Speichere Parameter unter 'schnell'
    gcs._app_db.set_value(view_guid, 'schnell', {'search_text': 'lau'})
    
    # 2. Speichere s_string + s_source (ZUSAMMEN!)
    gcs._app_db.set_value(view_guid, 's_string', 'lau')
    gcs._app_db.set_value(view_guid, 's_source', 'schnell')
    
    # 3. Speichere alles
    gcs._app_db.save_all_values()
    
    # 4. Matrix Manager aufrufen
    matrix_manager.apply_filter('lau')
```

**Gespeichert**:
- `gruppe='view_guid'`, `feld='schnell'` → `{"search_text": "lau"}`
- `gruppe='view_guid'`, `feld='s_string'` → `"lau"`
- `gruppe='view_guid'`, `feld='s_source'` → `"schnell"`

---

### 2. Parameter Dialog (Einfach) speichert s_string + s_source

**Datei**: `search_parameter_dialog.py`
**Methode**: `accept_changes()`

```python
def accept_changes(self):
    new_filters = {'familienname_show': 'Müller'}
    filter_type = 'einfach'
    
    # 1. Speichere Parameter
    self.save_persistent_filters(new_filters)
    
    # 2. Baue search_string
    search_string = "familienname_show:Müller"
    
    # 3. Speichere s_string + s_source (ZUSAMMEN!)
    gcs._app_db.set_value(view_guid, 's_string', search_string)
    gcs._app_db.set_value(view_guid, 's_source', 'einfach')
    gcs._app_db.save_all_values()
    
    # 4. Matrix Manager aufrufen
    matrix_manager.apply_filter(search_string)
```

**Gespeichert**:
- `gruppe='view_guid'`, `feld='familienname_show'` → `{"simple_search": "Müller", "conditions": []}`
- `gruppe='view_guid'`, `feld='s_string'` → `"familienname_show:Müller"`
- `gruppe='view_guid'`, `feld='s_source'` → `"einfach"`

---

### 3. Parameter Dialog (Komplex) speichert s_string + s_source

**Gleicher Code wie oben**, nur:
- `filter_type = 'komplex'`
- `search_string = "EXTENDED:familienname_show:AND|IS|enthält|Müller"`
- `s_source = 'komplex'`

**Gespeichert**:
- `gruppe='view_guid'`, `feld='familienname_show'` → `{"simple_search": "", "conditions": [...]}`
- `gruppe='view_guid'`, `feld='s_string'` → `"EXTENDED:familienname_show:AND|IS|enthält|Müller"`
- `gruppe='view_guid'`, `feld='s_source'` → `"komplex"`

---

### 4. Extended Filter Engine speichert s_string + s_source

**Datei**: `extended_filter_engine.py`
**Methode**: `save_field_conditions()`

```python
def save_field_conditions(self, field_key: str, conditions: List):
    # 1. Speichere Conditions für dieses Feld
    gcs._app_db.set_value(view_guid, field_key, current_data)
    
    # 2. Baue search_string für ALLE Extended Felder
    search_string = self._build_search_string_from_conditions(field_key, conditions)
    
    # 3. Speichere s_string + s_source (ZUSAMMEN!)
    gcs._app_db.set_value(view_guid, 's_string', search_string)
    gcs._app_db.set_value(view_guid, 's_source', 'komplex')
    gcs._app_db.save_all_values()
```

**Hinweis**: Extended Filter setzt immer `s_source = 'komplex'`

---

### 5. Matrix Manager lädt s_string (nicht mehr search_string)

**Datei**: `pdvm_view_matrix_manager.py`
**Methode**: `_load_search_string_from_gcs()`

```python
def _load_search_string_from_gcs(self) -> Optional[str]:
    """Lädt s_string aus GCS"""
    
    # Lade s_string + s_source
    s_string, _ = gcs._app_db.get_value(self.view_guid, 's_string')
    s_source, _ = gcs._app_db.get_value(self.view_guid, 's_source')
    
    if s_string:
        logger.info(f"s_string geladen: '{s_string}' (Quelle: {s_source})")
        return s_string
    else:
        return None
```

---

### 6. View-Aufbau lädt Schnellsuche NUR wenn s_source == 'schnell'

**Datei**: `pdvm_view_dialog.py`
**Methode**: `_load_and_apply_persistent_filters()`

```python
def _load_and_apply_persistent_filters(self):
    """Lädt persistente Filter in UI - NUR Schnellsuche wenn s_source=='schnell'"""
    
    if hasattr(self, 'search_input'):
        # Prüfe s_source
        s_source, _ = gcs._app_db.get_value(self.view_guid, 's_source')
        
        if s_source == 'schnell':
            # Nur bei Schnellsuche: Text anzeigen
            schnell_data, _ = gcs._app_db.get_value(self.view_guid, 'schnell')
            if schnell_data:
                search_text = schnell_data.get('search_text', '')
                self.search_input.setText(search_text)
                logger.info(f"✅ Schnellsuche wiederhergestellt: '{search_text}'")
        else:
            # Anderer Filter aktiv → Suchfeld LEER
            self.search_input.clear()
            logger.info(f"ℹ️ Schnellsuche-Feld leer (s_source='{s_source}')")
```

---

## Datenbank-Struktur

**Tabelle**: `anwendungsdaten`

### Beispiel 1: Schnellsuche aktiv

| gruppe | feld | wert |
|--------|------|------|
| `view_guid` | `schnell` | `{"search_text": "lau"}` |
| `view_guid` | `s_string` | `"lau"` |
| `view_guid` | `s_source` | `"schnell"` |

**UI-Verhalten**: Schnellsuche-Feld zeigt `"lau"`

---

### Beispiel 2: Einfacher Filter aktiv

| gruppe | feld | wert |
|--------|------|------|
| `view_guid` | `schnell` | `{"search_text": "lau"}` _(bleibt erhalten!)_ |
| `view_guid` | `familienname_show` | `{"simple_search": "Müller", "conditions": []}` |
| `view_guid` | `s_string` | `"familienname_show:Müller"` |
| `view_guid` | `s_source` | `"einfach"` |

**UI-Verhalten**: Schnellsuche-Feld ist **LEER** (weil `s_source != 'schnell'`)

---

### Beispiel 3: Komplexer Filter aktiv

| gruppe | feld | wert |
|--------|------|------|
| `view_guid` | `schnell` | `{"search_text": "lau"}` _(bleibt erhalten!)_ |
| `view_guid` | `familienname_show` | `{"simple_search": "", "conditions": [...]}` |
| `view_guid` | `s_string` | `"EXTENDED:familienname_show:AND\|IS\|enthält\|Müller"` |
| `view_guid` | `s_source` | `"komplex"` |

**UI-Verhalten**: Schnellsuche-Feld ist **LEER** (weil `s_source != 'schnell'`)

---

## Verhalten nach Filter-Wechsel

### Szenario: Schnellsuche → Einfacher Filter

1. User gibt "lau" in Schnellsuche ein
   - Gespeichert: `s_string="lau"`, `s_source="schnell"`
   - UI: Schnellsuche-Feld zeigt "lau" ✅

2. User setzt Einfachen Filter "Müller"
   - Gespeichert: `s_string="familienname_show:Müller"`, `s_source="einfach"`
   - UI: Schnellsuche-Feld wird **GELEERT** ✅ (weil s_source != 'schnell')

3. App-Restart
   - Matrix Manager lädt: `s_string="familienname_show:Müller"`
   - Filter wird angewendet ✅
   - UI: Schnellsuche-Feld bleibt **LEER** ✅ (weil s_source == 'einfach')

---

### Szenario: Einfacher Filter → Schnellsuche

1. User setzt Einfachen Filter "Müller"
   - Gespeichert: `s_string="familienname_show:Müller"`, `s_source="einfach"`
   - UI: Schnellsuche-Feld ist leer ✅

2. User gibt "lau" in Schnellsuche ein
   - Gespeichert: `s_string="lau"`, `s_source="schnell"`
   - UI: Schnellsuche-Feld zeigt "lau" ✅

3. App-Restart
   - Matrix Manager lädt: `s_string="lau"`
   - Filter wird angewendet ✅
   - UI: Schnellsuche-Feld zeigt "lau" ✅ (weil s_source == 'schnell')

---

## Test-Szenarien

### Test 1: Schnellsuche persistent
1. Gib "lau" in Schnellsuche ein → Suchen
2. **Erwartung**: 3 Treffer, Suchfeld zeigt "lau"
3. App schließen & neu starten
4. View öffnen
5. **Erwartung**: 3 Treffer, Suchfeld zeigt **"lau"** ✅

**Log-Check**:
```
💾 Schnellsuche: s_string='lau' + s_source='schnell' gespeichert
🔄 Schnellsuche in UI wiederhergestellt: 'lau' (s_source='schnell')
```

---

### Test 2: Schnellsuche → Einfacher Filter (Feld leer)
1. Gib "lau" in Schnellsuche ein → 3 Treffer
2. Öffne Parameter-Dialog: `familienname_show` = "Müller"
3. **Erwartung**: Suchfeld wird **GELEERT** ✅
4. App schließen & neu starten
5. **Erwartung**: Filter aktiv, Suchfeld **LEER** ✅

**Log-Check**:
```
💾 EINFACH: s_string='familienname_show:Müller' + s_source='einfach'
ℹ️ Schnellsuche-Feld leer (s_source='einfach')
```

---

### Test 3: Einfacher Filter → Schnellsuche (Feld gefüllt)
1. Parameter-Dialog: `familienname_show` = "Müller"
2. Gib "lau" in Schnellsuche ein
3. **Erwartung**: Suchfeld zeigt "lau" ✅
4. App schließen & neu starten
5. **Erwartung**: Schnellsuche aktiv, Suchfeld zeigt **"lau"** ✅

**Log-Check**:
```
💾 Schnellsuche: s_string='lau' + s_source='schnell' gespeichert
🔄 Schnellsuche in UI wiederhergestellt: 'lau' (s_source='schnell')
```

---

### Test 4: Komplexer Filter (Feld leer)
1. Parameter-Dialog (KOMPLEX): `familienname_show` ENTHÄLT "lau"
2. **Erwartung**: Suchfeld ist **LEER** ✅
3. App schließen & neu starten
4. **Erwartung**: Komplexer Filter aktiv, Suchfeld **LEER** ✅

**Log-Check**:
```
💾 KOMPLEX: s_string='EXTENDED:...' + s_source='komplex'
ℹ️ Schnellsuche-Feld leer (s_source='komplex')
```

---

## Geänderte Dateien

| Datei | Änderung | Status |
|-------|----------|--------|
| `pdvm_view_controller.py` | `execute_search()` speichert `s_string + s_source` | ✅ |
| `search_parameter_dialog.py` | `accept_changes()` speichert `s_string + s_source` | ✅ |
| `extended_filter_engine.py` | `save_field_conditions()` speichert `s_string + s_source` | ✅ |
| `pdvm_view_matrix_manager.py` | `_load_search_string_from_gcs()` lädt `s_string` | ✅ |
| `pdvm_view_dialog.py` | `_load_and_apply_persistent_filters()` prüft `s_source` | ✅ |

---

## Zusammenfassung

### Design-Prinzip
- ✅ **s_string + s_source werden IMMER ZUSAMMEN gesetzt**
- ✅ **s_source zeigt an, welcher Filter aktiv ist**
- ✅ **UI-Feld nur bei passendem s_source befüllen**

### Vorteile
1. ✅ **Schnellsuche-Feld zeigt nur bei Schnellsuche Text**
2. ✅ **Nach Filter-Wechsel wird Feld korrekt geleert**
3. ✅ **Nach Restart wird richtiger Filter angezeigt**
4. ✅ **Sehr einfach & stabil**

### s_source Werte

| s_source | Filter-Typ | UI-Verhalten |
|----------|-----------|--------------|
| `'schnell'` | Globale Schnellsuche | Suchfeld befüllt |
| `'einfach'` | Parametrischer Filter (Simple) | Suchfeld leer |
| `'komplex'` | Parametrischer Filter (Extended) | Suchfeld leer |

---

**Status**: ✅ **FERTIG - BEREIT FÜR TESTS!**

Nächster Schritt: User testet alle 4 Szenarien!
