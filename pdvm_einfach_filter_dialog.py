"""
EINFACHER FILTER DIALOG - V3
=============================

Einfacher Dialog mit direkter Wert-Eingabe:
- Ein Textfeld pro sichtbare Spalte
- Standard-Operator: "enthält"
- UND-Verknüpfung zwischen Feldern
- Verwendet EinfachFilterManager für Ausführung
"""

import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QLineEdit, QFrame, QScrollArea, QWidget, QMessageBox
)
from PyQt5.QtCore import Qt

logger = logging.getLogger(__name__)


class FieldRow(QFrame):
    """Eine Zeile für ein Filter-Feld"""
    
    def __init__(self, field_key, field_label, parent=None):
        super().__init__(parent)
        self.field_key = field_key
        self.field_label = field_label
        
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(1)
        self.setStyleSheet("QFrame { background-color: #f9f9f9; margin: 2px; padding: 5px; }")
        
        self.init_ui()
    
    def init_ui(self):
        """Erstelle UI"""
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Label
        label = QLabel(f"{self.field_label}:")
        label.setMinimumWidth(150)
        label.setStyleSheet("font-weight: bold;")
        layout.addWidget(label)
        
        # Input
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText(f"Suche in {self.field_label}...")
        layout.addWidget(self.input_field)
        
        self.setLayout(layout)
    
    def get_value(self):
        """Hole Wert"""
        return self.input_field.text().strip()
    
    def set_value(self, value):
        """Setze Wert"""
        self.input_field.setText(value or '')


class SimpleFilterDialog(QDialog):
    """
    EINFACHER FILTER DIALOG V3
    
    Zeigt Textfelder für alle sichtbaren Spalten.
    Verwendet EinfachFilterManager für Filter-Ausführung.
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
        self.field_rows = {}
        
        self.setWindowTitle("🔍 Einfaches Filter")
        self.setModal(True)
        self.resize(700, 600)
        
        self.init_ui()
        self.load_existing_filters()
    
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
        
        # Erstelle Field-Rows für Spalten aus Filter-Projektion
        for control_key in self.filter_projection:
            if control_key in self.controls_config:
                control_data = self.controls_config[control_key]
                label = control_data.get('label', control_key)
                
                row = FieldRow(control_key, label, self)
                self.field_rows[control_key] = row
                scroll_layout.addWidget(row)
        
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
            
            # Lade 'einfach' Parameter - IMMER, auch wenn nicht aktiv!
            # Die Parameter bleiben erhalten, auch wenn aktuell ein anderer Filter aktiv ist
            params, _ = gcs._app_db.get_value(self.view_guid, 'einfach')
            
            logger.info(f"📥 Lade Einfach-Filter Parameter (unabhängig von s_source)")
            
            if params and isinstance(params, dict):
                logger.info(f"📋 Lade {len(params)} gespeicherte Filter")
                
                for field_key, value in params.items():
                    if field_key in self.field_rows:
                        self.field_rows[field_key].set_value(value)
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden Filter: {e}")
    
    def _clear_all(self):
        """Lösche alle Eingaben"""
        for row in self.field_rows.values():
            row.set_value('')
    
    def _apply_filter(self):
        """Filter anwenden - ruft EinfachFilterManager auf"""
        try:
            # Sammle alle Felder mit Werten
            filter_params = {}
            for field_key, row in self.field_rows.items():
                value = row.get_value()
                if value:  # Nur nicht-leere Werte
                    filter_params[field_key] = value
            
            # Wenn keine Parameter: Filter löschen (s_string/s_source = None)
            if not filter_params:
                logger.info(f"🗑️ Keine Parameter - Filter wird gelöscht")
                
                from einfach_filter_manager import EinfachFilterManager
                manager = EinfachFilterManager(
                    view_guid=self.view_guid,
                    matrix_manager=self.matrix_manager
                )
                
                # Lösche nur s_string/s_source, Parameter 'einfach' bleiben
                success = manager.clear_einfach_filter()
                
                if success:
                    logger.info("✅ Einfacher Filter gelöscht")
                    self.accept()
                else:
                    QMessageBox.warning(self, "Fehler", "Filter konnte nicht gelöscht werden")
                return
            
            logger.info(f"✅ Filter anwenden: {len(filter_params)} Felder")
            
            # EinfachFilterManager verwenden
            from einfach_filter_manager import EinfachFilterManager
            
            manager = EinfachFilterManager(
                view_guid=self.view_guid,
                matrix_manager=self.matrix_manager
            )
            
            success = manager.execute_einfach_filter(filter_params)
            
            if success:
                logger.info("✅ Einfacher Filter erfolgreich ausgeführt")
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
