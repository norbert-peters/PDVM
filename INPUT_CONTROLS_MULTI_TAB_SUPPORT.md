# ✅ MULTI-TAB SUPPORT FÜR INPUT-CONTROLS IMPLEMENTIERT

**Datum**: 22.10.2025  
**Status**: ✅ Grundfunktionalität implementiert (Dialog TODO)

---

## 🎯 IMPLEMENTIERTE FEATURES

### 1. ✅ Tab-Konfiguration aus Framedaten
- **EDIT_TABS**: Anzahl der Tabs (Int)
- **EDIT_TAB_LABEL_nn**: Label für jeden Tab (z.B. EDIT_TAB_LABEL_01, EDIT_TAB_LABEL_02)
- Wenn EDIT_TABS = 1 → Einzelne ScrollArea (kein TabWidget)
- Wenn EDIT_TABS > 1 → QTabWidget mit entsprechenden Tabs

### 2. ✅ Controls mit Tab + Order Attributen
- Metadaten enthalten jetzt `tab` (Tab-Nummer) und `order` (Reihenfolge)
- Controls werden nach Tab und Order sortiert
- Controls werden automatisch in den richtigen Tab platziert

### 3. ✅ Projektion aus app_db
- **frame_guid.FRAME_PROJ**: Persistente Projektion (JSON)
- Format: `{"FIELD_KEY": {"tab": 1, "order": 1}, ...}`
- Bei Laden: Projektion aus app_db überschreibt Metadaten-Default
- Wenn keine Projektion: Verwende Default aus Metadaten

### 4. ✅ Admin-Modus: Einstellungen-Button
- Button "⚙️ Einstellungen" (nur wenn `gcs.field_value('mode') == 'admin'`)
- Öffnet Dialog zur Anpassung von Tab + Order (TODO: Dialog implementieren)
- Zeigt aktuell Placeholder-Nachricht

### 5. ✅ frame_guid für Persistierung
- Optionaler Parameter in `__init__()`
- Falls nicht übergeben: Laden aus `framedaten_db.ROOT.FRAME_GUID`
- Fallback: "DEFAULT_FRAME"

---

## 📋 ARCHITEKTUR

### Datenfluss

```
[1] FRAMEDATEN LADEN
  ├─ ROOT.EDIT_TABS → num_tabs
  ├─ ROOT.EDIT_TAB_LABEL_01 → tab_config[1]
  ├─ ROOT.EDIT_TAB_LABEL_02 → tab_config[2]
  └─ METADATEN.{FIELD_KEY} → {tab, order, label, ...}

[2] PROJEKTION LADEN
  ├─ app_db.{frame_guid}.FRAME_PROJ (JSON)
  └─ Überschreibt Metadaten-tab/order

[3] CONTROLS SORTIEREN
  ├─ sort(key=(tab, order))
  └─ controls_matrix mit korrekter Reihenfolge

[4] UI ERSTELLEN
  ├─ num_tabs > 1 → QTabWidget mit Tabs
  └─ num_tabs == 1 → Einzelne ScrollArea

[5] CONTROLS PLATZIEREN
  ├─ Tab-Nummer aus Matrix → Ziel-Tab finden
  └─ Control in Tab-Container hinzufügen
```

### Metadaten-Format (ERWEITERT)

```json
{
  "PERSONDATEN_PERSDATEN_ANREDE": {
    "source_path": "root",
    "label": "Anrede",
    "tooltip": "Anrede bitte auswählen",
    "type": "dropdown",
    "tab": 1,        // NEU: Tab-Nummer
    "order": 1       // NEU: Reihenfolge im Tab
  },
  "PERSONDATEN_PERSDATEN_FAMILIENNAME": {
    "source_path": "root",
    "label": "Familienname",
    "tab": 1,
    "order": 2
  },
  "FINANZDATEN_FINANZDATEN_KONTOINHABER": {
    "source_path": "root_PERSDATEN",
    "label": "Kontoinhaber",
    "tab": 2,        // Anderer Tab!
    "order": 1
  }
}
```

### Persistierte Projektion (app_db)

**Gruppe**: `frame_guid`  
**Feld**: `FRAME_PROJ`  
**Format**: JSON-String

```json
{
  "PERSONDATEN_PERSDATEN_ANREDE": {"tab": 1, "order": 1},
  "PERSONDATEN_PERSDATEN_FAMILIENNAME": {"tab": 1, "order": 2},
  "FINANZDATEN_FINANZDATEN_KONTOINHABER": {"tab": 2, "order": 1}
}
```

**Priorität**: Persistierte Projektion > Metadaten-Default

---

## 🔧 CODE-ÄNDERUNGEN

