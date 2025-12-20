"""
PDVM System Editor V4 - BAUM-ANSATZ für verschachtelte Strukturen
==================================================================

NEUER ANSATZ:
- QTreeWidget zeigt KOMPLETTE verschachtelte Struktur
- Jede Ebene rekursiv durchgehen und anzeigen
- Editierbar: Doppelklick auf Item öffnet Edit-Dialog
- Unterstützt BELIEBIGE Verschachtelungstiefe

STRUKTUR-BEISPIEL:
ROOT
├─ TABLE: persondaten
├─ NAME: Persondaten
PERSDATEN
├─ PERSONALNUMMER
│  ├─ 2025043.0: "A1"
│  └─ abdatum
│     └─ 2025043.0: 1234567.0
├─ FAMILIENNAME
   ├─ 2025043.0: "Mannheimer"
   └─ abdatum
      └─ 2025043.0: 1234567.0

VERWENDUNG:
- Funktioniert mit ALLEN verschachtelten Strukturen
- Zeigt ALLES an (keine Ausnahmen)
- Editierbar per Doppelklick

Erstellt: 18.12.2025
"""

import sys
import json
import logging
from typing import Dict, Optional, Any, List
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLabel, QMessageBox, QApplication, QDialog,
    QLineEdit, QDialogButtonBox, QTextEdit, QSplitter
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor, QBrush

from pdvm_central_datenbank import PdvmCentralDatenbank
from pdvm_central_systemsteuerung import get_gcs

logger = logging.getLogger(__name__)


