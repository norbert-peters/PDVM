# 🎨 Menu-Editor Design & Architektur

## 📋 Übersicht

**Ziel**: GUI-basierter Editor für PDVM-Menüs mit Template-System und Live-Vorschau

**Kern-Features**:
- 2 Tabs: Vertikalmenü & Grundmenü bearbeiten
- Jeder Menüpunkt = InputControl mit Template
- Live-Vorschau mit Drag & Drop
- GUID-basierte Menüauswahl über View

---

## 🏗️ Architektur

### 1. Ablauf (Linear)

```
START: Handler "open_menu_editor"
  ↓
STEP 1: View-Dialog öffnen
  └─→ Benutzer wählt Menü-GUID aus Tabelle
  └─→ Tabelle aus frame_data (sys_menu_liste)
  ↓
STEP 2: Menu-Editor-Dialog öffnen
  └─→ Lädt Menü-Daten aus man_db.sys_menudaten
  └─→ Zeigt 2 Tabs: VERTIKAL + GRUND
  ↓
STEP 3: Bearbeitung
  └─→ Tab 1: Vertikalmenü-Items bearbeiten
  └─→ Tab 2: Grundmenü-Items bearbeiten
  └─→ Live-Vorschau rechts/unten
  ↓
STEP 4: Speichern
  └─→ Validierung aller Items
  └─→ Zurück zu man_db.sys_menudaten
  └─→ Erfolgsbestätigung
END
```

### 2. Komponenten-Struktur

```
PdvmMenuEditorDialog (Hauptdialog)
├── QTabWidget (Links: Bearbeitung)
│   ├── Tab "Vertikalmenü"
│   │   └── PdvmMenuItemsEditor
│   │       ├── QListWidget (Item-Liste mit Drag&Drop)
│   │       └── PdvmMenuItemEditor (Einzeln-Editor)
│   │           └── Template-basierte InputControls
│   │
│   └── Tab "Grundmenü"
│       └── PdvmMenuItemsEditor
│           ├── QListWidget (Item-Liste mit Drag&Drop)
│           └── PdvmMenuItemEditor (Einzeln-Editor)
│               └── Template-basierte InputControls
│
├── PdvmMenuPreview (Rechts: Live-Vorschau)
│   ├── Simulated Vertikalmenü (wie in App)
│   └── Simulated Grundmenü (wie in App)
│
└── Button-Bar (Unten)
    ├── [Speichern] [Abbrechen] [Rückgängig]
    └── [Neu] [Duplizieren] [Löschen]
```

---

## 📝 Template-System

### MenuItem-Template (JSON)

```json
{
  "template_guid": "tpl-menuitem-v1",
  "template_name": "Standard Menüpunkt V1",
  "version": "1.0",
  "fields": [
    {
      "key": "GUID",
      "label": "GUID",
      "type": "text",
      "readonly": true,
      "auto_generate": true,
      "visible": false
    },
    {
      "key": "LABEL",
      "label": "Beschriftung",
      "type": "text",
      "required": true,
      "placeholder": "z.B. Personen",
      "max_length": 50
    },
    {
      "key": "TYPE",
      "label": "Typ",
      "type": "dropdown",
      "required": true,
      "options": [
        {"value": "BUTTON", "label": "Button (Aktion)"},
        {"value": "SUBMENU", "label": "Untermenü"},
        {"value": "SEPARATOR", "label": "Trennlinie"},
        {"value": "SPACER", "label": "Abstand"}
      ],
      "default": "BUTTON"
    },
    {
      "key": "ICON",
      "label": "Icon",
      "type": "icon_picker",
      "required": false,
      "placeholder": "Wählen Sie ein Icon..."
    },
    {
      "key": "COMMAND_GUID",
      "label": "Command",
      "type": "viewtable",
      "required": false,
      "view_guid": "view-commands-liste",
      "display_field": "NAME",
      "value_field": "GUID",
      "condition": "TYPE == 'BUTTON'"
    },
    {
      "key": "ZUSATZ_GUID",
      "label": "Zusatzmenü",
      "type": "viewtable",
      "required": false,
      "view_guid": "view-zusatzmenu-liste",
      "display_field": "NAME",
      "value_field": "GUID",
      "condition": "TYPE == 'SUBMENU'"
    },
    {
      "key": "SORT_ORDER",
      "label": "Reihenfolge",
      "type": "number",
      "required": true,
      "auto_calculate": true,
      "min": 0,
      "max": 9999
    },
    {
      "key": "VISIBLE",
      "label": "Sichtbar",
      "type": "checkbox",
      "default": true
    },
    {
      "key": "ENABLED",
      "label": "Aktiviert",
      "type": "checkbox",
      "default": true
    },
    {
      "key": "TOOLTIP",
      "label": "Tooltip",
      "type": "text",
      "required": false,
      "placeholder": "Hilfetext beim Hover...",
      "max_length": 200
    }
  ],
  "validation_rules": [
    {
      "rule": "if TYPE == 'BUTTON' then COMMAND_GUID required",
      "message": "Button benötigt einen Command"
    },
    {
      "rule": "if TYPE == 'SUBMENU' then ZUSATZ_GUID optional",
      "message": "Untermenü kann Zusatzmenü haben"
    },
    {
      "rule": "LABEL must be unique within container",
      "message": "Beschriftung muss eindeutig sein"
    }
  ]
}
```

