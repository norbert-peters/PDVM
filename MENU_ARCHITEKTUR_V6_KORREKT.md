# PDVM Menu-Architektur V6 - KORREKT IMPLEMENTIERT

## 🎯 GRUNDPRINZIP

**VERTIKAL und GRUND sind IDENTISCHE Menü-Systeme** mit nur EINEM Unterschied:

| Aspekt | VERTIKAL | GRUND |
|--------|----------|-------|
| **Root-Items** | Vertikal dargestellt | Horizontal dargestellt |
| **Children** | In Popup (QMenu) | In Popup (QMenu) |
| **Rekursion** | Beliebige Tiefe (~50 Ebenen Loop-Sperre) | Beliebige Tiefe (~50 Ebenen Loop-Sperre) |
| **Zusatzmenü** | ✅ Jedes Element kann zusatz_guid haben | ✅ Jedes Element kann zusatz_guid haben |

---

## 📋 STRUKTUR

### **Menu-Gruppen in GCS**

```json
{
  "META": {
    "VERSION": "V3",
    "MIGRATED_FROM": "V2"
  },
  
  "VERTIKAL": {
    "item-guid-1": {
      "type": "SUBMENU",
      "label": "Finanzen",
      "parent_guid": null,           // Root-Item
      "zusatz_guid": "zusatz-123",   // Optional: Zusatzmenü
      "sort_order": 0
    },
    "item-guid-2": {
      "type": "BUTTON",
      "label": "Budget",
      "parent_guid": "item-guid-1",  // Child von "Finanzen"
      "command": {...},
      "sort_order": 0
    }
  },
  
  "GRUND": {
    // Identische Struktur wie VERTIKAL
    "item-guid-3": {
      "type": "SUBMENU",
      "label": "Apps",
      "parent_guid": null,
      "sort_order": 0
    }
  },
  
  "ZUSATZ": {
    "zusatz-123": {
      "type": "SUBMENU",               // MUSS Root-SUBMENU sein!
      "label": "Finanzen-Tools",
      "parent_guid": null,             // MUSS null sein!
      "sort_order": 0
    },
    "zusatz-child-1": {
      "type": "BUTTON",
      "label": "Steuerrechner",
      "parent_guid": "zusatz-123",     // Child vom Root-SUBMENU
      "command": {...},
      "sort_order": 0
    }
  }
}
```

---

## 🔧 RENDERING-PIPELINE V6

### **Datei: `pdvm_menu_rendering_pipeline_v6.py`**

```python
# EINFACHES MENÜ RENDERN (VERTIKAL oder GRUND)
render_menu('VERTIKAL', container, gcs, menu_handler)
# → Root-Items vertikal, Children in Popup, rekursiv

render_menu('GRUND', container, gcs, menu_handler)
# → Root-Items horizontal, Children in Popup, rekursiv

# GRUND MIT ZUSATZ RENDERN (bei Klick auf Item mit zusatz_guid)
render_grund_with_zusatz(container, gcs, clicked_item_guid, menu_handler)
# → GRUND + ZUSATZ kombiniert horizontal
```

### **Kern-Funktionen**

#### 1. `render_menu(gruppe, container, gcs, menu_handler)`
**Rendert VERTIKAL oder GRUND identisch**

```python
def render_menu(gruppe, container, gcs, menu_handler=None):
    # 1. Daten aus GCS laden
    matrix = load_from_gcs(gruppe)
    
    # 2. Richtung bestimmen
    direction = 'vertical' if gruppe == 'VERTIKAL' else 'horizontal'
    
    # 3. Rekursiv rendern
    _render_menu_recursive(matrix, container, direction, ...)
```

**Ablauf:**
- Root-Items nach `direction` rendern (vertikal/horizontal)
- Für SUBMENU: Children in Popup (QMenu)
- Popup-Items rekursiv rendern (Sub-Submenus möglich)
- Loop-Sperre bei 50 Ebenen

---

#### 2. `render_grund_with_zusatz(container, gcs, clicked_item_guid, menu_handler)`
**GRUND + ZUSATZ kombiniert horizontal**

```python
def render_grund_with_zusatz(container, gcs, clicked_item_guid, menu_handler=None):
    # 1. GRUND aus GCS laden
    grund_matrix = load_from_gcs('GRUND')
    
    # 2. zusatz_guid vom geklickten Item holen
    # WICHTIG: Item kann aus VERTIKAL oder GRUND kommen!
    zusatz_guid = _get_zusatz_guid_from_item(gcs, clicked_item_guid)
    
    # 3. ZUSATZ laden (falls zusatz_guid vorhanden)
    zusatz_matrix = []
    if zusatz_guid:
        zusatz_matrix = gcs.load_zusatzmenu_data(zusatz_guid)
    
    # 4. Kombinieren
    combined = grund_matrix + zusatz_matrix
    
    # 5. Horizontal rendern
    _render_menu_recursive(combined, container, 'horizontal', ...)
```

---

#### 3. `_get_zusatz_guid_from_item(gcs, item_guid)`
**Holt zusatz_guid aus VERTIKAL ODER GRUND**

```python
def _get_zusatz_guid_from_item(gcs, item_guid):
    # 1. In VERTIKAL suchen
    vertikal = gcs._menu_system_db.get_gruppe('VERTIKAL')
    if item_guid in vertikal:
        return vertikal[item_guid].get('zusatz_guid')
    
    # 2. In GRUND suchen
    grund = gcs._menu_system_db.get_gruppe('GRUND')
    if item_guid in grund:
        return grund[item_guid].get('zusatz_guid')
    
    return None
```

**KRITISCH:** Item kann in **beiden** Gruppen sein!

---

#### 4. `_render_item(item, matrix, layout, ...)`
**Rendert einzelnes Item rekursiv**

