# V2 Filter-Persistierung: EINFACHES KONZEPT ✅

## Konzept (User-Vorgabe)

> "Jeder Eingabe zu einem Filter betrachten wir als Filterdialog - auch die Schnellsuche. 
> Jeder dieser Dialoge ist autonom!!"

### Ablauf (EINFACH)

```
1. DIALOG (autonom):
   ├─ Sammelt Parameter
   ├─ Speichert Parameter: gcs._app_db.set_value(view_guid, 'schnell'/'einfach'/'komplex', params)
   ├─ Baut search_string aus Parametern
   ├─ Speichert search_string: gcs._app_db.set_value(view_guid, 'search_string', search_string)
   ├─ save_all_values() ✅
   └─ Ruft MatrixManager.apply_filter(search_string) auf
       ↓
2. MATRIX MANAGER:
   ├─ Liest search_string (wenn nicht übergeben)
   ├─ Führt Filter aus → FilterMatrix
   └─ Pipeline durchlaufen (Sort → Projection → View)
```

**KEIN komplizierter Zwischenschritt!** Dialog → MatrixManager → Fertig!

---

## Implementierung

### 1. Schnellsuche (Global Search)

**Datei**: `pdvm_view_controller.py`
**Methode**: `execute_search()`

```python
def execute_search(self):
    """V2 EINFACH: Dialog-autonom"""
    search_text = getattr(self, 'pending_search_text', '')
    
    # 1. Speichere Parameter unter 'schnell'
    gcs._app_db.set_value(self.view_guid, 'schnell', {
        'search_text': search_text
    })
    
    # 2. Speichere search_string
    gcs._app_db.set_value(self.view_guid, 'search_string', search_text)
    
    # 3. CRITICAL: Speichere alles
    gcs._app_db.save_all_values()
    
    # 4. Matrix Manager aufrufen
    self.matrix_manager.apply_filter(search_text)
    
    # 5. UI aktualisieren
    self.refresh_ui_from_matrix()
```

**Gespeicherte Daten**:
- `gruppe='view_guid'`, `feld='schnell'` → `{'search_text': 'lau'}`
- `gruppe='view_guid'`, `feld='search_string'` → `'lau'`

---

### 2. Parameter Dialog (Einfach/Komplex)

**Datei**: `search_parameter_dialog.py`
**Methode**: `accept_changes()`

```python
def accept_changes(self):
    """V2 EINFACH: Dialog ist AUTONOM"""
    
    # Sammle Filter
    new_filters = {...}  # aus UI
    extended_summary = {...}  # aus extended_filter_engine
    
    # 1. Speichere Parameter unter 'einfach' oder 'komplex'
    filter_type = 'komplex' if extended_summary else 'einfach'
    self.save_persistent_filters(new_filters)
    
    # 2. Baue search_string
    search_parts = []
    if extended_summary:
        # KOMPLEX: "EXTENDED:field:summary"
        for field_key, summary in extended_summary.items():
            search_parts.append(f"EXTENDED:{field_key}:{summary}")
    else:
        # EINFACH: "field:value"
        for field_key, value in new_filters.items():
            search_parts.append(f"{field_key}:{value}")
    
    search_string = "||".join(search_parts)
    
    # 3. Speichere search_string
    gcs._app_db.set_value(self.view_guid, 'search_string', search_string)
    gcs._app_db.save_all_values()
    
    # 4. Matrix Manager aufrufen
    matrix_manager.apply_filter(search_string)
```

**Gespeicherte Daten** (Einfach):
- `gruppe='view_guid'`, `feld='familienname_show'` → `{'simple_search': 'Müller', 'conditions': []}`
- `gruppe='view_guid'`, `feld='search_string'` → `'familienname_show:Müller'`

**Gespeicherte Daten** (Komplex):
- `gruppe='view_guid'`, `feld='familienname_show'` → `{'simple_search': '', 'conditions': [...]}`
- `gruppe='view_guid'`, `feld='search_string'` → `'EXTENDED:familienname_show:AND|IS|enthält|Müller'`

---

### 3. Extended Filter (Komplex)

**Datei**: `extended_filter_engine.py`
**Methode**: `save_field_conditions()` - **BEREITS RICHTIG!**

