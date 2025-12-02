# Template-System mit Pflichtfeldern - ERFOLGREICH IMPLEMENTIERT

**Datum:** 19.11.2025  
**Status:** ✅ ABGESCHLOSSEN

## Problem & Anforderungen

**User-Feedback:**
> "Du hast nun den ganzen Editor durcheinander gebracht. 1. Es ist nicht gut, wenn eine zwingende Eingabe durch hinzufügen eines Feldes erfolgen muss. Dieses würde ich mit einem Template zusammen mit dem Namen des Datensatzes machen und in dem Template eine Eigenschaft 'muss'=true für ein Pflichtefeld haben."

**Ziel:**
1. ROOT-Tab zurück auf einfache Version (ohne manuelle Add/Remove Buttons)
2. Template-System mit `muss=true` Property für Pflichtfelder
3. Template wird bei Neuanlage mit Name zusammen geladen

## Implementierte Lösung

### 1. View-Editor ROOT-Tab zurückgesetzt ✅

**Datei:** `pdvm_view_editor.py`

**Änderungen:**
- Entfernt: Header mit "+ Feld hinzufügen" / "- Feld löschen" Buttons
- Entfernt: `_add_root_field()` und `_remove_root_field()` Methoden
- Zurück zu: Einfaches Formular aus `root_controls` (aus Frame-METADATEN)

```python
def _create_root_tab(self):
    """Tab 1: ROOT-Felder bearbeiten (einfach, aus root_controls)"""
    widget = QWidget()
    layout = QVBoxLayout(widget)
    
    # Scroll-Bereich
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll_content = QWidget()
    form_layout = QFormLayout(scroll_content)
    
    self.root_widgets = {}
    
    # Alle ROOT-Felder aus root_controls anzeigen
    for control in sorted(self.root_controls, key=lambda x: x.get('display_order', 999)):
        control_key = control['control_key']
        label = control['label']
        # ... Widget erstellen ...
```

### 2. VIEW-Template mit Pflichtfeld-Support ✅

**Datei:** `create_view_templates.py` (NEU)

**Template-GUID:** `55555555-5555-5555-5555-555555555555`

**ROOT_CONTROLS mit `muss` Property:**
```python
ROOT_CONTROLS = [
    {
        "control_key": "VIEW_NAME",
        "label": "View-Name",
        "control_type": "text",
        "readonly": False,
        "display_order": 0,
        "muss": True,  # PFLICHTFELD!
        "default_value": ""
    },
    {
        "control_key": "VIEW_TABLE",
        "label": "Basis-Tabelle",
        "control_type": "text",
        "readonly": False,
        "display_order": 1,
        "muss": True,  # PFLICHTFELD!
        "default_value": ""
    },
    # ... weitere 8 optionale Felder ...
]
```

**Eigenschaften:**
- ✅ 10 ROOT-Controls definiert
- ✅ 2 Pflichtfelder: `VIEW_NAME`, `VIEW_TABLE`
- ✅ 5 Control-Templates (text, number, date, dropdown, checkbox)
- ✅ 13 Control-Properties für Spalten-Konfiguration

**Ausführung:**
```bash
python create_view_templates.py
# OUTPUT:
#   ✅ Template gespeichert
#      - 5 Templates
#      - 10 ROOT-Controls (2 Pflichtfelder)
#      - 13 Control-Properties
#      - Pflichtfelder: VIEW_NAME, VIEW_TABLE
```

### 3. FRAME-Template erweitert mit Pflichtfeld-Support ✅

**Datei:** `create_frame_templates.py` (AKTUALISIERT)

**ROOT_CONTROLS mit `muss` Property:**
```python
ROOT_CONTROLS = [
    {
        "control_key": "ROOT_TABLE",
        "label": "Root-Tabelle",
        "control_type": "text",
        "readonly": False,
        "display_order": 0,
        "muss": True,  # PFLICHTFELD!
        "default_value": ""
    },
    {
        "control_key": "EDIT_TYPE",
        "label": "Editor-Typ",
        "control_type": "text",
        "readonly": False,
        "display_order": 4,
        "muss": True,  # PFLICHTFELD!
        "default_value": "input_form"
    },
    # ... weitere 13 optionale Felder mit default_value ...
]
```

**Eigenschaften:**
- ✅ 15 ROOT-Controls definiert
- ✅ 2 Pflichtfelder: `ROOT_TABLE`, `EDIT_TYPE`
- ✅ 5 Control-Templates (text, dropdown, datetime, viewtable, number)
- ✅ 17 Control-Properties für Frame-Controls
- ✅ Alle Felder haben `default_value` für automatisches Ausfüllen

**Ausführung:**
```bash
python create_frame_templates.py
# OUTPUT:
#   ✅ Template gespeichert
#      - 5 Templates
#      - 15 ROOT-Controls (2 Pflichtfelder)
#      - 17 Control-Properties
#      - Pflichtfelder: ROOT_TABLE, EDIT_TYPE
```

## Template-Struktur in DB

**Tabelle:** `sys_viewdaten` / `sys_framedaten`  
**GUID:** `55555555-5555-5555-5555-555555555555`