### 1. Neue Member-Variablen

```python
class PdvmInputControlsManagerV2:
    def __init__(self, framedaten_db, selected_guid, frame_guid=None):
        # NEU: Frame-GUID für Persistierung
        self.frame_guid = frame_guid or framedaten_db.get_value('ROOT', 'FRAME_GUID')[0]
        
        # NEU: Tab-Konfiguration
        self.tab_config: Dict[int, str] = {}  # {1: "Tab 1", 2: "Tab 2"}
        self.num_tabs: int = 1
        
        # NEU: TabWidget (nur wenn mehrere Tabs)
        self.tab_widget: Optional[QTabWidget] = None
```

### 2. Neue Methode: `_load_tab_config()`

```python
def _load_tab_config(self):
    """Lädt Tab-Konfiguration aus Framedaten"""
    # EDIT_TABS laden
    edit_tabs, _ = self.framedaten_db.get_value('ROOT', 'EDIT_TABS')
    self.num_tabs = int(edit_tabs) if edit_tabs else 1
    
    # Tab-Labels laden
    for i in range(1, self.num_tabs + 1):
        field_name = f"EDIT_TAB_LABEL_{i:02d}"
        label, _ = self.framedaten_db.get_value('ROOT', field_name)
        self.tab_config[i] = label if label else f"Tab {i}"
```

### 3. Neue Methode: `_apply_projection()`

```python
def _apply_projection(self, controls_meta: list) -> list:
    """Wendet Projektion auf Controls an (Tab + Order)"""
    # Projektion aus app_db laden
    projection_json, _ = gcs._app_db.get_value(self.frame_guid, 'FRAME_PROJ')
    
    if projection_json:
        projection = json.loads(projection_json)
        
        # Tab + Order aus Projektion überschreiben
        for meta in controls_meta:
            field_key = meta['field_key']
            if field_key in projection:
                proj_data = projection[field_key]
                meta['tab'] = proj_data.get('tab', meta['tab'])
                meta['order'] = proj_data.get('order', meta['order'])
    
    # Nach Tab + Order sortieren
    controls_meta.sort(key=lambda x: (x['tab'], x['order']))
    return controls_meta
```

### 4. Erweiterte Methode: `_create_ui()`

```python
def _create_ui(self, header_text: str) -> QWidget:
    """Erstellt UI mit Header + Tabs/ScrollArea + Admin-Button"""
    
    # Einstellungen-Button (nur Admin-Modus)
    mode = gcs.field_value('mode')
    if mode == 'admin':
        settings_button = QPushButton("⚙️ Einstellungen")
        settings_button.clicked.connect(self._open_settings_dialog)
        header_layout.addWidget(settings_button)
    
    # Tabs oder Single ScrollArea
    if self.num_tabs > 1:
        self.tab_widget = QTabWidget()
        
        for tab_num in range(1, self.num_tabs + 1):
            tab_label = self.tab_config.get(tab_num, f"Tab {tab_num}")
            
            scroll = QScrollArea()
            tab_container = QWidget()
            tab_layout = QVBoxLayout(tab_container)
            
            scroll.setWidget(tab_container)
            self.tab_widget.addTab(scroll, tab_label)
        
        main_layout.addWidget(self.tab_widget)
    else:
        # Einzelne ScrollArea
        ...
```

### 5. Erweiterte Methode: `_render_all_controls()`

```python
def _render_all_controls(self):
    """RENDER-Kommando + Platzierung in Tabs"""
    
    if self.num_tabs > 1:
        # Controls nach Tab-Nummer verteilen
        for item in self.controls_matrix:
            control = item['control']
            tab_num = item.get('tab', 1)
            tab_index = tab_num - 1
            
            # Tab-Container holen
            scroll_widget = self.tab_widget.widget(tab_index)
            tab_container = scroll_widget.widget()
            
            # Control platzieren
            control.setParent(tab_container)
            control.render()
            tab_container.layout().addWidget(control)
        
        # Stretch in jedem Tab
        for tab_index in range(self.tab_widget.count()):
            ...
    else:
        # Alle Controls in controls_container
        ...
```

### 6. Erweiterte Methode: `_build_controls_matrix()`

```python
# In Matrix einfügen (mit field_key!)
self.controls_matrix.append({
    'control': control,
    'field_key': field_key,  # WICHTIG für Projektion!
    'order': meta.get('order', 0),
    'tab': meta.get('tab', 1),
    'instance_key': instance_key
})
```

### 7. Neue Methode: `_open_settings_dialog()` (Stub)

