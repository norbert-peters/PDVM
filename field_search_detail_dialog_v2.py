"""
MODAL-DIALOG: FIELD SEARCH DETAILS V2
=====================================

MODERNE LINEARE VERSION: Nur noch Bedingungszeilen, keine normalen Felder mehr
Unterstützt klare (AND/OR) (NOT) (Operator) 'Wert' Struktur
"""

import sys
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QLineEdit, QComboBox, QCheckBox,
                             QDialogButtonBox, QFrame, QScrollArea, QWidget,
                             QMessageBox, QGroupBox, QGridLayout, QFormLayout,
                             QListWidget, QListWidgetItem, QSplitter,
                             QTextEdit, QRadioButton, QButtonGroup)
from PyQt5.QtCore import Qt, pyqtSignal, QDate
from PyQt5.QtGui import QFont, QIcon
import logging
import json

logger = logging.getLogger(__name__)


class SearchCondition:
    """
    MODERNE Suchbedingung: (AND/OR) (NOT) (Operator) 'Wert'
    Beispiel: "OR NOT enthält 'test'" oder "AND = 'wert'"
    """
    def __init__(self, value="", operator_type="enthält", logic_operator="AND", negate=False):
        self.value = value
        self.operator_type = operator_type  # enthält, beginnt mit, endet mit, =, !=, >, <, >=, <=
        self.logic_operator = logic_operator  # AND, OR (None für erste Bedingung)
        self.negate = negate  # NOT-Modifikator
    
    def to_dict(self):
        return {
            'value': self.value,
            'operator_type': self.operator_type,
            'logic_operator': self.logic_operator,
            'negate': self.negate
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            value=data.get('value', ''),
            operator_type=data.get('operator_type', 'enthält'),
            logic_operator=data.get('logic_operator', 'AND'),
            negate=data.get('negate', False)
        )
    
    def get_display_text(self):
        """
        Formatierter Text für Liste: "(AND) NOT enthält 'test'"
        """
        parts = []
        
        # Logic Operator in Klammern (außer bei erster Bedingung)
        if self.logic_operator:
            parts.append(f"({self.logic_operator})")
        
        # NOT wenn negiert
        if self.negate:
            parts.append("NOT")
        
        # Operator
        parts.append(self.operator_type)
        
        # Wert in Anführungszeichen
        parts.append(f"'{self.value}'")
        
        return " ".join(parts)