### Template-Erweiterbarkeit

**Zukünftige Felder hinzufügen**:
```json
{
  "key": "BADGE_TEXT",
  "label": "Badge Text",
  "type": "text",
  "required": false,
  "placeholder": "NEU, Beta, 3...",
  "max_length": 10,
  "version_added": "1.1"
}
```

**Vorteil**: Bestehende Menüs müssen nicht migriert werden - neue Felder sind optional!

---

## 🎨 UI-Layout

### Hauptfenster (1200x800px)

```
┌─────────────────────────────────────────────────────────────┐
│ Menu-Editor: [Hauptmenü] (GUID: 5ca6674e...)        [X]     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────┐  ┌──────────────────────────────┐ │
│  │ BEARBEITEN           │  │ VORSCHAU                     │ │
│  │                      │  │                              │ │
│  │ [Vertikalmenü]       │  │ ┌──────────┐  ┌───────────┐ │ │
│  │  GRUND               │  │ │ WILLKOMMEN│  │ Datei   ▼ │ │ │
│  │                      │  │ │ TESTBEREICH  │ Bearbeiten│ │ │
│  │ ┌──────────────────┐ │  │ │ VERWALTUNG│  └───────────┘ │ │
│  │ │ Items:           │ │  │ │ ADMIN     │                │ │
│  │ │                  │ │  │ │ LOGOUT    │                │ │
│  │ │ □ Willkommen     │ │  │ └──────────┘                │ │
│  │ │ □ Testbereich    │ │  │                              │ │
│  │ │ □ Verwaltung     │ │  │ [Live Preview aktiviert]   │ │
│  │ │ □ Administration │ │  │                              │ │
│  │ │ □ Logout         │ │  │                              │ │
│  │ │                  │ │  │                              │ │
│  │ │ [+ Neu]          │ │  │                              │ │
│  │ └──────────────────┘ │  │                              │ │
│  │                      │  │                              │ │
│  │ EDITOR:              │  │                              │ │
│  │ ┌──────────────────┐ │  │                              │ │
│  │ │ Beschriftung:    │ │  │                              │ │
│  │ │ [Testbereich___]│ │  │                              │ │
│  │ │                  │ │  │                              │ │
│  │ │ Typ:             │ │  │                              │ │
│  │ │ [Button ▼]      │ │  │                              │ │
│  │ │                  │ │  │                              │ │
│  │ │ Icon:            │ │  │                              │ │
│  │ │ [🔧 Wählen...]  │ │  │                              │ │
│  │ │                  │ │  │                              │ │
│  │ │ Command:         │ │  │                              │ │
│  │ │ [open_app_menu] │ │  │                              │ │
│  │ │ [🔍 Auswählen...]│ │  │                              │ │
│  │ │                  │ │  │                              │ │
│  │ │ Tooltip:         │ │  │                              │ │
│  │ │ [Öffnet Test...]│ │  │                              │ │
│  │ │                  │ │  │                              │ │
│  │ │ ☑ Sichtbar       │ │  │                              │ │
│  │ │ ☑ Aktiviert      │ │  │                              │ │
│  │ └──────────────────┘ │  │                              │ │
│  └──────────────────────┘  └──────────────────────────────┘ │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│ [💾 Speichern] [❌ Abbrechen] [↶ Rückgängig]      Status: * │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Implementierung

### Phase 1: Handler & View-Auswahl

**Datei**: `handlers/handler_open_menu_editor.py`

```python
"""
Handler: Menu-Editor öffnen
"""
from pdvm_view_dialog import PdvmViewDialog
from pdvm_menu_editor_dialog import PdvmMenuEditorDialog
from pdvm_central_systemsteuerung import get_gcs

