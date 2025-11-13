"""
🎯 PDVM Menu-Editor - OPTIMIERTE VERSION
=========================================

KONZEPT (nach User-Feedback 12.11.2025):

1. EBENEN-LOGIK:
   - root = -1 (kein Parent)
   - Nur SUBMENU-Items können Parent sein
   - Drag & Drop: Item hängt sich IMMER an vorliegendes SUBMENU
   - Mapping: Parent-GUID → Ebene (linear & einfach)

2. NEUSORTIERUNG:
   - Bei Ebenen-Wechsel: Alte + Neue Ebene neu sortieren
   - Automatisch beim Drag & Drop
   - Redundante Sortierung vor save_all() ENTFERNT

3. GCS-NUTZUNG (MINIMAL):
   - Nur Stichtag: gcs.st_inst.PdvmDateTime
   - Nur AB-Datum Formatierung
   - KEIN Template-System (nicht nötig im Editor)

4. AUTONOMIE:
   - Eigene PdvmCentralDatenbank Instanz
   - Keine Vermischung mit GCS-Menu-System
   - Editor rendert Menu nur zur Darstellung (kein Handler-Aufruf)

Autor: PDVM V2.0
Datum: 12.11.2025
"""

import logging
import uuid
from typing import Dict, Set, Optional, Any, List, Tuple
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QListWidget, QListWidgetItem, QPushButton, QTabWidget,
    QLabel, QLineEdit, QComboBox, QTextEdit, QFormLayout,
    QGroupBox, QMessageBox, QFrame, QDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor

from pdvm_central_datenbank import PdvmCentralDatenbank

logger = logging.getLogger(__name__)


# ============================================================================
# HILFSFUNKTIONEN
# ============================================================================

def resort_parent_children(items: Dict[str, Any], parent_guid: Optional[str], 
                          stichtag: float, db: PdvmCentralDatenbank) -> None:
    """
    Sortiert alle Kinder eines Parents neu (sort_order = 0, 1, 2, ...)
    
    Args:
        items: Alle Items der Gruppe
        parent_guid: Parent dessen Kinder sortiert werden
        stichtag: Aktueller Stichtag
        db: Datenbank-Instanz
    """
    # Kinder finden
    children = [
        (guid, data) for guid, data in items.items() 
        if data.get('parent_guid') == parent_guid
    ]
    
    # Nach sort_order sortieren
    children.sort(key=lambda x: x[1].get('sort_order', 0))
    
    # Neu nummerieren
    for index, (guid, data) in enumerate(children):
        if data.get('sort_order') != index:
            data['sort_order'] = index
            gruppe = data.get('_gruppe', 'VERTIKAL')  # Gruppe merken!
            db.set_value(gruppe, guid, data, stichtag)
            logger.debug(f"  ↻ {data.get('label')}: sort_order → {index}")


# ============================================================================
# MENÜ-ITEM EDITOR (Rechte Seite)
# ============================================================================

