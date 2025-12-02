# Property Input Control - Template Beispiele

## Template-Struktur für ROOT_CONTROLS (55555555-5555-5555-5555-555555555555)

```python
ROOT_CONTROLS = {
    # STRING (read_only)
    "guid-table": {
        "name": "TABLE",
        "label": "Tabelle",
        "type": "string",
        "display_order": 0,
        "read_only": True,
        "required": True
    },
    
    # STRING (edierbar)
    "guid-self-guid": {
        "name": "SELF_GUID",
        "label": "Eigene GUID",
        "type": "string",
        "display_order": 1,
        "read_only": True
    },
    
    # STRING (mit max_length)
    "guid-beschr-name": {
        "name": "BESCHREIBUNG_NAME",
        "label": "Beschreibungsname",
        "type": "string",
        "display_order": 2,
        "required": True,
        "max_length": 100
    },
    
    # DROPDOWN (mit Options aus configs.dropdown)
    "guid-default-lang": {
        "name": "DEFAULT_LANGUAGE",
        "label": "Standardsprache",
        "type": "dropdown",
        "display_order": 3,
        "default": "DE-DE",
        "configs": {
            "dropdown": ["DE-DE", "EN-US", "FR-FR", "IT-IT", "ES-ES"]
        }
    },
    
    # INT (mit min/max)
    "guid-priority": {
        "name": "PRIORITY",
        "label": "Priorität",
        "type": "int",
        "display_order": 4,
        "min": 0,
        "max": 100,
        "default": 50
    },
    
    # BOOL (Checkbox)
    "guid-active": {
        "name": "ACTIVE",
        "label": "Aktiv",
        "type": "bool",
        "display_order": 5,
        "default": True
    },
    
    # MULTILINE (TextEdit)
    "guid-description": {
        "name": "DESCRIPTION",
        "label": "Beschreibung",
        "type": "multiline",
        "display_order": 6,
        "max_length": 500
    }
}
```

## Verwendung im System-Editor

```python
from pdvm_property_input_control import PdvmPropertyInputControl

class PdvmSystemEditor(QWidget):
    def __init__(self, table_name, guid):
        # ...
        self.property_widgets = {}  # {property_name: PdvmPropertyInputControl}
        self._build_property_controls()
    
    def _build_property_controls(self):
        """Erstellt Property Input Controls aus Template (sortiert nach display_order)."""
        # Template laden (55555...)
        template_db = PdvmCentralDatenbank(self.table_name, '55555555-5555-5555-5555-555555555555')
        root_controls = template_db.get_value_by_group('ROOT_CONTROLS')
        
        if not root_controls:
            logger.warning("Keine ROOT_CONTROLS im Template gefunden")
            return
        
        # Nach display_order sortieren
        sorted_controls = sorted(
            root_controls.items(),
            key=lambda x: self._safe_display_order(x[1])
        )
        
        # Vertikales Layout für Properties
        properties_layout = QVBoxLayout()
        
        # Property Input Controls erstellen
        for control_guid, control_def in sorted_controls:
            prop_name = control_def.get('name')
            if not prop_name:
                continue
            
            # Aktuellen Wert aus DB holen
            current_value, _ = self.db.get_value('ROOT', prop_name)
            
            # Property Input Control erstellen (konfiguriert sich selbst!)
            property_ic = PdvmPropertyInputControl(control_def, current_value)
            property_ic.value_changed.connect(self._on_property_changed)
            
            # Zu Layout hinzufügen
            properties_layout.addWidget(property_ic)
            
            # In Dictionary speichern für späteren Zugriff
            self.property_widgets[prop_name] = property_ic
            
            logger.debug(f"Property Input Control erstellt: {prop_name} (order={property_ic.get_display_order()})")
        
        properties_layout.addStretch()
        
        logger.info(f"✅ {len(self.property_widgets)} Property Input Controls erstellt (sortiert)")
    
    def _safe_display_order(self, control_def):
        """Sichere display_order Konvertierung."""
        order = control_def.get('display_order', 999)
        if order == '' or order is None:
            return 999
        try:
            return int(order)
        except (ValueError, TypeError):
            return 999
    
    def _on_property_changed(self, property_name: str, new_value):
        """Handler wenn Property-Wert geändert wurde."""
        logger.info(f"Property geändert: {property_name} = {new_value}")
        
        # In DB speichern
        from pdvm_central_systemsteuerung import get_gcs
        gcs = get_gcs()
        stichtag = gcs.st_inst.PdvmDateTime if gcs else None
        
        self.db.set_value('ROOT', property_name, new_value, stichtag)
        
        # Dirty-Flag setzen (für "Änderungen übernehmen" Dialog)
        self.dirty = True
    
    def save_all_properties(self):
        """Speichert alle Properties in DB."""
        # Validierung aller Properties
        for prop_name, property_ic in self.property_widgets.items():
            is_valid, error_msg = property_ic.validate()
            
            if not is_valid:
                QMessageBox.warning(self, "Validierung fehlgeschlagen", error_msg)
                return False
        
        # Alle Werte nochmal holen und speichern
        for prop_name, property_ic in self.property_widgets.items():
            value = property_ic.get_value()
            
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            stichtag = gcs.st_inst.PdvmDateTime if gcs else None
            
            self.db.set_value('ROOT', prop_name, value, stichtag)
        
        # In DB persistieren
        self.db.save_all_values()
        
        logger.info("✅ Alle Properties gespeichert")
        return True
```

## Features

### ✅ Implementiert:
1. **Template-gesteuert**: Control-Definition steuert alles (Label, Type, read_only, etc.)
2. **display_order**: Sortierung nach display_order im System-Editor
3. **read_only**: Widgets disabled + grauer Hintergrund
4. **Dropdown aus configs.dropdown**: QComboBox wenn Options vorhanden, sonst QLineEdit
5. **Type-basierte Widgets**: string, int, float, bool, dropdown, multiline
6. **Validierung**: required, min/max, max_length
7. **Signal value_changed**: Für Live-Updates

### 📋 Dropdown-Logik:
```python
# Im Template:
"configs": {
    "dropdown": ["Option1", "Option2", "Option3"]
}

# Wenn configs.dropdown fehlt → QLineEdit (keine Auswahl)
# Wenn configs.dropdown vorhanden → QComboBox mit Options
```

### 🎨 Visual Feedback:
- **read_only**: Grauer Hintergrund (#f0f0f0) + disabled
- **Label**: Rechts-aligned, feste Breite 150px
- **Input**: Mindest-Breite abhängig vom Type

## Migration System-Editor

**ALT** (manuell, 200+ Zeilen):
```python
# Jedes Property einzeln erstellt
for feld_name, feld_data in felder.items():
    label = QLabel(...)
    edit = QLineEdit(...)
    # ... read_only vergessen
    # ... display_order nicht beachtet
```

**NEU** (autonom, ~50 Zeilen):
```python
# Template-gesteuert, automatisch sortiert
for control_guid, control_def in sorted_controls:
    property_ic = PdvmPropertyInputControl(control_def, current_value)
    property_ic.value_changed.connect(self._on_property_changed)
    layout.addWidget(property_ic)
```

## Nächste Schritte

1. **System-Editor anpassen**: `pdvm_system_editor.py` umbauen auf Property Input Controls
2. **Template erweitern**: ROOT_CONTROLS für alle sys_* Tabellen definieren
3. **Testen**: Reihenfolge + read_only + Dropdown in sys_beschreibungen
4. **Integration**: Genereller Dialog anpassen (Phase 2)
