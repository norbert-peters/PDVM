# V2 Filter-Persistierung: Bugfix Complete ✅

## Problem-Analyse

**User-Report**: "Kein einziges Filter ist persistent und einen persistenten search_string finde ich auch nicht."

**Root Cause**: Filter wurden **NICHT** über `LinearFilterExecutionManager` ausgeführt!
- Schnellsuche rief direkt `matrix_manager.apply_search_filter()` auf
- Parameter Dialog rief nicht-existente `execute_parameter_dialog_filter()` auf
- **KEINE** Persistierung erfolgte, da `save_all_values()` nie aufgerufen wurde

## Implementierte Fixes

### 1. Schnellsuche (Global Search) ✅

**Datei**: `pdvm_view_controller.py`
**Methode**: `execute_search()`

**VORHER** (❌ Fehler):
```python
def execute_search(self):
    search_text = getattr(self, 'pending_search_text', '')
    # Direkt Matrix Manager - KEINE Persistierung!
    self.matrix_manager.apply_search_filter(search_text, visible_columns)
    self.refresh_ui_from_matrix()
```

**NACHHER** (✅ Korrekt):
```python
def execute_search(self):
    search_text = getattr(self, 'pending_search_text', '')
    # V2: LinearFilterExecutionManager mit Persistierung!
    if hasattr(self, 'filter_execution_manager'):
        success = self.filter_execution_manager.execute_global_search_filter(search_text)
        # Manager speichert:
        # - 'gesamt' → {'search_text': 'lau'}
        # - 'search_string' → 'lau'
        # - save_all_values() ✅
    self.refresh_ui_from_matrix()
```

**Was passiert**:
1. `execute_global_search_filter()` im Manager aufgerufen
2. Manager reset auf komplette Datenbasis
3. Manager speichert Parameters + search_string
4. Manager ruft `save_all_values()` auf ✅
5. Manager führt Filter aus
6. Controller aktualisiert UI

---

### 2. Parametrischer Filter (Simple/Complex) ✅

#### 2a. Neue Manager-Methode

**Datei**: `linear_filter_execution_manager.py`
**Methode**: `execute_parametric_filter()` - **NEU ERSTELLT**

```python
def execute_parametric_filter(self, search_string: str, filter_params: dict = None) -> bool:
    """
    V2: PARAMETRISCHER FILTER - filtert nach Feldern + persistiert search_string
    
    Args:
        search_string: Formatierter Filter-String (z.B. 'familienname_show:Müller')
        filter_params: Optional - Filter-Parameter für UI-Anzeige (dict)
    
    Returns:
        bool: True wenn erfolgreich, False wenn Fehler
    """
    # Reset zur kompletten Datenbasis
    self._reset_to_complete_data()
    
    # V2: Speichere search_string (Parameters wurden bereits vom Dialog gespeichert)
    gcs._app_db.set_value(self.view_guid, 'search_string', search_string)
    gcs._app_db.save_all_values()  # ✅ CRITICAL!
    
    # Führe Filter aus
    matrix_manager.apply_filter(search_string)
    
    return True
```

#### 2b. Parameter Dialog Korrektur

**Datei**: `search_parameter_dialog.py`
**Methode**: `accept_changes()`

**VORHER** (❌ Fehler):
```python
# Dialog speichert search_string selbst (doppelte Arbeit)
self._save_search_string_to_gcs(new_filters, extended_summary)

# Ruft nicht-existente Methode auf!
success = self.linear_filter_manager.execute_parameter_dialog_filter(
    new_filters, 
    extended_conditions, 
    force_complex=True
)  # ❌ AttributeError: Diese Methode existiert nicht!
```

**NACHHER** (✅ Korrekt):
```python
# Dialog speichert NUR Parameter für UI
self.save_persistent_filters(new_filters)

# Dialog baut search_string aus Parametern
search_parts = []
if extended_summary and len(extended_summary) > 0:
    # KOMPLEX: "EXTENDED:field:summary"
    for field_key, summary in extended_summary.items():
        search_parts.append(f"EXTENDED:{field_key}:{summary}")
else:
    # EINFACH: "field:value"
    for field_key, value in new_filters.items():
        search_parts.append(f"{field_key}:{value}")

search_string = "||".join(search_parts)

# V2: Manager macht ALLES (Reset + Filter + Persistierung)!
success = self.linear_filter_manager.execute_parametric_filter(
    search_string, 
    filter_params=new_filters
)  # ✅ Methode existiert + persistiert korrekt!
```

---

### 3. Extended Filter (Complex) ✅

**Datei**: `extended_filter_engine.py`
**Methode**: `save_field_conditions()` - **BEREITS V2-KONFORM**

**Status**: Keine Änderungen nötig! ✅

