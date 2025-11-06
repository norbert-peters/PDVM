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
    PERFEKTE 4-POSITIONEN STRUKTUR:
    1. Logic-Operator: FIRST | AND | OR  
    2. Negation: IS | NOT  
    3. Bedingung: = | != | > | < | >= | <= | enthält | beginnt mit | endet mit  
    4. Wert: 'wert'
    
    Beispiele:
    - "FIRST IS = 'Maier'" (erste Bedingung)
    - "AND NOT = 'test'" (weitere Bedingung mit NOT)
    - "OR IS enthält 'Paul'" (weitere Bedingung ohne NOT)
    """
    def __init__(self, value="", operator_type="=", logic_operator="FIRST", negation="IS"):
        self.value = value
        self.operator_type = operator_type  # =, !=, >, <, >=, <=, enthält, beginnt mit, endet mit
        self.logic_operator = logic_operator  # FIRST, AND, OR
        self.negation = negation  # IS, NOT
    
    def to_dict(self):
        return {
            'value': self.value,
            'operator_type': self.operator_type,
            'logic_operator': self.logic_operator,
            'negation': self.negation
        }
    
    @classmethod
    def from_dict(cls, data):
        # Migration von alter Struktur
        if 'negate' in data:
            # Alte negate boolean zu neuer negation string
            negation = "NOT" if data.get('negate', False) else "IS"
        else:
            negation = data.get('negation', 'IS')
        
        # Logic-Operator Migration
        logic_op = data.get('logic_operator', 'FIRST')
        if logic_op is None:
            logic_op = 'FIRST'
        
        return cls(
            value=data.get('value', ''),
            operator_type=data.get('operator_type', '='),
            logic_operator=logic_op,
            negation=negation
        )
    
    def get_display_text(self):
        """
        KONSISTENTE 4-POSITIONEN ANZEIGE:
        "FIRST IS = 'test'"
        "AND NOT enthält 'wert'"
        "OR IS > '100'"
        """
        return f"{self.logic_operator} {self.negation} {self.operator_type} '{self.value}'"


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
        
        # 🔒 Loading-Flag für UI-Update-Blockierung
        self._loading_condition = False
        
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
        PERFEKTE 4-POSITIONEN REGEL: Erste Bedingung hat FIRST
        """
        if not self.conditions:
            self.conditions = [SearchCondition(
                value='',
                operator_type='=',
                logic_operator='FIRST',  # Erste Bedingung hat FIRST
                negation='IS'
            )]
            logger.info("🔄 PERFEKTE STRUKTUR: Erste Bedingung 'FIRST IS = \"\"' erstellt")
        else:
            # Erste Bedingung muss FIRST haben
            if self.conditions[0].logic_operator != 'FIRST':
                self.conditions[0].logic_operator = 'FIRST'
                logger.info("🔄 PERFEKTE STRUKTUR: Erste Bedingung auf FIRST gesetzt")

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
        info_label = QLabel("Perfekte 4-Positionen Struktur: [FIRST/AND/OR] [IS/NOT] [Bedingung] 'Wert'")
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
        """PERFEKTE 4-POSITIONEN EDITOR"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        edit_label = QLabel("4-Positionen Editor:")
        edit_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        layout.addWidget(edit_label)
        
        # Form für 4-Positionen Struktur
        form_widget = QWidget()
        form_layout = QFormLayout(form_widget)
        
        # POSITION 4: Wert (oben für bessere Bedienung)
        self.value_edit = QLineEdit()
        self.value_edit.setPlaceholderText("Wert eingeben...")
        self.value_edit.textChanged.connect(self.update_current_condition)
        form_layout.addRow("4️⃣ Wert:", self.value_edit)
        
        # POSITION 1: Logic-Operator (FIRST/AND/OR)
        self.logic_combo = QComboBox()
        self.logic_combo.addItems(["FIRST", "AND", "OR"])
        self.logic_combo.currentTextChanged.connect(self.update_current_condition)
        form_layout.addRow("1️⃣ Verknüpfung:", self.logic_combo)
        
        # POSITION 2: Negation (IS/NOT)
        self.negation_combo = QComboBox()
        self.negation_combo.addItems(["IS", "NOT"])
        self.negation_combo.currentTextChanged.connect(self.update_current_condition)
        form_layout.addRow("2️⃣ Negation:", self.negation_combo)
        
        # POSITION 3: Bedingung/Operator
        self.operator_combo = QComboBox()
        self.operator_combo.addItems([
            "=",
            "!=", 
            ">",
            "<",
            ">=",
            "<=",
            "enthält",
            "beginnt mit",
            "endet mit"
        ])
        self.operator_combo.currentTextChanged.connect(self.update_current_condition)
        form_layout.addRow("3️⃣ Bedingung:", self.operator_combo)
        
        layout.addWidget(form_widget)
        
        # Vorschau mit großer, klarer Anzeige
        preview_label = QLabel("Vorschau:")
        preview_label.setFont(QFont("Segoe UI", 9, QFont.Bold))
        layout.addWidget(preview_label)
        
        self.preview_label = QLabel("")
        self.preview_label.setStyleSheet("""
            background-color: #e3f2fd; 
            padding: 15px; 
            border: 2px solid #1976d2; 
            font-family: 'Courier New'; 
            font-size: 14px; 
            font-weight: bold;
            border-radius: 5px;
        """)
        self.preview_label.setWordWrap(True)
        layout.addWidget(self.preview_label)
        
        # Hilfetexte
        help_label = QLabel("""
        <b>Beispiele:</b><br>
        • FIRST IS = 'Maier'<br>
        • AND NOT = 'test'<br>
        • OR IS enthält 'Paul'
        """)
        help_label.setStyleSheet("color: #666; font-size: 10px; margin-top: 10px;")
        layout.addWidget(help_label)
        
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
        """Bedingung wurde ausgewählt - lade in 4-Positionen Editor"""
        current_item = self.conditions_list.currentItem()
        if not current_item:
            return
        
        condition_index = current_item.data(Qt.UserRole)
        if condition_index >= len(self.conditions):
            return
        
        # 🔒 KRITISCH: UI-Updates blockieren während Laden
        self._loading_condition = True
        
        self.current_condition_index = condition_index
        condition = self.conditions[condition_index]
        
        logger.info(f"🔍 DEBUG WECHSEL: Bedingung {condition_index} ausgewählt: {condition.get_display_text()}")
        logger.info(f"🔍 DEBUG WECHSEL: logic_operator='{condition.logic_operator}', negation='{condition.negation}', operator_type='{condition.operator_type}', value='{condition.value}'")
        
        # ALLE Bedingungen zur Kontrolle ausgeben
        for i, c in enumerate(self.conditions):
            logger.info(f"🔍 DEBUG ALLE: Bedingung {i}: logic='{c.logic_operator}', negation='{c.negation}', operator='{c.operator_type}', value='{c.value}'")
        
        # POSITION 4: Wert setzen
        logger.info(f"🔍 DEBUG SETZE: Wert '{condition.value}' → UI")
        self.value_edit.setText(condition.value)
        
        # POSITION 1: Logic-Operator setzen
        logic_index = self.logic_combo.findText(condition.logic_operator)
        if logic_index >= 0:
            logger.info(f"🔍 DEBUG SETZE: Logic '{condition.logic_operator}' → UI Index {logic_index}")
            self.logic_combo.setCurrentIndex(logic_index)
        
        # POSITION 2: Negation setzen  
        negation_index = self.negation_combo.findText(condition.negation)
        if negation_index >= 0:
            logger.info(f"🔍 DEBUG SETZE: Negation '{condition.negation}' → UI Index {negation_index}")
            self.negation_combo.setCurrentIndex(negation_index)
        
        # POSITION 3: Operator setzen
        operator_index = self.operator_combo.findText(condition.operator_type)
        if operator_index >= 0:
            logger.info(f"🔍 DEBUG SETZE: Operator '{condition.operator_type}' → UI Index {operator_index}")
            self.operator_combo.setCurrentIndex(operator_index)
        
        # Spezielle Regeln für erste Bedingung
        if condition_index == 0:
            # Erste Bedingung: Logic-Operator auf FIRST sperren
            self.logic_combo.setEnabled(False)
            self.logic_combo.setCurrentText("FIRST")
            logger.info(f"🔍 DEBUG ERSTE: Logic auf FIRST gesperrt")
        else:
            # Weitere Bedingungen: Logic-Operator freischalten (nicht FIRST)
            self.logic_combo.setEnabled(True)
            if condition.logic_operator == "FIRST":
                self.logic_combo.setCurrentText("AND")  # Fallback
                logger.info(f"🔍 DEBUG WEITERE: FIRST → AND Fallback")
        
        # 🔓 UI-Updates wieder freigeben
        self._loading_condition = False
        
        logger.info(f"🔍 DEBUG FINALE UI: Logic='{self.logic_combo.currentText()}', Negation='{self.negation_combo.currentText()}', Operator='{self.operator_combo.currentText()}', Wert='{self.value_edit.text()}'")
        self.update_preview()
    
    def update_current_condition(self):
        """Aktualisiert die aktuelle Bedingung basierend auf 4-Positionen UI"""
        # 🚫 Während Laden keine Updates durchführen
        if hasattr(self, '_loading_condition') and self._loading_condition:
            logger.info("🔒 DEBUG: Update blockiert während Condition-Laden")
            return
            
        if self.current_condition_index < 0 or self.current_condition_index >= len(self.conditions):
            return
        
        condition = self.conditions[self.current_condition_index]
        
        logger.info(f"🔍 DEBUG: Aktualisiere Bedingung {self.current_condition_index}")
        logger.info(f"🔍 DEBUG: VOR Update: logic='{condition.logic_operator}', negation='{condition.negation}', operator='{condition.operator_type}', value='{condition.value}'")
        
        # POSITION 4: Wert aktualisieren
        condition.value = self.value_edit.text()
        
        # POSITION 1: Logic-Operator aktualisieren
        if self.current_condition_index == 0:
            # Erste Bedingung muss FIRST bleiben
            condition.logic_operator = "FIRST"
        else:
            # Weitere Bedingungen können AND/OR sein
            condition.logic_operator = self.logic_combo.currentText()
        
        # POSITION 2: Negation aktualisieren
        condition.negation = self.negation_combo.currentText()
        
        # POSITION 3: Operator aktualisieren
        condition.operator_type = self.operator_combo.currentText()
        
        logger.info(f"🔍 DEBUG: NACH Update: logic='{condition.logic_operator}', negation='{condition.negation}', operator='{condition.operator_type}', value='{condition.value}'")
        
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
        """Fügt neue Bedingung hinzu - 4-Positionen Struktur"""
        new_condition = SearchCondition(
            value='',
            operator_type='=',
            logic_operator='AND',  # Position 1: AND (neue Bedingungen nie FIRST)
            negation='IS'  # Position 2: IS (Standard positiv)
        )
        
        self.conditions.append(new_condition)
        self.load_conditions()
        
        # Neue Bedingung auswählen
        self.conditions_list.setCurrentRow(len(self.conditions) - 1)
        
        logger.info("✅ Neue Bedingung hinzugefügt: AND IS = ''")
    
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