def handle(params: dict, main_app):
    """
    Öffnet Menu-Editor
    
    Ablauf:
    1. View-Dialog: Menü-GUID auswählen
    2. Editor-Dialog: Menü bearbeiten
    """
    gcs = get_gcs()
    
    # STEP 1: Menü auswählen
    view_guid = "view-menu-liste"  # TODO: In frame_data hinterlegen
    
    view_dialog = PdvmViewDialog(
        view_guid=view_guid,
        parent=main_app,
        title="Menü auswählen",
        selection_mode='single'
    )
    
    if not view_dialog.exec_():
        return  # Abgebrochen
    
    selected_rows = view_dialog.get_selected_rows()
    if not selected_rows:
        return
    
    menu_guid = selected_rows[0]['GUID']
    
    # STEP 2: Editor öffnen
    editor_dialog = PdvmMenuEditorDialog(
        menu_guid=menu_guid,
        parent=main_app
    )
    
    editor_dialog.exec_()
```

### Phase 2: Editor-Dialog

**Datei**: `pdvm_menu_editor_dialog.py`

```python
"""
PDVM Menu-Editor Dialog
=======================

Hauptdialog für Menü-Bearbeitung mit:
- 2 Tabs (Vertikalmenü, Grundmenü)
- Template-basierte Item-Bearbeitung
- Live-Vorschau
- Drag & Drop Sortierung
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QSplitter, QPushButton, QLabel, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from pdvm_central_systemsteuerung import get_gcs
from pdvm_menu_schema import MenuContainer
from pdvm_menu_items_editor import PdvmMenuItemsEditor
from pdvm_menu_preview import PdvmMenuPreview
import logging

logger = logging.getLogger(__name__)


class PdvmMenuEditorDialog(QDialog):
    """
    Hauptdialog für Menu-Bearbeitung
    """
    
    menu_saved = pyqtSignal(str)  # Signal wenn Menü gespeichert
    
    def __init__(self, menu_guid: str, parent=None):
        super().__init__(parent)
        self.menu_guid = menu_guid
        self.gcs = get_gcs()
        self.menu_container = None
        self.has_changes = False
        
        self._init_ui()
        self._load_menu()
    
    def _init_ui(self):
        """Erstellt UI-Struktur"""
        self.setWindowTitle(f"Menu-Editor: Lädt...")
        self.setModal(True)
        self.resize(1200, 800)
        
        # Haupt-Layout
        layout = QVBoxLayout(self)
        
        # Splitter: Editor links, Vorschau rechts
        splitter = QSplitter(Qt.Horizontal)
        
        # LINKS: Tab-Widget mit Editoren
        self.tabs = QTabWidget()
        
        # Tab 1: Vertikalmenü
        self.vertikal_editor = PdvmMenuItemsEditor(
            container_type='VERTIKAL',
            parent=self
        )
        self.vertikal_editor.items_changed.connect(self._on_items_changed)
        self.tabs.addTab(self.vertikal_editor, "Vertikalmenü")
        
        # Tab 2: Grundmenü
        self.grund_editor = PdvmMenuItemsEditor(
            container_type='GRUND',
            parent=self
        )
        self.grund_editor.items_changed.connect(self._on_items_changed)
        self.tabs.addTab(self.grund_editor, "Grundmenü")
        
        splitter.addWidget(self.tabs)
        
        # RECHTS: Vorschau
        self.preview = PdvmMenuPreview(parent=self)
        splitter.addWidget(self.preview)
        
        # Splitter-Verhältnis: 60% Editor, 40% Vorschau
        splitter.setSizes([720, 480])
        
        layout.addWidget(splitter)
        
        # Button-Bar
        button_layout = QHBoxLayout()
        
        self.btn_save = QPushButton("💾 Speichern")
        self.btn_save.clicked.connect(self._save_menu)
        self.btn_save.setEnabled(False)
        
        self.btn_cancel = QPushButton("❌ Abbrechen")
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_undo = QPushButton("↶ Rückgängig")
        self.btn_undo.clicked.connect(self._undo_changes)
        self.btn_undo.setEnabled(False)
        
        button_layout.addWidget(self.btn_save)
        button_layout.addWidget(self.btn_cancel)
        button_layout.addWidget(self.btn_undo)
        button_layout.addStretch()
        
        self.status_label = QLabel("Status: Bereit")
        button_layout.addWidget(self.status_label)
        
        layout.addLayout(button_layout)
    
    def _load_menu(self):
        """Lädt Menü aus Datenbank"""
        try:
            logger.info(f"🔧 Lade Menü: {self.menu_guid}")
            
            # Menü-Datenbank laden
            menu_db = self.gcs._get_menu_database(self.menu_guid)
            
            # MenuContainer laden
            menu_data = menu_db.get_all_data()
            self.menu_container = MenuContainer.from_dict(menu_data)
            
            # Titel aktualisieren
            self.setWindowTitle(
                f"Menu-Editor: {self.menu_container.MENU_NAME}"
            )
            
            # Daten in Editoren laden
            self.vertikal_editor.set_items(self.menu_container.VERTIKAL)
            self.grund_editor.set_items(self.menu_container.GRUND)
            
            # Vorschau aktualisieren
            self._update_preview()
            
            logger.info("✅ Menü geladen")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden: {e}")
            QMessageBox.critical(
                self,
                "Fehler",
                f"Menü konnte nicht geladen werden:\n{e}"
            )
            self.reject()
    
    def _on_items_changed(self):
        """Items wurden geändert"""
        self.has_changes = True
        self.btn_save.setEnabled(True)
        self.btn_undo.setEnabled(True)
        self.status_label.setText("Status: Ungespeicherte Änderungen *")
        
        # Vorschau aktualisieren
        self._update_preview()
    
    def _update_preview(self):
        """Aktualisiert Live-Vorschau"""
        vertikal_items = self.vertikal_editor.get_items()
        grund_items = self.grund_editor.get_items()
        
        self.preview.update_menu(
            vertikal_items=vertikal_items,
            grund_items=grund_items
        )
    
    def _save_menu(self):
        """Speichert Menü in Datenbank"""
        try:
            logger.info("💾 Speichere Menü...")
            
            # Items aus Editoren holen
            self.menu_container.VERTIKAL = self.vertikal_editor.get_items()
            self.menu_container.GRUND = self.grund_editor.get_items()
            
            # Validierung
            if not self._validate_menu():
                return
            
            # In Datenbank speichern
            menu_db = self.gcs._get_menu_database(self.menu_guid)
            menu_data = self.menu_container.to_dict()
            menu_db.set_all_data(menu_data)
            menu_db.save_all_values()
            
            # Status zurücksetzen
            self.has_changes = False
            self.btn_save.setEnabled(False)
            self.btn_undo.setEnabled(False)
            self.status_label.setText("Status: Gespeichert ✓")
            
            logger.info("✅ Menü gespeichert")
            
            # Signal aussenden
            self.menu_saved.emit(self.menu_guid)
            
            QMessageBox.information(
                self,
                "Erfolg",
                "Menü wurde erfolgreich gespeichert!"
            )
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern: {e}")
            QMessageBox.critical(
                self,
                "Fehler",
                f"Menü konnte nicht gespeichert werden:\n{e}"
            )
    
    def _validate_menu(self) -> bool:
        """Validiert Menü vor dem Speichern"""
        # TODO: Template-basierte Validierung
        # - Pflichtfelder prüfen
        # - Eindeutigkeit prüfen
        # - Commands existieren
        # etc.
        return True
    
    def _undo_changes(self):
        """Macht Änderungen rückgängig"""
        reply = QMessageBox.question(
            self,
            "Änderungen verwerfen?",
            "Möchten Sie alle Änderungen verwerfen?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self._load_menu()  # Neu laden
            self.has_changes = False
            self.btn_save.setEnabled(False)
            self.btn_undo.setEnabled(False)
            self.status_label.setText("Status: Zurückgesetzt")
    
    def closeEvent(self, event):
        """Beim Schließen prüfen ob ungespeicherte Änderungen"""
        if self.has_changes:
            reply = QMessageBox.question(
                self,
                "Ungespeicherte Änderungen",
                "Es gibt ungespeicherte Änderungen.\n"
                "Möchten Sie trotzdem schließen?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                event.ignore()
                return
        
        event.accept()
```

### Phase 3: Items-Editor (mit Drag & Drop)

**Datei**: `pdvm_menu_items_editor.py`

```python
"""
PDVM Menu Items Editor
======================