class FieldSearchDetailDialog(QDialog):
    """
    MODERNE LINEARE VERSION: Dialog nur für Bedingungszeilen
    Keine normalen Felder mehr - nur noch strukturierte Bedingungen
    """
    
    def __init__(self, field_name, current_conditions=None, parent=None):
        super().__init__(parent)
        
        self.field_name = field_name
        self.conditions = current_conditions or []
        
        # Convert von alter Struktur falls nötig
        self._convert_old_conditions()
        
        # NEUE REGEL: Erste Bedingung ohne Logic-Operator
        self._ensure_first_condition()
        
        # UI Komponenten
        self.conditions_list = None
        self.current_condition_widgets = {}
        self.current_condition_index = -1
        
        self.setup_ui()
        self.load_conditions()
        logger.info(f"✅ FieldSearchDetailDialog UI für '{self.field_name}' erstellt")
    
    def _convert_old_conditions(self):
        """
        MIGRATION: Konvertiert alte Bedingungsstruktur zur neuen
        """
        if not self.conditions:
            return
        
        # Prüfe ob alte Struktur (dict oder SearchCondition mit search_type)
        converted = []
        for condition in self.conditions:
            if isinstance(condition, dict):
                # Dict zu SearchCondition
                if 'search_type' in condition:
                    # Alte Struktur
                    converted.append(SearchCondition(
                        value=condition.get('value', ''),
                        operator_type=self._convert_search_type(condition.get('search_type', 'contains')),
                        logic_operator=condition.get('operator', 'AND'),
                        negate=condition.get('negate', False)
                    ))
                else:
                    # Neue Struktur als dict
                    converted.append(SearchCondition.from_dict(condition))
            elif hasattr(condition, 'search_type'):
                # Alte SearchCondition Klasse
                converted.append(SearchCondition(
                    value=condition.value,
                    operator_type=self._convert_search_type(condition.search_type),
                    logic_operator=condition.operator or 'AND',
                    negate=condition.negate
                ))
            else:
                # Schon neue SearchCondition
                converted.append(condition)
        
        self.conditions = converted
        logger.info(f"🔄 {len(converted)} Bedingungen zur neuen Struktur konvertiert")
    
    def _convert_search_type(self, old_search_type):
        """
        Konvertiert alte search_type zu neuen operator_type
        """
        mapping = {
            'contains': 'enthält',
            'startswith': 'beginnt mit',
            'endswith': 'endet mit', 
            'exact': '=',
            'wildcard': 'enthält',  # Fallback
            'regex': 'enthält'      # Fallback
        }
        return mapping.get(old_search_type, 'enthält')
    
    def _ensure_first_condition(self):
        """
        NEUE REGEL: Erste Bedingung ohne Logic-Operator
        """
        if not self.conditions:
            self.conditions = [SearchCondition(
                value='',
                operator_type='enthält',
                logic_operator=None,  # Erste Bedingung hat keinen Logic-Operator
                negate=False
            )]
            logger.info("🔄 NEUE REGEL: Erste Bedingung automatisch erstellt")
        else:
            # Erste Bedingung darf keinen Logic-Operator haben
            if self.conditions[0].logic_operator is not None:
                self.conditions[0].logic_operator = None
                logger.info("🔄 NEUE REGEL: Logic-Operator von erster Bedingung entfernt")

    def setup_ui(self):
        """MODERNE UI ohne normale Felder"""
        self.setWindowTitle(f"Erweiterte Suche: {self.field_name}")
        self.setModal(True)
        self.resize(700, 600)
        
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel(f"Bedingungen für: {self.field_name}")
        header_font = QFont("Segoe UI", 14, QFont.Bold)
        header_label.setFont(header_font)
        layout.addWidget(header_label)
        
        # Info-Text
        info_label = QLabel("Strukturierte Bedingungen: (AND/OR) (NOT) (Operator) 'Wert'")
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #666; margin-bottom: 15px; font-size: 11px;")
        layout.addWidget(info_label)
        
        # Haupt-Splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Linke Seite: Bedingungen-Liste
        left_widget = self._create_conditions_list()
        splitter.addWidget(left_widget)
        
        # Rechte Seite: Bedingung bearbeiten
        right_widget = self._create_condition_editor()
        splitter.addWidget(right_widget)
        
        # Splitter-Verhältnis
        splitter.setSizes([300, 400])
        layout.addWidget(splitter)
        
        # Dialog-Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _create_conditions_list(self):
        """Erstellt die Bedingungen-Liste (links)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        list_label = QLabel("Bedingungen:")
        list_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        layout.addWidget(list_label)
        
        self.conditions_list = QListWidget()
        self.conditions_list.setMinimumWidth(280)
        self.conditions_list.itemSelectionChanged.connect(self.on_condition_selected)
        layout.addWidget(self.conditions_list)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        add_button = QPushButton("➕ Hinzufügen")
        add_button.clicked.connect(self.add_condition)
        add_button.setStyleSheet("QPushButton { background-color: #28a745; color: white; }")
        buttons_layout.addWidget(add_button)
        
        remove_button = QPushButton("➖ Entfernen")
        remove_button.clicked.connect(self.remove_condition)
        remove_button.setStyleSheet("QPushButton { background-color: #dc3545; color: white; }")
        buttons_layout.addWidget(remove_button)
        
        layout.addLayout(buttons_layout)
        
        return widget
    
    def _create_condition_editor(self):
        """Erstellt den Bedingung-Editor (rechts)"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        edit_label = QLabel("Bedingung bearbeiten:")
        edit_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        layout.addWidget(edit_label)
        
        # Form für aktuelle Bedingung
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        
        # Suchbegriff (oben)
        self.value_edit = QLineEdit()
        self.value_edit.setPlaceholderText("Suchbegriff eingeben...")
        self.value_edit.textChanged.connect(self.update_current_condition)
        form_layout.addRow("Suchbegriff:", self.value_edit)
        
        # Operator-Typ
        self.operator_combo = QComboBox()
        self.operator_combo.addItems([
            "enthält",
            "beginnt mit", 
            "endet mit",
            "= (gleich)",
            "!= (ungleich)",
            "> (größer)",
            "< (kleiner)",
            ">= (größer/gleich)",
            "<= (kleiner/gleich)"
        ])
        self.operator_combo.currentTextChanged.connect(self.update_current_condition)
        form_layout.addRow("Bedingung:", self.operator_combo)
        
        # Logic-Operator (AND/OR) - nur für nicht-erste Bedingungen
        logic_widget = QWidget()
        logic_layout = QHBoxLayout(logic_widget)
        logic_layout.setContentsMargins(0, 0, 0, 0)
        
        self.logic_group = QButtonGroup()
        self.and_radio = QRadioButton("AND")
        self.or_radio = QRadioButton("OR")
        self.and_radio.setChecked(True)
        
        self.and_radio.toggled.connect(self.update_current_condition)
        self.or_radio.toggled.connect(self.update_current_condition)
        
        self.logic_group.addButton(self.and_radio)
        self.logic_group.addButton(self.or_radio)
        
        logic_layout.addWidget(self.and_radio)
        logic_layout.addWidget(self.or_radio)
        logic_layout.addStretch()
        
        self.logic_label = QLabel("Verknüpfung:")
        form_layout.addRow(self.logic_label, logic_widget)
        
        # NOT-Checkbox
        self.negate_checkbox = QCheckBox("NOT (Bedingung negieren)")
        self.negate_checkbox.toggled.connect(self.update_current_condition)
        form_layout.addRow("", self.negate_checkbox)
        
        layout.addWidget(form_widget)
        
        # Vorschau
        preview_label = QLabel("Vorschau:")
        preview_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
        layout.addWidget(preview_label)
        
        self.preview_label = QLabel("")
        self.preview_label.setStyleSheet("background-color: #f8f9fa; padding: 10px; border: 1px solid #dee2e6; font-family: 'Courier New';")
        self.preview_label.setWordWrap(True)
        layout.addWidget(self.preview_label)
        
        layout.addStretch()
        
        return widget
    
    def load_conditions(self):
        """Lädt Bedingungen in die Liste"""
        self.conditions_list.clear()
        
        for i, condition in enumerate(self.conditions):
            item = QListWidgetItem(condition.get_display_text())
            item.setData(Qt.UserRole, i)
            self.conditions_list.addItem(item)
        
        # Erste Bedingung auswählen falls vorhanden
        if self.conditions_list.count() > 0:
            self.conditions_list.setCurrentRow(0)
        
        logger.info(f"✅ {len(self.conditions)} Bedingungen geladen (erste Bedingung geschützt)")
    
    def on_condition_selected(self):
        """Bedingung wurde ausgewählt - lade in Editor"""
        current_item = self.conditions_list.currentItem()
        if not current_item:
            return
        
        condition_index = current_item.data(Qt.UserRole)
        if condition_index >= len(self.conditions):
            return
        
        self.current_condition_index = condition_index
        condition = self.conditions[condition_index]
        
        # Widgets mit Bedingungsdaten füllen
        self.value_edit.setText(condition.value)
        
        # Operator setzen
        operator_text = condition.operator_type
        if operator_text == "=":
            operator_text = "= (gleich)"
        elif operator_text == "!=":
            operator_text = "!= (ungleich)"
        # Weitere Mappings...
        
        combo_index = self.operator_combo.findText(operator_text)
        if combo_index >= 0:
            self.operator_combo.setCurrentIndex(combo_index)
        
        # Logic-Operator (nur für nicht-erste Bedingung)
        if condition_index == 0:
            # Erste Bedingung: Logic-Operator ausblenden
            self.logic_label.setVisible(False)
            self.and_radio.setVisible(False)
            self.or_radio.setVisible(False)
        else:
            # Weitere Bedingungen: Logic-Operator anzeigen
            self.logic_label.setVisible(True)
            self.and_radio.setVisible(True)
            self.or_radio.setVisible(True)
            
            if condition.logic_operator == "OR":
                self.or_radio.setChecked(True)
            else:
                self.and_radio.setChecked(True)
        
        # NOT-Status
        self.negate_checkbox.setChecked(condition.negate)
        
        self.update_preview()
    
    def update_current_condition(self):
        """Aktualisiert die aktuelle Bedingung basierend auf UI"""
        if self.current_condition_index < 0 or self.current_condition_index >= len(self.conditions):
            return
        
        condition = self.conditions[self.current_condition_index]
        
        # Wert aktualisieren
        condition.value = self.value_edit.text()
        
        # Operator-Typ aktualisieren
        operator_text = self.operator_combo.currentText()
        if operator_text.startswith("= "):
            condition.operator_type = "="
        elif operator_text.startswith("!= "):
            condition.operator_type = "!="
        elif operator_text.startswith("> "):
            condition.operator_type = ">"
        elif operator_text.startswith("< "):
            condition.operator_type = "<"
        elif operator_text.startswith(">= "):
            condition.operator_type = ">="
        elif operator_text.startswith("<= "):
            condition.operator_type = "<="
        else:
            condition.operator_type = operator_text
        
        # Logic-Operator (nur für nicht-erste Bedingung)
        if self.current_condition_index > 0:
            condition.logic_operator = "OR" if self.or_radio.isChecked() else "AND"
        
        # NOT-Status
        condition.negate = self.negate_checkbox.isChecked()
        
        # Liste aktualisieren
        current_item = self.conditions_list.currentItem()
        if current_item:
            current_item.setText(condition.get_display_text())
        
        self.update_preview()
    
    def update_preview(self):
        """Aktualisiert die Vorschau-Anzeige"""
        if not self.conditions:
            self.preview_label.setText("Keine Bedingungen definiert")
            return
        
        # Alle Bedingungen als Text zusammenfassen
        parts = []
        for condition in self.conditions:
            parts.append(condition.get_display_text())
        
        preview_text = " ".join(parts)
        self.preview_label.setText(preview_text)
    
    def add_condition(self):
        """Fügt neue Bedingung hinzu (immer ohne NOT)"""
        new_condition = SearchCondition(
            value='',
            operator_type='enthält',
            logic_operator='AND',  # Neue Bedingungen immer mit AND
            negate=False  # REGEL: Neue Bedingungen ohne NOT
        )
        
        self.conditions.append(new_condition)
        self.load_conditions()
        
        # Neue Bedingung auswählen
        self.conditions_list.setCurrentRow(len(self.conditions) - 1)
        
        logger.info("✅ Neue Bedingung hinzugefügt (ohne NOT)")
    
    def remove_condition(self):
        """Entfernt ausgewählte Bedingung (außer der ersten)"""
        current_row = self.conditions_list.currentRow()
        
        if current_row <= 0:
            QMessageBox.information(self, "Info", "Die erste Bedingung kann nicht gelöscht werden.")
            return
        
        if current_row < len(self.conditions):
            del self.conditions[current_row]
            self.load_conditions()
            logger.info(f"✅ Bedingung {current_row} entfernt")
    
    def get_conditions(self):
        """Gibt aktuelle Bedingungen zurück"""
        # Leere Bedingungen ausfiltern
        valid_conditions = []
        for condition in self.conditions:
            if condition.value.strip():  # Nur Bedingungen mit Wert
                valid_conditions.append(condition)
        
        logger.info(f"✅ FieldSearchDetailDialog für '{self.field_name}' mit {len(valid_conditions)} Bedingungen übernommen")
        return valid_conditions