# PDVM Dropdown/Help V3 System - Vollständige Dokumentation

## 🎯 Übersicht

Das **V3 Dropdown/Help-System** ist eine **datenbankgesteuerte, mehrsprachige Lösung** für Dropdowns und Hilfetexte im PDVM-System.

### Kernmerkmale
- ✅ **Einheitliche Struktur** für Dropdowns und Help-Texte
- ✅ **Mehrsprachigkeit** mit DEFAULT_LANGUAGE + Override
- ✅ **Config-basiert** (keine hardcodierten Options)
- ✅ **Template-gesteuert** (vollständig in Datenbank)
- ✅ **edit_list Integration** (wiederverwendbarer Listen-Editor)
- ✅ **Cache-System** für Performance

---

## 📁 Architektur

### 1. Datenbank-Struktur

#### sys_dropdowndaten (Beispiel: Anrede)
```json
{
  "ROOT": {
    "SELF_GUID": "2a60c785-0829-46db-a16b-9369596fab63",
    "DEFAULT_LANGUAGE": "DE-DE",
    "BESCHREIBUNG_NAME": "Die Dropdowns für den Bereich Personal",
    "TABLE": "sys_dropdowndaten",
    "VERSION": "1.0",
    "CREATED_AT": 1733155200.0,
    "MODIFIED_AT": 1733155200.0
  },
  "DE-DE": {
    "49b877af-f852-4a9b-9dac-088d6239bf47": {
      "name": "anrede",
      "label": "Anrede",
      "display_order": "0",
      "list_name": "anrede",
      "enabled": true,
      "edit_list": [
        {"key": "w", "value": "Frau"},
        {"key": "m", "value": "Herr"},
        {"key": "d", "value": "Frau oder Herr"}
      ]
    }
  },
  "EN-US": {
    "49b877af-f852-4a9b-9dac-088d6239bf47": {
      "name": "anrede",
      "label": "Salutation",
      "display_order": "0",
      "list_name": "salutation",
      "enabled": true,
      "edit_list": [
        {"key": "w", "value": "Mrs"},
        {"key": "m", "value": "Mr"},
        {"key": "d", "value": "Mrs or Mr"}
      ]
    }
  }
}
```

#### sys_beschreibungen (Beispiel: Help-Text)
```json
{
  "ROOT": {
    "SELF_GUID": "0f6ea4fd-f231-4f8f-9b3f-8ed4d671a132",
    "DEFAULT_LANGUAGE": "DE-DE",
    "BESCHREIBUNG_NAME": "Beschreibungen und Hilfetexte",
    "TABLE": "sys_beschreibungen"
  },
  "DE-DE": {
    "06135ae7-7b69-43d4-b0c4-1b6e9f628bcc": {
      "name": "anrede",
      "label": "Anrede",
      "display_order": "0",
      "show": true,
      "type": "dropdown",
      "read_only": true,
      "format_text": "<!DOCTYPE HTML...>Wählen Sie die Anrede aus...</body></html>"
    }
  }
}
```

### 2. Config-Struktur

#### Dropdown-Config
```json
{
  "table": "sys_dropdowndaten",
  "key": "2a60c785-0829-46db-a16b-9369596fab63",
  "feld": "anrede",
  "gruppe": ""  // Optional: Sprach-Override (leer = DEFAULT_LANGUAGE)
}
```

#### Help-Config
```json
{
  "table": "sys_beschreibungen",
  "key": "0f6ea4fd-f231-4f8f-9b3f-8ed4d671a132",
  "feld": "anrede",
  "gruppe": ""
}
```

---

## 🔧 Komponenten

### 1. PdvmConfigEditorWidget (`pdvm_config_editor_widget.py`)

**Zweck**: UI-Widget für Config-Pflege im System-Editor

**Features**:
- ✅ Tabellen-Auswahl (sys_dropdowndaten, sys_beschreibungen)
- ✅ Key-Auswahl aus Datenbank (UID + BESCHREIBUNG_NAME)
- ✅ Feld-Auswahl aus DEFAULT_LANGUAGE Gruppe
- ✅ Sprach-Override (optional)
- ✅ Live-Validierung + Info-Label
- ✅ Signal `config_changed(dict)`

**Verwendung**:
```python
from pdvm_config_editor_widget import PdvmConfigEditorWidget

# Widget erstellen
config_widget = PdvmConfigEditorWidget(
    config_type='dropdown',  # oder 'help'
    initial_config=existing_config,  # optional
    parent=self
)

# Signal verbinden
config_widget.config_changed.connect(self.on_config_changed)

# Config auslesen
config = config_widget.get_config()
# Returns: {"table": "...", "key": "...", "feld": "...", "gruppe": "..."}
```

### 2. GCS Dropdown/Help Methoden (`pdvm_central_systemsteuerung.py`)

#### get_dropdown_options_v3(config)
```python
from pdvm_central_systemsteuerung import get_gcs
gcs = get_gcs()

config = {
    "table": "sys_dropdowndaten",
    "key": "2a60c785-0829-46db-a16b-9369596fab63",
    "feld": "anrede",
    "gruppe": ""
}

options = gcs.get_dropdown_options_v3(config)
# Returns: [{"key": "w", "value": "Frau"}, {"key": "m", "value": "Herr"}, ...]
```

#### translate_dropdown_value_v3(config, raw_value)
```python
display_text = gcs.translate_dropdown_value_v3(config, "m")
# Returns: "Herr"
```

#### get_help_text(config)
```python
help_config = {
    "table": "sys_beschreibungen",
    "key": "0f6ea4fd-f231-4f8f-9b3f-8ed4d671a132",
    "feld": "anrede",
    "gruppe": ""
}

help_html = gcs.get_help_text(help_config)
# Returns: "<!DOCTYPE HTML...>..."
```