class MenuItemEditor(QFrame):
    """
    Editor für einzelnes Menü-Item
    Schreibt direkt in Datenbank via set_value()
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
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        form.addRow("Typ:", self.type_combo)
        
        # Label
        self.label_edit = QLineEdit()
        self.label_edit.setPlaceholderText("z.B. 'Datei öffnen'")
        form.addRow("Label:", self.label_edit)
        
        # Handler (nur bei BUTTON)
        self.handler_edit = QLineEdit()
        self.handler_edit.setPlaceholderText("z.B. 'open_view'")
        self.handler_label = QLabel("Handler:")
        form.addRow(self.handler_label, self.handler_edit)
        
        # Tooltip
        self.tooltip_edit = QLineEdit()
        self.tooltip_edit.setPlaceholderText("Tooltip-Text (optional)")
        form.addRow("Tooltip:", self.tooltip_edit)
        
        # Params (JSON) - nur bei BUTTON
        self.params_edit = QTextEdit()
        self.params_edit.setPlaceholderText('{"view_guid": "..."}')
        self.params_edit.setMaximumHeight(80)
        self.params_label = QLabel("Parameter:")
        form.addRow(self.params_label, self.params_edit)
        
        # Template-GUID (nur bei SPACER) - mit Auswahl-Button
        template_layout = QHBoxLayout()
        self.template_edit = QLineEdit()
        self.template_edit.setPlaceholderText("Template-GUID für Spacer")
        self.template_edit.setReadOnly(True)  # Nur über Button änderbar
        template_layout.addWidget(self.template_edit)
        
        self.btn_select_template = QPushButton("📋 Auswählen")
        self.btn_select_template.clicked.connect(self._on_select_template)
        template_layout.addWidget(self.btn_select_template)
        
        self.template_label = QLabel("Template:")
        form.addRow(self.template_label, template_layout)
        
        layout.addLayout(form)
        
        # Übernehmen Button
        self.btn_apply = QPushButton("✅ Übernehmen")
        self.btn_apply.setStyleSheet(
            "background-color: #4CAF50; color: white; "
            "font-weight: bold; padding: 8px;"
        )
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
    
    def _on_select_template(self):
        """Öffnet Dialog zur Template-Auswahl (View-basiert)"""
        try:
            logger.info("📋 Öffne Template-Auswahl-Dialog...")
            
            from pdvm_input_viewtable_selection_dialog import PdvmInputViewtableSelectionDialog
            from PyQt5.QtWidgets import QDialog
            
            # Template-View GUID (vom User vorgegeben)
            TEMPLATE_VIEW_GUID = "8746d0cc-6acb-4f14-a7cb-3d48f97b0751"
            
            # Dialog öffnen
            dialog = PdvmInputViewtableSelectionDialog(
                viewtable_guid=TEMPLATE_VIEW_GUID,
                current_guid=self.template_edit.text().strip() or None,
                parent=self
            )
            
            result = dialog.exec_()
            
            # Auswahl übernehmen
            if result == QDialog.Accepted and dialog.selected_guid:
                self.template_edit.setText(dialog.selected_guid)
                logger.info(f"✅ Template gewählt: {dialog.selected_guid[:20]}...")
            else:
                logger.info("ℹ️ Template-Auswahl abgebrochen")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Öffnen des Template-Dialogs: {e}", exc_info=True)
    
    def _set_enabled(self, enabled: bool):
        """Aktiviert/Deaktiviert Editor"""
        self.type_combo.setEnabled(enabled)
        self.label_edit.setEnabled(enabled)
        self.handler_edit.setEnabled(enabled)
        self.tooltip_edit.setEnabled(enabled)
        self.params_edit.setEnabled(enabled)
        self.template_edit.setEnabled(enabled)
        self.btn_select_template.setEnabled(enabled)
        self.btn_apply.setEnabled(enabled)
    
    def _on_type_changed(self, index: int):
        """Type geändert → Handler/Params/Template ein/ausblenden"""
        type_map = ['BUTTON', 'SUBMENU', 'SEPARATOR', 'SPACER']
        item_type = type_map[index]
        
        # Handler/Params nur bei BUTTON
        show_command = (item_type == 'BUTTON')
        self.handler_label.setVisible(show_command)
        self.handler_edit.setVisible(show_command)
        self.params_label.setVisible(show_command)
        self.params_edit.setVisible(show_command)
        
        # Template nur bei SPACER
        show_template = (item_type == 'SPACER')
        self.template_label.setVisible(show_template)
        self.template_edit.setVisible(show_template)
        self.btn_select_template.setVisible(show_template)
    
    def set_database(self, db: PdvmCentralDatenbank):
        """Setzt Datenbank-Instanz"""
        self.db = db
    
    def load_item(self, gruppe: str, item_guid: str):
        """Lädt Item aus Datenbank"""
        if not self.db:
            logger.warning("⚠️ Keine Datenbank gesetzt!")
            return
        
        self.current_gruppe = gruppe
        self.current_guid = item_guid
        
        try:
            # Item aus DB holen
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
                self.params_edit.setPlainText(
                    json.dumps(params, indent=2, ensure_ascii=False) if params else ''
                )
            else:
                self.handler_edit.clear()
                self.params_edit.clear()
            
            # Template-GUID
            template_guid = item_data.get('template_guid', '')
            self.template_edit.setText(template_guid if template_guid else '')
            
            self._set_enabled(True)
            self.info_label.setText(f"📋 Bearbeite: {item_data.get('label', 'N/A')}")
            
            logger.info(f"✅ Editor geladen: {item_data.get('label')} (GUID={item_guid})")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden: {e}", exc_info=True)
            self.info_label.setText(f"❌ Fehler: {str(e)}")
    
    def _apply_changes(self):
        """Übernimmt Änderungen in Datenbank"""
        if not self.db or not self.current_gruppe or not self.current_guid:
            return
        
        try:
            # GCS für Stichtag holen
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            if not gcs:
                raise ValueError("GCS nicht verfügbar - Login erforderlich!")
            
            stichtag = gcs.st_inst.PdvmDateTime
            
            # Aktuelles Item holen
            item_data = self.db.get_static_value(self.current_gruppe, self.current_guid)
            
            # Type auslesen
            type_map = ['BUTTON', 'SUBMENU', 'SEPARATOR', 'SPACER']
            old_type = item_data.get('type')
            new_type = type_map[self.type_combo.currentIndex()]
            item_data['type'] = new_type
            
            # Felder aktualisieren
            item_data['label'] = self.label_edit.text().strip() or 'Unbekannt'
            item_data['tooltip'] = self.tooltip_edit.text().strip() or None
            
            # Command (nur bei BUTTON)
            if new_type == 'BUTTON':
                handler = self.handler_edit.text().strip()
                if handler:
                    import json
                    params_text = self.params_edit.toPlainText().strip()
                    try:
                        params = json.loads(params_text) if params_text else {}
                    except json.JSONDecodeError as je:
                        QMessageBox.warning(
                            self, "JSON-Fehler", 
                            f"Parameter sind kein gültiges JSON:\n{str(je)}"
                        )
                        return
                    
                    item_data['command'] = {
                        'handler': handler,
                        'params': params
                    }
                else:
                    item_data['command'] = None
            else:
                item_data['command'] = None
            
            # Template-GUID (nur bei SPACER)
            if new_type == 'SPACER':
                template_guid = self.template_edit.text().strip()
                item_data['template_guid'] = template_guid if template_guid else None
            else:
                item_data['template_guid'] = None
            
            # KRITISCH: Wenn von SUBMENU zu anderem Typ gewechselt
            # → Alle Kinder zu Parent verschieben!
            if old_type == 'SUBMENU' and new_type != 'SUBMENU':
                self._move_children_to_parent(item_data)
            
            # In DB schreiben
            self.db.set_value(self.current_gruppe, self.current_guid, item_data, stichtag)
            
            # Signal für orange Rahmen + Reload
            self.item_changed.emit(self.current_guid)
            
            self.info_label.setText(f"✅ Übernommen (noch nicht gespeichert!)")
            logger.info(f"✅ Item geändert: {item_data['label']} (GUID={self.current_guid})")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Übernehmen: {e}", exc_info=True)
            QMessageBox.critical(self, "Fehler", f"Übernehmen fehlgeschlagen:\n{str(e)}")
    
    def _move_children_to_parent(self, item_data: Dict):
        """
        Verschiebt alle Kinder dieses Items zum Großeltern
        (wenn Item von SUBMENU zu anderem Typ wechselt)
        """
        item_guid = self.current_guid
        parent_guid = item_data.get('parent_guid')
        
        # Alle Items der Gruppe holen
        items = self.db.get_gruppe(self.current_gruppe)
        
        # Kinder finden
        children = [
            (guid, data) for guid, data in items.items()
            if data.get('parent_guid') == item_guid
        ]
        
        if not children:
            return
        
        logger.info(f"↗️ Verschiebe {len(children)} Kinder von {item_data.get('label')} zum Parent")
        
        # GCS für Stichtag
        from pdvm_central_systemsteuerung import get_gcs
        gcs = get_gcs()
        stichtag = gcs.st_inst.PdvmDateTime
        
        # Kinder verschieben
        for child_guid, child_data in children:
            child_data['parent_guid'] = parent_guid
            self.db.set_value(self.current_gruppe, child_guid, child_data, stichtag)
        
        # Beide Ebenen neu sortieren
        resort_parent_children(items, item_guid, stichtag, self.db)  # Alte Ebene
        resort_parent_children(items, parent_guid, stichtag, self.db)  # Neue Ebene


# ============================================================================
# MENÜ-LISTE (Linke Seite mit Drag & Drop)
# ============================================================================

class MenuListWidget(QWidget):
    """
    Liste für eine Gruppe (VERTIKAL/GRUND/ZUSATZ)
    
    Zeigt Items hierarchisch mit Einrückung
    Drag & Drop → Automatische Parent-Zuordnung + Neusortierung
    """
    
    item_selected = pyqtSignal(str, str)  # gruppe, guid
    items_changed = pyqtSignal()  # Items geändert → Reload nötig
    
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
        
        # Header
        header = QLabel(f"📋 {self.gruppe}")
        header.setStyleSheet("font-weight: bold; font-size: 12px; padding: 5px;")
        layout.addWidget(header)
        
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
        
        # Buttons (NUR Neu + Löschen - KEIN Einrücken/Ausrücken!)
        btn_layout = QHBoxLayout()
        
        self.btn_add = QPushButton("➕ Neu")
        self.btn_add.clicked.connect(self._on_add_item)
        btn_layout.addWidget(self.btn_add)
        
        self.btn_delete = QPushButton("🗑️ Löschen")
        self.btn_delete.clicked.connect(self._on_delete_item)
        self.btn_delete.setEnabled(False)
        btn_layout.addWidget(self.btn_delete)
        
        btn_layout.addStretch()  # Links ausrichten
        
        layout.addLayout(btn_layout)
    
    def set_database(self, db: PdvmCentralDatenbank):
        """Setzt Datenbank-Instanz"""
        self.db = db
    
    def load_items(self):
        """Lädt Items aus Datenbank"""
        if not self.db:
            return
        
        self.list_widget.clear()
        
        try:
            # Gruppe aus DB holen
            items = self.db.get_gruppe(self.gruppe)
            
            if not items:
                logger.info(f"📋 {self.gruppe}: Keine Items vorhanden")
                return
            
            # Hierarchisch sortieren (OHNE Parent-Level-Mapping!)
            sorted_items = self._build_hierarchy(items)
            
            # In Liste einfügen
            for item_guid, item_data, level in sorted_items:
                self._add_list_item(item_guid, item_data, level)
            
            logger.info(f"✅ {self.gruppe}: {len(items)} Items geladen")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden von {self.gruppe}: {e}", exc_info=True)
    
    def _build_hierarchy(self, items: Dict[str, Any]) -> List[Tuple[str, Dict, int]]:
        """
        Baut hierarchische Liste
        
        EINFACHE REGEL:
        - Level wird aus Parent-Hierarchie berechnet
        - Keine Unterscheidung nach Type
        
        Returns:
            Liste von (item_guid, item_data, level)
        """
        result = []
        
        def add_with_children(item_guid, item_data, level=0):
            result.append((item_guid, item_data, level))
            
            # Kinder finden (egal welcher Type!)
            children = [
                (g, d) for g, d in items.items() 
                if d.get('parent_guid') == item_guid
            ]
            children.sort(key=lambda x: x[1].get('sort_order', 0))
            
            # Kinder rekursiv mit level+1
            for child_guid, child_data in children:
                add_with_children(child_guid, child_data, level + 1)
        
        # Top-Level Items (parent_guid = None)
        top_level = [
            (g, d) for g, d in items.items() 
            if d.get('parent_guid') is None
        ]
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
        list_item.setData(Qt.UserRole + 1, level)
        list_item.setData(Qt.UserRole + 2, item_data.get('parent_guid'))
        
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
        self.load_items()  # Neu laden um Farbe zu zeigen
    
    def clear_modified(self):
        """Entfernt alle Änderungs-Markierungen"""
        self.modified_guids.clear()
        self.load_items()
    
    def _on_selection_changed(self, current, previous):
        """Item ausgewählt"""
        if current:
            item_guid = current.data(Qt.UserRole)
            self.btn_delete.setEnabled(True)
            
            self.item_selected.emit(self.gruppe, item_guid)
        else:
            self.btn_delete.setEnabled(False)
    
    def _on_add_item(self):
        """Neues Item hinzufügen"""
        if not self.db:
            return
        
        try:
            # GCS für Stichtag
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            if not gcs:
                raise ValueError("GCS nicht verfügbar!")
            
            stichtag = gcs.st_inst.PdvmDateTime
            
            # Neue GUID generieren
            new_guid = str(uuid.uuid4())
            
            # sort_order = Anzahl Top-Level Items (parent_guid = None)
            items = self.db.get_gruppe(self.gruppe)
            top_level_count = len([
                d for d in items.values() 
                if d is not None and d.get('parent_guid') is None
            ])
            
            # Neues Item erstellen (IMMER in Root!)
            new_item = {
                'guid': new_guid,
                'type': 'BUTTON',
                'label': 'Neuer Menüpunkt',
                'icon': None,
                'command': None,
                'parent_guid': None,  # IMMER Root!
                'sort_order': top_level_count,
                'visible': True,
                'enabled': True,
                'tooltip': None,
                '_gruppe': self.gruppe
            }
            
            # In DB schreiben
            self.db.set_value(self.gruppe, new_guid, new_item, stichtag)
            
            # Als geändert markieren
            self.mark_modified(new_guid)
            
            # Signal aussenden
            self.items_changed.emit()
            
            logger.info(f"➕ Neues Item erstellt: {new_guid}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen: {e}", exc_info=True)
            QMessageBox.critical(self, "Fehler", f"Item konnte nicht erstellt werden:\n{str(e)}")
    
    def _on_delete_item(self):
        """Aktuelles Item löschen"""
        current_item = self.list_widget.currentItem()
        if not current_item or not self.db:
            return
        
        item_guid = current_item.data(Qt.UserRole)
        items = self.db.get_gruppe(self.gruppe)
        item_data = items.get(item_guid)
        
        if not item_data:
            return
        
        label = item_data.get('label', 'Unbekannt')
        item_type = item_data.get('type', 'BUTTON')
        
        # SICHERHEITSPRÜFUNG: Prüfen ob Kinder vorhanden (besonders bei SUBMENU!)
        children = [
            d for d in items.values() 
            if d is not None and d.get('parent_guid') == item_guid
        ]
        
        if children:
            child_labels = [c.get('label', 'Unbekannt') for c in children[:3]]
            child_info = ', '.join(child_labels)
            if len(children) > 3:
                child_info += f" (+{len(children)-3} weitere)"
            
            QMessageBox.warning(
                self,
                "Löschen nicht möglich",
                f"Menüpunkt '{label}' ({item_type}) hat {len(children)} Unter-Items:\n\n"
                f"{child_info}\n\n"
                "Bitte zuerst alle Unter-Items löschen oder verschieben."
            )
            return
        
        # SICHERHEITSABFRAGE
        reply = QMessageBox.question(
            self,
            "Löschen bestätigen",
            f"Menüpunkt '{label}' ({item_type}) wirklich löschen?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # GCS für Stichtag
                from pdvm_central_systemsteuerung import get_gcs
                gcs = get_gcs()
                if not gcs:
                    raise ValueError("GCS nicht verfügbar!")
                
                stichtag = gcs.st_inst.PdvmDateTime
                parent_guid = item_data.get('parent_guid')
                
                # SAUBER LÖSCHEN mit delete_field() statt set_value(None)
                self.db.delete_field(self.gruppe, item_guid)
                
                # Parent-Ebene neu sortieren (Lücken schließen)
                items = self.db.get_gruppe(self.gruppe)  # Neu holen nach delete
                resort_parent_children(items, parent_guid, stichtag, self.db)
                
                # Liste neu laden
                self.load_items()
                
                # Signal aussenden
                self.items_changed.emit()
                
                logger.info(f"🗑️ Item gelöscht: {label} ({item_type}, GUID={item_guid})")
                
            except Exception as e:
                logger.error(f"❌ Fehler beim Löschen: {e}", exc_info=True)
                QMessageBox.critical(self, "Fehler", f"Löschen fehlgeschlagen:\n{str(e)}")
    
    def _on_items_reordered(self, parent, start, end, destination, row):
        """
        Items wurden per Drag & Drop verschoben
        
        MINI-PIPELINE (LINEAR & VORHERSAGBAR):
        1. Verschobenes Item + alten Parent merken
        2. Neuen Parent basierend auf Position ermitteln (SUBMENU-Regel)
        3. Item mit neuem Parent in DB schreiben
        4. sort_order für alte + neue Parent-Ebene neu nummerieren
        5. Liste LÖSCHEN und NEU RENDERN aus DB
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
            
            # 1. VERSCHOBENES ITEM + ALTER PARENT
            moved_row = row if row < start else row - 1
            moved_item = self.list_widget.item(moved_row)
            
            if not moved_item:
                return
            
            moved_guid = moved_item.data(Qt.UserRole)
            moved_data = items.get(moved_guid)
            
            if not moved_data:
                return
            
            old_parent = moved_data.get('parent_guid')
            
            # 2. NEUER PARENT (basierend auf Position)
            new_parent = None
            
            if moved_row > 0:
                prev_item = self.list_widget.item(moved_row - 1)
                prev_guid = prev_item.data(Qt.UserRole)
                prev_data = items.get(prev_guid)
                
                if prev_data:
                    prev_type = prev_data.get('type')
                    
                    # SUBMENU-REGEL: SUBMENU direkt darüber → Parent = SUBMENU
                    if prev_type == 'SUBMENU':
                        new_parent = prev_guid
                    else:
                        new_parent = prev_data.get('parent_guid')
            
            # 3. ITEM MIT NEUEM PARENT IN DB SCHREIBEN
            if old_parent != new_parent:
                logger.info(
                    f"🔗 {moved_data.get('label')}: "
                    f"Parent {old_parent} → {new_parent}"
                )
                moved_data['parent_guid'] = new_parent
                moved_data['_gruppe'] = self.gruppe
                self.db.set_value(self.gruppe, moved_guid, moved_data, stichtag)
                self.mark_modified(moved_guid)
            
            # 4. SORT_ORDER FÜR ALTE + NEUE EBENE NEU NUMMERIEREN
            if old_parent != new_parent:
                # Beide Ebenen neu sortieren
                resort_parent_children(items, old_parent, stichtag, self.db)
                resort_parent_children(items, new_parent, stichtag, self.db)
            else:
                # Gleicher Parent → Nur eine Ebene sortieren
                resort_parent_children(items, old_parent, stichtag, self.db)
            
            # 5. LISTE NEU LADEN (rendert Hierarchie aus DB)
            self.load_items()
            
            # Signal aussenden
            self.items_changed.emit()
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Reordering: {e}", exc_info=True)


