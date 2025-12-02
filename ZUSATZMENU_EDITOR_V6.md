# Zusatzmenü-Editor V6 - GUID-Matching Architektur

## 🎯 PRINZIP

**Zusatzmenüs basieren auf automatischem GUID-Matching** - keine manuelle Verlinkung!

```
VERTIKAL/GRUND-Item           ZUSATZ Root-SUBMENU
┌────────────────────┐        ┌────────────────────┐
│ GUID: abc-123      │   ══►  │ GUID: abc-123      │
│ Label: "Finanzen"  │        │ Type: SUBMENU      │
│ Type: SUBMENU      │        │ parent_guid: null  │
└────────────────────┘        └────────────────────┘
                                       │
                                       ▼
                              ┌────────────────────┐
                              │ Child 1            │
                              │ parent_guid: abc-123│
                              └────────────────────┘
```

**System erkennt Verlinkung automatisch**: `Item-GUID == Root-SUBMENU-GUID`

---

## 📋 EDITOR-ABLAUF

### 1. **Zusatzmenü-Button klicken**

User wählt Item aus (BUTTON oder SUBMENU) und klickt **"📎 Zusatzmenü bearbeiten"**

### 2. **Root-SUBMENU prüfen/erstellen**

Editor prüft: `db.get_static_value("ZUSATZ", item_guid)`

**Falls nicht vorhanden:**
```python
zusatz_root = {
    'type': 'SUBMENU',
    'label': f'Zusatzmenü: {item_label}',
    'parent_guid': None,  # MUSS null sein!
    'sort_order': 0,
    # ... weitere Felder
}
db.set_value("ZUSATZ", item_guid, zusatz_root, stichtag)
```

**KRITISCH**: GUID des Root-SUBMENU = GUID des Items!

### 3. **Children anzeigen**

Editor lädt alle Items mit `parent_guid == item_guid` aus ZUSATZ-Gruppe

```python
zusatz_list.set_root_filter(item_guid)
zusatz_list.load_items()
```

### 4. **Bearbeiten**

User kann:
- Neue Items hinzufügen (parent_guid = item_guid)
- Bestehende Items bearbeiten
- Items löschen
- Items per Drag & Drop sortieren

### 5. **Speichern**

```python
db.save_all_values()
```

**System erkennt automatisch:**
- Root-SUBMENU in ZUSATZ mit GUID = Item-GUID
- `prepare_menu_with_zusatz()` findet Match
- Verlinkung aktiv ohne manuelle Einträge!

---

## 🔧 IMPLEMENTATION

### **MenuItemEditor._open_zusatzmenu_editor()**

```python
def _open_zusatzmenu_editor(self):
    # 1. Item laden
    item_guid = self.current_guid
    item_data = self.db.get_static_value(self.current_gruppe, item_guid)
    
    # 2. Root-SUBMENU prüfen/erstellen
    zusatz_root = self.db.get_static_value("ZUSATZ", item_guid)
    if not zusatz_root:
        zusatz_root = {
            'type': 'SUBMENU',
            'label': f'Zusatzmenü: {item_data["label"]}',
            'parent_guid': None,  # ROOT!
            'sort_order': 0
        }
        self.db.set_value("ZUSATZ", item_guid, zusatz_root, stichtag)
    
    # 3. Editor-Dialog öffnen
    dialog = QDialog(self)
    
    # Liste nur für Children dieses Root-SUBMENU
    zusatz_list = MenuListWidget("ZUSATZ")
    zusatz_list.set_root_filter(item_guid)
    
    # Item-Editor für Zusatzmenü
    zusatz_editor = MenuItemEditor()
    zusatz_editor.set_zusatzmenu_root(item_guid)
    zusatz_editor.btn_edit_zusatzmenu.hide()  # Keine Rekursion!
    
    # ... Dialog aufbauen und anzeigen
```

### **Wichtige Methoden**

#### `MenuListWidget.set_root_filter(root_guid)`
Filtert Liste auf Children eines bestimmten Root-SUBMENU