class EditValueDialog(QDialog):
    """Dialog zum Editieren eines einzelnen Wertes"""
    
    def __init__(self, key: str, value: Any, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Wert editieren: {key}")
        self.resize(500, 300)
        
        layout = QVBoxLayout(self)
        
        # Label
        layout.addWidget(QLabel(f"<b>Property:</b> {key}"))
        
        # Wert-Editor
        if isinstance(value, (dict, list)):
            # JSON für komplexe Typen
            self.editor = QTextEdit()
            self.editor.setPlainText(json.dumps(value, indent=2, ensure_ascii=False))
            self.is_json = True
        else:
            # Einfaches Textfeld
            self.editor = QLineEdit(str(value) if value is not None else "")
            self.is_json = False
        
        layout.addWidget(self.editor)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_value(self):
        """Gibt editierten Wert zurück (mit Typ-Konvertierung)"""
        if self.is_json:
            try:
                return json.loads(self.editor.toPlainText())
            except json.JSONDecodeError:
                return self.editor.toPlainText()
        else:
            text = self.editor.text()
            
            # Intelligente Typ-Erkennung
            if text.lower() in ['true', 'false']:
                return text.lower() == 'true'
            
            try:
                # Int?
                if '.' not in text:
                    return int(text)
            except ValueError:
                pass
            
            try:
                # Float?
                return float(text)
            except ValueError:
                pass
            
            # String
            return text


class PdvmSystemEditorTree(QWidget):
    """
    Baum-basierter System-Editor für beliebig verschachtelte Strukturen.
    
    Zeigt KOMPLETTE Datenstruktur als Baum an.
    Editierbar per Doppelklick auf Wert-Items.
    """
    
    def __init__(self, table_name: str, record_uid: str, parent=None):
        """
        ULTRA EINFACH: Dialog liefert bereits die richtige Tabelle + GUID!
        
        Args:
            table_name: Die richtige Tabelle (z.B. "persondaten")
            record_uid: GUID der ausgewählten Zeile
        """
        super().__init__(parent)
        
        self.actual_table = table_name
        self.record_uid = record_uid
        self.data: Dict = {}
        self.modified = False
        
        logger.info(f"📂 System-Editor: {table_name}.{record_uid[:8]}...")
        
        # Lade die ausgewählte GUID direkt
        self.db = PdvmCentralDatenbank(table_name, guid=record_uid)
        
        self._init_ui()
        self._load_data()
    
    def _init_ui(self):
        """UI initialisieren"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Header - zeige die EIGENTLICHE Tabelle an
        header = QLabel(f"<h3>📂 Dictionary: {self.actual_table}</h3>")
        layout.addWidget(header)
        
        # Info-Text
        info = QLabel("💡 <b>Doppelklick</b> auf Wert zum Editieren | 🔵 Blau = editierbar")
        info.setStyleSheet("color: gray; font-size: 10pt;")
        layout.addWidget(info)
        
        # Baum
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Struktur / Wert"])
        self.tree.setAlternatingRowColors(True)
        self.tree.setExpandsOnDoubleClick(False)  # Wir verwenden Doppelklick für Edit
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self.tree)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        btn_expand = QPushButton("🌳 Alles aufklappen")
        btn_expand.clicked.connect(self.tree.expandAll)
        button_layout.addWidget(btn_expand)
        
        btn_collapse = QPushButton("📁 Alles zuklappen")
        btn_collapse.clicked.connect(self.tree.collapseAll)
        button_layout.addWidget(btn_collapse)
        
        button_layout.addStretch()
        
        btn_reload = QPushButton("🔄 Neu laden")
        btn_reload.clicked.connect(self._load_data)
        button_layout.addWidget(btn_reload)
        
        btn_save = QPushButton("💾 Speichern")
        btn_save.clicked.connect(self._save_data)
        btn_save.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        button_layout.addWidget(btn_save)
        
        layout.addLayout(button_layout)
    
    def _load_data(self):
        """Daten aus DB laden - self.db.data ist bereits geladen!"""
        try:
            logger.info(f"📂 Lade Daten: {self.actual_table}.{self.record_uid[:8]}...")
            
            # PdvmCentralDatenbank hat Daten bereits geladen
            self.data = self.db.data
            
            if not self.data:
                logger.warning(f"⚠️ Keine Daten gefunden für {self.record_uid}")
            else:
                logger.info(f"✅ Daten geladen: {len(self.data)} Top-Level Keys")
                logger.info(f"   Keys: {list(self.data.keys())}")
            
            # Baum aufbauen
            self._build_tree()
            
            # Alles aufklappen für ersten Blick
            self.tree.expandAll()
            
            self.modified = False
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden: {e}", exc_info=True)
            QMessageBox.critical(self, "Fehler", f"Daten konnten nicht geladen werden:\n{e}")
    
    def _build_tree(self):
        """Baum aus self.data aufbauen (rekursiv)"""
        self.tree.clear()
        
        if not self.data:
            item = QTreeWidgetItem(self.tree)
            item.setText(0, "⚠️ Keine Daten vorhanden")
            return
        
        # Rekursiv durch Struktur gehen
        for key in sorted(self.data.keys()):
            value = self.data[key]
            item = self._create_tree_item(key, value, [key])
            self.tree.addTopLevelItem(item)
    
    def _create_tree_item(self, key: str, value: Any, path: List[str]) -> QTreeWidgetItem:
        """
        Erstellt Tree-Item rekursiv für beliebige Verschachtelung.
        
        Args:
            key: Aktueller Key
            value: Aktueller Wert
            path: Pfad vom Root (für späteres Editieren)
        
        Returns:
            QTreeWidgetItem
        """
        item = QTreeWidgetItem()
        
        # Farbe basierend auf Ebene
        if len(path) == 1:
            # Top-Level (ROOT, Gruppen)
            if key == "ROOT":
                item.setForeground(0, QBrush(QColor("#0066CC")))  # Blau
                font = QFont()
                font.setBold(True)
                item.setFont(0, font)
            else:
                item.setForeground(0, QBrush(QColor("#009900")))  # Grün
                font = QFont()
                font.setBold(True)
                item.setFont(0, font)
        
        # Pfad als UserData speichern (für Edit)
        item.setData(0, Qt.ItemDataRole.UserRole, path)
        
        if isinstance(value, dict):
            # Dict: Key als Node, rekursiv Kinder hinzufügen
            item.setText(0, f"📂 {key} ({len(value)} Items)")
            
            for sub_key in sorted(value.keys()):
                sub_value = value[sub_key]
                sub_path = path + [sub_key]
                child = self._create_tree_item(sub_key, sub_value, sub_path)
                item.addChild(child)
        
        elif isinstance(value, list):
            # Liste: Key als Node, Items mit Index
            item.setText(0, f"📋 {key} [{len(value)} Items]")
            
            for idx, list_item in enumerate(value):
                sub_path = path + [idx]
                child = self._create_tree_item(f"[{idx}]", list_item, sub_path)
                item.addChild(child)
        
        else:
            # Leaf: Wert direkt anzeigen (editierbar!)
            value_str = self._format_value(value)
            item.setText(0, f"🔵 {key}: {value_str}")
            item.setForeground(0, QBrush(QColor("#0066CC")))  # Blau = editierbar
            
            # Tooltip
            item.setToolTip(0, f"Doppelklick zum Editieren\nPfad: {' → '.join(str(p) for p in path)}")
        
        return item
    
    def _format_value(self, value: Any) -> str:
        """Formatiert Wert für Anzeige"""
        if value is None:
            return "∅ (None)"
        elif isinstance(value, bool):
            return f"✓ {value}" if value else f"✗ {value}"
        elif isinstance(value, (int, float)):
            return f"{value:,}".replace(",", ".")
        elif isinstance(value, str):
            if len(value) > 50:
                return f'"{value[:47]}..."'
            return f'"{value}"'
        else:
            return str(value)[:50]
    
    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Item doppelgeklickt → Editieren falls Leaf"""
        path = item.data(0, Qt.ItemDataRole.UserRole)
        if not path:
            return
        
        # Aktuellen Wert holen
        value = self._get_value_by_path(path)
        
        # Nur Leaf-Werte editierbar (keine Dicts/Lists)
        if isinstance(value, (dict, list)) and not item.text(0).startswith("🔵"):
            # Container → aufklappen/zuklappen
            if item.isExpanded():
                item.setExpanded(False)
            else:
                item.setExpanded(True)
            return
        
        # Edit-Dialog öffnen
        key = path[-1]
        dialog = EditValueDialog(key, value, self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_value = dialog.get_value()
            
            # Wert in Daten-Struktur setzen
            self._set_value_by_path(path, new_value)
            
            # Item-Text aktualisieren
            value_str = self._format_value(new_value)
            item.setText(0, f"🔵 {key}: {value_str}")
            
            self.modified = True
            logger.info(f"✏️ Wert geändert: {' → '.join(str(p) for p in path)} = {new_value}")
    
    def _get_value_by_path(self, path: List[str]) -> Any:
        """Holt Wert aus self.data anhand Pfad"""
        current = self.data
        
        for key in path:
            if isinstance(current, dict):
                current = current.get(key)
            elif isinstance(current, list):
                current = current[int(key)]
            else:
                return None
        
        return current
    
    def _set_value_by_path(self, path: List[str], value: Any):
        """Setzt Wert in self.data anhand Pfad"""
        current = self.data
        
        # Bis zum vorletzten Key navigieren
        for key in path[:-1]:
            if isinstance(current, dict):
                current = current[key]
            elif isinstance(current, list):
                current = current[int(key)]
        
        # Letzten Key setzen
        last_key = path[-1]
        if isinstance(current, dict):
            current[last_key] = value
        elif isinstance(current, list):
            current[int(last_key)] = value
    
    def _save_data(self):
        """Daten in DB speichern"""
        if not self.modified:
            QMessageBox.information(self, "Info", "Keine Änderungen zum Speichern.")
            return
        
        try:
            logger.info(f"💾 Speichere Dictionary: {len(self.data)} Gruppen")
            
            # Jede Gruppe separat speichern
            for gruppe_name, gruppe_data in self.data.items():
                if gruppe_name == 'ROOT':
                    # ROOT: Jede Property einzeln
                    for prop_name, prop_value in gruppe_data.items():
                        self.db.set_value('ROOT', prop_name, prop_value)
                        logger.info(f"  ✅ ROOT.{prop_name} = {prop_value}")
                else:
                    # Andere Gruppen: Komplette Struktur
                    self.db.set_value(gruppe_name, None, gruppe_data)
                    logger.info(f"  ✅ {gruppe_name}: {len(gruppe_data)} Items")
            
            # Speichern
            self.db.save_all_values()
            
            self.modified = False
            QMessageBox.information(self, "Erfolg", "✅ Daten erfolgreich gespeichert!")
            logger.info("💾 Speichern erfolgreich")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern: {e}", exc_info=True)
            QMessageBox.critical(self, "Fehler", f"Daten konnten nicht gespeichert werden:\n{e}")
    
    def get_widget(self):
        """Gibt sich selbst zurück (für pdvm_genereller_dialog Integration)"""
        return self


# Test-Code
if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Test mit 66666... Dictionary
    editor = PdvmSystemEditorTree('sys_framedaten', '66666666-6666-6666-6666-666666666666')
    editor.setWindowTitle("PDVM System Editor - Baum-Ansicht")
    editor.resize(800, 600)
    editor.show()
    
    sys.exit(app.exec())
