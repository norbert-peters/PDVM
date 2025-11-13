# 🎯 PDVM Menu-Editor - OPTIMIERTE VERSION

**Datum:** 12.11.2025  
**Status:** ✅ IMPLEMENTIERT  
**Datei:** `pdvm_menu_editor_optimized.py`

---

## 📋 Konzeption (User-Feedback)

### 1. **Vertikale Button-Darstellung** ✅
- Linke Seite: 2 Tabs (VERTIKAL, GRUND)
- Jeder Tab zeigt Menü als vertikale Button-Liste
- Hierarchie durch Einrückung visualisiert
- Icons je nach Type (🔘 BUTTON, 📁 SUBMENU, ─ SEPARATOR, ⏸ SPACER)

### 2. **SUBMENU-Ebenen-Logik** ✅ OPTIMIERT
```python
REGEL:
- root = Ebene -1 (parent_guid = None)
- Nur SUBMENU-Items können Parent sein
- Andere Types (BUTTON, SEPARATOR, SPACER) NIEMALS Parent!

BEISPIEL:
📁 Datei (SUBMENU)              ← Kann Parent sein
    🔘 Öffnen (BUTTON)          ← Kann KEIN Parent sein
    🔘 Speichern (BUTTON)       ← Kann KEIN Parent sein
    📁 Export (SUBMENU)         ← Kann Parent sein
        🔘 PDF (BUTTON)         ← Kann KEIN Parent sein
        🔘 Word (BUTTON)        ← Kann KEIN Parent sein
```

**Parent-Level-Mapping:**
```python
def get_parent_level_mapping(items: Dict[str, Any]) -> Dict[str, int]:
    """
    Erstellt Mapping: parent_guid → Ebene
    
    Logik:
    - None (root) → Ebene 0
    - SUBMENU-Items → Ebene +1
    - Andere Items → Ebene des Parents
    """
    mapping = {None: 0}  # root
    
    for guid, data in items.items():
        parent_guid = data.get('parent_guid')
        
        if parent_guid in mapping:
            parent_level = mapping[parent_guid]
            
            # Nur SUBMENU kann neue Ebene bilden
            if data.get('type') == 'SUBMENU':
                mapping[guid] = parent_level + 1
    
    return mapping
```

### 3. **Drag & Drop - LINEARE LOGIK** ✅
```python
def _on_items_reordered():
    """
    Verschobenes Item hängt sich an vorliegendes SUBMENU
    
    LOGIK:
    1. Item wird verschoben (beliebige Position)
    2. Rückwärts suchen nach vorliegendem SUBMENU
    3. Gefunden? → Neuer Parent = SUBMENU-GUID
    4. Nicht gefunden? → Parent = None (root)
    5. Alte + Neue Ebene NEU SORTIEREN
    """
    
    # Vorliegendes SUBMENU finden
    for check_row in range(moved_row - 1, -1, -1):
        check_data = items.get(check_guid)
        
        if check_data.get('type') == 'SUBMENU':
            new_parent = check_guid  # Gefunden!
            break
    
    # Parent geändert?
    if old_parent != new_parent:
        moved_data['parent_guid'] = new_parent
        
        # BEIDE Ebenen neu sortieren
        resort_parent_children(items, old_parent, stichtag, db)   # Alt
        resort_parent_children(items, new_parent, stichtag, db)   # Neu
```

**BEISPIEL:**
```
Vorher:
📁 Datei (SUBMENU)
    🔘 Öffnen
    🔘 Speichern
🔘 Beenden  ← Ziehe hierhin

Nachher:
📁 Datei (SUBMENU)
    🔘 Öffnen
    🔘 Speichern
    🔘 Beenden  ← Automatisch unter "Datei" (vorliegendes SUBMENU)!
```

### 4. **Neusortierung bei Ebenen-Wechsel** ✅
```python
def resort_parent_children(items, parent_guid, stichtag, db):
    """
    Sortiert alle Kinder eines Parents neu
    
    ABLAUF:
    1. Alle Kinder finden (parent_guid == parent)
    2. Nach sort_order sortieren
    3. Neu nummerieren: 0, 1, 2, 3, ...
    4. In DB schreiben
    """
    children = [
        (guid, data) for guid, data in items.items() 
        if data.get('parent_guid') == parent_guid
    ]
    
    children.sort(key=lambda x: x[1].get('sort_order', 0))
    
    for index, (guid, data) in enumerate(children):
        data['sort_order'] = index
        db.set_value(gruppe, guid, data, stichtag)
```

**WANN wird neu sortiert?**
- ✅ Drag & Drop (alte + neue Ebene)
- ✅ Einrücken (alte + neue Ebene)
- ✅ Ausrücken (alte + neue Ebene)
- ✅ Löschen (Parent-Ebene)
- ❌ **NICHT** vor save_all() (redundant!)

