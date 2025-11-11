"""
🎯 PDVM Menu-Editor - EINFACH & LINEAR
======================================

KONZEPT:
1. EINE Instanz PdvmCentralDatenbank für alle Daten (VERTIKAL/GRUND/ZUSATZ)
2. Matrix-Ansatz: Gruppe → Dict[guid → item_data]
3. Änderungen direkt in Matrix → orange Rahmen
4. save_all_values() speichert ALLES auf einmal
"""

import logging
import uuid
from typing import Dict, Set, Optional, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QListWidget, QListWidgetItem, QPushButton, QTabWidget,
    QLabel, QLineEdit, QComboBox, QTextEdit, QFormLayout,
    QGroupBox, QMessageBox, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor

from pdvm_central_systemsteuerung import get_gcs
from pdvm_central_datenbank import PdvmCentralDatenbank

logger = logging.getLogger(__name__)


class MenuItemEditor(QFrame):
    """
    Editor für einzelnes Menü-Item (rechts neben Liste)
    Schreibt direkt in Matrix via set_static_value()
    """
    
    item_changed = pyqtSignal(str)  # GUID des geänderten Items
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db: Optional[PdvmCentralDatenbank] = None
        self.current_gruppe: Optional[str] = None
        self.current_guid: Optional[str] = None
        self._init_ui()
    
    def _init_ui(self):
        """UI aufbauen"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header = QLabel("✏️ Menüpunkt bearbeiten")
        header.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(header)
        
        # Form
        form = QFormLayout()
        form.setSpacing(10)
        
        # Type (Dropdown mit Icons)
        self.type_combo = QComboBox()
        self.type_combo.addItems(['🔘 BUTTON', '📁 SUBMENU', '─ SEPARATOR', '⏸ SPACER'])
        form.addRow("Typ:", self.type_combo)
        
        # Label
        self.label_edit = QLineEdit()
        self.label_edit.setPlaceholderText("z.B. 'Datei öffnen'")
        form.addRow("Label:", self.label_edit)
        
        # Handler
        self.handler_edit = QLineEdit()
        self.handler_edit.setPlaceholderText("z.B. 'open_view'")
        form.addRow("Handler:", self.handler_edit)
        
        # Tooltip
        self.tooltip_edit = QLineEdit()
        self.tooltip_edit.setPlaceholderText("Tooltip-Text (optional)")
        form.addRow("Tooltip:", self.tooltip_edit)
        
        # Params (JSON)
        self.params_edit = QTextEdit()
        self.params_edit.setPlaceholderText('{"view_guid": "..."}')
        self.params_edit.setMaximumHeight(80)
        form.addRow("Parameter:", self.params_edit)
        
        layout.addLayout(form)
        
        # Übernehmen Button
        self.btn_apply = QPushButton("✅ Übernehmen")
        self.btn_apply.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        self.btn_apply.clicked.connect(self._apply_changes)
        layout.addWidget(self.btn_apply)
        
        # Info-Label
        self.info_label = QLabel("← Wähle einen Menüpunkt aus der Liste")
        self.info_label.setStyleSheet("color: gray; font-size: 10px;")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)
        
        layout.addStretch()
        
        # Initial deaktiviert
        self._set_enabled(False)
    
    def _set_enabled(self, enabled: bool):
        """Aktiviert/Deaktiviert Editor"""
        self.type_combo.setEnabled(enabled)
        self.label_edit.setEnabled(enabled)
        self.handler_edit.setEnabled(enabled)
        self.tooltip_edit.setEnabled(enabled)
        self.params_edit.setEnabled(enabled)
        self.btn_apply.setEnabled(enabled)
    
    def set_database(self, db: PdvmCentralDatenbank):
        """Setzt Datenbank-Instanz"""
        self.db = db
    
    def load_item(self, gruppe: str, item_guid: str):
        """Lädt Item aus Matrix"""
        if not self.db:
            logger.warning("⚠️ Keine Datenbank gesetzt!")
            return
        
        self.current_gruppe = gruppe
        self.current_guid = item_guid
        
        try:
            # Item aus Matrix holen
            item_data = self.db.get_static_value(gruppe, item_guid)
            
            if not item_data:
                logger.warning(f"⚠️ Item nicht gefunden: {item_guid}")
                return
            
            # UI befüllen
            item_type = item_data.get('type', 'BUTTON')
            type_map = {'BUTTON': 0, 'SUBMENU': 1, 'SEPARATOR': 2, 'SPACER': 3}
            self.type_combo.setCurrentIndex(type_map.get(item_type, 0))
            
            self.label_edit.setText(item_data.get('label', ''))
            self.tooltip_edit.setText(item_data.get('tooltip', ''))
            
            # Command
            command = item_data.get('command')
            if command and isinstance(command, dict):
                self.handler_edit.setText(command.get('handler', ''))
                params = command.get('params', {})
                import json
                self.params_edit.setPlainText(json.dumps(params, indent=2) if params else '')
            else:
                self.handler_edit.clear()
                self.params_edit.clear()
            
            self._set_enabled(True)
            self.info_label.setText(f"📋 Bearbeite: {item_data.get('label', 'N/A')}")
            
            logger.info(f"✅ Editor geladen: {item_data.get('label')} (GUID={item_guid})")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden: {e}", exc_info=True)
            self.info_label.setText(f"❌ Fehler: {str(e)}")
    
    def _apply_changes(self):
        """Übernimmt Änderungen in Matrix (noch nicht persistent!)"""
        if not self.db or not self.current_gruppe or not self.current_guid:
            return
        
        try:
            # Aktuelles Item holen
            item_data = self.db.get_static_value(self.current_gruppe, self.current_guid)
            
            # Type auslesen
            type_map = ['BUTTON', 'SUBMENU', 'SEPARATOR', 'SPACER']
            item_data['type'] = type_map[self.type_combo.currentIndex()]
            
            # Felder aktualisieren
            item_data['label'] = self.label_edit.text().strip() or 'Unbekannt'
            item_data['tooltip'] = self.tooltip_edit.text().strip() or None
            
            # Command
            handler = self.handler_edit.text().strip()
            if handler:
                import json
                params_text = self.params_edit.toPlainText().strip()
                try:
                    params = json.loads(params_text) if params_text else {}
                except json.JSONDecodeError:
                    params = {}
                
                item_data['command'] = {
                    'handler': handler,
                    'params': params
                }
            else:
                item_data['command'] = None
            
            # In Matrix schreiben (NICHT persistent!)
            # Feld=GUID, Wert=item_data
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            if not gcs:
                raise ValueError("GCS nicht verfügbar!")
            
            stichtag = gcs.st_inst.PdvmDateTime
            self.db.set_value(self.current_gruppe, self.current_guid, item_data, stichtag)
            
            # Signal für orange Rahmen
            self.item_changed.emit(self.current_guid)
            
            self.info_label.setText(f"✅ Übernommen (noch nicht gespeichert!)")
            logger.info(f"✅ Item geändert: {item_data['label']} (GUID={self.current_guid})")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Übernehmen: {e}", exc_info=True)
            QMessageBox.critical(self, "Fehler", f"Übernehmen fehlgeschlagen:\n{str(e)}")


class MenuListWidget(QWidget):
    """
    Liste für eine Gruppe (VERTIKAL/GRUND/ZUSATZ)
    Zeigt Items hierarchisch mit Einrückung
    """
    
    item_selected = pyqtSignal(str, str)  # gruppe, guid
    items_reordered = pyqtSignal(str)     # gruppe
    
    def __init__(self, gruppe: str, parent=None):
        super().__init__(parent)
        self.gruppe = gruppe
        self.db: Optional[PdvmCentralDatenbank] = None
        self.modified_guids: Set[str] = set()
        self._init_ui()
    
    def _init_ui(self):
        """UI aufbauen"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Liste mit Drag & Drop
        self.list_widget = QListWidget()
        self.list_widget.setDragEnabled(True)
        self.list_widget.setAcceptDrops(True)
        self.list_widget.setDragDropMode(QListWidget.InternalMove)
        self.list_widget.setDefaultDropAction(Qt.MoveAction)
        self.list_widget.currentItemChanged.connect(self._on_selection_changed)
        
        # Signal für Reordering
        self.list_widget.model().rowsMoved.connect(self._on_items_reordered)
        
        layout.addWidget(self.list_widget)
        
        # Buttons
        btn_layout = QHBoxLayout()
        
        self.btn_add = QPushButton("➕ Neu")
        self.btn_add.clicked.connect(self._on_add_item)
        btn_layout.addWidget(self.btn_add)
        
        self.btn_indent = QPushButton("→ Einrücken")
        self.btn_indent.clicked.connect(self._on_indent_item)
        self.btn_indent.setEnabled(False)
        self.btn_indent.setToolTip("Item unter vorherigem Item als Kind einhängen")
        btn_layout.addWidget(self.btn_indent)
        
        self.btn_outdent = QPushButton("← Ausrücken")
        self.btn_outdent.clicked.connect(self._on_outdent_item)
        self.btn_outdent.setEnabled(False)
        self.btn_outdent.setToolTip("Item eine Ebene nach oben")
        btn_layout.addWidget(self.btn_outdent)
        
        self.btn_delete = QPushButton("🗑️ Löschen")
        self.btn_delete.clicked.connect(self._on_delete_item)
        self.btn_delete.setEnabled(False)
        btn_layout.addWidget(self.btn_delete)
        
        layout.addLayout(btn_layout)
    
    def set_database(self, db: PdvmCentralDatenbank):
        """Setzt Datenbank-Instanz"""
        self.db = db
    
    def load_items(self):
        """Lädt Items aus Matrix"""
        if not self.db:
            return
        
        self.list_widget.clear()
        
        try:
            # Gruppe aus DB holen
            items = self.db.get_gruppe(self.gruppe)
            
            # Hierarchisch sortieren
            sorted_items = self._build_hierarchy(items)
            
            # In Liste einfügen
            for item_guid, item_data, level in sorted_items:
                self._add_list_item(item_guid, item_data, level)
            
            logger.info(f"✅ {self.gruppe}: {len(items)} Items geladen")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden von {self.gruppe}: {e}", exc_info=True)
    
    def _build_hierarchy(self, items: Dict[str, Any]):
        """Baut hierarchische Liste (parent_guid beachten)"""
        result = []
        
        def add_with_children(item_guid, item_data, level=0):
            result.append((item_guid, item_data, level))
            
            # Kinder finden und nach sort_order sortieren
            children = [(g, d) for g, d in items.items() if d.get('parent_guid') == item_guid]
            children.sort(key=lambda x: x[1].get('sort_order', 0))
            
            for child_guid, child_data in children:
                add_with_children(child_guid, child_data, level + 1)
        
        # Top-Level Items (parent_guid = None)
        top_level = [(g, d) for g, d in items.items() if d.get('parent_guid') is None]
        top_level.sort(key=lambda x: x[1].get('sort_order', 0))
        
        for guid, data in top_level:
            add_with_children(guid, data, 0)
        
        return result
    
    def _add_list_item(self, item_guid: str, item_data: Dict, level: int):
        """Fügt Item in Liste ein"""
        # Type Icon
        type_icons = {
            'BUTTON': '🔘',
            'SUBMENU': '📁',
            'SEPARATOR': '─',
            'SPACER': '⏸'
        }
        icon = type_icons.get(item_data.get('type', 'BUTTON'), '📄')
        
        # Label + Handler
        label = item_data.get('label', 'Unbekannt')
        command = item_data.get('command')
        handler = command.get('handler', '') if command else ''
        
        # Einrückung
        indent = "    " * level
        
        # Display-Text
        if handler:
            display = f"{indent}{icon} {label} → ⚡{handler}"
        else:
            display = f"{indent}{icon} {label}"
        
        # ListItem erstellen
        list_item = QListWidgetItem(display)
        list_item.setData(Qt.UserRole, item_guid)
        list_item.setData(Qt.UserRole + 1, level)  # Level speichern!
        list_item.setData(Qt.UserRole + 2, item_data.get('parent_guid'))  # Parent speichern!
        
        # Orange Rahmen für geänderte Items
        if item_guid in self.modified_guids:
            list_item.setForeground(QColor(255, 140, 0))  # Orange
            font = QFont()
            font.setBold(True)
            list_item.setFont(font)
        
        self.list_widget.addItem(list_item)
    
    def mark_modified(self, item_guid: str):
        """Markiert Item als geändert (orange)"""
        self.modified_guids.add(item_guid)
        self.load_items()  # Neu laden um orange Farbe zu zeigen
    
    def clear_modified(self):
        """Entfernt alle Änderungs-Markierungen"""
        self.modified_guids.clear()
        self.load_items()
    
    def _on_selection_changed(self, current, previous):
        """Item ausgewählt"""
        if current:
            item_guid = current.data(Qt.UserRole)
            self.btn_delete.setEnabled(True)
            self.btn_indent.setEnabled(True)
            self.btn_outdent.setEnabled(True)
            self.item_selected.emit(self.gruppe, item_guid)
        else:
            self.btn_delete.setEnabled(False)
            self.btn_indent.setEnabled(False)
            self.btn_outdent.setEnabled(False)
    
    def _on_add_item(self):
        """Neues Item hinzufügen"""
        if not self.db:
            return
        
        # Neue GUID generieren
        new_guid = str(uuid.uuid4())
        
        # Neues Item erstellen
        new_item = {
            'guid': new_guid,
            'type': 'BUTTON',
            'label': 'Neuer Menüpunkt',
            'icon': None,
            'command': None,
            'parent_guid': None,
            'sort_order': len(self.db.get_gruppe(self.gruppe)),
            'visible': True,
            'enabled': True,
            'tooltip': None
        }
        
        # In Matrix schreiben
        from pdvm_central_systemsteuerung import get_gcs
        gcs = get_gcs()
        if not gcs:
            logger.error("GCS nicht verfügbar!")
            return
        
        stichtag = gcs.st_inst.PdvmDateTime
        self.db.set_value(self.gruppe, new_guid, new_item, stichtag)
        
        # Als geändert markieren
        self.mark_modified(new_guid)
        
        logger.info(f"➕ Neues Item erstellt: {new_guid}")
    
    def _on_delete_item(self):
        """Aktuelles Item löschen"""
        current_item = self.list_widget.currentItem()
        if not current_item or not self.db:
            return
        
        item_guid = current_item.data(Qt.UserRole)
        item_data = self.db.get_static_value(self.gruppe, item_guid)
        label = item_data.get('label', 'Unbekannt')
        
        reply = QMessageBox.question(
            self,
            "Löschen bestätigen",
            f"Menüpunkt '{label}' wirklich löschen?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Aus Matrix löschen
            gruppe_data = self.db.get_gruppe(self.gruppe)
            del gruppe_data[item_guid]
            
            # Liste neu laden
            self.load_items()
            
            logger.info(f"🗑️ Item gelöscht: {label} ({item_guid})")
    
    def _on_indent_item(self):
        """Item einrücken (unter vorherigem Item als Kind)"""
        current_item = self.list_widget.currentItem()
        if not current_item or not self.db:
            return
        
        current_row = self.list_widget.row(current_item)
        if current_row == 0:
            QMessageBox.warning(self, "Nicht möglich", "Erstes Item kann nicht eingerückt werden!")
            return
        
        # Vorheriges Item holen
        prev_item = self.list_widget.item(current_row - 1)
        prev_guid = prev_item.data(Qt.UserRole)
        
        # Aktuelles Item holen
        item_guid = current_item.data(Qt.UserRole)
        items = self.db.get_gruppe(self.gruppe)
        item_data = items[item_guid]
        
        # Parent setzen
        from pdvm_central_systemsteuerung import get_gcs
        gcs = get_gcs()
        if not gcs:
            logger.error("GCS nicht verfügbar!")
            return
        
        stichtag = gcs.st_inst.PdvmDateTime
        
        old_parent = item_data.get('parent_guid')
        item_data['parent_guid'] = prev_guid
        item_data['sort_order'] = 0  # Erstes Kind
        
        self.db.set_value(self.gruppe, item_guid, item_data, stichtag)
        self.mark_modified(item_guid)
        
        logger.info(f"→ Eingerückt: {item_data.get('label')} unter {items[prev_guid].get('label')}")
    
    def _on_outdent_item(self):
        """Item ausrücken (eine Ebene nach oben)"""
        current_item = self.list_widget.currentItem()
        if not current_item or not self.db:
            return
        
        item_guid = current_item.data(Qt.UserRole)
        items = self.db.get_gruppe(self.gruppe)
        item_data = items[item_guid]
        
        current_parent = item_data.get('parent_guid')
        if current_parent is None:
            QMessageBox.warning(self, "Nicht möglich", "Top-Level Item kann nicht weiter ausgerückt werden!")
            return
        
        # Großeltern ermitteln
        parent_data = items.get(current_parent)
        if not parent_data:
            logger.error(f"Parent {current_parent} nicht gefunden!")
            return
        
        grandparent_guid = parent_data.get('parent_guid')
        
        # Parent auf Großeltern setzen
        from pdvm_central_systemsteuerung import get_gcs
        gcs = get_gcs()
        if not gcs:
            logger.error("GCS nicht verfügbar!")
            return
        
        stichtag = gcs.st_inst.PdvmDateTime
        
        item_data['parent_guid'] = grandparent_guid
        
        # sort_order: Nach dem alten Parent einfügen
        siblings = [g for g, d in items.items() if d.get('parent_guid') == grandparent_guid]
        item_data['sort_order'] = len(siblings)
        
        self.db.set_value(self.gruppe, item_guid, item_data, stichtag)
        self.mark_modified(item_guid)
        
        logger.info(f"← Ausgerückt: {item_data.get('label')} (Parent: {current_parent} → {grandparent_guid})")
    
    def _on_items_reordered(self, parent, start, end, destination, row):
        """
        Items wurden per Drag & Drop verschoben
        EINFACHE LINEARE LOGIK:
        - Position in Liste = Reihenfolge
        - Einrückung = Parent
        - Kinder folgen automatisch (haben den Parent)
        """
        if not self.db:
            return
        
        try:
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            if not gcs:
                logger.error("GCS nicht verfügbar!")
                return
            
            stichtag = gcs.st_inst.PdvmDateTime
            items = self.db.get_gruppe(self.gruppe)
            
            # Für jedes Item in der Liste:
            # 1. Parent aus Einrückung ermitteln (Item darüber mit weniger Einrückung)
            # 2. Order zählen (wie viele Geschwister VOR diesem Item)
            
            last_parent_per_level = {-1: None}  # Level -1 = root (parent=None)
            parent_child_count = {}  # parent_guid → counter für order
            
            for index in range(self.list_widget.count()):
                list_item = self.list_widget.item(index)
                item_guid = list_item.data(Qt.UserRole)
                
                if item_guid not in items:
                    continue
                
                item_data = items[item_guid]
                
                # Level aus Einrückung ermitteln
                display_text = list_item.text()
                current_level = (len(display_text) - len(display_text.lstrip())) // 4
                
                # Parent = Letztes Item mit (current_level - 1)
                parent_guid = last_parent_per_level.get(current_level - 1)
                
                # Order = Wie viele Kinder hat dieser Parent schon?
                if parent_guid not in parent_child_count:
                    parent_child_count[parent_guid] = 0
                
                order = parent_child_count[parent_guid]
                parent_child_count[parent_guid] += 1
                
                # Änderungen?
                old_parent = item_data.get('parent_guid')
                old_order = item_data.get('sort_order', 0)
                
                changed = False
                
                if old_parent != parent_guid:
                    item_data['parent_guid'] = parent_guid
                    changed = True
                    logger.info(f"🔗 {item_data.get('label')}: Parent {old_parent} → {parent_guid}")
                
                if old_order != order:
                    item_data['sort_order'] = order
                    changed = True
                
                if changed:
                    self.db.set_value(self.gruppe, item_guid, item_data, stichtag)
                    self.mark_modified(item_guid)
                
                # Für nächstes Item: Dieses Item als möglichen Parent merken
                last_parent_per_level[current_level] = item_guid
            
            logger.info(f"🔄 {self.gruppe}: Hierarchie aktualisiert")
            self.items_reordered.emit(self.gruppe)
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Reordering: {e}", exc_info=True)


class PdvmMenuEditorSimple(QWidget):
    """
    🎯 Einfacher Menu-Editor - LINEAR & ROBUST
    
    - EINE DB-Instanz für alles
    - Matrix-Ansatz
    - Orange Rahmen für Änderungen
    - save_all_values() für alles auf einmal
    """
    
    def __init__(self, menu_guid: str, parent=None):
        super().__init__(parent)
        self.menu_guid = menu_guid
        
        # EINE Instanz für ALLE Daten!
        self.db = PdvmCentralDatenbank('sys_menudaten', menu_guid)
        self.db._load_data()
        
        self._init_ui()
        self._load_all_data()
        
        logger.info(f"🎯 Menu-Editor initialisiert für {menu_guid}")
    
    def _init_ui(self):
        """UI aufbauen"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Splitter: Links (Liste) | Rechts (Editor)
        splitter = QSplitter(Qt.Horizontal)
        
        # === LINKE SEITE: Tabs mit Listen ===
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Tabs
        self.tabs = QTabWidget()
        
        # Tab 1: VERTIKAL
        self.vertikal_list = MenuListWidget("VERTIKAL")
        self.vertikal_list.set_database(self.db)
        self.vertikal_list.item_selected.connect(self._on_item_selected)
        self.tabs.addTab(self.vertikal_list, "📌 Vertikalmenü")
        
        # Tab 2: GRUND
        self.grund_list = MenuListWidget("GRUND")
        self.grund_list.set_database(self.db)
        self.grund_list.item_selected.connect(self._on_item_selected)
        self.tabs.addTab(self.grund_list, "🏠 Grundmenü")
        
        # Tab 3: ZUSATZ (später)
        # self.zusatz_list = MenuListWidget("ZUSATZ")
        # ...
        
        left_layout.addWidget(self.tabs)
        
        # Speichern Button (UNTEN)
        self.btn_save = QPushButton("💾 ALLES SPEICHERN")
        self.btn_save.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold; padding: 10px; font-size: 14px;")
        self.btn_save.clicked.connect(self._save_all)
        left_layout.addWidget(self.btn_save)
        
        # === RECHTE SEITE: Editor ===
        self.editor = MenuItemEditor()
        self.editor.set_database(self.db)
        self.editor.item_changed.connect(self._on_item_changed)
        
        # Splitter zusammenbauen
        splitter.addWidget(left_widget)
        splitter.addWidget(self.editor)
        splitter.setSizes([600, 400])
        
        layout.addWidget(splitter)
    
    def _load_all_data(self):
        """Lädt Daten in alle Tabs"""
        self.vertikal_list.load_items()
        self.grund_list.load_items()
        # self.zusatz_list.load_items()
    
    def _on_item_selected(self, gruppe: str, item_guid: str):
        """Item in Liste ausgewählt → Editor laden"""
        self.editor.load_item(gruppe, item_guid)
    
    def _on_item_changed(self, item_guid: str):
        """Item geändert → Orange Rahmen"""
        # Aktuellen Tab ermitteln
        current_index = self.tabs.currentIndex()
        if current_index == 0:
            self.vertikal_list.mark_modified(item_guid)
        elif current_index == 1:
            self.grund_list.mark_modified(item_guid)
        
        logger.info(f"📝 Item geändert (nicht persistent): {item_guid}")
    
    def _save_all(self):
        """Speichert ALLES auf einmal"""
        try:
            # GCS holen
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            if not gcs:
                raise ValueError("GCS nicht verfügbar!")
            
            stichtag = gcs.st_inst.PdvmDateTime
            
            # Validierung: Leere Labels → "Unbekannt"
            for gruppe in ['VERTIKAL', 'GRUND']:
                items = self.db.get_gruppe(gruppe)
                for guid, item_data in items.items():
                    if not item_data.get('label', '').strip():
                        item_data['label'] = 'Unbekannt'
                        self.db.set_value(gruppe, guid, item_data, stichtag)
            
            # ALLES speichern
            self.db.save_all_values()
            
            # Orange Rahmen entfernen
            self.vertikal_list.clear_modified()
            self.grund_list.clear_modified()
            
            QMessageBox.information(self, "Gespeichert", "Alle Änderungen wurden gespeichert!")
            logger.info(f"✅ Alle Änderungen gespeichert für Menü: {self.menu_guid}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern: {e}", exc_info=True)
            QMessageBox.critical(self, "Fehler", f"Speichern fehlgeschlagen:\n{str(e)}")


# ============================================================================
# Factory-Funktion für Dialog-Integration
# ============================================================================

def create_menu_editor_widget(menu_guid: str, parent=None) -> PdvmMenuEditorSimple:
    """Factory-Funktion für Dialog-System"""
    return PdvmMenuEditorSimple(menu_guid, parent)
