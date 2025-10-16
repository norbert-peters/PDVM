# ✅ NEUES V3 FILTER-SYSTEM: 3 Manager + Einheitlicher Parser

## 🎯 Problem mit V2

**V2 Probleme**:
1. ❌ Nur Schnellsuche speicherte Parameter - Einfach/Komplex NICHT
2. ❌ search_string hatte keine Struktur - "lau" nicht auswertbar
3. ❌ Matrix Manager konnte "lau" nicht ausführen (kein Feld!)
4. ❌ Jeder Dialog hatte eigene Logik

**User-Anforderung**:
> "Der Search_string muss eine einheitliche Struktur haben, damit er linear ausgewertet werden kann. Dem Search im MatrixManager muss es egal sein woher der String kommt."

---

## 🏗️ V3 Architektur

### Komponenten

```
┌─────────────────────────┐
│  3 Filter-Manager       │
├─────────────────────────┤
│ • SchnellsucheManager   │ → "GLOBAL:contains:lau"
│ • EinfachFilterManager  │ → "familienname_show:contains:Müller"
│ • KomplexFilterManager  │ → "familienname_show:AND|IS|contains|Müller"
└─────────────────────────┘
            │
            │ Einheitlicher search_string
            ↓
┌─────────────────────────┐
│  SearchStringParser     │
├─────────────────────────┤
│ parse(search_string)    │ → Callable (row → bool)
└─────────────────────────┘
            │
            │ Filter-Funktion
            ↓
┌─────────────────────────┐
│  MatrixManager          │
├─────────────────────────┤
│ apply_filter(func)      │ → FilterMatrix
└─────────────────────────┘
```

### Jeder Manager ist AUTONOM

```python
# Manager-Pattern (alle 3 gleich):
1. Sammelt Parameter aus UI
2. Speichert Parameter in DB (für UI-Reload)
3. Baut einheitlichen search_string
4. Speichert s_string + s_source
5. Ruft save_all_values() auf
6. Ruft matrix_manager.apply_filter(search_string)
```

---

## 📝 Einheitliche search_string Struktur

### Format-Übersicht

| Typ | Format | Beispiel |
|-----|--------|----------|
| **GLOBAL** | `GLOBAL:operator:wert` | `GLOBAL:contains:lau` |
| **EINFACH** | `feld:operator:wert` | `familienname_show:contains:Müller` |
| **EINFACH MULTI** | `feld1:op:val1\|\|feld2:op:val2` | `familienname_show:contains:Müller\|\|vorname_show:contains:Max` |
| **KOMPLEX** | `feld:pos1\|pos2\|pos3\|pos4` | `familienname_show:AND\|IS\|contains\|Müller` |
| **KOMPLEX MULTI** | `feld:pos...\|\|feld:pos...` | `familienname_show:AND\|IS\|contains\|Müller\|\|familienname_show:OR\|NOT\|equals\|Schmidt` |

### Format-Details

#### 1. GLOBAL-Suche (Schnellsuche)
```
"GLOBAL:contains:lau"
  │      │        │
  │      │        └─ Suchwert
  │      └─ Operator (contains/equals/startswith/endswith)
  └─ Spezial-Marker für "alle Spalten"
```

**Bedeutung**: Suche "lau" in ALLEN sichtbaren Spalten

#### 2. EINFACH (Ein Feld, ein Wert)
```
"familienname_show:contains:Müller"
  │                │         │
  │                │         └─ Suchwert
  │                └─ Operator
  └─ Feld-Key
```

**Bedeutung**: Suche "Müller" in Spalte familienname_show

#### 3. EINFACH MULTI (Mehrere Felder, AND-verknüpft)
```
"familienname_show:contains:Müller||vorname_show:contains:Max"
  │                                 │
  │                                 └─ AND-Trenner
  └─ Erste Bedingung
```

**Bedeutung**: familienname enthält "Müller" UND vorname enthält "Max"

#### 4. KOMPLEX (4-Positionen Struktur)
```
"familienname_show:AND|IS|contains|Müller"
  │                 │   │  │        │
  │                 │   │  │        └─ Position 4: Wert
  │                 │   │  └─ Position 3: Operator
  │                 │   └─ Position 2: IS/NOT (Negation)
  │                 └─ Position 1: AND/OR (für Multi)
  └─ Feld-Key
```

**Bedeutung**: familienname enthält "Müller" (IS = nicht negiert)

