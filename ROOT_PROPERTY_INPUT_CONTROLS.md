# ROOT Properties mit Property Input Controls

**Datum**: 26.11.2025  
**Erweiterung**: Property Input Controls auch für ROOT-Tab implementiert

## Problem

ROOT-Properties im ersten Tab wurden noch **manuell** mit `QFormLayout` erstellt:

```python
# ALT - Manuell:
form_layout = QFormLayout(scroll_content)

for key, value in sorted(root_data.items()):
    editor_widget = self._create_editor_widget(value, f"ROOT.{key}")
    label = QLabel(f"{key}:")
    form_layout.addRow(label, editor_widget)
```

**Fehlte**:
- ❌ Template-basierte Steuerung
- ❌ display_order Sortierung  
- ❌ read_only Visualisierung
- ❌ Dropdown aus configs.dropdown
- ❌ Konsistente UI mit Gruppen/Felder-Tab

## Lösung Implementiert

### 1. ROOT-Tab auf QVBoxLayout + Property Input Controls umgebaut

**Datei**: `pdvm_system_editor.py`, Lines 296-395

```python
def _create_root_tab(self) -> QWidget:
    """Erstellt ROOT Properties Tab mit Property Input Controls"""
    root_layout = QVBoxLayout(scroll_content)  # VBoxLayout!
    
    # Template-Controls für ROOT laden
    template_guid = '55555555-5555-5555-5555-555555555555'
    template_controls = self._load_template_controls(template_guid, 'ROOT')
    
    if template_controls:
        # === TEMPLATE-BASIERT ===
        
        # Build property_name → control_def map
        prop_controls = {}
        for ctrl_guid, ctrl_def in template_controls.items():
            prop_name = ctrl_def.get('name')
            if prop_name:
                prop_controls[prop_name] = ctrl_def
        
        # Sortiere nach display_order
        properties_sorted = []
        for prop_name, prop_value in root_data.items():
            control_def = prop_controls.get(prop_name, {})
            display_order = self._safe_display_order(control_def)
            properties_sorted.append((display_order, prop_name, prop_value, control_def))
        
        properties_sorted.sort(key=lambda x: x[0])
        
        # Property Input Controls erstellen
        for display_order, prop_name, prop_value, control_def in properties_sorted:
            property_ic = PdvmPropertyInputControl(control_def, prop_value)
            property_ic.value_changed.connect(
                lambda name, value, path=f"ROOT.{prop_name}": 
                    self._on_root_property_changed(path, value)
            )
            
            root_layout.addWidget(property_ic)
            self.root_widgets[prop_name] = property_ic
        
        logger.info(f"✅ {len(self.root_widgets)} ROOT Property Input Controls erstellt")
        
    else:
        # === FALLBACK: Legacy-Widgets ===
        for key, value in sorted(root_data.items()):
            row_widget = QWidget()
            row_layout = QHBoxLayout(row_widget)
            
            label = QLabel(f"{key}:")
            label.setMinimumWidth(150)
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
            editor_widget = self._create_editor_widget(value, f"ROOT.{key}")
            
            row_layout.addWidget(label)
            row_layout.addWidget(editor_widget)
            row_layout.addStretch()
            
            root_layout.addWidget(row_widget)
```

### 2. Handler für ROOT Properties erstellt

**Datei**: `pdvm_system_editor.py`, Lines 844-870

```python
def _on_root_property_changed(self, path: str, new_value):
    """
    Handler wenn ROOT Property-Wert in Property Input Control geändert wurde.
    
    Args:
        path: Pfad zum Property (z.B. "ROOT.TABLE")
        new_value: Neuer Wert
    """
    # Path parsen: ROOT.property_name
    parts = path.split('.')
    if len(parts) != 2 or parts[0] != 'ROOT':
        logger.error(f"❌ Ungültiger ROOT-Pfad: {path}")
        return
    
    property_name = parts[1]
    
    # Wert in ROOT-Daten aktualisieren
    if 'ROOT' in self.data:
        self.data['ROOT'][property_name] = new_value
        
        # Change-Tracking
        self._track_change('modify', path, 
                          self.original_data.get('ROOT', {}).get(property_name), 
                          new_value)
```

