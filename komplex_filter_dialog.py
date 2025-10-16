"""
KOMPLEXER FILTER DIALOG - V3
=============================

Komplexer Dialog mit 4-Positionen Struktur:
Position 1: AND/OR (Logische Verknüpfung)
Position 2: IS/NOT (Negation)
Position 3: Operator (enthält, =, >, etc.)
Position 4: Wert

Unterstützt mehrere Bedingungen pro Feld.
Verwendet KomplexFilterManager für Ausführung.
"""

import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QFrame, QScrollArea, QWidget,
    QComboBox, QGroupBox, QMessageBox
)
from PyQt5.QtCore import Qt

logger = logging.getLogger(__name__)


class ConditionRow(QFrame):
    """Eine Zeile für eine Bedingung (4 Positionen)"""
    
    def __init__(self, is_first=True, parent=None):
        super().__init__(parent)
        self.is_first = is_first
        
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(1)
        self.setStyleSheet("QFrame { background-color: #f9f9f9; margin: 2px; padding: 5px; }")
        
        self.init_ui()
    
    def init_ui(self):
        """Erstelle 4-Positionen UI"""
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Position 1: AND/OR (nur wenn nicht erste Bedingung)
        if self.is_first:
            logic_label = QLabel("FIRST")
            logic_label.setFixedWidth(80)
            logic_label.setStyleSheet("font-weight: bold; color: #27ae60;")
            layout.addWidget(logic_label)
            self.logic_combo = None
        else:
            self.logic_combo = QComboBox()
            self.logic_combo.addItems(["AND", "OR"])
            self.logic_combo.setFixedWidth(80)
            layout.addWidget(self.logic_combo)
        
        # Position 2: IS/NOT
        self.negation_combo = QComboBox()
        self.negation_combo.addItems(["IS", "NOT"])
        self.negation_combo.setFixedWidth(70)
        layout.addWidget(self.negation_combo)
        
        # Position 3: Operator
        self.operator_combo = QComboBox()
        self.operator_combo.addItems([
            "enthält",
            "beginnt mit",
            "endet mit",
            "ist gleich",
            "ist leer",
            ">",
            "<",
            ">=",
            "<="
        ])
        self.operator_combo.setFixedWidth(120)
        layout.addWidget(self.operator_combo)
        
        # Position 4: Wert
        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText("Wert...")
        layout.addWidget(self.value_input)
        
        # Löschen-Button (nur wenn nicht erste Bedingung)
        if not self.is_first:
            self.delete_button = QPushButton("🗑️")
            self.delete_button.setFixedWidth(40)
            self.delete_button.setStyleSheet("""
                QPushButton { 
                    background-color: #e74c3c; 
                    color: white;
                    border-radius: 3px;
                }
                QPushButton:hover { background-color: #c0392b; }
            """)
            layout.addWidget(self.delete_button)
        
        self.setLayout(layout)
    
    def get_condition(self):
        """Hole Bedingung als Dict"""
        logic_op = "FIRST" if self.is_first else self.logic_combo.currentText()
        
        return {
            'logic': logic_op,
            'negation': self.negation_combo.currentText(),
            'operator': self.operator_combo.currentText(),
            'value': self.value_input.text().strip()
        }
    
    def set_condition(self, condition):
        """Setze Bedingung aus Dict"""
        # Negation
        idx = self.negation_combo.findText(condition.get('negation', 'IS'))
        if idx >= 0:
            self.negation_combo.setCurrentIndex(idx)
        
        # Operator
        idx = self.operator_combo.findText(condition.get('operator', 'enthält'))
        if idx >= 0:
            self.operator_combo.setCurrentIndex(idx)
        
        # Wert
        self.value_input.setText(condition.get('value', ''))
        
        # Logic (nur wenn nicht FIRST)
        if not self.is_first and self.logic_combo:
            idx = self.logic_combo.findText(condition.get('logic', 'AND'))
            if idx >= 0:
                self.logic_combo.setCurrentIndex(idx)