#### 5. KOMPLEX MULTI (Mehrere komplexe Bedingungen)
```
"familienname_show:AND|IS|contains|Müller||familienname_show:OR|NOT|equals|Schmidt"
  │                                        │
  │                                        └─ AND-Trenner (zwischen Bedingungen)
  └─ Erste komplexe Bedingung
```

**Bedeutung**: 
- familienname enthält "Müller" (IS)
- UND familienname ist NICHT "Schmidt" (NOT)

---

## 🔍 SchnellsucheManager

### Datei
`schnellsuche_manager.py`

### Funktionen

#### `execute_schnellsuche(search_text: str)`
```python
manager = SchnellsucheManager(view_guid, matrix_manager)
manager.execute_schnellsuche("lau")

# Intern:
# 1. Speichert Parameter: {'search_text': 'lau'}
# 2. Baut search_string: "GLOBAL:contains:lau"
# 3. Speichert s_string + s_source='schnell'
# 4. Ruft save_all_values() auf
# 5. Ruft matrix_manager.apply_filter("GLOBAL:contains:lau")
```

#### `load_schnellsuche_ui()`
```python
# Lädt Schnellsuche NUR wenn s_source == 'schnell'
search_text = manager.load_schnellsuche_ui()
if search_text:
    search_input.setText(search_text)
```

#### `clear_schnellsuche()`
```python
# Löscht Parameter + s_string + s_source
manager.clear_schnellsuche()
```

### Gespeicherte Daten

```
gruppe = view_guid
├─ feld = 'schnell'   → {"search_text": "lau"}
├─ feld = 's_string'  → "GLOBAL:contains:lau"
└─ feld = 's_source'  → "schnell"
```

---

## 📋 EinfachFilterManager

### Datei
`einfach_filter_manager.py`

### Funktionen

#### `execute_einfach_filter(filter_params: Dict[str, str])`
```python
manager = EinfachFilterManager(view_guid, matrix_manager)
manager.execute_einfach_filter({
    "familienname_show": "Müller",
    "vorname_show": "Max"
})

# Intern:
# 1. Speichert für jedes Feld: {'simple_search': 'Müller', 'conditions': []}
# 2. Baut search_string: "familienname_show:contains:Müller||vorname_show:contains:Max"
# 3. Speichert s_string + s_source='einfach'
# 4. Ruft save_all_values() auf
# 5. Ruft matrix_manager.apply_filter(search_string)
```

#### `load_field_filter(field_key: str)`
```python
# Lädt Filter für ein Feld
value = manager.load_field_filter("familienname_show")
# Returns: "Müller" oder None
```

#### `clear_einfach_filter(field_keys: list)`
```python
# Löscht alle oder spezifische Felder
manager.clear_einfach_filter()  # Alle
manager.clear_einfach_filter(["familienname_show"])  # Nur ein Feld
```

### Gespeicherte Daten

```
gruppe = view_guid
├─ feld = 'familienname_show'  → {"simple_search": "Müller", "conditions": []}
├─ feld = 'vorname_show'       → {"simple_search": "Max", "conditions": []}
├─ feld = 's_string'           → "familienname_show:contains:Müller||vorname_show:contains:Max"
└─ feld = 's_source'           → "einfach"
```

---

## 🔬 KomplexFilterManager

### Datei
`komplex_filter_manager.py`

### Funktionen

#### `execute_komplex_filter(field_conditions: Dict[str, List[Dict]])`
```python
manager = KomplexFilterManager(view_guid, matrix_manager)
manager.execute_komplex_filter({
    "familienname_show": [
        {
            "position_1": "AND",
            "position_2": "IS",
            "position_3": "enthält",
            "position_4": "Müller"
        },
        {
            "position_1": "OR",
            "position_2": "NOT",
            "position_3": "ist",
            "position_4": "Schmidt"
        }
    ]
})

# Intern:
# 1. Speichert für Feld: {'simple_search': '', 'conditions': [...]}
# 2. Baut search_string: "familienname_show:AND|IS|enthält|Müller||familienname_show:OR|NOT|ist|Schmidt"
# 3. Speichert s_string + s_source='komplex'
# 4. Ruft save_all_values() auf
# 5. Ruft matrix_manager.apply_filter(search_string)
```

#### `load_field_conditions(field_key: str)`
```python
# Lädt Bedingungen für ein Feld
conditions = manager.load_field_conditions("familienname_show")
# Returns: Liste von Bedingungen
```

