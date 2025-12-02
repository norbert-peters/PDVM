# System-Editor V3 Dropdown/Config Integration - Zusammenfassung

## 🎯 Problem

Der System-Editor hatte **zwei Ebenen**, die unterschiedlich behandelt werden mussten:

1. **PROPERTIES-Ebene** (oben): 
   - Bei `type="dropdown"` sollte ein **fertiges Dropdown mit Auswahlliste** erscheinen
   - Werte aus `configs.dropdown` laden
   
2. **CONFIGS-Ebene** (unten):
   - Separater Bereich zum **Bearbeiten der Config-Struktur** selbst
   - Felder: `table`, `key`, `feld`, `gruppe`

**Problem**: Beide verwendeten die gleiche Config-Struktur, aber:
- Properties: Zeigt **Auswahlliste** (Frau/Herr/Diverse)
- Configs: Zeigt **Config-Editor** (table: sys_dropdowndaten, key: 2a60c785...)

---

## ✅ Implementierte Lösung

### 1. Properties-Ebene (`pdvm_property_input_control.py`)

**Änderung**: Dropdown lädt Options aus V3-Config und zeigt **QComboBox mit Auswahlliste**

```python
# VORHER: ConfigEditorWidget (FALSCH für Properties!)
widget = PdvmConfigEditorWidget(...)

# NACHHER: QComboBox mit Options aus V3-System
options_list = gcs.get_dropdown_options_v3(dropdown_config)
# → [{"key": "w", "value": "Frau"}, {"key": "m", "value": "Herr"}, ...]

widget = QComboBox()
for option in options_list:
    key = option.get('key')
    value = option.get('value')
    widget.addItem(value, userData=key)  # Display=Frau, Data=w
```

**Key-Features**:
- ✅ Display-Text: "Frau", "Herr", "Diverse"
- ✅ Gespeicherter Wert: "w", "m", "d" (Key, nicht Display!)
- ✅ `set_value()` sucht nach Key (userData), nicht Display-Text
- ✅ Signal emittiert Key-Wert

---

### 2. Configs-Ebene (`pdvm_system_editor.py`)

**Änderung**: Configs verwenden **ConfigEditorWidget** für table/key/feld/gruppe

```python
# VORHER: Einfache QLineEdit für alle Config-Felder
for config_key, config_val in config_value.items():
    editor = QLineEdit(str(config_val))  # ❌ FALSCH!

# NACHHER: ConfigEditorWidget für dropdown/help
if config_name in ['dropdown', 'help']:
    config_widget = PdvmConfigEditorWidget(
        config_type=config_name,
        initial_config=config_value,
        parent=self
    )
    config_widget.config_changed.connect(on_config_changed)
```

**Key-Features**:
- ✅ **dropdown** Config → ConfigEditorWidget mit Tabellen-/Key-/Feld-Auswahl
- ✅ **help** Config → ConfigEditorWidget (gleiche Struktur)
- ✅ **viewtable** Config → Legacy QLineEdit (keine spezielle Behandlung)
- ✅ Signal `config_changed` → Automatisches Change-Tracking

---

## 📊 Datenfluss

### Properties-Dropdown (Runtime)
```
Template laden (configs.dropdown Config)
  ↓
gcs.get_dropdown_options_v3(config)
  ↓
PdvmCentralDatenbank(table, key)
  ↓
DEFAULT_LANGUAGE → feld → edit_list
  ↓
QComboBox befüllen: addItem(value, userData=key)
  ↓
User wählt "Frau" aus
  ↓
Signal emittiert: "w" (key, nicht "Frau"!)
  ↓
In Datenbank speichern: "w"
```