class FieldGroup(QGroupBox):
    """Gruppe für ein Feld mit mehreren Bedingungen"""
    
    def __init__(self, field_key, field_label, parent=None):
        super().__init__(f"📋 {field_label}", parent)
        self.field_key = field_key
        self.field_label = field_label
        self.condition_rows = []
        
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #3498db;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        self.init_ui()
    
    def init_ui(self):
        """Erstelle UI"""
        self.main_layout = QVBoxLayout()
        
        # Container für Bedingungen
        self.conditions_layout = QVBoxLayout()
        self.main_layout.addLayout(self.conditions_layout)
        
        # Erste Bedingung hinzufügen
        self.add_condition()
        
        # Button für weitere Bedingung
        self.add_button = QPushButton("➕ Weitere Bedingung")
        self.add_button.setStyleSheet("""
            QPushButton { 
                background-color: #27ae60; 
                color: white;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover { background-color: #229954; }
        """)
        self.add_button.clicked.connect(self.add_condition)
        self.main_layout.addWidget(self.add_button)
        
        self.setLayout(self.main_layout)
    
    def add_condition(self):
        """Füge neue Bedingung hinzu"""
        is_first = len(self.condition_rows) == 0
        row = ConditionRow(is_first=is_first, parent=self)
        
        # Delete-Button verbinden (wenn nicht erste Zeile)
        if not is_first and hasattr(row, 'delete_button'):
            row.delete_button.clicked.connect(lambda: self.remove_condition(row))
        
        self.condition_rows.append(row)
        self.conditions_layout.addWidget(row)
    
    def remove_condition(self, row):
        """Entferne Bedingung"""
        if row in self.condition_rows and len(self.condition_rows) > 1:
            self.condition_rows.remove(row)
            row.deleteLater()
    
    def get_conditions(self):
        """Hole alle Bedingungen"""
        conditions = []
        for row in self.condition_rows:
            cond = row.get_condition()
            if cond['value']:  # Nur wenn Wert vorhanden
                conditions.append(cond)
        return conditions
    
    def set_conditions(self, conditions):
        """Setze Bedingungen"""
        # Lösche bestehende (außer erste)
        while len(self.condition_rows) > 1:
            self.remove_condition(self.condition_rows[-1])
        
        # Setze Bedingungen
        for i, cond in enumerate(conditions):
            if i >= len(self.condition_rows):
                self.add_condition()
            self.condition_rows[i].set_condition(cond)