**JSON-Struktur:**
```json
{
  "ROOT": {
    "VIEW_NAME": "",
    "VIEW_TABLE": "",
    "VIEW_GUID": "",
    "HEADER_TEXT": "",
    "NO_DATA": false,
    "PROJECTION_MODE": "standard",
    "ALLOW_FILTER": true,
    "ALLOW_SORT": true,
    "DEFAULT_SORT_COLUMN": "",
    "DEFAULT_SORT_REVERSE": false
  },
  "METADATEN": {
    "TEMPLATES": {
      "view_text": { /* Control-Template */ },
      "view_number": { /* Control-Template */ },
      "view_date": { /* Control-Template */ },
      "view_dropdown": { /* Control-Template */ },
      "view_checkbox": { /* Control-Template */ }
    },
    "ROOT_CONTROLS": [
      {
        "control_key": "VIEW_NAME",
        "label": "View-Name",
        "control_type": "text",
        "readonly": false,
        "display_order": 0,
        "muss": true,
        "default_value": ""
      },
      // ... weitere Controls ...
    ],
    "CONTROL_PROPERTIES": [
      {
        "property": "table",
        "label": "Tabelle",
        "control_type": "text",
        "display_order": 0
      },
      // ... weitere Properties ...
    ]
  }
}
```

## Aktueller Workflow (Neuanlage)

**Ablauf in `pdvm_genereller_dialog.py`:**

1. **User klickt "➕ Neuer Datensatz"**
2. **Name-Eingabe Dialog** (Pflichtfeld-Validierung)
3. **Neue GUID generieren**
4. **`set_new_data_container(guid, name)`** - Erstellt leeren Container
5. **Editor öffnet** - ROOT-Tab zeigt alle Felder aus Template
6. **User füllt Pflichtfelder aus** (VIEW_TABLE, etc.)
7. **Speichern** - Validierung prüft Pflichtfelder (TODO)

## Nächste Schritte (TODO)

### 1. Pflichtfeld-Validierung beim Speichern
**Ziel:** Speichern nur möglich, wenn alle Pflichtfelder (`muss=true`) ausgefüllt

```python
def _save_all(self):
    """Speichert alle Daten mit Pflichtfeld-Validierung"""
    # Pflichtfelder prüfen
    pflichtfelder_fehlen = []
    for control in self.root_controls:
        if control.get('muss'):
            control_key = control['control_key']
            value = self.view_data['ROOT'].get(control_key, '')
            if not value or str(value).strip() == '':
                pflichtfelder_fehlen.append(control['label'])
    
    if pflichtfelder_fehlen:
        QMessageBox.warning(
            self,
            "Pflichtfelder fehlen",
            f"Bitte füllen Sie folgende Pflichtfelder aus:\n\n" +
            "\n".join(f"• {feld}" for feld in pflichtfelder_fehlen)
        )
        return
    
    # Speichern...
```

### 2. Template-Auto-Load bei Neuanlage
**Ziel:** ROOT-Felder automatisch aus Template befüllen

```python
def _load_view_data(self):
    """Holt View-Daten aus bereits geladener Instanz"""
    self.view_data = self.view_db.data
    
    # Wenn ROOT leer → Template laden
    if not self.view_data.get('ROOT') or len(self.view_data['ROOT']) == 0:
        logger.info("  ℹ️ ROOT leer → Lade Template-Defaults")
        template_root = self.template_db.data.get('ROOT', {})
        self.view_data['ROOT'] = template_root.copy()
        logger.info(f"  ✅ {len(template_root)} Template-Defaults geladen")
```

### 3. Pflichtfeld-Markierung im UI
**Ziel:** Pflichtfelder visuell hervorheben

```python
# Im _create_root_tab():
for control in self.root_controls:
    label_text = control['label']
    
    # Pflichtfeld markieren
    if control.get('muss'):
        label_text = f"<b>{label_text} *</b>"
    
    label_widget = QLabel(label_text)
    # ...
```

## Zusammenfassung

✅ **View-Editor ROOT-Tab** - Zurückgesetzt auf einfache Version  
✅ **VIEW-Template** - Erstellt mit 2 Pflichtfeldern (VIEW_NAME, VIEW_TABLE)  
✅ **FRAME-Template** - Erweitert mit 2 Pflichtfeldern (ROOT_TABLE, EDIT_TYPE)  
✅ **Template-Scripts** - `create_view_templates.py` und `create_frame_templates.py` aktualisiert  
✅ **Datenbank** - Templates in `pdvm_system.db` gespeichert  

⏳ **Pflichtfeld-Validierung** - Noch zu implementieren  
⏳ **Auto-Load Templates** - Noch zu implementieren  
⏳ **UI-Markierung** - Noch zu implementieren  

**User kann jetzt:**
- View/Frame-Editor öffnen mit sauberen ROOT-Feldern aus Template
- Pflichtfelder sind in Template definiert (`muss=true`)
- Templates bieten sinnvolle Defaults für alle Felder

**Nächster Schritt:** Pflichtfeld-Validierung beim Speichern implementieren