```python
def _open_settings_dialog(self):
    """Öffnet Einstellungen-Dialog (TODO: Vollständiger Dialog)"""
    
    # Projektion aus Matrix erstellen
    current_projection = {}
    for item in self.controls_matrix:
        field_key = item.get('field_key')
        current_projection[field_key] = {
            'tab': item.get('tab', 1),
            'order': item.get('order', 0)
        }
    
    # TODO: Dialog öffnen
    QMessageBox.information(None, "Einstellungen", "TODO: Dialog implementieren")
```

### 8. Neue Methode: `_save_projection()`

```python
def _save_projection(self, projection: dict):
    """Speichert Projektion in app_db"""
    import json
    projection_json = json.dumps(projection)
    
    gcs._app_db.set_value(self.frame_guid, 'FRAME_PROJ', projection_json)
    gcs._app_db.save_all_values()
```

---

## 📊 BEISPIEL-ABLAUF

### Szenario: 3 Tabs mit verschiedenen Controls

**Framedaten**:
```
ROOT.EDIT_TABS = 3
ROOT.EDIT_TAB_LABEL_01 = "Personendaten"
ROOT.EDIT_TAB_LABEL_02 = "Finanzdaten"
ROOT.EDIT_TAB_LABEL_03 = "Sonstiges"
```

**Metadaten** (Auszug):
```json
{
  "PERSONDATEN_PERSDATEN_ANREDE": {"tab": 1, "order": 1},
  "PERSONDATEN_PERSDATEN_FAMILIENNAME": {"tab": 1, "order": 2},
  "PERSONDATEN_PERSDATEN_VORNAME": {"tab": 1, "order": 3},
  "FINANZDATEN_FINANZDATEN_KONTOINHABER": {"tab": 2, "order": 1},
  "FINANZDATEN_FINANZDATEN_IBAN": {"tab": 2, "order": 2}
}
```

**Ergebnis**:
- Tab 1 "Personendaten": Anrede, Familienname, Vorname
- Tab 2 "Finanzdaten": Kontoinhaber, IBAN
- Tab 3 "Sonstiges": (leer)

### Admin ändert Reihenfolge

**Admin klickt "⚙️ Einstellungen"**:
1. Dialog öffnet mit aktueller Projektion
2. Admin verschiebt "IBAN" von Tab 2 → Tab 1, Order = 2
3. Dialog speichert neue Projektion in `app_db.{frame_guid}.FRAME_PROJ`
4. Widget wird neu aufgebaut → IBAN erscheint jetzt in Tab 1

**Persistierte Projektion**:
```json
{
  "PERSONDATEN_PERSDATEN_ANREDE": {"tab": 1, "order": 1},
  "FINANZDATEN_FINANZDATEN_IBAN": {"tab": 1, "order": 2},  // GEÄNDERT!
  "PERSONDATEN_PERSDATEN_FAMILIENNAME": {"tab": 1, "order": 3},
  ...
}
```

---

## ✅ VORTEILE

1. **Flexible Anordnung**: Controls können in mehrere Tabs gruppiert werden
2. **Benutzer-spezifisch**: Projektion wird pro `frame_guid` persistiert
3. **Admin-Kontrolle**: Nur Admin-Modus kann Einstellungen ändern
4. **Default-Fallback**: Metadaten liefern sinnvolle Standard-Anordnung
5. **Linear & einfach**: Sortierung nach (tab, order) - keine Verschachtelungen

---

## 🧪 NÄCHSTE SCHRITTE

### [ ] 1. Einstellungen-Dialog implementieren
**Datei**: `pdvm_input_controls_settings_dialog.py`

**Features**:
- Liste aller Controls mit aktuellem Tab + Order
- Drag & Drop zwischen Tabs
- Order-Anpassung (Pfeile ↑↓)
- Live-Vorschau
- Speichern/Abbrechen

### [ ] 2. UI-Rebuild nach Einstellungen
**Methode**: `_rebuild_ui()`

**Ablauf**:
1. Widget löschen
2. `get_widget()` erneut aufrufen
3. Neues Widget in Dialog einsetzen

### [ ] 3. Testen mit echten Daten
- Frame mit EDIT_TABS = 2 oder 3 erstellen
- Metadaten mit verschiedenen tab + order Werten
- Admin-Modus aktivieren → Einstellungen testen
- Persistierung prüfen (app_db.FRAME_PROJ)

### [ ] 4. Validierung
- Ungültige Tab-Nummern abfangen
- Order-Duplikate behandeln
- Fehlerbehandlung bei fehlenden Tabs

---

**STATUS**: ✅ **GRUNDFUNKTIONALITÄT IMPLEMENTIERT - BEREIT FÜR EINSTELLUNGEN-DIALOG!**