class ComplexFilterDialog(QDialog):
    """
    KOMPLEXER FILTER DIALOG V3
    
    Zeigt 4-Positionen Struktur für alle sichtbaren Spalten.
    Verwendet KomplexFilterManager für Filter-Ausführung.
    """
    
    def __init__(self, parent, view_guid, controls_config, filter_projection, matrix_manager):
        """
        Args:
            parent: Parent-Widget
            view_guid: GUID der View
            controls_config: Dict mit allen Controls
            filter_projection: Liste der Spalten-Keys die gefiltert werden sollen
            matrix_manager: Matrix Manager für Filter-Ausführung
        """
        super().__init__(parent)
        
        self.view_guid = view_guid
        self.controls_config = controls_config
        self.filter_projection = filter_projection  # NEU: Nur Filter-Spalten
        self.matrix_manager = matrix_manager
        self.field_groups = {}
        
        self.setWindowTitle("🔬 Komplexes Filter")
        self.setModal(True)
        self.resize(900, 700)
        
        self.init_ui()
        self.load_existing_filters()
    
    def init_ui(self):
        """Erstelle UI"""
        layout = QVBoxLayout()
        
        # Titel
        title = QLabel("🔬 Komplexes Filter")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px; color: #2c3e50;")
        layout.addWidget(title)
        
        # Info
        info = QLabel("💡 4-Positionen Struktur: AND/OR + IS/NOT + Operator + Wert. Mehrere Bedingungen pro Feld möglich.")
        info.setStyleSheet("color: #7f8c8d; font-size: 11px; margin-bottom: 10px;")
        layout.addWidget(info)
        
        # Scroll-Bereich für Felder
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #ddd; }")
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_layout.setSpacing(5)
        
        # Erstelle Field-Groups für Spalten aus Filter-Projektion
        for control_key in self.filter_projection:
            if control_key in self.controls_config:
                control_data = self.controls_config[control_key]
                label = control_data.get('label', control_key)
                
                group = FieldGroup(control_key, label, self)
                self.field_groups[control_key] = group
                scroll_layout.addWidget(group)
        
        scroll_layout.addStretch()
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        clear_button = QPushButton("🗑️ Alle löschen")
        clear_button.clicked.connect(self._clear_all)
        button_layout.addWidget(clear_button)
        
        button_layout.addStretch()
        
        cancel_button = QPushButton("❌ Abbrechen")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        apply_button = QPushButton("✅ Filter anwenden")
        apply_button.setStyleSheet("""
            QPushButton { 
                background-color: #3498db; 
                color: white; 
                font-weight: bold; 
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        apply_button.clicked.connect(self._apply_filter)
        button_layout.addWidget(apply_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def load_existing_filters(self):
        """Lädt existierende Filter aus app_db - IMMER, unabhängig von s_source!"""
        try:
            from global_gcs import gcs
            
            if not gcs:
                return
            
            # Lade 'komplex' Parameter - IMMER, auch wenn nicht aktiv!
            # Die Parameter bleiben erhalten, auch wenn aktuell ein anderer Filter aktiv ist
            komplex_data, _ = gcs._app_db.get_value(self.view_guid, 'komplex')
            
            logger.info(f"📥 Lade Komplex-Filter Parameter (unabhängig von s_source)")
            
            if komplex_data and isinstance(komplex_data, dict):
                logger.info(f"📋 Lade {len(komplex_data)} gespeicherte Filter-Felder")
                
                for field_key, field_data in komplex_data.items():
                    if field_key in self.field_groups:
                        if isinstance(field_data, dict):
                            conditions = field_data.get('conditions', [])
                            if conditions:
                                self.field_groups[field_key].set_conditions(conditions)
                                logger.info(f"✅ Feld {field_key}: {len(conditions)} Bedingungen geladen")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden Filter: {e}")
    
    def _clear_all(self):
        """Lösche alle Eingaben"""
        for group in self.field_groups.values():
            # Setze erste Bedingung zurück
            while len(group.condition_rows) > 1:
                group.remove_condition(group.condition_rows[-1])
            
            if group.condition_rows:
                group.condition_rows[0].set_condition({
                    'logic': 'FIRST',
                    'negation': 'IS',
                    'operator': 'enthält',
                    'value': ''
                })
    
    def _apply_filter(self):
        """Filter anwenden - ruft KomplexFilterManager auf"""
        try:
            # Sammle alle Felder mit Bedingungen
            filter_params = {}
            for field_key, group in self.field_groups.items():
                conditions = group.get_conditions()
                if conditions:  # Nur Felder mit Bedingungen
                    filter_params[field_key] = conditions
            
            # Wenn keine Parameter: Filter löschen (s_string/s_source = None)
            if not filter_params:
                logger.info(f"🗑️ Keine Parameter - Filter wird gelöscht")
                
                from komplex_filter_manager import KomplexFilterManager
                manager = KomplexFilterManager(
                    view_guid=self.view_guid,
                    matrix_manager=self.matrix_manager
                )
                
                # Lösche nur s_string/s_source, Parameter 'komplex' bleiben
                success = manager.clear_komplex_filter()
                
                if success:
                    logger.info("✅ Komplexer Filter gelöscht")
                    self.accept()
                else:
                    QMessageBox.warning(self, "Fehler", "Filter konnte nicht gelöscht werden")
                return
            
            logger.info(f"✅ Filter anwenden: {len(filter_params)} Felder")
            
            # KomplexFilterManager verwenden
            from komplex_filter_manager import KomplexFilterManager
            
            manager = KomplexFilterManager(
                view_guid=self.view_guid,
                matrix_manager=self.matrix_manager
            )
            
            success = manager.execute_komplex_filter(filter_params)
            
            if success:
                logger.info("✅ Komplexer Filter erfolgreich ausgeführt")
                self.accept()  # Dialog schließen
            else:
                QMessageBox.warning(
                    self,
                    "Fehler",
                    "Beim Ausführen des Filters ist ein Fehler aufgetreten."
                )
            
        except Exception as e:
            logger.error(f"❌ Filter-Ausführung fehlgeschlagen: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            QMessageBox.critical(
                self,
                "Fehler",
                f"Kritischer Fehler beim Filtern:\n\n{str(e)}"
            )
