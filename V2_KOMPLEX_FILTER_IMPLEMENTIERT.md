# V2 Komplex-Filter Persistierung - IMPLEMENTIERT ✅

## Datum
2024-11-XX

## Überblick
Erweiterung des V2 Filter-Persistence Systems um **komplexe Filter (extended_filter_engine.py)**

## V2 Architektur - Komplex Filter

### Datenspeicherung
```
anwendungsdaten Tabelle:
├── Gruppe: view_guid
├── Feld: 'familienname_show' (Beispiel)
│   └── Wert: {"simple_search": "", "conditions": [...]}
├── Feld: 'vorname_show'
│   └── Wert: {"simple_search": "", "conditions": [...]}
├── Feld: 'search_string'  ← ZENTRAL für Pipeline!
│   └── Wert: "EXTENDED:familienname_show:AND|IS|enthält|Lau||EXTENDED:vorname_show:FIRST|IS|beginnt_mit|Max"
└── ...
```

### search_string Format
```python
# Ein Feld mit mehreren Bedingungen:
"EXTENDED:familienname_show:AND|IS|enthält|Lau||OR|NOT|beginnt_mit|Mei"

# Mehrere Felder:
"EXTENDED:familienname_show:AND|IS|enthält|Lau||EXTENDED:vorname_show:FIRST|IS|beginnt_mit|Max"

# Condition Format: "position|is_not|operator|value"
# position: FIRST | AND | OR
# is_not: IS | NOT
# operator: enthält | beginnt_mit | endet_mit | gleich | größer | kleiner
# value: Suchtext
```

## Implementierte Änderungen

### 1. `save_field_conditions()` - Extended (Zeile 146)
**Vorher:**
```python
def save_field_conditions(self, field_key: str, conditions: List):
    # Nur conditions speichern unter field_key
    gcs._app_db.set_value(self.view_guid, field_key, current_data)
    gcs._app_db.save_all_values()
```

**Nachher:**
```python
def save_field_conditions(self, field_key: str, conditions: List):
    # 1. Conditions speichern unter field_key (für UI)
    gcs._app_db.set_value(self.view_guid, field_key, current_data)
    
    # 2. V2: search_string für Pipeline speichern
    search_string = self._build_search_string_from_conditions(field_key, conditions)
    gcs._app_db.set_value(self.view_guid, 'search_string', search_string)
    
    # 3. Alles in einer Transaktion speichern
    gcs._app_db.save_all_values()
```

### 2. `_build_search_string_from_conditions()` - NEU
**Funktionalität:**
- Baut search_string für **ALLE** aktiven erweiterten Filter
- Nicht nur das aktuelle Feld!
- Format: `EXTENDED:field1:summary1||EXTENDED:field2:summary2`

**Logik:**
```python
def _build_search_string_from_conditions(self, field_key: str, conditions: List) -> Optional[str]:
    # 1. Aktualisiere extended_conditions für aktuelles Feld
    if conditions:
        self.extended_conditions[field_key] = conditions
    
    # 2. Durchlaufe ALLE aktiven Filter
    all_field_strings = []
    for fname, field_conditions in self.extended_conditions.items():
        # 3. Baue Summary pro Feld
        condition_strings = []
        for condition in field_conditions:
            cond_str = f"{position}|{is_not}|{operator}|{value}"
            condition_strings.append(cond_str)
        
        summary = "||".join(condition_strings)
        field_string = f"EXTENDED:{fname}:{summary}"
        all_field_strings.append(field_string)
    
    # 4. Verbinde alle Felder
    return "||".join(all_field_strings) if all_field_strings else None
```

**Wichtig:** Diese Methode behandelt **mehrere Felder gleichzeitig**, da `extended_conditions` ein Dictionary ist:
```python
{
    'familienname_show': [condition1, condition2],
    'vorname_show': [condition3],
    'geburtsdatum_show': [condition4, condition5]
}
```

### 3. `clear_field_conditions()` - Extended
**Vorher:**
```python
def clear_field_conditions(self, field_key: str):
    if field_key in self.extended_conditions:
        del self.extended_conditions[field_key]
```

**Nachher:**
```python
def clear_field_conditions(self, field_key: str):
    if field_key in self.extended_conditions:
        del self.extended_conditions[field_key]
        
        # V2: Persistenz aktualisieren
        gcs._app_db.set_value(self.view_guid, field_key, None)  # Feld löschen
        
        # search_string neu bauen (ohne das gelöschte Feld)
        search_string = self._build_search_string_from_conditions(field_key, [])
        gcs._app_db.set_value(self.view_guid, 'search_string', search_string)
        gcs._app_db.save_all_values()
```