## Template-Struktur für ROOT

**Erwartete Struktur** in Template-Datensatz (55555...):

```json
{
  "ROOT_CONTROLS": {
    "ctrl-guid-1": {
      "name": "TABLE",
      "label": "Tabelle",
      "type": "string",
      "display_order": 0,
      "read_only": true
    },
    "ctrl-guid-2": {
      "name": "SELF_GUID",
      "label": "GUID",
      "type": "string",
      "display_order": 1,
      "read_only": true
    },
    "ctrl-guid-3": {
      "name": "DEFAULT_LANGUAGE",
      "label": "Sprache",
      "type": "dropdown",
      "display_order": 2,
      "configs": {
        "dropdown": ["DE-DE", "EN-US", "FR-FR"]
      }
    },
    "ctrl-guid-4": {
      "name": "BESCHREIBUNG_NAME",
      "label": "Beschreibung",
      "type": "string",
      "display_order": 3
    }
  }
}
```

**Mapping**:
- `ROOT` Gruppe → `ROOT_CONTROLS` im Template
- Andere Gruppen → `CONTROL_PROPERTIES` im Template

## Architektur-Konsistenz

### VORHER: Zwei unterschiedliche UI-Systeme

```
ROOT-Tab:
  QFormLayout
  → addRow(label, editor_widget)
  → Manuell erstellt
  → Keine Template-Steuerung

Gruppen/Felder-Tab:
  QVBoxLayout
  → addWidget(PdvmPropertyInputControl)
  → Template-gesteuert
  → display_order, read_only, etc.
```

### NACHHER: Einheitliches System

```
ROOT-Tab:
  QVBoxLayout
  → addWidget(PdvmPropertyInputControl)
  → Template-gesteuert (ROOT_CONTROLS)
  → display_order, read_only, dropdown

Gruppen/Felder-Tab:
  QVBoxLayout
  → addWidget(PdvmPropertyInputControl)
  → Template-gesteuert (CONTROL_PROPERTIES)
  → display_order, read_only, dropdown
```

## Signal-Verbindung

### ROOT Properties
```python
property_ic.value_changed.connect(
    lambda name, value, path=f"ROOT.{prop_name}": 
        self._on_root_property_changed(path, value)
)
```

**Path-Format**: `ROOT.property_name` (z.B. `ROOT.TABLE`)

### Gruppen/Felder Properties
```python
property_ic.value_changed.connect(
    lambda name, value, g=gruppe_name, f=feld_guid: 
        self._on_property_changed(g, f, name, value)
)
```

**Parameter**: `gruppe_name`, `feld_guid`, `property_name`

## Erwartetes Verhalten

### ROOT-Tab öffnen
- ✅ Properties sortiert nach display_order (0, 1, 2, ...)
- ✅ Labels aus Template (z.B. "Tabelle:", "GUID:", "Sprache:")
- ✅ read_only Properties grau + disabled (TABLE, SELF_GUID)
- ✅ Dropdown für DEFAULT_LANGUAGE (aus configs.dropdown)
- ✅ Konsistente UI mit Gruppen/Felder-Tab

### ROOT Property ändern
- ✅ value_changed Signal emittiert
- ✅ `_on_root_property_changed()` aufgerufen
- ✅ Wert in `self.data['ROOT']` aktualisiert
- ✅ Change-Tracking registriert Änderung
- ✅ Änderung wird beim Speichern übernommen

### Speichern
- ✅ ROOT-Änderungen in `self.changes_stack`
- ✅ "Änderungen anzeigen" zeigt ROOT-Changes
- ✅ Speichern schreibt ROOT-Daten in DB

## Debug-Logs