# ============================================================================
# HAUPT-WIDGET
# ============================================================================

class PdvmMenuEditorOptimized(QWidget):
    """
    🎯 Menu-Editor - OPTIMIERT nach User-Feedback
    
    Features:
    - 2 Tabs: VERTIKAL, GRUND
    - Nur SUBMENU kann Parent sein
    - Drag & Drop → Automatische Parent-Zuordnung
    - Neusortierung bei Ebenen-Wechsel
    - Minimale GCS-Nutzung (nur Stichtag + AB-Datum)
    """
    
    def __init__(self, menu_guid: str, parent=None):
        super().__init__(parent)
        self.menu_guid = menu_guid
        
        # GCS für minimale Nutzung (Stichtag)
        from pdvm_central_systemsteuerung import get_gcs
        self.gcs = get_gcs()
        if not self.gcs:
            raise ValueError("GCS nicht verfügbar - Login erforderlich!")
        
        # AUTONOME DB-Instanz
        self.db = PdvmCentralDatenbank('sys_menudaten', menu_guid)
        self.db._load_data()
        
        self._init_ui()
        self._load_all_data()
        
        logger.info(f"🎯 Menu-Editor (optimiert) initialisiert für {menu_guid}")
    
    def _init_ui(self):
        """UI aufbauen"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Splitter: Links (Tabs mit Listen) | Rechts (Editor)
        splitter = QSplitter(Qt.Horizontal)
        
        # === LINKE SEITE: Tabs + Listen ===
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Tabs
        self.tabs = QTabWidget()
        
        # Tab 1: VERTIKAL
        self.vertikal_list = MenuListWidget("VERTIKAL")
        self.vertikal_list.set_database(self.db)
        self.vertikal_list.item_selected.connect(self._on_item_selected)
        self.vertikal_list.items_changed.connect(self._on_items_changed)
        self.tabs.addTab(self.vertikal_list, "📌 Vertikalmenü")
        
        # Tab 2: GRUND
        self.grund_list = MenuListWidget("GRUND")
        self.grund_list.set_database(self.db)
        self.grund_list.item_selected.connect(self._on_item_selected)
        self.grund_list.items_changed.connect(self._on_items_changed)
        self.tabs.addTab(self.grund_list, "🏠 Grundmenü")
        
        left_layout.addWidget(self.tabs)
        
        # Speichern Button (UNTEN)
        self.btn_save = QPushButton("💾 ALLES SPEICHERN")
        self.btn_save.setStyleSheet(
            "background-color: #2196F3; color: white; "
            "font-weight: bold; padding: 10px; font-size: 14px;"
        )
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
    
    def _on_item_selected(self, gruppe: str, item_guid: str):
        """Item in Liste ausgewählt → Editor laden"""
        self.editor.load_item(gruppe, item_guid)
    
    def _on_item_changed(self, item_guid: str):
        """Item geändert → Orange Rahmen + Reload"""
        # Aktuellen Tab ermitteln
        current_index = self.tabs.currentIndex()
        if current_index == 0:
            self.vertikal_list.mark_modified(item_guid)
        elif current_index == 1:
            self.grund_list.mark_modified(item_guid)
        
        logger.info(f"📝 Item geändert (nicht persistent): {item_guid}")
    
    def _on_items_changed(self):
        """Items wurden geändert (Drag & Drop, Ein/Ausrücken, etc.)"""
        # Aktuellen Tab neu laden
        current_index = self.tabs.currentIndex()
        if current_index == 0:
            self.vertikal_list.load_items()
        elif current_index == 1:
            self.grund_list.load_items()
    
    def _save_all(self):
        """
        Speichert ALLES auf einmal
        
        KEINE redundante Sortierung mehr!
        (sort_order ist bereits durch Drag & Drop korrekt)
        """
        try:
            stichtag = self.gcs.st_inst.PdvmDateTime
            
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
            
            # NEU LADEN (für Sicherheit)
            self._load_all_data()
            
            QMessageBox.information(
                self, "Gespeichert", 
                "Alle Änderungen wurden erfolgreich gespeichert!"
            )
            
            logger.info(f"✅ Alle Änderungen gespeichert für Menü: {self.menu_guid}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern: {e}", exc_info=True)
            QMessageBox.critical(
                self, "Fehler", 
                f"Speichern fehlgeschlagen:\n{str(e)}"
            )


# ============================================================================
# DIALOG-WRAPPER
# ============================================================================

class PdvmMenuEditorDialog(QDialog):
    """Dialog-Wrapper für Menu-Editor"""
    
    menu_saved = pyqtSignal(str)
    
    def __init__(self, menu_guid: str, parent=None):
        super().__init__(parent)
        self.menu_guid = menu_guid
        self.setWindowTitle("Menu-Editor")
        self.setModal(True)
        self.resize(1200, 800)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Editor Widget
        self.editor_widget = PdvmMenuEditorOptimized(menu_guid, self)
        layout.addWidget(self.editor_widget)
        
        logger.info(f"🎯 Menu-Editor Dialog geöffnet: {menu_guid}")


# ============================================================================
# FACTORY-FUNKTIONEN
# ============================================================================

def create_menu_editor_widget(menu_guid: str, parent=None) -> PdvmMenuEditorOptimized:
    """Factory-Funktion für Widget"""
    return PdvmMenuEditorOptimized(menu_guid, parent)


def create_menu_editor_dialog(menu_guid: str, parent=None) -> PdvmMenuEditorDialog:
    """Factory-Funktion für Dialog"""
    return PdvmMenuEditorDialog(menu_guid, parent)


# ============================================================================
# MAIN (nur für Tests)
# ============================================================================

if __name__ == "__main__":
    print("🧪 PdvmMenuEditorOptimized Test")
    print("=" * 60)
    print("Dieser Editor kann nur in der Anwendung getestet werden.")
    print("\nOptimierungen:")
    print("✅ Nur SUBMENU kann Parent sein")
    print("✅ Drag & Drop → Auto Parent-Zuordnung")
    print("✅ Neusortierung bei Ebenen-Wechsel")
    print("✅ Minimale GCS-Nutzung (Stichtag + AB-Datum)")
    print("✅ Keine redundante Sortierung vor save_all()")