```python
def save_field_conditions(self, field_key: str, conditions: List):
    # Speichere Conditions unter field_key
    gcs._app_db.set_value(self.view_guid, field_key, current_data)
    
    # V2: Baue search_string für ALLE Extended Felder
    search_string = self._build_search_string_from_conditions(field_key, conditions)
    gcs._app_db.set_value(self.view_guid, 'search_string', search_string)
    
    # CRITICAL: Speichere beide zusammen
    gcs._app_db.save_all_values()  # ✅
    
    logger.info(f"💾 V2: Erweiterte Bedingungen + search_string gespeichert")
```

**Multi-Field Support**: `_build_search_string_from_conditions()` baut search_string für **ALLE** aktiven Extended Filter:
```python
# Wenn Extended Conditions für Feld A, B, C existieren:
# → search_string = "EXTENDED:fieldA:summary1||EXTENDED:fieldB:summary2||EXTENDED:fieldC:summary3"
```

---

## V2 Persistierungs-Architektur (Final)

### Duale Speicherung

Alle 3 Filter-Typen nutzen das gleiche Pattern:

```python
# 1. Parameters für UI-Anzeige (Dialog-spezifisch)
gcs._app_db.set_value(view_guid, field_name, parameters_dict)

# 2. search_string für autonome Pipeline (universal)
gcs._app_db.set_value(view_guid, 'search_string', search_string)

# 3. CRITICAL: Speichere beide zusammen!
gcs._app_db.save_all_values()  # ✅
```

### search_string Formate

| Filter-Typ | Format | Beispiel |
|-----------|--------|----------|
| **Global Search** | Nur Text | `"lau"` |
| **Parametric Simple** | `field:value` | `"familienname_show:Müller"` |
| **Parametric Multi** | `field1:value1\|\|field2:value2` | `"familienname_show:Müller\|\|vorname_show:Hans"` |
| **Extended Single** | `EXTENDED:field:summary` | `"EXTENDED:familienname_show:AND\|IS\|enthält\|Müller"` |
| **Extended Multi** | `EXTENDED:field1:summary1\|\|EXTENDED:field2:summary2` | Siehe unten |

**Extended Multi-Field Beispiel**:
```
EXTENDED:familienname_show:AND|IS|enthält|Müller||OR|IS|enthält|Schmidt||
EXTENDED:vorname_show:AND|IS|beginnt mit|H
```

### Autonome Pipeline

```python
def rebuild_pipeline(self, search_string: Optional[str] = None):
    if search_string is None:
        # AUTONOM: Lade aus GCS
        search_string = self._load_search_string_from_gcs()
    
    # Wende Filter an (keine Konvertierung nötig!)
    self.apply_filter(search_string)
```

---

## Geänderte Dateien

| Datei | Änderungen | Status |
|-------|-----------|--------|
| `pdvm_view_controller.py` | `execute_search()` → `execute_global_search_filter()` | ✅ |
| `search_parameter_dialog.py` | `accept_changes()` → `execute_parametric_filter()` | ✅ |
| `linear_filter_execution_manager.py` | `execute_parametric_filter()` NEU | ✅ |
| `extended_filter_engine.py` | Bereits V2-konform | ✅ |

---

## Test-Szenarien (Bereit zum Testen)

### Test 1: Schnellsuche (Global)
1. Öffne View
2. Gib "lau" in Schnellsuche ein
3. Klicke "Suchen"
4. **Erwartung**: 3 Treffer (Laurenne × 2, Paul)
5. App schließen & neu starten
6. View öffnen
7. **Erwartung**: Filter ist **persistent**, 3 Zeilen angezeigt, Suchfeld zeigt "lau"

**Log-Check**:
```
💾 V2: Globale Suche + search_string persistent gespeichert
```

---

### Test 2: Parametrischer Filter (Simple)
1. Öffne View
2. Öffne Parameter-Dialog
3. Setze Filter: `familienname_show` = "Müller"
4. OK klicken
5. **Erwartung**: Treffer angezeigt
6. App schließen & neu starten
7. View öffnen
8. **Erwartung**: Filter ist **persistent**, Treffer angezeigt

**Log-Check**:
```
✅ Filter-Parameter persistent gespeichert (für UI)
💾 V2: Parametrischer Filter search_string gespeichert
✅ V2: Parametrischer Filter erfolgreich ausgeführt + persistiert
```

---

### Test 3: Extended Filter (Complex)
1. Öffne View
2. Öffne Parameter-Dialog
3. Wechsel zu KOMPLEX-Modus
4. Setze Extended Conditions: `familienname_show` ENTHÄLT "lau"
5. OK klicken
6. **Erwartung**: 3 Treffer (Laurenne × 2, Hans)
7. App schließen & neu starten
8. View öffnen
9. **Erwartung**: Filter ist **persistent**, 3 Zeilen angezeigt

