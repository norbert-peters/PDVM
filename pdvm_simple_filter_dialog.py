# pdvm_simple_filter_dialog.py
"""
EINFACHER FILTER DIALOG

Zeigt pro sichtbare Spalte ein Suchfeld mit:
- +/- Toggle (Positiv/Negativ)
- Nur "enthält" Operator
- UND-Verknüpfung zwischen Feldern
- Persistente Speicherung in App-DB
"""

import logging
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QLineEdit, QFrame, QScrollArea, QWidget)
from PyQt5.QtCore import Qt

logger = logging.getLogger(__name__)


class SimpleFieldWidget(QFrame):
    """Widget für ein einzelnes einfaches Filter-Feld"""
    
    def __init__(self, field_key, field_label, parent=None):
        super().__init__(parent)
        self.field_key = field_key
        self.field_label = field_label
        self.is_positive = True  # True = +, False = -
        
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(1)
        self.init_ui()
    
    def init_ui(self):
        """Erstelle UI für einfaches Feld"""
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Label
        self.label = QLabel(f"{self.field_label}:")
        self.label.setMinimumWidth(150)
        layout.addWidget(self.label)
        
        # Input
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText(f"Suche in {self.field_label}...")
        layout.addWidget(self.input_field)
        
        # +/- Button
        self.toggle_button = QPushButton("✅ +")
        self.toggle_button.setFixedWidth(60)
        self.toggle_button.clicked.connect(self._toggle_mode)
        self._update_button_style()
        layout.addWidget(self.toggle_button)
        
        self.setLayout(layout)
    
    def _toggle_mode(self):
        """Schalte zwischen + und - um"""
        self.is_positive = not self.is_positive
        self._update_button_style()
    
    def _update_button_style(self):
        """Aktualisiere Button-Style"""
        if self.is_positive:
            self.toggle_button.setText("✅ +")
            self.toggle_button.setStyleSheet("""
                QPushButton { 
                    background-color: #27ae60; 
                    color: white; 
                    font-weight: bold; 
                    border-radius: 4px;
                }
                QPushButton:hover { background-color: #229954; }
            """)
        else:
            self.toggle_button.setText("❌ -")
            self.toggle_button.setStyleSheet("""
                QPushButton { 
                    background-color: #e74c3c; 
                    color: white; 
                    font-weight: bold; 
                    border-radius: 4px;
                }
                QPushButton:hover { background-color: #c0392b; }
            """)
    
    def get_value(self):
        """Hole Wert"""
        return self.input_field.text().strip()
    
    def get_mode(self):
        """Hole Modus (True = positiv, False = negativ)"""
        return self.is_positive
    
    def set_value(self, value):
        """Setze Wert"""
        self.input_field.setText(value or '')
    
    def set_mode(self, is_positive):
        """Setze Modus"""
        self.is_positive = is_positive
        self._update_button_style()


class PdvmSimpleFilterDialog(QDialog):
    """
    EINFACHER FILTER DIALOG
    
    Features:
    - Ein Suchfeld pro sichtbare Spalte
    - +/- Toggle (Positiv/Negativ)
    - Nur "enthält" Operator
    - UND-Verknüpfung zwischen Feldern
    - Persistente Speicherung
    """
    
    def __init__(self, view_guid, visible_columns, column_control, parent=None):
        super().__init__(parent)
        self.view_guid = view_guid
        self.visible_columns = visible_columns
        self.column_control = column_control
        self.field_widgets = {}
        
        self.setWindowTitle("🔍 Einfaches Filter")
        self.setModal(True)
        self.resize(700, 600)
        
        self.init_ui()
        self.load_persistent_data()
    
    def init_ui(self):
        """Erstelle UI"""
        layout = QVBoxLayout()
        
        # Titel
        title = QLabel("🔍 Einfaches Filter")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px; color: #2c3e50;")
        layout.addWidget(title)
        
        # Info
        info = QLabel("💡 Sucht mit 'enthält' Operator. Mehrere Felder werden mit UND verknüpft.")
        info.setStyleSheet("color: #7f8c8d; font-size: 11px; margin-bottom: 10px;")
        layout.addWidget(info)
        
        # Scroll-Bereich für Felder
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #ddd; }")
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        scroll_layout.setSpacing(2)
        
        # Erstelle Field-Widgets für sichtbare Spalten
        for col_key in self.visible_columns:
            if col_key in self.column_control:
                col_data = self.column_control[col_key]
                label = col_data.get('label', col_key)
                
                widget = SimpleFieldWidget(col_key, label, self)
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
            widget.set_value('')
            widget.set_mode(True)
    
    def _apply_filter(self):
        """Filter anwenden"""
        # Sammle Filter-Daten
        filter_data = {}
        
        for field_key, widget in self.field_widgets.items():
            value = widget.get_value()
            if value:  # Nur nicht-leere Felder
                filter_data[field_key] = {
                    'value': value,
                    'mode': 'positive' if widget.get_mode() else 'negative'
                }
        
        logger.info(f"🔍 Einfaches Filter angewendet: {len(filter_data)} Felder")
        
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
            
            # Lade aus App-DB: uid=user_guid, gruppe=view_guid, feld=einfach
            data, _ = gcs._app_db.get_value(self.view_guid, 'einfach')
            
            if data and isinstance(data, dict):
                logger.info(f"🔄 Lade persistent: {len(data)} Felder")
                
                for field_key, field_data in data.items():
                    if field_key in self.field_widgets:
                        widget = self.field_widgets[field_key]
                        widget.set_value(field_data.get('value', ''))
                        mode = field_data.get('mode', 'positive')
                        widget.set_mode(mode == 'positive')
        
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden persistent: {e}")
    
    def save_persistent_data(self, filter_data):
        """Speichere Daten persistent"""
        try:
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            if not gcs:
                return
            
            # Speichere in App-DB: uid=user_guid, gruppe=view_guid, feld=einfach
            gcs._app_db.set_value(self.view_guid, 'einfach', filter_data)
            logger.info(f"💾 Persistent gespeichert: {len(filter_data)} Felder")
        
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern persistent: {e}")


def show_simple_filter_dialog(parent, view_guid, visible_columns, column_control):
    """
    Zeige einfachen Filter-Dialog
    
    Args:
        parent: Parent-Widget
        view_guid: View-GUID für Persistierung
        visible_columns: Liste sichtbarer Spalten
        column_control: Column-Control Dictionary
    
    Returns:
        filter_data dict oder None
    """
    dialog = PdvmSimpleFilterDialog(view_guid, visible_columns, column_control, parent)
    
    if dialog.exec_():
        return dialog.get_filter_data()
    
    return None