```python
def load_items(self):
    items = self.db.get_gruppe(self.gruppe)
    
    if self.root_filter_guid:
        # Nur Children des Root-SUBMENU
        filtered_items = {
            guid: data for guid, data in items.items()
            if guid != self.root_filter_guid  # Root selbst ausblenden
            and data.get('parent_guid') == self.root_filter_guid
            or self._is_descendant_of_root(guid, items)
        }
        items = filtered_items
```

#### `MenuItemEditor.set_zusatzmenu_root(root_guid)`
Setzt parent_guid für neue Items im Zusatzmenü

```python
def _on_add_item(self):
    new_item = {
        'type': 'BUTTON',
        'label': 'Neuer Menüpunkt',
        'parent_guid': self.root_filter_guid,  # Nicht None!
        'sort_order': top_level_count
    }
    db.set_value("ZUSATZ", new_guid, new_item, stichtag)
```

---

## ✅ VALIDIERUNG

### **Beim Laden prüfen:**

```python
zusatz_root = self.db.get_static_value("ZUSATZ", item_guid)
if zusatz_root:
    # Sicherstellen dass Struktur korrekt ist
    if zusatz_root.get('type') != 'SUBMENU':
        zusatz_root['type'] = 'SUBMENU'
    if zusatz_root.get('parent_guid') is not None:
        zusatz_root['parent_guid'] = None
    self.db.set_value("ZUSATZ", item_guid, zusatz_root, stichtag)
```

### **Beim Speichern prüfen:**

```python
# Leere Labels korrigieren
items = self.db.get_gruppe("ZUSATZ")
for guid, item in items.items():
    if item and not item.get('label', '').strip():
        item['label'] = 'Unbekannt'
        self.db.set_value("ZUSATZ", guid, item, stichtag)
```

---

## 🗑️ LÖSCHEN

### **Komplett-Löschung** (Root + alle Children)

```python
def delete_zusatzmenu():
    items = self.db.get_gruppe("ZUSATZ")
    to_delete = [item_guid]  # Root
    
    # Rekursiv alle Descendants finden
    def find_descendants(parent_guid):
        for guid, item in items.items():
            if item and item.get('parent_guid') == parent_guid:
                to_delete.append(guid)
                find_descendants(guid)
    
    find_descendants(item_guid)
    
    # Alle löschen
    for guid in to_delete:
        self.db.delete_field("ZUSATZ", guid)
    
    self.db.save_all_values()
```

---

## 🎨 UI-FEATURES

### **Info-Header**

```
┌──────────────────────────────────────────────────┐
│ Zusatzmenü-Editor V6 (GUID-Matching)            │
├──────────────────────────────────────────────────┤
│ Menü-Item: Finanzen (SUBMENU)                   │
│ Item-GUID: 17ac6504-a80d-4087-a8c2-2cb6235eb3c3 │
├──────────────────────────────────────────────────┤
│ ℹ️ Funktionsweise:                              │
│ • Zusatzmenü als Root-SUBMENU mit GLEICHER GUID │
│ • System erkennt Verlinkung automatisch         │
│ • Zusatzmenü erscheint horizontal neben GRUND   │
│ • KEINE manuelle Verlinkung nötig!              │
└──────────────────────────────────────────────────┘
```

### **Buttons**

- **🗑️ Zusatzmenü löschen**: Löscht Root-SUBMENU + alle Children
- **💾 Speichern**: Speichert alle Änderungen (Verlinkung erfolgt automatisch!)
- **Schließen**: Schließt Dialog ohne Speichern

### **Liste**

- Zeigt nur Children des Root-SUBMENU (Root selbst ausgeblendet)
- Drag & Drop zum Sortieren
- Orange Markierung für ungespeicherte Änderungen
- ➕ Neu / 🗑️ Löschen Buttons

---

## 🔄 INTEGRATION mit Rendering

### **GCS.prepare_menu_with_zusatz()**

Scannt ZUSATZ-Gruppe nach Root-SUBMENUs und matched mit Items:

```python
def prepare_menu_with_zusatz(self):
    # ZUSATZ-Root-SUBMENUs finden
    zusatz_data = self._menu_system_db.get_gruppe('ZUSATZ')
    root_submenus = []
    
    for guid, item in zusatz_data.items():
        if item.get('type') == 'SUBMENU' and item.get('parent_guid') is None:
            root_submenus.append((guid, item))
    
    # In VERTIKAL und GRUND nach Matches suchen
    for root_guid, root_item in root_submenus:
        for gruppe in ['VERTIKAL', 'GRUND']:
            gruppe_data = self._menu_system_db.get_gruppe(gruppe)
            if root_guid in gruppe_data:
                # Match gefunden!
                item = gruppe_data[root_guid]
                item['zusatz_guid'] = root_guid
                self._menu_system_db.set_value(gruppe, root_guid, item)
                
                # Zu Children propagieren
                self._propagate_zusatz_to_children(gruppe, root_guid, root_guid)
```

### **Rendering**

Bei Klick auf Item mit zusatz_guid:

```python
def make_handler(item_guid, cmd, zusatz):
    def on_click():
        # 1. GRUND neu rendern mit Zusatz
        grund_container = gcs.get_container('grund')
        if zusatz:
            render_grund_with_zusatz(grund_container, gcs, item_guid, menu_handler)
        else:
            render_menu('GRUND', grund_container, gcs, menu_handler)
        
        # 2. Command ausführen
        if cmd:
            menu_handler.execute_command(cmd)
    
    return on_click
```

---

## ✅ VORTEILE V6

| Aspekt | Alt | V6 (GUID-Matching) |
|--------|-----|-------------------|
| **Verlinkung** | Manuell zusatz_guid eintragen | Automatisch via GUID |
| **Wartung** | Zusatz_guid synchronisieren | Keine Synchronisation nötig |
| **Fehleranfälligkeit** | Hoch (falsche GUIDs) | Niedrig (System managed) |
| **Editor-Komplexität** | Zusatz_guid-Feld pflegen | Nur Root-SUBMENU erstellen |
| **Vererbung** | Manuell propagieren | Automatisch via GCS |

---

## 📝 BEISPIEL

### **1. Item erstellen**

```
VERTIKAL
├─ 🔘 Stammdaten (BUTTON)
│  GUID: abc-123
└─ ...
```

### **2. Zusatzmenü bearbeiten**

Editor erstellt automatisch:

```
ZUSATZ
├─ 📁 Zusatzmenü: Stammdaten (SUBMENU, GUID: abc-123)
│  parent_guid: null
│  └─ 🔘 Export (BUTTON)
│     parent_guid: abc-123
│  └─ 🔘 Import (BUTTON)
│     parent_guid: abc-123
```

### **3. System erkennt Match**

```python
prepare_menu_with_zusatz()
# Findet: VERTIKAL["abc-123"] und ZUSATZ["abc-123"]
# Setzt: VERTIKAL["abc-123"]["zusatz_guid"] = "abc-123"
```

### **4. Rendering**

Klick auf "Stammdaten" → GRUND + ZUSATZ horizontal:

```
┌──────────────┬──────────┬────────┬────────┬─────────┬────────┐
│ Apps         │ Berichte │ System │ Admin  │ Export  │ Import │
└──────────────┴──────────┴────────┴────────┴─────────┴────────┘
          GRUND (4 Items)              ZUSATZ (2 Items)
```

---

## 🎓 ZUSAMMENFASSUNG

✅ **Einfach**: Root-SUBMENU mit gleicher GUID wie Item
✅ **Automatisch**: System erkennt Verlinkung via GUID-Matching
✅ **Wartbar**: Keine manuelle zusatz_guid-Pflege
✅ **Sicher**: Validierung beim Laden/Speichern
✅ **Flexibel**: Beliebige Hierarchie in Zusatzmenü möglich

**Editor macht V6-Architektur transparent für User** - System managed alles automatisch!