**Log-Check**:
```
💾 V2: Erweiterte Bedingungen + search_string gespeichert: familienname_show = 1 Bedingungen
🔧 V2 search_string gebaut für 1 Felder: EXTENDED:familienname_show:...
✅ V2: Parametrischer Filter erfolgreich ausgeführt + persistiert
```

---

### Test 4: Multi-Field Extended Filter
1. Öffne View
2. Öffne Parameter-Dialog (KOMPLEX)
3. Feld A: `familienname_show` ENTHÄLT "lau"
4. Feld B: `vorname_show` BEGINNT MIT "L"
5. OK klicken
6. **Erwartung**: Treffer angezeigt
7. App schließen & neu starten
8. View öffnen
9. **Erwartung**: **BEIDE** Extended Filter persistent

**Log-Check**:
```
🔧 V2 search_string gebaut für 2 Felder: EXTENDED:familienname_show:...||EXTENDED:vorname_show:...
```

---

### Test 5: Filter Overwrite
1. Setze Global Search "lau" → 3 Treffer
2. Setze Parametric Filter "Müller" → Überschreibt Global
3. App schließen & neu starten
4. **Erwartung**: Parametric Filter aktiv (nicht Global)

---

### Test 6: Filter Reset
1. Setze beliebigen Filter
2. Klicke Filter-Reset (🗑️)
3. **Erwartung**: Alle Zeilen angezeigt, Filter gelöscht
4. App schließen & neu starten
5. **Erwartung**: KEIN Filter aktiv, alle Zeilen angezeigt

---

### Test 7: Pipeline Autonomy (Stichtag-Wechsel)
1. Setze Filter "lau"
2. Wechsel Stichtag
3. **Erwartung**: Filter bleibt aktiv nach Daten-Reload

---

## Debug-Hilfe

### Log-Patterns für erfolgreiche Persistierung

**Global Search**:
```
🔍 Führe Schnellsuche aus: 'lau'
💾 V2: Globale Suche + search_string persistent gespeichert
✅ V2: Parametrischer Filter erfolgreich ausgeführt + persistiert (wenn success)
✅ Schnellsuche abgeschlossen
```

**Parametric Filter**:
```
✅ Filter-Parameter persistent gespeichert (für UI)
🔍 V2: search_string = 'familienname_show:Müller'
💾 V2: Parametrischer Filter search_string gespeichert
✅ V2: Parametrischer Filter erfolgreich ausgeführt + persistiert
```

**Extended Filter**:
```
💾 V2: Erweiterte Bedingungen + search_string gespeichert: familienname_show = 1 Bedingungen
🔍 search_string: EXTENDED:familienname_show:AND|IS|enthält|lau
```

### Datenbank-Check

**SQL Query** (in `anwendungsdaten` Tabelle):
```sql
SELECT gruppe, feld, wert 
FROM anwendungsdaten 
WHERE gruppe = '0d10a0d0-b1a5-4544-b284-e8a09ca979b5' 
  AND feld IN ('search_string', 'gesamt', 'familienname_show', 'vorname_show');
```

**Erwartete Einträge**:
- `feld='search_string'` → `wert='...'` (je nach Filter-Typ)
- `feld='gesamt'` → `wert='{"search_text":"lau"}'` (bei Global Search)
- `feld='familienname_show'` → `wert='{"simple_search":"Müller","conditions":[]}'` (bei Parametric)

---

## Zusammenfassung

### Was war kaputt:
1. ❌ Schnellsuche rief direkt `matrix_manager.apply_search_filter()` auf
2. ❌ Parameter Dialog rief nicht-existente `execute_parameter_dialog_filter()` auf
3. ❌ **KEINE** `save_all_values()` Aufrufe → Nichts wurde in DB geschrieben

### Was ist jetzt:
1. ✅ Schnellsuche ruft `execute_global_search_filter()` auf
2. ✅ Parameter Dialog ruft `execute_parametric_filter()` auf (NEU)
3. ✅ Extended Filter war bereits V2-konform
4. ✅ **ALLE** Filter rufen `save_all_values()` auf
5. ✅ Pipeline lädt `search_string` autonom

### Architektur V2 (Final):
```
User-Aktion
    ↓
Dialog/UI (sammelt Parameter)
    ↓
LinearFilterExecutionManager.execute_*_filter()
    ↓
1. Reset zu kompletter Datenbasis
2. Speichere Parameters (für UI)
3. Speichere search_string (für Pipeline)
4. save_all_values() ✅
5. Matrix Manager apply_filter()
    ↓
DB (persistent)
Pipeline (autonom bei restart)
```

**Status**: ✅ **ALLE 3 Filter-Typen implementiert & bereit für Tests!**

---

**Nächster Schritt**: User testet alle 7 Szenarien!