### 5. **GCS-Nutzung - MINIMAL** ✅
```python
class PdvmMenuEditorOptimized(QWidget):
    def __init__(self, menu_guid: str, parent=None):
        # GCS NUR für:
        # 1. Stichtag
        # 2. AB-Datum Formatierung
        from pdvm_central_systemsteuerung import get_gcs
        self.gcs = get_gcs()
        
        # AUTONOME DB-Instanz (KEINE GCS-DB!)
        self.db = PdvmCentralDatenbank('sys_menudaten', menu_guid)
        self.db._load_data()
```

**KEIN Template-System:**
- Editor arbeitet direkt mit Menu-GUID
- Keine `!guid!` Ersetzung nötig
- View-Input-Controls bereits in Template-Daten gespeichert

**GCS nur für:**
1. ✅ `gcs.st_inst.PdvmDateTime` - Stichtag für set_value()
2. ✅ `gcs.temp_dt_inst` - AB-Datum Formatierung (falls nötig)
3. ❌ **NICHT** für Template-System
4. ❌ **NICHT** für Menu-Rendering (eigene Darstellung!)

### 6. **Item-Bearbeitung ohne Handler-Aufruf** ✅
```python
def _on_item_selected(self, gruppe: str, item_guid: str):
    """
    Item ausgewählt → NUR Editor laden
    
    KEIN Handler-Aufruf!
    (Editor ist autonomes System für Menü-Bearbeitung)
    """
    self.editor.load_item(gruppe, item_guid)
```

---

## 🏗️ Architektur

### Komponenten-Hierarchie
```
PdvmMenuEditorOptimized (Haupt-Widget)
├── QSplitter
│   ├── LINKS: Tabs + Listen
│   │   ├── QTabWidget
│   │   │   ├── Tab 1: MenuListWidget (VERTIKAL)
│   │   │   └── Tab 2: MenuListWidget (GRUND)
│   │   └── QPushButton (💾 ALLES SPEICHERN)
│   └── RECHTS: MenuItemEditor
│       ├── Type ComboBox
│       ├── Label LineEdit
│       ├── Handler LineEdit (nur bei BUTTON)
│       ├── Params TextEdit (nur bei BUTTON)
│       └── QPushButton (✅ Übernehmen)
```

### Datenfluss
```
START
  ↓
PdvmCentralDatenbank('sys_menudaten', menu_guid)
  ↓
MenuListWidget.load_items()
  ├→ get_parent_level_mapping()  # Parent → Ebene
  ├→ _build_hierarchy()          # Hierarchisch sortieren
  └→ _add_list_item()            # In Liste einfügen
  ↓
USER: Klick auf Item
  ↓
MenuItemEditor.load_item()
  ├→ get_static_value()          # Item aus DB
  └→ UI befüllen
  ↓
USER: Änderungen + "Übernehmen"
  ↓
MenuItemEditor._apply_changes()
  ├→ set_value(gruppe, guid, data, stichtag)
  ├→ item_changed Signal → Orange Rahmen
  └→ NICHT persistent!
  ↓
USER: "ALLES SPEICHERN"
  ↓
PdvmMenuEditorOptimized._save_all()
  ├→ Validierung (leere Labels)
  ├→ save_all_values()           # PERSISTENT!
  ├→ clear_modified()            # Orange weg
  └→ _load_all_data()            # Neu laden
```

---

## 🔧 Wichtige Funktionen

### 1. **Parent-Level-Mapping**
```python
parent_levels = get_parent_level_mapping(items)
# Ergebnis:
# {
#     None: 0,                          # root
#     'datei-submenu-guid': 1,          # Ebene 1
#     'export-submenu-guid': 2,         # Ebene 2
# }
```

### 2. **Hierarchie aufbauen**
```python
sorted_items = self._build_hierarchy(items, parent_levels)
# Ergebnis: [(guid, data, level), ...]
```

### 3. **Neusortierung**
```python
resort_parent_children(items, parent_guid, stichtag, db)
# Effekt: sort_order = 0, 1, 2, 3, ...
```

### 4. **Drag & Drop Parent-Zuordnung**
```python
# Rückwärts suchen nach SUBMENU
for check_row in range(moved_row - 1, -1, -1):
    if check_data.get('type') == 'SUBMENU':
        new_parent = check_guid
        break
```

### 5. **Type-Wechsel-Sicherheit**
```python
# Wenn von SUBMENU zu anderem Type:
if old_type == 'SUBMENU' and new_type != 'SUBMENU':
    self._move_children_to_parent(item_data)
    # Alle Kinder zum Großeltern verschieben!
```

---

## ⚡ Optimierungen vs. alte Version