```python
def _render_item(item, matrix, parent_layout, menu_handler, gcs, depth=0):
    # Loop-Sperre
    if depth >= 50:
        return
    
    # SEPARATOR
    if item['type'] == 'SEPARATOR':
        return
    
    # SUBMENU
    if item['type'] == 'SUBMENU':
        # Button mit Popup erstellen
        button = QPushButton(f"{label} ▼")
        popup = QMenu(button)
        
        # Children in Popup rendern (rekursiv!)
        children = find_children(matrix, item['guid'])
        for child in children:
            _add_popup_item(child, matrix, popup, ..., depth+1)
        
        button.setMenu(popup)
        parent_layout.addWidget(button)
    
    # BUTTON
    if item['type'] == 'BUTTON':
        button = QPushButton(label)
        
        # Click-Handler
        def on_click():
            # 1. Command ausführen (falls vorhanden)
            if command:
                menu_handler.execute_command(command)
            
            # 2. Zusatzmenü aktivieren (falls vorhanden)
            if zusatz_guid:
                grund_container = gcs.get_container('grund')
                render_grund_with_zusatz(grund_container, gcs, item_guid, menu_handler)
        
        button.clicked.connect(on_click)
        parent_layout.addWidget(button)
```

---

#### 5. `_add_popup_item(item, matrix, popup_menu, ...)`
**Fügt Item zu Popup hinzu (rekursiv für Sub-Submenus)**

```python
def _add_popup_item(item, matrix, popup_menu, menu_handler, gcs, depth):
    # Loop-Sperre
    if depth >= 50:
        return
    
    # SEPARATOR
    if item['type'] == 'SEPARATOR':
        popup_menu.addSeparator()
    
    # SUBMENU → Sub-Submenu
    if item['type'] == 'SUBMENU':
        sub_menu = popup_menu.addMenu(f"{label} ▶")
        children = find_children(matrix, item['guid'])
        for child in children:
            _add_popup_item(child, matrix, sub_menu, ..., depth+1)  # REKURSIV!
    
    # BUTTON → Action
    if item['type'] == 'BUTTON':
        action = popup_menu.addAction(label)
        
        def on_trigger():
            if command:
                menu_handler.execute_command(command)
            if zusatz_guid:
                render_grund_with_zusatz(...)
        
        action.triggered.connect(on_trigger)
```

---

## 🎬 ABLAUF

### **System-Start**

```python
# 1. Container in GCS registrieren
gcs.register_menu_containers(
    vertical=vertical_widget,
    grund=grund_widget
)

# 2. Menü laden
PdvmMenuSystemAutonomous.load_startmenu(startmenu_guid)
```

**Intern:**
```python
# Templates expandieren
gcs.expand_templates_in_gruppe('VERTIKAL')
gcs.expand_templates_in_gruppe('GRUND')
gcs.expand_templates_in_gruppe('ZUSATZ')

# Zusatzmenü-GUIDs vorbereiten
gcs.prepare_menu_with_zusatz()

# Menüs rendern
render_menu('VERTIKAL', vertical_container, gcs, menu_handler)
render_menu('GRUND', grund_container, gcs, menu_handler)
```

---

### **User klickt auf Item MIT zusatz_guid**

```
1. User klickt Button "Finanzen" (aus VERTIKAL)
   ↓
2. Click-Handler prüft: zusatz_guid vorhanden?
   ↓
3. JA → render_grund_with_zusatz(container, gcs, "finanzen-guid", handler)
   ↓
4. Funktion holt:
   - GRUND-Items aus GCS
   - zusatz_guid von "Finanzen" → "zusatz-123"
   - ZUSATZ-Children von "zusatz-123"
   ↓
5. Kombiniert: GRUND + ZUSATZ
   ↓
6. Rendert horizontal: [Apps][Testbereich][System][Admin] + [Steuerrechner][Budget]
```

---

### **User klickt auf Item OHNE zusatz_guid**

```
1. User klickt Button "Apps" (aus GRUND)
   ↓
2. Click-Handler prüft:
   - Command? → JA → execute_command()
   - zusatz_guid? → NEIN → nichts
   ↓
3. GRUND bleibt unverändert
```

---

## ✅ VORTEILE

1. **EINFACH**: Beide Menüs nutzen identische Logik
2. **FLEXIBEL**: Beliebige Verschachtelungs-Tiefe
3. **KONSISTENT**: Jedes Element kann Zusatzmenü haben
4. **ROBUST**: Loop-Sperre verhindert Endlos-Rekursion
5. **SAUBER**: Klare Trennung VERTIKAL/GRUND/ZUSATZ

---

## 🔍 WICHTIGE DATEIEN

- `pdvm_menu_rendering_pipeline_v6.py` - **Neue Pipeline (KORREKT)**
- `pdvm_menu_system_autonomous.py` - Nutzt V6-Pipeline
- `pdvm_central_systemsteuerung.py` - GCS mit Container-Verwaltung

---

## 🎯 ZUSAMMENFASSUNG

**ALT (FALSCH):**
- zusatz_guid nur aus VERTIKAL geholt
- GRUND und VERTIKAL unterschiedliche Logik
- Kompliziert und fehleranfällig

**NEU (RICHTIG):**
- zusatz_guid aus **VERTIKAL ODER GRUND** geholt
- Beide Menüs **IDENTISCHE Logik** (nur Richtung unterschiedlich)
- Einfach und robust

**ZUSATZMENÜ wird angezeigt wenn:**
1. User klickt Item (aus VERTIKAL oder GRUND)
2. Item hat `zusatz_guid`
3. In ZUSATZ-Gruppe existiert Root-SUBMENU mit dieser GUID
4. → GRUND wird neu gerendert: `GRUND + ZUSATZ`