```python
def save_field_conditions(self, field_key: str, conditions: List):
    """Speichert Extended Conditions + baut search_string für ALLE Extended Felder"""
    
    # 1. Speichere Conditions für dieses Feld
    gcs._app_db.set_value(self.view_guid, field_key, {
        'simple_search': '',
        'conditions': [c.to_dict() for c in conditions]
    })
    
    # 2. Baue search_string für ALLE Extended Felder (multi-field support!)
    search_string = self._build_search_string_from_conditions(field_key, conditions)
    # Format: "EXTENDED:field1:summary1||EXTENDED:field2:summary2"
    
    # 3. Speichere search_string
    gcs._app_db.set_value(self.view_guid, 'search_string', search_string)
    
    # 4. CRITICAL: Speichere alles
    gcs._app_db.save_all_values()
```

**Multi-Field Support**: Wenn Extended Conditions für Feld A, B, C existieren:
```
search_string = "EXTENDED:fieldA:summary1||EXTENDED:fieldB:summary2||EXTENDED:fieldC:summary3"
```

---

### 4. Matrix Manager (Autonom)

**Datei**: `pdvm_view_matrix_manager.py`
**Methode**: `rebuild_pipeline()` - **BEREITS RICHTIG!**

```python
def rebuild_pipeline(self, search_string: Optional[str] = None):
    """Pipeline AUTONOM durchlaufen"""
    
    # 1. BasisMatrix vorhanden?
    if self.basis_matrix is None:
        return
    
    # 2. Filter AUTONOM laden (wenn nicht übergeben)
    if search_string is None:
        search_string = self._load_search_string_from_gcs()
    
    # 3. Filter anwenden → FilterMatrix
    self.apply_filter(search_string)
    
    # 4. Sort AUTONOM laden & anwenden → SortMatrix
    sort_config = self._load_sort_config_from_gcs()
    self.apply_sort(sort_config)
    
    # 5. Projektion erfolgt on-demand

def _load_search_string_from_gcs(self) -> Optional[str]:
    """Lädt search_string aus GCS"""
    search_string, _ = gcs._app_db.get_value(self.view_guid, 'search_string')
    return search_string
```

---

## Datenbank-Struktur

**Tabelle**: `anwendungsdaten`

| gruppe (view_guid) | feld | wert |
|--------------------|------|------|
| `0d10a0d0-...` | `schnell` | `{"search_text": "lau"}` |
| `0d10a0d0-...` | `familienname_show` | `{"simple_search": "Müller", "conditions": []}` |
| `0d10a0d0-...` | `search_string` | `"familienname_show:Müller"` |
| `0d10a0d0-...` | `sort` | `[{"column_key": "anrede_show", ...}]` |

**Wichtig**: 
- **Immer nur EIN `search_string` aktiv** (letzter Filter gewinnt)
- Parameter bleiben für UI-Anzeige erhalten
- `search_string` ist **universal** für Pipeline

---

## Filter-Typen & search_string Formate

| Dialog | Feld-Name | search_string Format | Beispiel |
|--------|-----------|----------------------|----------|
| **Schnellsuche** | `'schnell'` | Nur Text | `"lau"` |
| **Einfach** | `'familienname_show'` | `field:value` | `"familienname_show:Müller"` |
| **Einfach Multi** | Mehrere Felder | `field1:value1\|\|field2:value2` | `"familienname_show:Müller\|\|vorname_show:Hans"` |
| **Komplex Single** | `'familienname_show'` | `EXTENDED:field:summary` | `"EXTENDED:familienname_show:AND\|IS\|enthält\|Müller"` |
| **Komplex Multi** | Mehrere Felder | `EXTENDED:field1:...\|\|EXTENDED:field2:...` | Siehe unten |

**Komplex Multi-Field Beispiel**:
```
EXTENDED:familienname_show:AND|IS|enthält|Müller||EXTENDED:vorname_show:AND|IS|beginnt mit|H
```

---

## Autonomie & Persistierung

### Beim Filter setzen:
```
User → Dialog (autonom)
         ├─ Speichert Parameter
         ├─ Baut & speichert search_string
         ├─ save_all_values()
         └─ MatrixManager.apply_filter()
```

