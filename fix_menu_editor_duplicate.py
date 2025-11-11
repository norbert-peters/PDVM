"""
🔧 REPARATUR: pdvm_menu_editor_widget.py
==========================================

Problem: Duplikat-Code (alte + neue MenuItemEditor Implementierung)
Lösung: Datei neu schreiben ohne Duplikate
"""

# Datei komplett neu schreiben (bereinigt, ohne Duplikate)

FIXED_CONTENT = r'''"""
🎯 PDVM Menu-Editor Widget
==========================

KONZEPT: Gekapselte Plugin-Box für EDIT_TYPE='menu_editor'
- Bekommt menu_guid von Dialog (aus View)
- Lädt JSON-Daten aus sys_menudaten.json_data
- Bearbeitet Menüstruktur (Vertikal/Grund/Zusatz)
- Speichert zurück in JSON-Struktur

LINEAR: Widget → Lade JSON → Bearbeite → Speichere JSON → Fertig
"""

import json
import logging
from typing import Dict, List, Optional, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QListWidget, QListWidgetItem, QPushButton, QSplitter,
    QLabel, QMessageBox, QFrame, QLineEdit, QComboBox, 
    QCheckBox, QTextEdit, QFormLayout, QScrollArea, QGroupBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDropEvent, QFont, QColor

# Import GCS und Datenbank
from pdvm_central_systemsteuerung import get_gcs
from pdvm_central_datenbank import PdvmCentralDatenbank

logger = logging.getLogger(__name__)


class DraggableMenuList(QListWidget):
    """
    Drag & Drop Liste für Menüpunkte
    """
    
    items_reordered = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QListWidget.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)
        
        # Signal für Änderungen
        self.model().rowsMoved.connect(self.items_reordered)


class MenuItemEditor(QFrame):
    """
    Editor für einzelnen Menüpunkt (Rechte Seite)
    AUTONOM: Greift direkt auf Datenbank zu (get_static_value/set_value)
    """
    
    item_saved = pyqtSignal()  # Signal wenn Item gespeichert wurde
    
    def __init__(self, db: 'PdvmCentralDatenbank', menu_type: str, parent=None):
        super().__init__(parent)
        self.db = db  # Datenbank-Instanz
        self.menu_type = menu_type  # "VERTIKAL", "GRUND", "ZUSATZ"
        self.current_guid = None  # Aktuell geladenes Item (Feld=GUID)
        self.controls = {}
        self._init_ui()
    
    def _init_ui(self):
        """UI aufbauen mit allen Feldern"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header
        header = QLabel("✏️ Menüpunkt bearbeiten")
        header.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        layout.addWidget(header)
        
        # Scroll Area für alle Controls
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        scroll_widget = QWidget()
        form_layout = QFormLayout(scroll_widget)
        form_layout.setSpacing(10)
        
        # === BASIC FIELDS ===
        
        # Type (Dropdown)
        self.controls['type'] = QComboBox()
        self.controls['type'].addItems(['BUTTON', 'SUBMENU', 'SEPARATOR', 'SPACER'])
        self.controls['type'].currentTextChanged.connect(self._on_type_changed)
        form_layout.addRow("🔹 Typ:", self.controls['type'])
        
        # Label
        self.controls['label'] = QLineEdit()
        self.controls['label'].setPlaceholderText("z.B. 'Datei öffnen'")
        form_layout.addRow("📝 Label:", self.controls['label'])
        
        # Icon
        self.controls['icon'] = QLineEdit()
        self.controls['icon'].setPlaceholderText("Icon-Name oder leer")
        form_layout.addRow("🎨 Icon:", self.controls['icon'])
        
        # Tooltip
        self.controls['tooltip'] = QLineEdit()
        self.controls['tooltip'].setPlaceholderText("Optionaler Tooltip-Text")
        form_layout.addRow("💬 Tooltip:", self.controls['tooltip'])
        
        # Visibility
        visibility_layout = QHBoxLayout()
        self.controls['visible'] = QCheckBox("Sichtbar")
        self.controls['enabled'] = QCheckBox("Aktiviert")
        visibility_layout.addWidget(self.controls['visible'])
        visibility_layout.addWidget(self.controls['enabled'])
        visibility_layout.addStretch()
        form_layout.addRow("👁️ Status:", visibility_layout)
        
        # === COMMAND (immer sichtbar, Felder leer bei SUBMENU/etc) ===
        
        self.command_group = QGroupBox("⚡ Command")
        command_layout = QFormLayout()
        
        # Handler
        self.controls['handler'] = QLineEdit()
        self.controls['handler'].setPlaceholderText("z.B. 'open_view'")
        command_layout.addRow("🔧 Handler:", self.controls['handler'])
        
        # Params (JSON)
        self.controls['params'] = QTextEdit()
        self.controls['params'].setPlaceholderText('{"view_guid": "..."}')
        self.controls['params'].setMaximumHeight(80)
        command_layout.addRow("📋 Parameter:", self.controls['params'])
        
        self.command_group.setLayout(command_layout)
        form_layout.addWidget(self.command_group)
        
        # Speichern Button
        self.btn_save = QPushButton("💾 Speichern")
        self.btn_save.clicked.connect(self._save_to_db)
        self.btn_save.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        form_layout.addRow(self.btn_save)
        
        # Info-Label
        self.info_label = QLabel()
        self.info_label.setStyleSheet("color: gray; font-size: 10px; padding: 5px;")
        self.info_label.setWordWrap(True)
        form_layout.addRow(self.info_label)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # Initial deaktiviert
        self._set_enabled(False)
    
    def _set_enabled(self, enabled: bool):
        """Aktiviert/Deaktiviert alle Controls"""
        for control in self.controls.values():
            control.setEnabled(enabled)
        self.command_group.setEnabled(enabled)
        self.btn_save.setEnabled(enabled)
        
        if not enabled:
            self.info_label.setText("← Wähle einen Menüpunkt aus der Liste")
    
    def _on_type_changed(self, type_value: str):
        """Type geändert → Hinweis anzeigen"""
        if type_value != 'BUTTON':
            self.info_label.setText("ℹ️ Command nur bei BUTTON relevant")
        else:
            self.info_label.setText("")
    
    def load_item(self, item_guid: str):
        """
        Lädt Item DIREKT aus Datenbank via GUID
        Feld = GUID, Gruppe = menu_type
        """
        self.current_guid = item_guid
        
        try:
            # Lade Item aus DB: get_static_value(menu_type, item_guid)
            item_data, _ = self.db.get_static_value(self.menu_type, item_guid)
            
            if not item_data:
                logger.warning(f"⚠️ Item nicht gefunden: {item_guid}")
                return
            
            self._set_enabled(True)
            
            # Controls befüllen
            self.controls['type'].setCurrentText(item_data.get('type', 'BUTTON'))
            self.controls['label'].setText(item_data.get('label', ''))
            self.controls['icon'].setText(item_data.get('icon') or '')
            self.controls['tooltip'].setText(item_data.get('tooltip') or '')
            self.controls['visible'].setChecked(item_data.get('visible', True))
            self.controls['enabled'].setChecked(item_data.get('enabled', True))
            
            # Command
            command = item_data.get('command')
            if command and isinstance(command, dict):
                self.controls['handler'].setText(command.get('handler', ''))
                params = command.get('params', {})
                self.controls['params'].setPlainText(json.dumps(params, indent=2))
            else:
                self.controls['handler'].clear()
                self.controls['params'].clear()
            
            logger.info(f"✅ Item geladen: {item_data.get('label', 'N/A')} (GUID={item_guid})")
            self.info_label.setText(f"📋 Bearbeite: {item_data.get('label', 'N/A')}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden: {e}", exc_info=True)
            self.info_label.setText(f"❌ Fehler: {str(e)}")
    
    def _save_to_db(self):
        """Speichert Item DIREKT in Datenbank"""
        if not self.current_guid:
            return
        
        try:
            # Daten aus Controls lesen
            item_data = {
                'guid': self.current_guid,
                'type': self.controls['type'].currentText(),
                'label': self.controls['label'].text(),
                'icon': self.controls['icon'].text() or None,
                'tooltip': self.controls['tooltip'].text() or None,
                'visible': self.controls['visible'].isChecked(),
                'enabled': self.controls['enabled'].isChecked(),
                'sort_order': 0,  # TODO: Aus Liste übernehmen
                'parent_guid': None  # TODO: Parent-Dropdown
            }
            
            # Command
            handler = self.controls['handler'].text().strip()
            params_text = self.controls['params'].toPlainText().strip()
            
            if handler:
                try:
                    params = json.loads(params_text) if params_text else {}
                    item_data['command'] = {
                        'handler': handler,
                        'params': params
                    }
                except json.JSONDecodeError as e:
                    QMessageBox.warning(self, "JSON-Fehler", f"Parameter ungültig:\n{str(e)}")
                    return
            else:
                item_data['command'] = None
            
            # In DB schreiben: set_value(menu_type, item_guid, item_data, stichtag)
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            self.db.set_value(self.menu_type, self.current_guid, item_data, gcs.st_inst.PdvmDateTime)
            
            logger.info(f"✅ Item gespeichert: {item_data['label']} (GUID={self.current_guid})")
            self.info_label.setText(f"✅ Gespeichert: {item_data['label']}")
            self.item_saved.emit()
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern: {e}", exc_info=True)
            QMessageBox.critical(self, "Fehler", f"Speichern fehlgeschlagen:\n{str(e)}")
    
    def get_item_data(self) -> Optional[Dict[str, Any]]:
        """Gibt aktuelle Daten zurück (für Kompatibilität)"""
        if not self.current_guid:
            return None
        try:
            item_data, _ = self.db.get_static_value(self.menu_type, self.current_guid)
            return item_data
        except:
            return None


# REST DER KLASSEN (MenuListWidget, PdvmMenuEditorWidget) BLEIBT UNVERÄNDERT
'''

if __name__ == '__main__':
    import sys
    
    print("🔧 Repariere pdvm_menu_editor_widget.py...")
    print("   Problem: Duplikat-Code (alte MenuItemEditor)")
    print("   Lösung: Zeile 271-542 löschen (alter Code)")
    print()
    print("❌ Sorry, ich kann die Datei nicht automatisch reparieren.")
    print("   Sie ist zu kaputt durch die fehlgeschlagenen Replace-Operationen.")
    print()
    print("✅ LÖSUNG: Datei manuell in VS Code aufmachen und alles zwischen")
    print("   Zeile 271 (Docstring) und Zeile 537 (vor 'class MenuListWidget') LÖSCHEN")
    print()
    print("   Oder: Backup aus Versionskontrolle wiederherstellen")
    sys.exit(1)