#### `clear_komplex_filter(field_keys: list)`
```python
# Löscht alle oder spezifische Felder
manager.clear_komplex_filter()  # Alle
manager.clear_komplex_filter(["familienname_show"])  # Nur ein Feld
```

### Gespeicherte Daten

```
gruppe = view_guid
├─ feld = 'familienname_show'  → {"simple_search": "", "conditions": [{...}, {...}]}
├─ feld = 's_string'           → "familienname_show:AND|IS|enthält|Müller||familienname_show:OR|NOT|ist|Schmidt"
└─ feld = 's_source'           → "komplex"
```

---

## 🔍 SearchStringParser

### Datei
`search_string_parser.py`

### Funktionen

#### `parse(search_string: str)`
```python
from search_string_parser import get_search_string_parser

parser = get_search_string_parser()
filter_func = parser.parse("GLOBAL:contains:lau")

# filter_func ist jetzt Callable: row → bool
# Kann direkt für Filterung verwendet werden:
filtered_rows = [row for row in basis_matrix if filter_func(row)]
```

### Parser-Logik

```python
def parse(search_string: str) -> Callable:
    # 1. GLOBAL-Suche?
    if search_string.startswith("GLOBAL:"):
        return _parse_global_search(search_string)
    
    # 2. Multi-Field (mit ||)?
    if "||" in search_string:
        return _parse_multi_field(search_string)
    
    # 3. Komplex (mit |)?
    if "|" in search_string:
        return _parse_komplex_single(search_string)
    
    # 4. Einfach
    return _parse_einfach_single(search_string)
```

### Operator-Unterstützung

| Operator | Bedeutung | Beispiel |
|----------|-----------|----------|
| `contains` | enthält | "lau" in "Lauer" ✅ |
| `equals` | ist gleich | "Müller" == "Müller" ✅ |
| `startswith` | beginnt mit | "Müller" beginnt mit "Mü" ✅ |
| `endswith` | endet mit | "Müller" endet mit "er" ✅ |
| `>` | größer | 1980 > 1970 ✅ |
| `<` | kleiner | 1970 < 1980 ✅ |
| `>=` | größer gleich | 1980 >= 1980 ✅ |
| `<=` | kleiner gleich | 1970 <= 1980 ✅ |
| `!=` | ungleich | "Müller" != "Schmidt" ✅ |

---

## 🔄 Integration in Matrix Manager

### Änderungen in `pdvm_view_matrix_manager.py`

```python
from search_string_parser import get_search_string_parser

class ViewMatrixManager:
    
    def apply_filter(self, search_string: str = None):
        """Filter anwenden mit einheitlichem Parser"""
        
        if not search_string:
            # Kein Filter: alle Zeilen
            self.filter_matrix = deepcopy(self.basis_matrix)
            return
        
        # Parser verwenden
        parser = get_search_string_parser()
        filter_func = parser.parse(search_string)
        
        if not filter_func:
            logger.error("❌ Parser konnte search_string nicht verarbeiten")
            self.filter_matrix = deepcopy(self.basis_matrix)
            return
        
        # Filter anwenden
        self.filter_matrix = [
            row for row in self.basis_matrix
            if filter_func(row)
        ]
        
        logger.info(f"✅ Filter: {len(self.filter_matrix)} von {len(self.basis_matrix)} Zeilen")
```

---

## 📚 Beispiel-Workflows

### Workflow 1: Schnellsuche
```python
# 1. User gibt "lau" ein
# 2. UI ruft Manager auf
manager = SchnellsucheManager(view_guid, matrix_manager)
manager.execute_schnellsuche("lau")

# 3. Manager speichert:
#    - schnell: {"search_text": "lau"}
#    - s_string: "GLOBAL:contains:lau"
#    - s_source: "schnell"

# 4. Manager ruft Matrix Manager
matrix_manager.apply_filter("GLOBAL:contains:lau")

# 5. Matrix Manager nutzt Parser
parser = get_search_string_parser()
filter_func = parser.parse("GLOBAL:contains:lau")
# → Sucht "lau" in ALLEN Spalten

# 6. App Restart
# 7. Matrix Manager lädt autonom
s_string = gcs._app_db.get_value(view_guid, 's_string')
# → "GLOBAL:contains:lau"
matrix_manager.apply_filter(s_string)
```

