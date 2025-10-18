# pdvm_complex_filter_detail_dialog.py
"""
Detail-Dialog für KOMPLEXE Filter-Bedingungen

Ermöglicht mehrere Bedingungen pro Feld mit:
- Verschiedene Operatoren (enthält, gleich, größer, kleiner, etc.)
- UND/ODER Verknüpfung zwischen Bedingungen
- NOT-Unterstützung pro Bedingung
- Persistierung der Einstellungen
"""

import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QCheckBox, QScrollArea, QWidget,
    QFrame, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

logger = logging.getLogger(__name__)


class ComplexConditionWidget(QWidget):
    """
    Widget für EINE komplexe Filter-Bedingung
    
    Layout: [NOT-Checkbox] [Operator-Auswahl] [Wert-Eingabe] [Löschen-Button]
    """
    
    # Verfügbare Operatoren
    OPERATORS = [
        ('enthält', 'contains'),
        ('enthält von vorne', 'startswith'),
        ('gleich', 'equals'),
        ('gleich größer', 'gte'),
        ('gleich kleiner', 'lte'),
        ('größer', 'gt'),
        ('kleiner', 'lt')
    ]
    
    def __init__(self, parent=None, on_delete=None):
        super().__init__(parent)
        self.on_delete = on_delete
        self._init_ui()
    
    def _init_ui(self):
        """Initialisiert Bedingungszeile"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(8)
        
        # NOT Checkbox
        self.not_checkbox = QCheckBox("NOT")
        self.not_checkbox.setFixedWidth(60)
        self.not_checkbox.setStyleSheet("""
            QCheckBox {
                font-weight: bold;
                color: #f44336;
            }
        """)
        layout.addWidget(self.not_checkbox)
        
        # Operator Auswahl
        self.operator_combo = QComboBox()
        self.operator_combo.setFixedWidth(150)
        for display_name, internal_name in self.OPERATORS:
            self.operator_combo.addItem(display_name, internal_name)
        layout.addWidget(self.operator_combo)
        
        # Wert Eingabe
        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText("Wert eingeben...")
        self.value_input.setMinimumWidth(200)
        layout.addWidget(self.value_input, 1)
        
        # Löschen Button
        delete_btn = QPushButton("🗑️")
        delete_btn.setFixedSize(30, 28)
        delete_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        delete_btn.clicked.connect(self._handle_delete)
        layout.addWidget(delete_btn)
    
    def _handle_delete(self):
        """Behandelt Lösch-Button Klick"""
        if self.on_delete:
            self.on_delete(self)
    
    def get_condition_data(self):
        """
        Gibt Bedingungsdaten zurück
        
        Returns:
            dict oder None: {
                'operator': str,  # Internal name (contains, equals, etc.)
                'value': str,
                'not': bool
            }
        """
        value = self.value_input.text().strip()
        if not value:
            return None
        
        return {
            'operator': self.operator_combo.currentData(),
            'operator_display': self.operator_combo.currentText(),
            'value': value,
            'not': self.not_checkbox.isChecked()
        }
    
    def set_condition_data(self, data):
        """Setzt Bedingungsdaten"""
        if not data:
            return
        
        # Operator setzen
        operator = data.get('operator', 'contains')
        index = self.operator_combo.findData(operator)
        if index >= 0:
            self.operator_combo.setCurrentIndex(index)
        
        # Wert setzen
        self.value_input.setText(data.get('value', ''))
        
        # NOT setzen
        self.not_checkbox.setChecked(data.get('not', False))


class PdvmComplexFilterDetailDialog(QDialog):
    """
    Detail-Dialog für komplexe Filter-Bedingungen eines Feldes
    
    Features:
    - Mehrere Bedingungen pro Feld
    - UND/ODER Verknüpfung
    - Verschiedene Operatoren
    - NOT-Unterstützung
    - Visuelle Vorschau der Bedingungen
    """
    
    def __init__(self, parent, column_name, column_display_name, existing_conditions=None, logic_mode='UND'):
        super().__init__(parent)
        self.column_name = column_name
        self.column_display_name = column_display_name
        self.existing_conditions = existing_conditions or []
        self.logic_mode = logic_mode  # 'UND' oder 'ODER'
        
        self.condition_widgets = []
        
        self._init_ui()
        self._load_existing_conditions()
        
        logger.info(f"🔧 Detail-Dialog für Feld: {column_display_name} ({len(self.existing_conditions)} Bedingungen)")
    
    def _init_ui(self):
        """Initialisiert Dialog-UI"""
        self.setWindowTitle(f"Komplexe Filter-Details: {self.column_display_name}")
        self.setMinimumSize(650, 400)
        
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        
        # Header
        header_label = QLabel(f"🔧 Komplexe Bedingungen für: {self.column_display_name}")
        header_label.setFont(QFont("Arial", 11, QFont.Bold))
        header_label.setStyleSheet("color: #1976D2; padding: 5px;")
        main_layout.addWidget(header_label)
        
        # Info Label
        info_label = QLabel("Definieren Sie mehrere Bedingungen für dieses Feld:")
        info_label.setStyleSheet("color: #666; padding: 2px;")
        main_layout.addWidget(info_label)
        
        # Scroll Area für Bedingungen
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(200)
        
        scroll_widget = QWidget()
        self.conditions_layout = QVBoxLayout(scroll_widget)
        self.conditions_layout.setSpacing(5)
        self.conditions_layout.addStretch()
        
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)
        
        # Bedingung hinzufügen Button
        add_btn = QPushButton("➕ Neue Bedingung hinzufügen")
        add_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        add_btn.clicked.connect(self._add_condition)
        main_layout.addWidget(add_btn)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(separator)
        
        # UND/ODER Toggle + Vorschau
        control_layout = QHBoxLayout()
        
        # UND/ODER Toggle
        logic_label = QLabel("Verknüpfung:")
        logic_label.setFont(QFont("Arial", 9, QFont.Bold))
        control_layout.addWidget(logic_label)
        
        self.logic_toggle_btn = QPushButton(self.logic_mode)
        self.logic_toggle_btn.setFixedSize(80, 35)
        self.logic_toggle_btn.clicked.connect(self._toggle_logic)
        self._update_logic_button_style()
        control_layout.addWidget(self.logic_toggle_btn)
        
        control_layout.addStretch()
        
        # Vorschau Label
        self.preview_label = QLabel("Vorschau: (keine Bedingungen)")
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: #f5f5f5;
                padding: 8px;
                border: 1px solid #ccc;
                border-radius: 4px;
                font-family: Consolas, monospace;
                font-size: 9pt;
            }
        """)
        self.preview_label.setWordWrap(True)
        control_layout.addWidget(self.preview_label, 1)
        
        main_layout.addLayout(control_layout)
        
        # Button Bar
        button_layout = QHBoxLayout()
        
        # Alle löschen
        clear_btn = QPushButton("🗑️ Alle löschen")
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #da190b;
            }
        """)
        clear_btn.clicked.connect(self._clear_all_conditions)
        button_layout.addWidget(clear_btn)
        
        button_layout.addStretch()
        
        # Abbrechen
        cancel_btn = QPushButton("❌ Abbrechen")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #9E9E9E;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #757575;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        # OK
        ok_btn = QPushButton("✅ OK")
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        ok_btn.clicked.connect(self._handle_ok)
        button_layout.addWidget(ok_btn)
        
        main_layout.addLayout(button_layout)
        
        # Initial eine leere Bedingung hinzufügen, wenn keine vorhanden
        if not self.existing_conditions:
            self._add_condition()
    
    def _add_condition(self):
        """Fügt eine neue Bedingungszeile hinzu"""
        condition_widget = ComplexConditionWidget(
            parent=self,
            on_delete=self._remove_condition
        )
        
        self.condition_widgets.append(condition_widget)
        
        # Füge vor dem Stretch ein
        self.conditions_layout.insertWidget(
            self.conditions_layout.count() - 1,
            condition_widget
        )
        
        self._update_preview()
        logger.info(f"➕ Neue Bedingung hinzugefügt (Gesamt: {len(self.condition_widgets)})")
    
    def _remove_condition(self, widget):
        """Entfernt eine Bedingungszeile"""
        if widget in self.condition_widgets:
            self.condition_widgets.remove(widget)
            widget.deleteLater()
            self._update_preview()
            logger.info(f"🗑️ Bedingung entfernt (Verbleibend: {len(self.condition_widgets)})")
    
    def _toggle_logic(self):
        """Toggle zwischen UND und ODER"""
        self.logic_mode = 'ODER' if self.logic_mode == 'UND' else 'UND'
        self.logic_toggle_btn.setText(self.logic_mode)
        self._update_logic_button_style()
        self._update_preview()
        logger.info(f"🔄 Logik geändert auf: {self.logic_mode}")
    
    def _update_logic_button_style(self):
        """Aktualisiert Button-Stil basierend auf Logik"""
        if self.logic_mode == 'UND':
            self.logic_toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    font-weight: bold;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #0b7dda;
                }
            """)
        else:  # ODER
            self.logic_toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: #FF9800;
                    color: white;
                    font-weight: bold;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #e68900;
                }
            """)
    
    def _update_preview(self):
        """Aktualisiert Vorschau der Bedingungen"""
        conditions = self.get_all_conditions()
        
        if not conditions:
            self.preview_label.setText("Vorschau: (keine Bedingungen)")
            return
        
        # Baue lesbare Vorschau
        preview_parts = []
        for cond in conditions:
            not_prefix = "NOT " if cond.get('not', False) else ""
            op_display = cond.get('operator_display', cond.get('operator', '?'))
            value = cond.get('value', '')
            preview_parts.append(f"{not_prefix}{self.column_display_name} {op_display} '{value}'")
        
        separator = f" {self.logic_mode} "
        preview_text = separator.join(preview_parts)
        
        self.preview_label.setText(f"Vorschau: {preview_text}")
    
    def _clear_all_conditions(self):
        """Löscht alle Bedingungen"""
        # Deutsche Button-Labels
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Alle löschen?")
        msg_box.setText("Möchten Sie wirklich alle Bedingungen löschen?")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg_box.setDefaultButton(QMessageBox.No)
        
        # Deutsche Übersetzungen
        yes_button = msg_box.button(QMessageBox.Yes)
        yes_button.setText("Ja")
        no_button = msg_box.button(QMessageBox.No)
        no_button.setText("Nein")
        
        reply = msg_box.exec_()
        
        if reply == QMessageBox.Yes:
            for widget in self.condition_widgets[:]:
                self._remove_condition(widget)
            
            # Füge eine leere Bedingung hinzu
            self._add_condition()
            logger.info("🗑️ Alle Bedingungen gelöscht")
    
    def _load_existing_conditions(self):
        """Lädt existierende Bedingungen"""
        if not self.existing_conditions:
            return
        
        for condition_data in self.existing_conditions:
            self._add_condition()
            # Setze Daten in das zuletzt hinzugefügte Widget
            if self.condition_widgets:
                self.condition_widgets[-1].set_condition_data(condition_data)
        
        self._update_preview()
        logger.info(f"📂 {len(self.existing_conditions)} Bedingungen geladen")
    
    def _handle_ok(self):
        """Behandelt OK-Button"""
        conditions = self.get_all_conditions()
        
        if not conditions:
            # Deutsche Button-Labels
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Keine Bedingungen")
            msg_box.setText("Keine gültigen Bedingungen definiert. Trotzdem schließen?")
            msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
            msg_box.setDefaultButton(QMessageBox.No)
            
            # Deutsche Übersetzungen
            yes_button = msg_box.button(QMessageBox.Yes)
            yes_button.setText("Ja")
            no_button = msg_box.button(QMessageBox.No)
            no_button.setText("Nein")
            
            reply = msg_box.exec_()
            
            if reply == QMessageBox.No:
                return
        
        logger.info(f"✅ Detail-Dialog geschlossen mit {len(conditions)} Bedingungen ({self.logic_mode})")
        self.accept()
    
    def get_all_conditions(self):
        """
        Gibt alle definierten Bedingungen zurück
        
        Returns:
            list: Liste von Condition-Dictionaries
        """
        conditions = []
        for widget in self.condition_widgets:
            condition_data = widget.get_condition_data()
            if condition_data:
                conditions.append(condition_data)
        return conditions
    
    def get_result_data(self):
        """
        Gibt komplette Ergebnis-Daten zurück
        
        Returns:
            dict: {
                'column': str,
                'conditions': list,
                'logic': str  # 'UND' oder 'ODER'
            }
        """
        return {
            'column': self.column_name,
            'column_display': self.column_display_name,
            'conditions': self.get_all_conditions(),
            'logic': self.logic_mode
        }