### Config-Editor (Design-Time)
```
User klickt "+ Config" → "dropdown" auswählen
  ↓
ConfigEditorWidget erstellen
  ↓
Tabelle auswählen: sys_dropdowndaten
  ↓
Key auswählen: "Personal-Dropdowns (2a60c785...)"
  ↓
Feld auswählen: "anrede"
  ↓
config_changed Signal
  ↓
Config in Template speichern:
{
  "table": "sys_dropdowndaten",
  "key": "2a60c785-0829-46db-a16b-9369596fab63",
  "feld": "anrede",
  "gruppe": ""
}
```

---

## 🔧 Geänderte Dateien

### 1. `pdvm_property_input_control.py`
**Zeilen 176-215** (Dropdown-Erstellung):
- ✅ Options aus `gcs.get_dropdown_options_v3()` laden
- ✅ QComboBox mit `addItem(value, userData=key)`
- ✅ Signal emittiert Key (nicht Display-Text)

**Zeilen 464-479** (`set_value`):
- ✅ Suche nach Key (userData) statt Display-Text
- ✅ Fallback auf Display-Text für Legacy-Kompatibilität

### 2. `pdvm_system_editor.py`
**Zeilen 847-895** (`_refresh_properties_editor`):
- ✅ ConfigEditorWidget für dropdown/help Configs
- ✅ Signal `config_changed` → Change-Tracking
- ✅ Fallback auf Legacy-Methode für andere Configs

**Zeilen 872-886** (neu: `_add_legacy_config_fields`):
- ✅ Helper-Methode für nicht-V3 Configs
- ✅ Einfache QLineEdit-Felder wie vorher

---

## 📋 Verwendungsbeispiele

### Template-Definition (sys_viewdaten)
```json
{
  "CONTROL_PROPERTIES": {
    "guid-123": {
      "name": "anrede",
      "label": "Anrede",
      "type": "dropdown",
      "display_order": 5,
      "configs": {
        "dropdown": {
          "table": "sys_dropdowndaten",
          "key": "2a60c785-0829-46db-a16b-9369596fab63",
          "feld": "anrede",
          "gruppe": ""
        }
      }
    }
  }
}
```

### Properties-Editor zeigt
```
┌─────────────────────────────────────┐
│ PROPERTIES                          │
├─────────────────────────────────────┤
│ Name:     [Anrede-Feld_________]    │
│ Label:    [Anrede______________]    │
│ Anrede:   [ Frau        ▼ ]         │ ← QComboBox mit Options!
│           ( Frau / Herr / Diverse ) │
├─────────────────────────────────────┤
│ CONFIGS                             │
├─────────────────────────────────────┤
│ DROPDOWN ┌──────────────────────┐   │
│          │ Tabelle:              │   │
│          │ [sys_dropdowndaten ▼] │   │ ← ConfigEditorWidget!
│          │                       │   │
│          │ Datensatz:            │   │
│          │ [Personal-Dropdowns ▼]│   │
│          │                       │   │
│          │ Feld:                 │   │
│          │ [anrede           ▼]  │   │
│          └──────────────────────┘   │
└─────────────────────────────────────┘
```

---

## 🎯 Vorteile

1. **Klare Trennung**: Properties (Auswahl) vs. Configs (Konfiguration)
2. **User-freundlich**: Dropdown zeigt lesbare Werte ("Frau" statt "w")
3. **Korrekte Speicherung**: Key-Werte ("w") in Datenbank, nicht Display-Text
4. **Mehrsprachig**: Config einmal anlegen, Options pro Sprache
5. **Wartbar**: Config-Änderungen ohne Code-Deployment

---

## ✅ Checkliste

- [x] PropertyInputControl: Dropdown zeigt Options aus V3-Config
- [x] PropertyInputControl: set_value() sucht nach Key (userData)
- [x] PropertyInputControl: Signal emittiert Key-Wert
- [x] SystemEditor: ConfigEditorWidget für dropdown/help Configs
- [x] SystemEditor: Legacy-Methode für andere Configs
- [x] SystemEditor: Change-Tracking für Config-Änderungen

---

**Status**: ✅ Vollständig implementiert  
**Datum**: 02.12.2025  
**Version**: V3.0
