# pdvm_dropdown_filter_dialog_v3.py
"""
Dropdown-Filter-Dialog V3 für neue Architektur
"""

import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QCheckBox, QPushButton, 
    QScrollArea, QLabel, QFrame, QWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

logger = logging.getLogger(__name__)

class PdvmDropdownFilterDialogV3(QDialog):
    """
    Dropdown-Filter-Dialog V3 für neue Original/Show-Spalten-Architektur
    """
    
    def __init__(self, field_name: str, options: dict, current_state: dict = None, parent=None):
        super().__init__(parent)
        self.field_name = field_name
        self.options = options  # key -> display_value
        self.current_state = current_state or {}
        
        # UI Setup
        self.setWindowTitle(f"Dropdown-Filter: {field_name}")
        self.setModal(True)
        self.resize(400, 500)
        
        self._setup_ui()
        self._load_current_state()
    
    def _setup_ui(self):
        """Erstellt die UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Title
        title_label = QLabel(f"🎛️ Dropdown-Filter: {self.field_name}")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        layout.addWidget(title_label)
        
        # Control Area
        self._create_control_area(layout)
        
        # Scroll Area for Options
        self._create_options_area(layout)
        
        # Button Area
        self._create_button_area(layout)
    
    def _create_control_area(self, layout):
        """Erstellt den Kontroll-Bereich"""
        control_frame = QFrame()
        control_frame.setFrameShape(QFrame.StyledPanel)
        control_layout = QVBoxLayout(control_frame)
        
        # Show Empty Checkbox
        self.show_empty_checkbox = QCheckBox("📝 Leere Werte anzeigen")
        self.show_empty_checkbox.setChecked(True)
        control_layout.addWidget(self.show_empty_checkbox)
        
        # Control Buttons
        button_layout = QHBoxLayout()
        
        self.select_all_btn = QPushButton("✅ Alle auswählen")
        self.select_all_btn.clicked.connect(self._select_all)
        button_layout.addWidget(self.select_all_btn)
        
        self.select_none_btn = QPushButton("❌ Alle abwählen")
        self.select_none_btn.clicked.connect(self._select_none)
        button_layout.addWidget(self.select_none_btn)
        
        control_layout.addLayout(button_layout)
        layout.addWidget(control_frame)
    
    def _create_options_area(self, layout):
        """Erstellt den scrollbaren Optionen-Bereich"""
        # Scroll Area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(300)
        
        # Options Widget
        options_widget = QWidget()
        options_layout = QVBoxLayout(options_widget)
        options_layout.setSpacing(5)
        
        # Checkboxes für alle Optionen
        self.option_checkboxes = {}
        
        # Sortierte Optionen
        sorted_options = sorted(self.options.items(), key=lambda x: str(x[1]).lower())
        
        for key, display_value in sorted_options:
            checkbox = QCheckBox(f"{display_value} ({key})")
            checkbox.setChecked(True)  # Default: alle ausgewählt
            self.option_checkboxes[key] = checkbox
            options_layout.addWidget(checkbox)
        
        # Spacer
        options_layout.addStretch()
        
        scroll_area.setWidget(options_widget)
        layout.addWidget(scroll_area)
    
    def _create_button_area(self, layout):
        """Erstellt den Button-Bereich"""
        button_layout = QHBoxLayout()
        
        # Apply Button
        self.apply_btn = QPushButton("✅ Filter anwenden")
        self.apply_btn.setStyleSheet("background-color: #28a745; color: white; font-weight: bold; padding: 8px;")
        self.apply_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.apply_btn)
        
        # Clear Button
        self.clear_btn = QPushButton("🔄 Zurücksetzen")
        self.clear_btn.clicked.connect(self._reset_filter)
        button_layout.addWidget(self.clear_btn)
        
        # Cancel Button
        self.cancel_btn = QPushButton("🚫 Abbrechen")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(button_layout)
    
    def _load_current_state(self):
        """Lädt den aktuellen Filter-Zustand"""
        try:
            selected_keys = self.current_state.get("selected_keys", set())
            show_empty = self.current_state.get("show_empty", True)
            
            # Show Empty Checkbox
            self.show_empty_checkbox.setChecked(show_empty)
            
            # Option Checkboxes
            if selected_keys:
                # Nur ausgewählte Keys aktivieren
                for key, checkbox in self.option_checkboxes.items():
                    checkbox.setChecked(key in selected_keys)
            # Sonst bleiben alle aktiviert (Default)
            
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Laden des Filter-Zustands: {e}")
    
    def _select_all(self):
        """Wählt alle Optionen aus"""
        for checkbox in self.option_checkboxes.values():
            checkbox.setChecked(True)
    
    def _select_none(self):
        """Wählt keine Optionen aus"""
        for checkbox in self.option_checkboxes.values():
            checkbox.setChecked(False)
    
    def _reset_filter(self):
        """Setzt den Filter zurück"""
        self.show_empty_checkbox.setChecked(True)
        self._select_all()
    
    def get_filter_settings(self) -> tuple:
        """
        Gibt die Filter-Einstellungen zurück
        
        Returns:
            tuple: (selected_keys: set, show_empty: bool)
        """
        selected_keys = set()
        for key, checkbox in self.option_checkboxes.items():
            if checkbox.isChecked():
                selected_keys.add(key)
        
        show_empty = self.show_empty_checkbox.isChecked()
        
        return selected_keys, show_empty
