# pdvm_complex_filter_dialog.py
"""
KOMPLEXER FILTER DIALOG

4-Positionen Struktur für jeden Filter:
Position 1: FIRST/AND/OR (Logische Verknüpfung)
Position 2: IS/NOT (Negation)
Position 3: Operator (=, enthält, beginnt mit, etc.)
Position 4: Wert

Unterstützt mehrere Bedingungen pro Feld.
Persistente Speicherung in App-DB.
"""

import logging
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QLineEdit, QFrame, QScrollArea, QWidget,
                             QComboBox, QGroupBox)
from PyQt5.QtCore import Qt

logger = logging.getLogger(__name__)


class SearchCondition:
    """Eine einzelne Suchbedingung mit 4-Positionen Struktur"""
    
    def __init__(self, value="", operator_type="enthält", logic_operator="FIRST", negation="IS"):
        self.value = value
        self.operator_type = operator_type  # Position 3
        self.logic_operator = logic_operator  # Position 1
        self.negation = negation  # Position 2
    
    def to_dict(self):
        return {
            'value': self.value,
            'operator_type': self.operator_type,
            'logic_operator': self.logic_operator,
            'negation': self.negation
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            value=data.get('value', ''),
            operator_type=data.get('operator_type', 'enthält'),
            logic_operator=data.get('logic_operator', 'FIRST'),
            negation=data.get('negation', 'IS')
        )


class ConditionWidget(QFrame):
    """Widget für eine einzelne Bedingung (4 Positionen)"""
    
    def __init__(self, condition=None, is_first=True, parent=None):
        super().__init__(parent)
        self.is_first = is_first
        
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(1)
        self.setStyleSheet("QFrame { background-color: #f9f9f9; margin: 2px; padding: 5px; }")
        
        self.init_ui()
        
        if condition:
            self.set_condition(condition)
    
    def init_ui(self):
        """Erstelle 4-Positionen UI"""
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Position 1: FIRST/AND/OR
        self.logic_combo = QComboBox()
        if self.is_first:
            self.logic_combo.addItems(["FIRST"])
            self.logic_combo.setEnabled(False)
        else:
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
        
        # Löschen-Button
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
        """Hole Bedingung"""
        return SearchCondition(
            value=self.value_input.text().strip(),
            operator_type=self.operator_combo.currentText(),
            logic_operator=self.logic_combo.currentText(),
            negation=self.negation_combo.currentText()
        )
    
    def set_condition(self, condition):
        """Setze Bedingung"""
        self.value_input.setText(condition.value)
        
        # Operator
        idx = self.operator_combo.findText(condition.operator_type)
        if idx >= 0:
            self.operator_combo.setCurrentIndex(idx)
        
        # Negation
        idx = self.negation_combo.findText(condition.negation)
        if idx >= 0:
            self.negation_combo.setCurrentIndex(idx)
        
        # Logic (nur wenn nicht FIRST)
        if not self.is_first:
            idx = self.logic_combo.findText(condition.logic_operator)
            if idx >= 0:
                self.logic_combo.setCurrentIndex(idx)


class ComplexFieldWidget(QFrame):
    """Widget für ein Feld mit mehreren Bedingungen"""
    
    def __init__(self, field_key, field_label, parent=None):
        super().__init__(parent)
        self.field_key = field_key
        self.field_label = field_label
        self.condition_widgets = []
        
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(2)
        self.init_ui()
    
    def init_ui(self):
        """Erstelle UI für Feld"""
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        
        # Header
        header_layout = QHBoxLayout()
        
        label = QLabel(f"📋 {self.field_label}")
        label.setStyleSheet("font-weight: bold; font-size: 12px;")
        header_layout.addWidget(label)
        
        header_layout.addStretch()
        
        # Hinzufügen-Button
        self.add_button = QPushButton("➕ Bedingung")
        self.add_button.setFixedWidth(120)
        self.add_button.setStyleSheet("""
            QPushButton { 
                background-color: #27ae60; 
                color: white;
                border-radius: 3px;
                padding: 3px;
            }
            QPushButton:hover { background-color: #229954; }
        """)
        self.add_button.clicked.connect(self._add_condition)
        header_layout.addWidget(self.add_button)
        
        self.main_layout.addLayout(header_layout)
        
        # Container für Bedingungen
        self.conditions_layout = QVBoxLayout()
        self.conditions_layout.setSpacing(2)
        self.main_layout.addLayout(self.conditions_layout)
        
        # Erste Bedingung hinzufügen
        self._add_condition()
        
        self.setLayout(self.main_layout)
    
    def _add_condition(self):
        """Füge neue Bedingung hinzu"""
        is_first = len(self.condition_widgets) == 0
        widget = ConditionWidget(is_first=is_first, parent=self)
        widget.delete_button.clicked.connect(lambda: self._remove_condition(widget))
        
        self.condition_widgets.append(widget)
        self.conditions_layout.addWidget(widget)
        
        logger.debug(f"➕ Bedingung hinzugefügt für {self.field_key} (gesamt: {len(self.condition_widgets)})")
    
    def _remove_condition(self, widget):
        """Entferne Bedingung"""
        if len(self.condition_widgets) <= 1:
            logger.warning("⚠️ Mindestens eine Bedingung muss bleiben")
            return
        
        self.condition_widgets.remove(widget)
        self.conditions_layout.removeWidget(widget)
        widget.deleteLater()
        
        # Erste Bedingung aktualisieren (muss immer FIRST sein)
        if self.condition_widgets:
            first = self.condition_widgets[0]
            first.is_first = True
            first.logic_combo.clear()
            first.logic_combo.addItems(["FIRST"])
            first.logic_combo.setEnabled(False)
        
        logger.debug(f"🗑️ Bedingung entfernt von {self.field_key} (gesamt: {len(self.condition_widgets)})")
    
    def get_conditions(self):
        """Hole alle Bedingungen"""
        conditions = []
        for widget in self.condition_widgets:
            cond = widget.get_condition()
            if cond.value:  # Nur nicht-leere Bedingungen
                conditions.append(cond)
        return conditions
    
    def set_conditions(self, conditions):
        """Setze Bedingungen"""
        # Lösche alle bestehenden
        while len(self.condition_widgets) > 0:
            widget = self.condition_widgets[0]
            self.condition_widgets.remove(widget)
            self.conditions_layout.removeWidget(widget)
            widget.deleteLater()
        
        # Erstelle neue
        for i, cond in enumerate(conditions):
            is_first = (i == 0)
            widget = ConditionWidget(cond, is_first, self)
            widget.delete_button.clicked.connect(lambda w=widget: self._remove_condition(w))
            
            self.condition_widgets.append(widget)
            self.conditions_layout.addWidget(widget)