### ROOT-Tab Laden (mit Template)
```
🔍 DEBUG ROOT: Template Controls geladen: True
🔍 DEBUG ROOT: Anzahl Controls: 4
  ROOT Property Input Control: TABLE (order=0)
  ROOT Property Input Control: SELF_GUID (order=1)
  ROOT Property Input Control: DEFAULT_LANGUAGE (order=2)
  ROOT Property Input Control: BESCHREIBUNG_NAME (order=3)
✅ 4 ROOT Property Input Controls erstellt
```

### ROOT-Tab Laden (ohne Template - Fallback)
```
🔍 DEBUG ROOT: Template Controls geladen: False
⚠️ Keine ROOT_CONTROLS im Template → Legacy-Mode
```

### ROOT Property ändern
```
ROOT Property geändert: DEFAULT_LANGUAGE = EN-US
✅ ROOT Property aktualisiert: DEFAULT_LANGUAGE
```

## Fallback-Modus

Falls **keine ROOT_CONTROLS im Template**:
```python
# Legacy-Widgets mit horizontalem Layout
for key, value in sorted(root_data.items()):
    row_widget = QWidget()
    row_layout = QHBoxLayout(row_widget)
    
    label = QLabel(f"{key}:")
    label.setMinimumWidth(150)
    editor_widget = self._create_editor_widget(value, f"ROOT.{key}")
    
    row_layout.addWidget(label)
    row_layout.addWidget(editor_widget)
    root_layout.addWidget(row_widget)
```

**Funktioniert weiterhin**, aber ohne Template-Features.

## Testing-Checkliste

### ROOT-Tab mit Template
- [ ] System-Editor öffnen → ROOT-Tab
- [ ] Properties sortiert nach display_order
- [ ] Labels aus Template sichtbar
- [ ] TABLE + SELF_GUID grau + disabled
- [ ] DEFAULT_LANGUAGE als Dropdown
- [ ] Property ändern → Wert aktualisiert

### ROOT-Tab ohne Template (Fallback)
- [ ] Template löschen/deaktivieren
- [ ] ROOT-Tab öffnen
- [ ] Legacy-Widgets angezeigt
- [ ] Alphabetische Sortierung
- [ ] Property-Namen als Labels
- [ ] Funktioniert wie vorher

### Speichern & Persistierung
- [ ] ROOT Property ändern
- [ ] "Änderungen anzeigen" → ROOT-Change sichtbar
- [ ] Speichern → Daten in DB geschrieben
- [ ] Editor schließen + neu öffnen → Änderung persistiert

### Signal-Verbindung
- [ ] Property ändern → Log: "ROOT Property geändert"
- [ ] Change-Tracking funktioniert
- [ ] Undo/Redo mit ROOT-Changes

## Dateien Geändert

### pdvm_system_editor.py
**Lines 296-395**: `_create_root_tab()` komplett umgebaut
- QVBoxLayout statt QFormLayout
- Template-basierte Property Input Controls
- Legacy-Fallback mit Wrapper-Widgets

**Lines 844-870**: `_on_root_property_changed()` neu erstellt
- Handler für ROOT Property-Änderungen
- Path-Parsing: `ROOT.property_name`
- Change-Tracking Integration

## Zusammenfassung

**Vorher**:
- ROOT-Tab: Manuell mit QFormLayout
- Gruppen/Felder-Tab: Template-basiert mit Property Input Controls
- **Zwei unterschiedliche Systeme**

**Nachher**:
- ROOT-Tab: Template-basiert mit Property Input Controls (ROOT_CONTROLS)
- Gruppen/Felder-Tab: Template-basiert mit Property Input Controls (CONTROL_PROPERTIES)
- **Einheitliches System überall**

**Vorteile**:
- ✅ Konsistente UI in beiden Tabs
- ✅ Template-gesteuerte Konfiguration überall
- ✅ display_order, read_only, dropdown überall verfügbar
- ✅ Weniger Code-Duplikation
- ✅ Einfachere Wartung

---

**STATUS**: ROOT Property Input Controls implementiert. Bereit für Test.