### Bei App-Restart:
```
App Start → View öffnen
             ├─ Controller initialisiert Matrix Manager
             ├─ Matrix Manager ruft rebuild_pipeline() auf
             ├─ Matrix Manager lädt search_string aus GCS (AUTONOM)
             ├─ Matrix Manager lädt sort aus GCS (AUTONOM)
             └─ Pipeline durchlaufen → View zeigt gefilterte Daten
```

### Bei Stichtag-Wechsel:
```
User wechselt Stichtag
  ├─ Daten neu laden (BasisMatrix neu)
  ├─ rebuild_pipeline() aufgerufen
  ├─ search_string aus GCS laden (AUTONOM)
  └─ Filter erneut anwenden
```

---

## Vorteile des einfachen Konzepts

1. ✅ **Jeder Dialog ist autonom** - keine Abhängigkeiten
2. ✅ **Keine komplexen Manager-Ketten** - direkt Dialog → MatrixManager
3. ✅ **search_string ist universal** - Pipeline versteht alle Formate
4. ✅ **Immer nur ein Filter aktiv** - kein Konflikt, letzter gewinnt
5. ✅ **Matrix Manager ist autonom** - lädt alles selbst beim restart
6. ✅ **Sehr stabil** - weniger Code, weniger Fehlerquellen

---

## Geänderte Dateien

| Datei | Methode | Änderung |
|-------|---------|----------|
| `pdvm_view_controller.py` | `execute_search()` | Dialog-autonom: Parameter + search_string speichern + MatrixManager aufrufen |
| `search_parameter_dialog.py` | `accept_changes()` | Dialog-autonom: Parameter + search_string speichern + MatrixManager aufrufen |
| `extended_filter_engine.py` | `save_field_conditions()` | Bereits richtig (multi-field support) |
| `pdvm_view_matrix_manager.py` | `rebuild_pipeline()` | Bereits richtig (autonom) |

**KEINE komplexen Manager** wie `LinearFilterExecutionManager` nötig!

---

## Test-Szenarien

### Test 1: Schnellsuche
1. Gib "lau" ein → Suchen
2. **Erwartung**: 3 Treffer
3. App schließen & neu starten
4. **Erwartung**: Filter aktiv, 3 Treffer, Suchfeld zeigt "lau"

**Log-Check**:
```
💾 Schnellsuche Parameter + search_string gespeichert
✅ Schnellsuche Filter angewendet
```

### Test 2: Parametrischer Filter
1. Parameter-Dialog: `familienname_show` = "Müller"
2. OK klicken
3. **Erwartung**: Treffer angezeigt
4. App schließen & neu starten
5. **Erwartung**: Filter aktiv, Treffer angezeigt

**Log-Check**:
```
💾 Filter-Parameter unter 'einfach' gespeichert
💾 search_string gespeichert: 'familienname_show:Müller'
✅ EINFACH-Filter angewendet
```

### Test 3: Extended Filter
1. Parameter-Dialog (KOMPLEX): `familienname_show` ENTHÄLT "lau"
2. OK klicken
3. **Erwartung**: 3 Treffer
4. App schließen & neu starten
5. **Erwartung**: Filter aktiv, 3 Treffer

**Log-Check**:
```
💾 Filter-Parameter unter 'komplex' gespeichert
💾 search_string gespeichert: 'EXTENDED:familienname_show:...'
✅ KOMPLEX-Filter angewendet
```

### Test 4: Filter Overwrite
1. Schnellsuche "lau" → 3 Treffer
2. Parameter Filter "Müller" → Überschreibt Schnellsuche
3. App restart
4. **Erwartung**: Parameter Filter aktiv (nicht Schnellsuche)

**Warum?** `search_string` wird überschrieben → letzter gewinnt!

---

## Zusammenfassung

### Konzept
- ✅ **Jeder Dialog autonom** - speichert selbst, ruft MatrixManager auf
- ✅ **KEIN komplizierter Zwischenschritt** - Dialog → MatrixManager
- ✅ **Matrix Manager autonom** - lädt search_string & sort selbst
- ✅ **Sehr einfach & stabil** - wenig Code, klare Struktur

### Ablauf
```
Dialog → Parameter + search_string speichern → save_all_values() → MatrixManager.apply_filter()
```

### Bei Restart
```
View öffnen → Matrix Manager rebuild_pipeline() → Lädt search_string aus GCS → Filter anwenden
```

**Status**: ✅ **EINFACH & FERTIG - BEREIT FÜR TESTS!**
