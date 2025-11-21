# Template-Editor: + Feld Button für Template-Modus ✅

## Problem (GELÖST)
Im Template-Modus funktionierte der **"+ Feld"** Button nicht, da die Methoden nur auf View-Modus (`type == 'folder'`) prüften, aber Template-Modus `type == 'template_folder'` verwendet.

## Lösung implementiert

### 1. `_add_field()` - Erweitert für Template-Modus
```python
def _add_field(self):
    # Item-Type ermitteln
    item_type = item_data.get('type')
    
    # TEMPLATE-MODUS
    if self.edit_mode == 'template':
        # Wenn Template-Control ausgewählt → zu Parent wechseln
        if item_type == 'template_control':
            current_item = current_item.parent()
            item_data = current_item.data(0, Qt.UserRole)
            item_type = item_data.get('type')
            
        # Prüfen ob template_folder ausgewählt
        if item_type != 'template_folder':
            QMessageBox.warning(...)
            return
            
        meta_key = item_data['meta_key']  # TEMPLATES, ROOT_CONTROLS, etc.
        self._add_template_item(meta_key)
        return
    
    # VIEW-MODUS (unverändert)
    # ... bestehende Logik
```

### 2. `_remove_field()` - Erweitert für Template-Modus
```python
def _remove_field(self):
    item_type = item_data.get('type')
    
    # TEMPLATE-MODUS
    if self.edit_mode == 'template':
        # Nur template_control kann gelöscht werden
        if item_type != 'template_control':
            QMessageBox.warning(...)
            return
            
        meta_key = item_data['meta_key']
        item_key = item_data['item_key']
        
        # Bestätigung
        reply = QMessageBox.question(...)
        
        # Aus METADATEN löschen
        del self.view_data['METADATEN'][meta_key][item_key]
        
        # TreeView aktualisieren
        self._refresh_field_list()
        return
    
    # VIEW-MODUS (unverändert)
    # ... bestehende Logik
```

### 3. `_add_template_item()` - NEU
```python
def _add_template_item(self, meta_key):
    """Fügt neues Item zu Template-Folder hinzu"""
    
    # Item-Key eingeben
    item_key, ok = QInputDialog.getText(...)
    
    # Standard-Struktur je nach meta_key
    if meta_key == 'TEMPLATES':
        # Kopiere view_text als Basis oder erstelle neue Struktur
        new_item_data = {
            'table': '',
            'gruppe': '',
            'feld': '',
            'label': '',
            'control_type': 'text',
            'width': 150,
            'visible': True,
            # ... alle Standard-Felder
        }
    elif meta_key == 'ROOT_CONTROLS':
        new_item_data = {
            'label': item_key,
            'control_type': 'text',
            'readonly': False,
            'display_order': 999,
            # ...
        }
    elif meta_key == 'CONTROL_PROPERTIES':
        new_item_data = {
            'label': item_key,
            'control_type': 'text',
            'readonly': False,
            # ...
        }
    
    # Item hinzufügen
    self.view_data['METADATEN'][meta_key][item_key] = new_item_data
    
    # TreeView aktualisieren
    self._refresh_field_list()
    
    # Neues Item automatisch auswählen
    # ... Tree durchsuchen und Item auswählen
```

## Verwendung

### Im Template-Modus (GUID 55555...)

1. **Folder auswählen**: 
   - Klick auf 🔧 TEMPLATES, ⚙️ ROOT_CONTROLS oder 🎨 CONTROL_PROPERTIES
   - ODER ein Item darunter auswählen (wechselt automatisch zum Parent-Folder)

2. **"+ Feld" klicken**:
   - Dialog öffnet sich: "Name für neues {TEMPLATES/ROOT_CONTROLS/CONTROL_PROPERTIES}-Item:"
   - Namen eingeben (z.B. "view_custom", "CUSTOM_FIELD", "new_property")
   - OK klicken

3. **Neues Item wird erstellt**:
   - Mit Standard-Struktur basierend auf meta_key
   - Automatisch im Tree angezeigt
   - Automatisch ausgewählt und Editor geöffnet

4. **Item bearbeiten**:
   - Alle Felder im Editor erscheinen
   - Änderungen sofort gespeichert

### Im View-Modus (normale GUIDs)

- Funktioniert wie bisher (unverändert)
- Muss controls/standard_controls Folder auswählen

## Standard-Strukturen

### TEMPLATES
```json
{
  "table": "",
  "gruppe": "",
  "feld": "",
  "label": "",
  "tooltip": "",
  "control_type": "text",
  "width": 150,
  "visible": true,
  "sortable": true,
  "filterable": true,
  "editable": false,
  "alignment": "left",
  "display_order": 0
}
```

### ROOT_CONTROLS
```json
{
  "label": "Field Name",
  "control_type": "text",
  "readonly": false,
  "display_order": 999,
  "muss": false,
  "default_value": "",
  "options": []
}
```

### CONTROL_PROPERTIES
```json
{
  "label": "Property Name",
  "control_type": "text",
  "readonly": false,
  "display_order": 999
}
```

## Features ✅

- ✅ **Intelligente Folder-Erkennung**: Auch wenn Control ausgewählt → wechselt automatisch zum Parent
- ✅ **Modus-abhängig**: Unterschiedliche Logik für Template vs. View
- ✅ **Automatische Auswahl**: Neues Item wird direkt ausgewählt und Editor geöffnet
- ✅ **Duplikat-Prüfung**: Verhindert doppelte Item-Keys
- ✅ **Standard-Strukturen**: Sinnvolle Defaults basierend auf meta_key
- ✅ **Konsistente Fehlermeldungen**: Klare Hinweise für User

## Test

Im laufenden Template-Editor:
1. Template öffnen (GUID 55555555-5555-5555-5555-555555555555)
2. Einen Folder auswählen (z.B. TEMPLATES)
3. "+ Feld" klicken
4. Name eingeben (z.B. "view_my_custom")
5. ✅ Neues Template erscheint im Tree
6. ✅ Editor zeigt alle Felder an
7. ✅ Felder können bearbeitet werden
8. ✅ "💾 Speichern" persistiert Änderungen

---

**Status**: ✅ **VOLLSTÄNDIG IMPLEMENTIERT & GETESTET**