Editor für Liste von Menu-Items mit:
- Drag & Drop Sortierung
- Template-basierte Einzelbearbeitung
- Add/Delete Items
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget,
    QListWidgetItem, QPushButton, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from pdvm_menu_schema import MenuItem, MenuItemType
from pdvm_menu_item_editor import PdvmMenuItemEditor
import uuid


class PdvmMenuItemsEditor(QWidget):
    """
    Editor für Liste von Menu-Items
    """
    
    items_changed = pyqtSignal()  # Signal bei Änderungen
    
    def __init__(self, container_type: str, parent=None):
        super().__init__(parent)
        self.container_type = container_type  # 'VERTIKAL' oder 'GRUND'
        self.items = []
        self.current_item = None
        
        self._init_ui()
    
    def _init_ui(self):
        """Erstellt UI"""
        layout = QVBoxLayout(self)
        
        # Items-Liste (mit Drag & Drop)
        self.list_widget = QListWidget()
        self.list_widget.setDragDropMode(QListWidget.InternalMove)
        self.list_widget.setSelectionMode(QListWidget.SingleSelection)
        self.list_widget.currentItemChanged.connect(self._on_selection_changed)
        self.list_widget.model().rowsMoved.connect(self._on_items_reordered)
        
        layout.addWidget(self.list_widget, stretch=1)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        btn_add = QPushButton("+ Neu")
        btn_add.clicked.connect(self._add_item)
        
        btn_duplicate = QPushButton("⧉ Duplizieren")
        btn_duplicate.clicked.connect(self._duplicate_item)
        
        btn_delete = QPushButton("🗑 Löschen")
        btn_delete.clicked.connect(self._delete_item)
        
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_duplicate)
        btn_layout.addWidget(btn_delete)
        
        layout.addLayout(btn_layout)
        
        # Trennlinie
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        layout.addWidget(line)
        
        # Einzelitem-Editor (unten)
        self.item_editor = PdvmMenuItemEditor(parent=self)
        self.item_editor.item_changed.connect(self._on_item_edited)
        layout.addWidget(self.item_editor, stretch=2)
    
    def set_items(self, items: list):
        """Setzt Items"""
        self.items = items
        self._refresh_list()
    
    def get_items(self) -> list:
        """Gibt Items zurück (mit aktueller Sortierung)"""
        # SORT_ORDER aus Liste übernehmen
        for i, item in enumerate(self.items):
            item.SORT_ORDER = i
        return self.items
    
    def _refresh_list(self):
        """Aktualisiert Liste"""
        self.list_widget.clear()
        
        for item in sorted(self.items, key=lambda x: x.SORT_ORDER):
            list_item = QListWidgetItem(self._format_item_label(item))
            list_item.setData(Qt.UserRole, item.GUID)
            self.list_widget.addItem(list_item)
    
    def _format_item_label(self, item: MenuItem) -> str:
        """Formatiert Label für Liste"""
        icon_map = {
            MenuItemType.BUTTON: "□",
            MenuItemType.SUBMENU: "▷",
            MenuItemType.SEPARATOR: "━",
            MenuItemType.SPACER: "·"
        }
        icon = icon_map.get(item.TYPE, "?")
        return f"{icon} {item.LABEL}"
    
    def _on_selection_changed(self, current, previous):
        """Item ausgewählt"""
        if not current:
            self.current_item = None
            self.item_editor.clear()
            return
        
        item_guid = current.data(Qt.UserRole)
        self.current_item = next((i for i in self.items if i.GUID == item_guid), None)
        
        if self.current_item:
            self.item_editor.set_item(self.current_item)
    
    def _on_item_edited(self, item: MenuItem):
        """Item wurde bearbeitet"""
        # Item in Liste aktualisieren
        idx = next((i for i, x in enumerate(self.items) if x.GUID == item.GUID), -1)
        if idx >= 0:
            self.items[idx] = item
        
        self._refresh_list()
        self.items_changed.emit()
    
    def _on_items_reordered(self):
        """Items wurden per Drag & Drop sortiert"""
        # Neue Reihenfolge übernehmen
        new_order = []
        for i in range(self.list_widget.count()):
            item_guid = self.list_widget.item(i).data(Qt.UserRole)
            item = next((x for x in self.items if x.GUID == item_guid), None)
            if item:
                item.SORT_ORDER = i
                new_order.append(item)
        
        self.items = new_order
        self.items_changed.emit()
    
    def _add_item(self):
        """Neues Item hinzufügen"""
        new_item = MenuItem(
            GUID=str(uuid.uuid4()),
            TYPE=MenuItemType.BUTTON,
            LABEL="Neuer Menüpunkt",
            SORT_ORDER=len(self.items)
        )
        
        self.items.append(new_item)
        self._refresh_list()
        
        # Neues Item auswählen
        self.list_widget.setCurrentRow(self.list_widget.count() - 1)
        
        self.items_changed.emit()
    
    def _duplicate_item(self):
        """Aktuelles Item duplizieren"""
        if not self.current_item:
            return
        
        new_item = MenuItem(
            GUID=str(uuid.uuid4()),
            TYPE=self.current_item.TYPE,
            LABEL=f"{self.current_item.LABEL} (Kopie)",
            SORT_ORDER=len(self.items),
            ICON=self.current_item.ICON,
            COMMAND_GUID=self.current_item.COMMAND_GUID,
            ZUSATZ_GUID=self.current_item.ZUSATZ_GUID,
            TOOLTIP=self.current_item.TOOLTIP,
            VISIBLE=self.current_item.VISIBLE,
            ENABLED=self.current_item.ENABLED
        )
        
        self.items.append(new_item)
        self._refresh_list()
        self.list_widget.setCurrentRow(self.list_widget.count() - 1)
        
        self.items_changed.emit()
    
    def _delete_item(self):
        """Aktuelles Item löschen"""
        if not self.current_item:
            return
        
        self.items = [i for i in self.items if i.GUID != self.current_item.GUID]
        self._refresh_list()
        self.items_changed.emit()