class PdvmComplexFilterDialog(QDialog):
    """
    KOMPLEXER FILTER DIALOG
    
    Features:
    - 4-Positionen Struktur pro Bedingung
    - Mehrere Bedingungen pro Feld
    - Logische Verknüpfung (AND/OR)
    - Negation (IS/NOT)
    - Verschiedene Operatoren
    - Persistente Speicherung
    """
    
    def __init__(self, view_guid, visible_columns, column_control, parent=None):
        super().__init__(parent)
        self.view_guid = view_guid
        self.visible_columns = visible_columns
        self.column_control = column_control
        self.field_widgets = {}
        
        self.setWindowTitle("🔍 Komplexes Filter")
        self.setModal(True)
        self.resize(900, 700)
        
        self.init_ui()
        self.load_persistent_data()
    
    def init_ui(self):
        """Erstelle UI"""
        layout = QVBoxLayout()
        
        # Titel
        title = QLabel("🔍 Komplexes Filter")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px; color: #2c3e50;")
        layout.addWidget(title)
        
        # Info
        info = QLabel("💡 4-Positionen Struktur: FIRST/AND/OR | IS/NOT | Operator | Wert")
        info.setStyleSheet("color: #7f8c8d; font-size: 11px; margin-bottom: 10px;")
        layout.addWidget(info)
        
        # Scroll-Bereich für Felder
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #ddd; }")
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_layout.setSpacing(5)
        
        # Erstelle Field-Widgets für sichtbare Spalten
        for col_key in self.visible_columns:
            if col_key in self.column_control:
                col_data = self.column_control[col_key]
                label = col_data.get('label', col_key)
                
                widget = ComplexFieldWidget(col_key, label, self)
                self.field_widgets[col_key] = widget
                scroll_layout.addWidget(widget)
        
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
    
    def _clear_all(self):
        """Lösche alle Eingaben"""
        for widget in self.field_widgets.values():
            widget.set_conditions([])
            # Eine leere Bedingung hinzufügen
            widget._add_condition()
    
    def _apply_filter(self):
        """Filter anwenden"""
        # Sammle Filter-Daten
        filter_data = {}
        
        for field_key, widget in self.field_widgets.items():
            conditions = widget.get_conditions()
            if conditions:  # Nur Felder mit Bedingungen
                filter_data[field_key] = {
                    'conditions': [c.to_dict() for c in conditions]
                }
        
        logger.info(f"🔍 Komplexes Filter angewendet: {len(filter_data)} Felder")
        
        # Speichere persistent
        self.save_persistent_data(filter_data)
        
        # Setze als Dialog-Result
        self.filter_data = filter_data
        self.accept()
    
    def get_filter_data(self):
        """Hole Filter-Daten"""
        return getattr(self, 'filter_data', {})
    
    def load_persistent_data(self):
        """Lade persistent gespeicherte Daten"""
        try:
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            if not gcs:
                return
            
            # Lade aus App-DB: uid=user_guid, gruppe=view_guid, feld=komplex
            data, _ = gcs._app_db.get_value(self.view_guid, 'komplex')
            
            if data and isinstance(data, dict):
                logger.info(f"🔄 Lade persistent: {len(data)} Felder")
                
                for field_key, field_data in data.items():
                    if field_key in self.field_widgets:
                        widget = self.field_widgets[field_key]
                        conditions_data = field_data.get('conditions', [])
                        conditions = [SearchCondition.from_dict(c) for c in conditions_data]
                        if conditions:
                            widget.set_conditions(conditions)
        
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden persistent: {e}")
    
    def save_persistent_data(self, filter_data):
        """Speichere Daten persistent"""
        try:
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            if not gcs:
                return
            
            # Speichere in App-DB: uid=user_guid, gruppe=view_guid, feld=komplex
            gcs._app_db.set_value(self.view_guid, 'komplex', filter_data)
            logger.info(f"💾 Persistent gespeichert: {len(filter_data)} Felder")
        
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern persistent: {e}")


def show_complex_filter_dialog(parent, view_guid, visible_columns, column_control):
    """
    Zeige komplexen Filter-Dialog
    
    Args:
        parent: Parent-Widget
        view_guid: View-GUID für Persistierung
        visible_columns: Liste sichtbarer Spalten
        column_control: Column-Control Dictionary
    
    Returns:
        filter_data dict oder None
    """
    dialog = PdvmComplexFilterDialog(view_guid, visible_columns, column_control, parent)
    
    if dialog.exec_():
        return dialog.get_filter_data()
    
    return None
