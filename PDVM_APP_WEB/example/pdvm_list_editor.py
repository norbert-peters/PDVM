# -*- coding: utf-8 -*-
"""
PDVM List Editor - Template-basierter Listen-Editor
====================================================

Dialog zum Bearbeiten von Listen mit konfigurierbaren Feldern.
Template-gesteuert für maximale Flexibilität.

Features:
- Template aus 55555...LIST_TEMPLATES (z.B. list_anrede, list_default)
- Spalten aus Template-Definition
- Add/Remove/Edit von List-Items
- Export als List[Dict]

Struktur:
    Template: list_anrede
    {
        "fields": [
            {"name": "key", "label": "Schlüssel", "type": "string", "required": true},
            {"name": "value", "label": "Anzeige", "type": "string", "required": true},
            {"name": "titel", "label": "Titel", "type": "string", "required": false}
        ]
    }
    
    Ergebnis:
    [
        {"key": "herr", "value": "Herr", "titel": ""},
        {"key": "frau", "value": "Frau", "titel": ""}
    ]

Erstellt: 30.11.2025
"""

import logging
import json
from typing import List, Dict, Any, Optional
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QMessageBox, QInputDialog, QLabel
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

logger = logging.getLogger(__name__)


class PdvmListEditor(QDialog):
    """
    Template-basierter Listen-Editor.
    
    Lädt Template aus 55555...LIST_TEMPLATES und erstellt
    dynamische Tabelle basierend auf Template-Feldern.
    """
    
    def __init__(
        self,
        list_name: str,
        initial_data: List[Dict[str, Any]] = None,
        table_name: str = None,
        parent=None
    ):
        """
        Initialisiert Listen-Editor.
        
        Args:
            list_name: Name der Liste (z.B. "anrede", "land") → bestimmt Template
            initial_data: Initiale Listen-Daten (optional)
            table_name: Name der Tabelle für Template-Suche (z.B. "sys_viewdaten")
            parent: Parent-Widget
        """
        super().__init__(parent)
        
        self.list_name = list_name
        self.table_name = table_name or "sys_viewdaten"
        self.list_data = initial_data or []
        self.template = None
        self.accepted = False
        
        self.setWindowTitle(f"Listen-Editor: {list_name}")
        self.setMinimumSize(800, 600)
        
        # Template laden
        self._load_template()
        
        # UI aufbauen
        self._setup_ui()
        
        # Daten laden
        if self.list_data:
            self._load_data()
        
        logger.info(f"✅ Listen-Editor initialisiert: {list_name}")
    
    def _load_template(self):
        """Lädt Template aus 55555...LIST_TEMPLATES"""
        from pdvm_central_datenbank import PdvmCentralDatenbank
        
        try:
            # Template-DB öffnen
            template_guid = '55555555-5555-5555-5555-555555555555'
            template_db = PdvmCentralDatenbank(self.table_name, template_guid)
            
            # LIST_TEMPLATES Gruppe laden
            list_templates = template_db.get_value_by_group('LIST_TEMPLATES')
            
            if not list_templates:
                logger.warning(f"⚠️ Keine LIST_TEMPLATES in 55555... gefunden → verwende Fallback")
                self._use_fallback_template()
                return
            
            # Spezifisches Template suchen: list_{list_name}
            specific_template_name = f"list_{self.list_name}"
            template_found = None
            
            for template_guid, template_data in list_templates.items():
                template_name = template_data.get('name', '')
                if template_name == specific_template_name:
                    template_found = template_data
                    logger.info(f"✅ Spezifisches Template gefunden: {specific_template_name}")
                    break
            
            # Fallback: list_default
            if not template_found:
                for template_guid, template_data in list_templates.items():
                    template_name = template_data.get('name', '')
                    if template_name == 'list_default':
                        template_found = template_data
                        logger.info(f"✅ Fallback-Template verwendet: list_default")
                        break
            
            if template_found:
                self.template = template_found
            else:
                logger.warning(f"⚠️ Kein Template gefunden → verwende Fallback")
                self._use_fallback_template()
        
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden des Templates: {e}")
            self._use_fallback_template()
    
    def _use_fallback_template(self):
        """Verwendet hart-codierten Fallback-Template (nur key, value)"""
        self.template = {
            'name': 'list_default',
            'label': 'Standard-Liste',
            'fields': [
                {'name': 'key', 'label': 'Schlüssel', 'type': 'string', 'required': True},
                {'name': 'value', 'label': 'Wert', 'type': 'string', 'required': True}
            ]
        }
        logger.info("✅ Fallback-Template verwendet (key, value)")
    
    def _setup_ui(self):
        """Baut UI auf"""
        layout = QVBoxLayout(self)
        
        # Info-Label
        template_name = self.template.get('name', 'unbekannt')
        info_label = QLabel(f"<b>Liste:</b> {self.list_name} | <b>Template:</b> {template_name}")
        info_label.setStyleSheet("padding: 5px; background-color: #E8F4F8; border-radius: 3px;")
        layout.addWidget(info_label)
        
        # === TABELLE ===
        self.table = QTableWidget()
        
        # Spalten aus Template erstellen
        fields = self.template.get('fields', [])
        self.table.setColumnCount(len(fields))
        
        # Header setzen
        headers = [field.get('label', field.get('name', '')) for field in fields]
        self.table.setHorizontalHeaderLabels(headers)
        
        # Spaltenbreite
        header = self.table.horizontalHeader()
        for i in range(len(fields)):
            header.setSectionResizeMode(i, QHeaderView.Stretch)
        
        layout.addWidget(self.table)
        
        # === BUTTONS ===
        button_layout = QHBoxLayout()
        
        # Zeile hinzufügen
        add_btn = QPushButton("+ Zeile hinzufügen")
        add_btn.clicked.connect(self._add_row)
        button_layout.addWidget(add_btn)
        
        # Zeile löschen
        remove_btn = QPushButton("- Zeile löschen")
        remove_btn.clicked.connect(self._remove_row)
        button_layout.addWidget(remove_btn)
        
        button_layout.addStretch()
        
        # JSON anzeigen (Debug)
        json_btn = QPushButton("📄 JSON anzeigen")
        json_btn.clicked.connect(self._show_json)
        button_layout.addWidget(json_btn)
        
        layout.addLayout(button_layout)
        
        # === DIALOG BUTTONS ===
        dialog_button_layout = QHBoxLayout()
        
        dialog_button_layout.addStretch()
        
        # Abbrechen
        cancel_btn = QPushButton("❌ Abbrechen")
        cancel_btn.clicked.connect(self.reject)
        dialog_button_layout.addWidget(cancel_btn)
        
        # Übernehmen
        ok_btn = QPushButton("✅ Übernehmen")
        ok_btn.clicked.connect(self._accept)
        dialog_button_layout.addWidget(ok_btn)
        
        layout.addLayout(dialog_button_layout)
    
    def _load_data(self):
        """Lädt Daten in Tabelle"""
        self.table.setRowCount(len(self.list_data))
        
        fields = self.template.get('fields', [])
        
        for row_idx, item_data in enumerate(self.list_data):
            for col_idx, field in enumerate(fields):
                field_name = field.get('name', '')
                value = item_data.get(field_name, '')
                
                item = QTableWidgetItem(str(value))
                self.table.setItem(row_idx, col_idx, item)
        
        logger.info(f"✅ {len(self.list_data)} Zeilen geladen")
    
    def _add_row(self):
        """Fügt neue leere Zeile hinzu"""
        row_count = self.table.rowCount()
        self.table.insertRow(row_count)
        
        # Leere Items erstellen
        fields = self.template.get('fields', [])
        for col_idx, field in enumerate(fields):
            item = QTableWidgetItem('')
            self.table.setItem(row_count, col_idx, item)
        
        logger.info(f"✅ Neue Zeile hinzugefügt (Zeile {row_count + 1})")
    
    def _remove_row(self):
        """Entfernt ausgewählte Zeile"""
        current_row = self.table.currentRow()
        
        if current_row < 0:
            QMessageBox.warning(self, "Fehler", "Bitte Zeile auswählen!")
            return
        
        reply = QMessageBox.question(
            self,
            "Zeile löschen",
            f"Zeile {current_row + 1} wirklich löschen?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.table.removeRow(current_row)
            logger.info(f"❌ Zeile {current_row + 1} gelöscht")
    
    def _collect_data(self) -> List[Dict[str, Any]]:
        """Sammelt Daten aus Tabelle"""
        result = []
        fields = self.template.get('fields', [])
        
        for row_idx in range(self.table.rowCount()):
            row_data = {}
            
            for col_idx, field in enumerate(fields):
                field_name = field.get('name', f'field_{col_idx}')
                item = self.table.item(row_idx, col_idx)
                value = item.text() if item else ''
                
                # Type-Konvertierung
                field_type = field.get('type', 'string')
                if field_type == 'int':
                    try:
                        value = int(value) if value else 0
                    except ValueError:
                        value = 0
                elif field_type == 'float':
                    try:
                        value = float(value) if value else 0.0
                    except ValueError:
                        value = 0.0
                elif field_type == 'bool':
                    value = value.lower() in ['true', '1', 'yes', 'ja']
                
                row_data[field_name] = value
            
            result.append(row_data)
        
        return result
    
    def _validate_data(self) -> bool:
        """Validiert Daten (required fields)"""
        fields = self.template.get('fields', [])
        
        for row_idx in range(self.table.rowCount()):
            for col_idx, field in enumerate(fields):
                if field.get('required', False):
                    item = self.table.item(row_idx, col_idx)
                    value = item.text() if item else ''
                    
                    if not value.strip():
                        field_label = field.get('label', field.get('name', ''))
                        QMessageBox.warning(
                            self,
                            "Validierung",
                            f"Zeile {row_idx + 1}, Spalte '{field_label}': Pflichtfeld!"
                        )
                        return False
        
        return True
    
    def _show_json(self):
        """Zeigt JSON-Daten in Dialog (Debug)"""
        data = self._collect_data()
        json_str = json.dumps(data, indent=2, ensure_ascii=False)
        
        from PyQt5.QtWidgets import QTextEdit
        
        dialog = QDialog(self)
        dialog.setWindowTitle("JSON-Daten")
        dialog.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(dialog)
        
        json_view = QTextEdit()
        json_view.setPlainText(json_str)
        json_view.setReadOnly(True)
        layout.addWidget(json_view)
        
        close_btn = QPushButton("Schließen")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.exec_()
    
    def _accept(self):
        """Validiert und übernimmt Daten"""
        if not self._validate_data():
            return
        
        self.list_data = self._collect_data()
        self.accepted = True
        self.accept()
        
        logger.info(f"✅ Listen-Daten übernommen: {len(self.list_data)} Items")
    
    def get_data(self) -> List[Dict[str, Any]]:
        """
        Gibt Listen-Daten zurück.
        
        Returns:
            List[Dict]: Listen-Daten
        """
        return self.list_data


# ========================================
# STANDALONE-TEST
# ========================================

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Test mit initialen Daten
    initial_data = [
        {'key': 'herr', 'value': 'Herr'},
        {'key': 'frau', 'value': 'Frau'},
        {'key': 'divers', 'value': 'Divers'}
    ]
    
    editor = PdvmListEditor('anrede', initial_data, 'sys_viewdaten')
    
    if editor.exec_() == QDialog.Accepted:
        print("✅ Daten übernommen:")
        print(json.dumps(editor.get_data(), indent=2, ensure_ascii=False))
    else:
        print("❌ Abgebrochen")
    
    sys.exit(0)