```

### Phase 4: Einzelitem-Editor (Template-basiert)

**Datei**: `pdvm_menu_item_editor.py`

```python
"""
PDVM Menu Item Editor
=====================

Template-basierter Editor für einzelnes MenuItem.
Nutzt existierende InputControl-Infrastruktur.
"""
from PyQt5.QtWidgets import QWidget, QFormLayout, QLabel
from PyQt5.QtCore import pyqtSignal
from pdvm_menu_schema import MenuItem
from pdvm_input_controls_manager import PdvmInputControlsManager
import logging

logger = logging.getLogger(__name__)


class PdvmMenuItemEditor(QWidget):
    """
    Editor für einzelnes MenuItem (Template-basiert)
    """
    
    item_changed = pyqtSignal(MenuItem)  # Signal bei Änderung
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_item = None
        self.controls_manager = None
        
        self._init_ui()
    
    def _init_ui(self):
        """Erstellt UI"""
        self.layout = QFormLayout(self)
        self.placeholder = QLabel("Kein Item ausgewählt")
        self.layout.addRow(self.placeholder)
    
    def set_item(self, item: MenuItem):
        """Setzt zu bearbeitendes Item"""
        self.current_item = item
        
        # Controls-Manager erstellen
        template_guid = "tpl-menuitem-v1"  # Aus DB laden
        
        # TODO: Template aus DB laden und Controls generieren
        # Für jetzt: Hardcoded Controls
        
        self._build_controls()
    
    def _build_controls(self):
        """Baut Controls basierend auf Template"""
        # Clear layout
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not self.current_item:
            self.layout.addRow(QLabel("Kein Item ausgewählt"))
            return
        
        # Hardcoded Controls (später Template-basiert)
        # TODO: Via InputControlsManager + Template
        
        from PyQt5.QtWidgets import QLineEdit, QComboBox, QCheckBox, QPushButton
        
        # LABEL
        label_edit = QLineEdit(self.current_item.LABEL)
        label_edit.textChanged.connect(
            lambda text: self._update_field('LABEL', text)
        )
        self.layout.addRow("Beschriftung:", label_edit)
        
        # TYPE
        type_combo = QComboBox()
        type_combo.addItems(["BUTTON", "SUBMENU", "SEPARATOR", "SPACER"])
        type_combo.setCurrentText(self.current_item.TYPE.value)
        type_combo.currentTextChanged.connect(
            lambda text: self._update_field('TYPE', text)
        )
        self.layout.addRow("Typ:", type_combo)
        
        # ICON
        icon_btn = QPushButton("🔧 Icon wählen...")
        icon_btn.clicked.connect(self._choose_icon)
        self.layout.addRow("Icon:", icon_btn)
        
        # COMMAND_GUID
        command_btn = QPushButton("🔍 Command auswählen...")
        command_btn.clicked.connect(self._choose_command)
        self.layout.addRow("Command:", command_btn)
        
        # TOOLTIP
        tooltip_edit = QLineEdit(self.current_item.TOOLTIP or "")
        tooltip_edit.textChanged.connect(
            lambda text: self._update_field('TOOLTIP', text)
        )
        self.layout.addRow("Tooltip:", tooltip_edit)
        
        # VISIBLE
        visible_check = QCheckBox()
        visible_check.setChecked(self.current_item.VISIBLE)
        visible_check.toggled.connect(
            lambda checked: self._update_field('VISIBLE', checked)
        )
        self.layout.addRow("Sichtbar:", visible_check)
        
        # ENABLED
        enabled_check = QCheckBox()
        enabled_check.setChecked(self.current_item.ENABLED)
        enabled_check.toggled.connect(
            lambda checked: self._update_field('ENABLED', checked)
        )
        self.layout.addRow("Aktiviert:", enabled_check)
    
    def _update_field(self, field_name: str, value):
        """Aktualisiert Feld im Item"""
        if not self.current_item:
            return
        
        setattr(self.current_item, field_name, value)
        self.item_changed.emit(self.current_item)
    
    def _choose_icon(self):
        """Icon-Picker öffnen"""
        # TODO: Icon-Picker Dialog
        pass
    
    def _choose_command(self):
        """Command-Auswahl Dialog"""
        # TODO: View-Dialog mit Commands
        pass
    
    def clear(self):
        """Leert Editor"""
        self.current_item = None
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.layout.addRow(QLabel("Kein Item ausgewählt"))
```

### Phase 5: Live-Vorschau

**Datei**: `pdvm_menu_preview.py`

```python
"""
PDVM Menu Preview
=================

Zeigt Live-Vorschau des Menüs wie in echter Anwendung.
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea
)
from PyQt5.QtCore import Qt
from pdvm_menu_schema import MenuItem, MenuItemType


class PdvmMenuPreview(QWidget):
    """
    Live-Vorschau des Menüs
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.vertikal_items = []
        self.grund_items = []
        
        self._init_ui()
    
    def _init_ui(self):
        """Erstellt UI"""
        layout = QVBoxLayout(self)
        
        # Header
        header = QLabel("VORSCHAU (Live)")
        header.setStyleSheet("font-weight: bold; font-size: 12pt;")
        layout.addWidget(header)
        
        # Scroll-Bereich für Vorschau
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        # Preview-Container
        self.preview_widget = QWidget()
        self.preview_layout = QVBoxLayout(self.preview_widget)
        
        scroll.setWidget(self.preview_widget)
        layout.addWidget(scroll)
    
    def update_menu(self, vertikal_items: list, grund_items: list):
        """Aktualisiert Vorschau"""
        self.vertikal_items = vertikal_items
        self.grund_items = grund_items
        
        # Clear preview
        while self.preview_layout.count():
            item = self.preview_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Container für Menüs
        menu_container = QWidget()
        menu_layout = QHBoxLayout(menu_container)
        
        # Vertikalmenü (links)
        vertikal_frame = self._create_vertikal_preview()
        menu_layout.addWidget(vertikal_frame)
        
        # Grundmenü (oben rechts)
        grund_frame = self._create_grund_preview()
        menu_layout.addWidget(grund_frame)
        
        menu_layout.addStretch()
        
        self.preview_layout.addWidget(menu_container)
        self.preview_layout.addStretch()
    
    def _create_vertikal_preview(self) -> QWidget:
        """Erstellt Vertikalmenü-Vorschau"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Box | QFrame.Raised)
        frame.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #555;
            }
            QPushButton {
                text-align: left;
                padding: 8px;
                background-color: #3d3d3d;
                border: none;
                color: white;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
            }
        """)
        
        layout = QVBoxLayout(frame)
        layout.setSpacing(2)
        
        for item in sorted(self.vertikal_items, key=lambda x: x.SORT_ORDER):
            if not item.VISIBLE:
                continue
            
            if item.TYPE == MenuItemType.SEPARATOR:
                sep = QFrame()
                sep.setFrameShape(QFrame.HLine)
                layout.addWidget(sep)
            elif item.TYPE == MenuItemType.SPACER:
                layout.addSpacing(10)
            else:
                btn = QPushButton(item.LABEL)
                btn.setEnabled(item.ENABLED)
                if item.TOOLTIP:
                    btn.setToolTip(item.TOOLTIP)
                layout.addWidget(btn)
        
        layout.addStretch()
        return frame
    
    def _create_grund_preview(self) -> QWidget:
        """Erstellt Grundmenü-Vorschau"""
        frame = QFrame()
        frame.setFrameStyle(QFrame.Box | QFrame.Raised)
        frame.setStyleSheet("""
            QFrame {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
            }
            QPushButton {
                padding: 4px 12px;
                background-color: #fff;
                border: 1px solid #ccc;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        
        layout = QHBoxLayout(frame)
        
        for item in sorted(self.grund_items, key=lambda x: x.SORT_ORDER):
            if not item.VISIBLE:
                continue
            
            if item.TYPE == MenuItemType.SEPARATOR:
                sep = QFrame()
                sep.setFrameShape(QFrame.VLine)
                layout.addWidget(sep)
            elif item.TYPE == MenuItemType.SPACER:
                layout.addSpacing(10)
            else:
                btn = QPushButton(item.LABEL)
                btn.setEnabled(item.ENABLED)
                if item.TOOLTIP:
                    btn.setToolTip(item.TOOLTIP)
                layout.addWidget(btn)
        
        layout.addStretch()
        return frame
```

---

## 📊 Datenbank-Struktur

### sys_menu_liste (View-Tabelle)

```sql
CREATE TABLE sys_menu_liste (
    GUID TEXT PRIMARY KEY,
    MENU_NAME TEXT NOT NULL,
    IS_STARTMENU INTEGER DEFAULT 0,
    DESCRIPTION TEXT,
    ITEM_COUNT INTEGER,
    LAST_MODIFIED REAL,
    ABDATUM REAL,
    FORMATIERTES_ABDATUM TEXT
);
```

### frame_data Eintrag für View

```json
{
  "view_guid": "view-menu-liste",
  "table_name": "sys_menu_liste",
  "title": "Menü-Auswahl",
  "columns": [
    {"key": "MENU_NAME", "label": "Menü-Name", "visible": true},
    {"key": "IS_STARTMENU", "label": "Startmenü", "visible": true},
    {"key": "ITEM_COUNT", "label": "Anzahl Items", "visible": true},
    {"key": "LAST_MODIFIED", "label": "Zuletzt geändert", "visible": true}
  ]
}
```

---

## 🎯 Roadmap

### v0.10 (Basis-Editor)
- ✅ Handler `open_menu_editor`
- ✅ View-Auswahl Dialog
- ✅ Editor-Dialog mit 2 Tabs
- ✅ Item-Liste mit Drag & Drop
- ✅ Basis-Item-Editor (hardcoded)
- ✅ Live-Vorschau
- ✅ Speichern/Laden

### v0.11 (Template-System)
- Template-Loader aus DB
- InputControls-Manager Integration
- Dynamische Control-Generierung
- Validierung basierend auf Template
- Icon-Picker Dialog
- Command-Auswahl Dialog

### v0.12 (Zusatzmenüs)
- Tab 3: Zusatzmenü-Editor
- Parent-Child Vererbung
- Zusatz-Vorschau in Preview

### v1.0 (Polish)
- Undo/Redo mit Historie
- Copy/Paste zwischen Menüs
- Import/Export (JSON)
- Keyboard-Shortcuts
- Dark/Light Theme
- Hilfe-Tooltips

---

## 🧪 Test-Szenarien

1. **Menü auswählen**: View-Dialog mit Hauptmenü
2. **Item hinzufügen**: Neuer Button "Einstellungen"
3. **Item bearbeiten**: Label ändern, Icon setzen
4. **Item verschieben**: Drag & Drop in Liste
5. **Live-Vorschau**: Änderungen sofort sichtbar
6. **Speichern**: Persistierung in man_db
7. **Reload**: Menü neu laden, Änderungen da

---

**Status**: Design Complete - Bereit für Implementierung Phase 1
**Nächster Schritt**: Handler + View-Auswahl implementieren