## Integration in Pipeline

### Matrix Manager (bereits V2)
```python
# pdvm_view_matrix_manager.py

def rebuild_pipeline(self, search_string: Optional[str] = None):
    if search_string is None:
        search_string = self._load_search_string_from_gcs()  # Lädt nur search_string!
    
    self.apply_filter(search_string)

def _load_search_string_from_gcs(self) -> Optional[str]:
    gcs = get_gcs()
    search_string, _ = gcs._app_db.get_value(self.view_guid, 'search_string')
    return search_string
```

### Call-Flow
```
User setzt komplexen Filter
    ↓
SearchParameterDialog.accept_changes()
    ↓
extended_filter_engine.set_field_conditions(field_key, conditions)
    ↓
extended_filter_engine.save_field_conditions(field_key, conditions)
    ↓
1. Speichere conditions unter 'field_key' (für UI)
2. Baue search_string aus ALLEN extended_conditions
3. Speichere search_string unter 'search_string' (für Pipeline)
4. save_all_values()
    ↓
App Neustart
    ↓
Matrix Manager: rebuild_pipeline()
    ↓
_load_search_string_from_gcs() → Lädt nur 'search_string'
    ↓
apply_filter(search_string) → Filtert autonom
```

## Vorteile V2

### ✅ Keine Konversion
- Pipeline lädt direkt search_string
- Keine Umwandlung von conditions → search_string bei jedem Start
- Einfacher Code!

### ✅ Mehrere Felder gleichzeitig
- `_build_search_string_from_conditions()` berücksichtigt ALLE aktiven Filter
- Korrekte Kombination mit || Separator

### ✅ Trennung von Concerns
- **Parameters** (conditions) → UI Darstellung (Dialog)
- **search_string** → Pipeline Filterung (autonom)
- Klare Verantwortlichkeiten!

### ✅ Konsistenz
- Gleiche Struktur wie einfacher Filter (search_parameter_dialog.py)
- Gleiche GCS Persistence Pattern

## Testplan

### Test 1: Einzelfeld mit mehreren Bedingungen
```
1. Öffne Komplex-Filter für 'familienname_show'
2. Setze Bedingung: FIRST | IS | enthält | "Lau"
3. Setze Bedingung: OR | NOT | beginnt_mit | "Mei"
4. Speichern
5. App neu starten
6. ✅ Filter sollte aktiv sein
7. ✅ search_string: "EXTENDED:familienname_show:FIRST|IS|enthält|Lau||OR|NOT|beginnt_mit|Mei"
```

### Test 2: Mehrere Felder gleichzeitig
```
1. Setze Filter für 'familienname_show': enthält "Lau"
2. Setze Filter für 'vorname_show': beginnt_mit "Max"
3. Speichern
4. App neu starten
5. ✅ Beide Filter sollten aktiv sein
6. ✅ search_string: "EXTENDED:familienname_show:...||EXTENDED:vorname_show:..."
```

### Test 3: Feld löschen
```
1. Setze Filter für 'familienname_show' und 'vorname_show'
2. Lösche Filter für 'familienname_show'
3. ✅ search_string sollte nur noch 'vorname_show' enthalten
4. App neu starten
5. ✅ Nur 'vorname_show' Filter aktiv
```

### Test 4: Alle löschen
```
1. Setze Filter für mehrere Felder
2. Lösche alle Filter
3. ✅ search_string sollte None sein
4. App neu starten
5. ✅ Keine Filter aktiv
```

## Nächste Schritte

### ⏳ Gesamt-Suche V2
- Implementierung in `pdvm_view_controller.py`
- Speichern unter 'gesamt' + 'search_string'

### ⏳ Linear Filter Manager Cleanup
- Alte Persistence-Methoden entfernen
- Nur Execution-Logik behalten

### ⏳ Vollständige Tests
- Alle 3 Filter-Typen testen
- Kombinationen testen
- Reset-Funktionalität testen

## Status
✅ **IMPLEMENTIERT** - Komplex-Filter speichern jetzt Parameters + search_string
✅ **MULTI-FELD** - Mehrere Felder werden korrekt kombiniert
✅ **DELETE** - Löschen aktualisiert search_string korrekt
⏳ **TESTING** - Praktische Tests stehen noch aus

## Dateien geändert
- `extended_filter_engine.py`:
  - Zeile 146-193: `save_field_conditions()` - V2 Extension
  - Zeile 195-268: `_build_search_string_from_conditions()` - NEU
  - Zeile 270-285: `clear_field_conditions()` - V2 Extension