### Workflow 2: Einfacher Filter
```python
# 1. User setzt Filter: Familienname = "Müller"
# 2. UI ruft Manager auf
manager = EinfachFilterManager(view_guid, matrix_manager)
manager.execute_einfach_filter({
    "familienname_show": "Müller"
})

# 3. Manager speichert:
#    - familienname_show: {"simple_search": "Müller", "conditions": []}
#    - s_string: "familienname_show:contains:Müller"
#    - s_source: "einfach"

# 4. Manager ruft Matrix Manager
matrix_manager.apply_filter("familienname_show:contains:Müller")

# 5. Matrix Manager nutzt Parser
parser = get_search_string_parser()
filter_func = parser.parse("familienname_show:contains:Müller")
# → Prüft nur Spalte familienname_show

# 6. App Restart
# 7. Matrix Manager lädt autonom
s_string = gcs._app_db.get_value(view_guid, 's_string')
# → "familienname_show:contains:Müller"
matrix_manager.apply_filter(s_string)
```

### Workflow 3: Komplexer Filter
```python
# 1. User setzt komplexen Filter:
#    - Familienname enthält "Müller" (IS)
#    - ODER Familienname ist NICHT "Schmidt" (NOT)

# 2. UI ruft Manager auf
manager = KomplexFilterManager(view_guid, matrix_manager)
manager.execute_komplex_filter({
    "familienname_show": [
        {"position_1": "AND", "position_2": "IS", "position_3": "enthält", "position_4": "Müller"},
        {"position_1": "OR", "position_2": "NOT", "position_3": "ist", "position_4": "Schmidt"}
    ]
})

# 3. Manager speichert:
#    - familienname_show: {"simple_search": "", "conditions": [...]}
#    - s_string: "familienname_show:AND|IS|enthält|Müller||familienname_show:OR|NOT|ist|Schmidt"
#    - s_source: "komplex"

# 4. Manager ruft Matrix Manager
matrix_manager.apply_filter(s_string)

# 5. Matrix Manager nutzt Parser
parser = get_search_string_parser()
filter_func = parser.parse(s_string)
# → Prüft: (enthält "Müller") UND NICHT (ist "Schmidt")

# 6. App Restart
# 7. Matrix Manager lädt autonom
s_string = gcs._app_db.get_value(view_guid, 's_string')
matrix_manager.apply_filter(s_string)
```

---

## ✅ Vorteile von V3

### 1. Einheitliche Struktur
- ✅ Jeder search_string hat klare Struktur
- ✅ Matrix Manager kann JEDEN String ausführen
- ✅ Egal welcher Dialog - Format ist einheitlich

### 2. Vollständige Persistierung
- ✅ ALLE Filter speichern Parameter
- ✅ ALLE Filter speichern s_string + s_source
- ✅ ALLE Filter rufen save_all_values() auf

### 3. Autonome Manager
- ✅ Jeder Manager ist in sich geschlossen
- ✅ Keine komplexen Abhängigkeiten
- ✅ Einfache Wartung und Debugging

### 4. Zentraler Parser
- ✅ Eine Stelle für Filter-Logik
- ✅ Konsistente Operator-Anwendung
- ✅ Einfache Erweiterung (neue Operatoren)

### 5. Testbarkeit
- ✅ Jeder Manager isoliert testbar
- ✅ Parser isoliert testbar
- ✅ Klare Input/Output Contracts

---

## 🚀 Nächste Schritte

### 1. Matrix Manager anpassen
- Alte `_apply_unified_search_filter()` Logik entfernen
- Neue Parser-Integration implementieren
- Filter-Funktion direkt anwenden

### 2. UI-Dialoge anpassen
- `pdvm_view_controller.py`: SchnellsucheManager verwenden
- `search_parameter_dialog.py`: EinfachFilterManager verwenden
- `extended_filter_engine.py`: KomplexFilterManager verwenden

### 3. Tests
- Schnellsuche "lau" → 3 Treffer → Restart → 3 Treffer ✅
- Einfach "Müller" → 2 Treffer → Restart → 2 Treffer ✅
- Komplex "enthält Müller AND NICHT Schmidt" → Restart ✅

### 4. Cleanup
- Alte LinearFilterExecutionManager Dateien entfernen
- Alte Filter-Logik in Matrix Manager entfernen
- Dokumentation aktualisieren

---

**Status**: ✅ **V3 KOMPLETT DESIGNED - BEREIT FÜR IMPLEMENTATION**