| Feature | Alte Version | Optimierte Version |
|---------|-------------|-------------------|
| **Ebenen-Logik** | Alle Types können Parent sein | ✅ Nur SUBMENU kann Parent sein |
| **Drag & Drop** | Komplexe Level-Berechnung | ✅ Einfach: Vorliegendes SUBMENU suchen |
| **Sortierung** | Redundant vor save_all() | ✅ Nur bei Ebenen-Wechsel |
| **GCS-Nutzung** | Template-System + GCS-DB | ✅ Nur Stichtag + AB-Datum |
| **Parent-Mapping** | Keine Mapping-Funktion | ✅ get_parent_level_mapping() |
| **Type-Wechsel** | Keine Sicherheit | ✅ Kinder automatisch verschieben |
| **Reload nach Save** | Fehlte | ✅ _load_all_data() |

---

## 🚀 Verwendung

### Dialog öffnen
```python
from pdvm_menu_editor_optimized import create_menu_editor_dialog

dialog = create_menu_editor_dialog(menu_guid='xyz-123', parent=self)
dialog.exec_()
```

### Widget einbetten
```python
from pdvm_menu_editor_optimized import create_menu_editor_widget

editor = create_menu_editor_widget(menu_guid='xyz-123', parent=self)
layout.addWidget(editor)
```

### Handler registrieren
```python
# In handlers/handler_open_menu_editor.py
def handle_open_menu_editor(params: dict):
    from pdvm_menu_editor_optimized import create_menu_editor_dialog
    
    menu_guid = params.get('menu_guid')
    dialog = create_menu_editor_dialog(menu_guid)
    dialog.exec_()
```

---

## 📝 Datenbank-Struktur

### sys_menudaten (PdvmCentralDatenbank)
```python
{
    'MENU_GUID': 'xyz-123',
    'MENU_NAME': 'Hauptmenü',
    'VERTIKAL': {
        'item-1-guid': {
            'guid': 'item-1-guid',
            'type': 'SUBMENU',
            'label': 'Datei',
            'parent_guid': None,        # root
            'sort_order': 0,
            'visible': True,
            'enabled': True,
            'command': None,
            'icon': None,
            'tooltip': None
        },
        'item-2-guid': {
            'guid': 'item-2-guid',
            'type': 'BUTTON',
            'label': 'Öffnen',
            'parent_guid': 'item-1-guid',  # Unter "Datei"
            'sort_order': 0,
            'command': {
                'handler': 'open_view',
                'params': {'view_guid': 'abc-456'}
            }
        }
    },
    'GRUND': { ... },
    'ZUSATZ': { ... },
    'COMMANDS': [ ... ]
}
```

---

## ✅ Tests

### 1. **SUBMENU-Logik testen**
```python
# 1. BUTTON unter SUBMENU einhängen → ✅
# 2. BUTTON unter BUTTON einhängen → ❌ Verhindert!
# 3. SUBMENU zu BUTTON ändern → ✅ Kinder automatisch verschoben
```

### 2. **Drag & Drop testen**
```python
# 1. Item zwischen zwei Geschwister ziehen → ✅ sort_order angepasst
# 2. Item von Ebene 2 → Ebene 0 ziehen → ✅ Parent = vorliegendes SUBMENU
# 3. Item unter zugeklapptes SUBMENU → ✅ Wie erstes Kind
```

### 3. **Neusortierung testen**
```python
# 1. Item löschen → ✅ Geschwister neu sortiert
# 2. Item einrücken → ✅ Alte + Neue Ebene sortiert
# 3. Item ausrücken → ✅ Alte + Neue Ebene sortiert
```

### 4. **Persistierung testen**
```python
# 1. Änderungen → Orange Rahmen → ✅
# 2. Speichern → Orange weg → ✅
# 3. Neu laden → Daten korrekt → ✅
```

---

## 🎯 Zusammenfassung

### ✅ Alle Anforderungen erfüllt
1. ✅ Vertikale Button-Darstellung mit 2 Tabs
2. ✅ Nur SUBMENU kann Parent sein (linear & einfach)
3. ✅ Drag & Drop mit automatischer Parent-Zuordnung
4. ✅ Neusortierung bei Ebenen-Wechsel (nicht redundant!)
5. ✅ Minimale GCS-Nutzung (nur Stichtag + AB-Datum)
6. ✅ Item-Bearbeitung ohne Handler-Aufruf
7. ✅ Orange Rahmen für Änderungen
8. ✅ save_all_values() für alles auf einmal
9. ✅ Reload nach Speichern
10. ✅ Type-Wechsel-Sicherheit (SUBMENU → andere)

### 🚀 Vorteile
- **Linear:** Keine komplexe If-Then-Logik
- **Robust:** Type-Wechsel-Sicherheit, Validierung
- **Performant:** Minimale GCS-Nutzung, autonome DB
- **Benutzerfreundlich:** Orange Rahmen, Live-Vorschau, Undo-Sicherheit

---

**Status:** ✅ BEREIT FÜR PRODUKTION  
**Autor:** PDVM V2.0  
**Datum:** 12.11.2025