### 3. Integration in PdvmPropertyInputControl

**Automatische Erkennung**:
```python
# Template-Definition
control_def = {
    "name": "type",
    "label": "Typ",
    "type": "dropdown",
    "configs": {
        "dropdown": {
            "table": "sys_dropdowndaten",
            "key": "4f290b6f-1205-494b-8f03-c6446c0df169",
            "feld": "alligment",
            "gruppe": ""
        }
    }
}

# Property-Input-Control erstellt automatisch Config-Editor-Widget!
property_ic = PdvmPropertyInputControl(control_def, current_value)
```

---

## 📋 Datenfluss

### Dropdown-Laden
```
System-Editor öffnen
  ↓
PropertyInputControl erkennt type="dropdown" + configs.dropdown (dict)
  ↓
ConfigEditorWidget erstellen
  ↓
Tabelle wählen → PdvmDatenbank.execute_query(sys_dropdowndaten)
  ↓
Key wählen → PdvmCentralDatenbank(table, key) → ROOT laden
  ↓
Feld wählen → DEFAULT_LANGUAGE Gruppe → edit_list extrahieren
  ↓
Config speichern in Template
```

### Dropdown-Verwendung (Runtime)
```
View öffnen mit Dropdown-Spalte
  ↓
Control-Definition aus Template laden (configs.dropdown)
  ↓
gcs.get_dropdown_options_v3(config)
  ↓
PdvmCentralDatenbank(table, key)
  ↓
ROOT → DEFAULT_LANGUAGE → feld → edit_list
  ↓
Cache speichern (_dropdown_cache_v3)
  ↓
Dropdown befüllen mit Options
```

---

## 🎨 Template-Integration

### System-Editor Template (sys_viewdaten)
```json
{
  "CONTROL_PROPERTIES": {
    "6919b30c-a4b6-48b0-b3d3-ea730a04ddde": {
      "name": "type",
      "label": "Typ",
      "type": "dropdown",
      "display_order": 6,
      "configs": {
        "dropdown": {
          "table": "sys_dropdowndaten",
          "key": "4f290b6f-1205-494b-8f03-c6446c0df169",
          "feld": "control_type",
          "gruppe": ""
        }
      }
    }
  }
}
```

---

## ⚙️ Erweiterte Features

### 1. Mehrsprachigkeit

**Automatische Spracherkennung**:
```python
# GCS Language: DE-DE
options = gcs.get_dropdown_options_v3(config)
# → Verwendet DE-DE aus DEFAULT_LANGUAGE

# Expliziter Override
config["gruppe"] = "EN-US"
options = gcs.get_dropdown_options_v3(config)
# → Verwendet EN-US
```

### 2. Cache-System

**Performance-Optimierung**:
- Cache-Key: `{table}_{key}_{feld}_{gruppe}`
- Lebensdauer: Pro Session
- Clear: Bei Logout oder explizitem Cache-Clear

### 3. Validierung

**Config-Validierung**:
```python
def validate_config(config: dict) -> bool:
    """Prüft ob Config vollständig"""
    required = ['table', 'key', 'feld']
    return all(k in config and config[k] for k in required)
```

---

## 🚀 Implementierungsstatus

### ✅ Abgeschlossen
1. ✅ GCS Methoden (`get_dropdown_options_v3`, `translate_dropdown_value_v3`, `get_help_text`)
2. ✅ ConfigEditorWidget (UI + Basis-Funktionalität)
3. ✅ Integration in PropertyInputControl
4. ✅ DB-Zugriff in ConfigEditorWidget

### 🔄 In Arbeit
1. 🔄 set_config() Implementierung (Key/Feld setzen nach Laden)
2. 🔄 Template-Update für alle Dropdowns im System-Editor

### 📋 TODO
1. ⏳ Zusätzliche Config-Parameter (allow_empty, default_value, placeholder)
2. ⏳ Help-Config-Widget (analog zu Dropdown)
3. ⏳ Validierungs-Feedback im Config-Editor
4. ⏳ Migration alter Dropdown-Definitionen zu V3

---

## 📝 Beispiel: Kompletter Workflow

### Schritt 1: Dropdown in DB anlegen
```sql
INSERT INTO sys_dropdowndaten (uid, daten) VALUES (
  '2a60c785-0829-46db-a16b-9369596fab63',
  '{"ROOT": {"SELF_GUID": "...", "DEFAULT_LANGUAGE": "DE-DE", ...}, "DE-DE": {...}}'
);
```

### Schritt 2: Template konfigurieren
```python
# In pdvm_system_editor.py
template = {
    "CONTROL_PROPERTIES": {
        "guid-123": {
            "name": "anrede",
            "type": "dropdown",
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

### Schritt 3: In View verwenden
```python
# Automatisch durch PropertyInputControl!
# Keine manuelle Dropdown-Befüllung mehr nötig
```

---

## 🎯 Vorteile

1. **Zentrale Verwaltung**: Dropdowns in Datenbank, nicht im Code
2. **Mehrsprachigkeit**: Automatisch ohne Code-Änderung
3. **Wiederverwendbarkeit**: Gleiche Dropdowns in mehreren Views
4. **Template-gesteuert**: Vollständig konfigurierbar
5. **Performance**: Cache-System für schnellen Zugriff
6. **Wartbarkeit**: Änderungen in DB, kein Code-Deployment

---

**Version**: 3.0  
**Datum**: 02.12.2025  
**Status**: ✅ Phase 3 Implementiert (Integration in System-Editor)
