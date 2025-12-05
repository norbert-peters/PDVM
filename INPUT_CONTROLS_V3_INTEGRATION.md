# Input-Controls V3 Integration - Zusammenfassung

## ✅ Implementierte Änderungen

### 1. **Dropdown V3 Integration**
**Datei**: `pdvm_input_type_dropdown.py`

**Vorher** (Legacy):
```python
dropdown_config = {
    'key': 'guid',
    'value': 'feldname'
}
dropdown_dict = gcs.get_dropdown_options(key, value)
# Returns: {'m': 'Herr', 'w': 'Frau'}
```

**Jetzt** (V3):
```python
# Aus field_config.configs.dropdown
dropdown_config = {
    'table': 'sys_dropdowndaten',
    'key': '2a60c785-...',  # UID des Datensatzes
    'feld': 'anrede',
    'gruppe': ''  # Optional
}
edit_list = gcs.get_dropdown_options_v3(dropdown_config)
# Returns: [{"key": "w", "value": "Frau"}, {"key": "m", "value": "Herr"}]
```

**Features**:
- ✅ Mehrsprachige Unterstützung via DEFAULT_LANGUAGE
- ✅ Cache für Performance (`_dropdown_cache_v3`)
- ✅ Robuste Error-Handling

---

### 2. **Hilfe-Funktion V3**
**Datei**: `pdvm_input_control.py`

**Vorher**:
- Grauer `?` Button (disabled)
- "noch nicht implementiert"

**Jetzt** (V3):
```python
# Aus field_config.configs.help
help_config = {
    'table': 'sys_beschreibungen',
    'key': 'dded74a4-...',
    'feld': 'PERSONDATEN_PERSDATEN_ANREDE',
    'gruppe': ''
}
help_html = gcs.get_help_text(help_config)
```

**Dialog**:
- QTextBrowser mit HTML-Formatierung
- format_text wird korrekt angezeigt
- Links können geöffnet werden
- Schließen-Button

**Button-Styling**:
- **Blau** wenn Hilfe verfügbar (aktiv)
- **Grau** wenn keine Hilfe (disabled)

---

### 3. **ViewTable V3**
**Datei**: `pdvm_input_type_viewtable.py`

**Vorher**:
```python
viewtable_config = {
    'guid': 'view-guid'
}
```

**Jetzt** (V3):
```python
# Aus field_config.configs.viewtable
viewtable_config = {
    'table': 'sys_viewdaten',
    'key': '86aa89c0-...',  # Dies ist die view_guid!
    'feld': ''
}
# key wird als viewtable_guid verwendet
```

---

## 📋 Config-Struktur V3

**Beispiel aus sys_framedaten**:
```json
{
  "PERSONDATEN": {
    "7e4ba8d2-...": {
      "name": "pers_anrede",
      "label": "Anrede",
      "type": "dropdown",
      "configs": {
        "dropdown": {
          "table": "sys_dropdowndaten",
          "key": "ddaa6590-...",
          "feld": "anrede",
          "gruppe": ""
        },
        "help": {
          "table": "sys_beschreibungen",
          "key": "dded74a4-...",
          "feld": "PERSONDATEN_PERSDATEN_ANREDE",
          "gruppe": ""
        }
      }
    },
    "a8efde81-...": {
      "name": "pers_zu_finanzen",
      "type": "viewtable",
      "configs": {
        "viewtable": {
          "table": "sys_viewdaten",
          "key": "86aa89c0-...",
          "feld": ""
        },
        "help": {
          "table": "sys_beschreibungen",
          "key": "dded74a4-...",
          "feld": "PERSONDATEN_PERSDATEN_GEBURTSDATUM",
          "gruppe": ""
        }
      }
    }
  }
}
```

---

## 🔧 GCS-Methoden verwendet

### 1. `get_dropdown_options_v3(config)`
- Lädt edit_list aus sys_dropdowndaten
- Mehrsprachig via DEFAULT_LANGUAGE
- Cache-Unterstützung
- Returns: `[{"key": "...", "value": "..."}]`

### 2. `translate_dropdown_value_v3(config, raw_value)`
- Übersetzt Key → Display-Wert
- Verwendet gleichen Cache
- Returns: `str` (Display-Wert)

### 3. `get_help_text(config)`
- Lädt format_text aus sys_beschreibungen
- Mehrsprachig via DEFAULT_LANGUAGE
- Returns: `str` (HTML)

---

## ✅ Alte Strukturen entfernt

### In `pdvm_input_type_dropdown.py`:
- ❌ `dropdown_config = field_config.get('dropdown_config', {})`
- ❌ `gcs.get_dropdown_options(key, value)`
- ✅ Verwendet jetzt `configs.dropdown` und `get_dropdown_options_v3()`

### In `pdvm_input_control.py`:
- ❌ Alte help_config Struktur
- ❌ Direkter Zugriff auf sys_beschreibungen
- ✅ Verwendet jetzt `configs.help` und `get_help_text()`

### In `pdvm_input_type_viewtable.py`:
- ❌ `viewtable_config.get('guid')`
- ✅ Verwendet jetzt `configs.viewtable.key`

---

## 🧪 Testing

**Dropdown**:
1. Feld mit `type: "dropdown"` und `configs.dropdown`
2. ComboBox sollte Optionen aus sys_dropdowndaten zeigen
3. Wert speichern → Key wird gespeichert

**Hilfe**:
1. Feld mit `configs.help`
2. Blauer `?` Button sollte aktiv sein
3. Klick → Dialog mit formatiertem Text
4. Ohne `configs.help` → Grauer Button (disabled)

**ViewTable**:
1. Feld mit `type: "viewtable"` und `configs.viewtable`
2. Button zeigt GUID
3. Klick → Auswahl-Dialog mit View
4. Auswahl speichert GUID

---

## 📊 Zusammenfassung

| Feature | Status | Methode |
|---------|--------|---------|
| Dropdown V3 | ✅ | `get_dropdown_options_v3()` |
| Übersetzung V3 | ✅ | `translate_dropdown_value_v3()` |
| Hilfe V3 | ✅ | `get_help_text()` |
| ViewTable V3 | ✅ | `configs.viewtable.key` |
| Alte Strukturen entfernt | ✅ | Legacy Code ersetzt |

---

**Status**: ✅ Vollständig implementiert (03.12.2025)
**Dateien**: 
- `pdvm_input_type_dropdown.py`
- `pdvm_input_control.py`
- `pdvm_input_type_viewtable.py`
