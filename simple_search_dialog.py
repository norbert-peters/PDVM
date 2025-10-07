# simple_search_dialog.py
# KOMPLETT NEUER EINFACHER SEARCH PARAMETER DIALOG

import logging
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QLineEdit
from PyQt5.QtCore import pyqtSignal

logger = logging.getLogger(__name__)

class SimpleSearchParameterDialog(QDialog):
    """
    EINFACHER SEARCH PARAMETER DIALOG - NUR DAS NÖTIGSTE
    
    GERADLINIGER 3-SCHRITT ABLAUF:
    1. Filter aus persistenten Daten laden (beim Start)
    2. UI anzeigen 
    3. Bei OK: persistent speichern + Filter anwenden
    """
    
    def __init__(self, view_guid, linear_filter_manager=None, parent=None):
        super().__init__(parent)
        self.view_guid = view_guid
        self.linear_filter_manager = linear_filter_manager
        self.filter_widgets = {}
        
        self.setWindowTitle("Filter-Parameter")
        self.setModal(True)
        self.resize(500, 300)
        
        self.init_ui()
        self.load_persistent_filters()
    
    def init_ui(self):
        """Erstelle einfache UI - NUR das Nötigste"""
        layout = QVBoxLayout()
        
        # Titel
        title = QLabel("🔍 Filter-Parameter")
        title.setStyleSheet("font-size: 14px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)
        
        # Standard Filter-Felder
        self.create_filter_fields(layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        ok_button = QPushButton("✅ Filter anwenden")
        ok_button.clicked.connect(self.accept_changes)
        
        cancel_button = QPushButton("❌ Abbrechen") 
        cancel_button.clicked.connect(self.reject)
        
        clear_button = QPushButton("🗑️ Alle löschen")
        clear_button.clicked.connect(self.clear_all_filters)
        
        button_layout.addWidget(clear_button)
        button_layout.addStretch()
        button_layout.addWidget(cancel_button)
        button_layout.addWidget(ok_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def create_filter_fields(self, layout):
        """Erstelle Filter-Felder - nur Standard-Spalten"""
        # Standard Felder - EINFACH
        standard_fields = [
            ('familienname_show', 'Familienname'),
            ('vorname_show', 'Vorname'),
            ('anrede_show', 'Anrede'),
            ('geburtsdatum_show', 'Geburtsdatum'),
            ('email_show', 'E-Mail')
        ]
        
        for field_key, label_text in standard_fields:
            field_layout = QHBoxLayout()
            
            # Label
            label = QLabel(f"{label_text}:")
            label.setMinimumWidth(100)
            
            # Input
            input_widget = QLineEdit()
            input_widget.setPlaceholderText(f"Filter für {label_text}...")
            
            field_layout.addWidget(label)
            field_layout.addWidget(input_widget)
            
            layout.addLayout(field_layout)
            
            # Speichere Widget
            self.filter_widgets[field_key] = input_widget
            
    def load_persistent_filters(self):
        """SCHRITT 1: Lade persistente Filter - EINFACH"""
        logger.info("📂 Lade persistente Filter...")
        
        try:
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            
            if not gcs or not hasattr(gcs, '_app_db'):
                logger.warning("⚠️ GCS nicht verfügbar - keine persistenten Filter")
                return
                
            loaded_count = 0
            for field_key, widget in self.filter_widgets.items():
                try:
                    filter_data, _ = gcs._app_db.get_value(self.view_guid, field_key) or (None, None)
                    
                    if filter_data and isinstance(filter_data, dict):
                        simple_value = filter_data.get('simple_search', '')
                        if simple_value:
                            widget.setText(simple_value)
                            loaded_count += 1
                            logger.info(f"📥 {field_key} = '{simple_value}'")
                            
                except Exception as e:
                    logger.warning(f"⚠️ Fehler beim Laden von {field_key}: {e}")
                    
            logger.info(f"✅ {loaded_count} persistente Filter geladen")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden persistenter Filter: {e}")
    
    def accept_changes(self):
        """SCHRITT 2+3: Sammle Filter und führe aus - EINFACH"""
        logger.info("🎯 === EINFACHER FILTER-ABLAUF ===")
        
        try:
            # Sammle Filter aus UI
            filter_data = {}
            for field_key, widget in self.filter_widgets.items():
                value = widget.text().strip()
                if value:
                    filter_data[field_key] = value
                    logger.info(f"🔧 Filter: {field_key} = '{value}'")
            
            logger.info(f"📊 {len(filter_data)} Filter gesammelt")
            
            # Speichere persistent
            self._save_persistent(filter_data)
            
            # Führe Filter aus
            self._execute_filter(filter_data)
            
            # Dialog schließen
            self.accept()
            logger.info("✅ Einfacher Filter-Ablauf abgeschlossen")
            
        except Exception as e:
            logger.error(f"❌ Fehler im Filter-Ablauf: {e}")
            self.reject()
    
    def _save_persistent(self, filter_data):
        """Speichere Filter persistent - EINFACH"""
        try:
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            
            if not gcs or not hasattr(gcs, '_app_db'):
                logger.warning("⚠️ GCS nicht verfügbar - keine Persistierung")
                return
                
            for field_key, value in filter_data.items():
                save_data = {
                    'field_key': field_key,
                    'simple_search': value,
                    'created_at': '2025-10-06'
                }
                gcs._app_db.set_value(self.view_guid, field_key, save_data)
                logger.info(f"💾 {field_key} gespeichert")
                
        except Exception as e:
            logger.error(f"❌ Persistierung fehlgeschlagen: {e}")
    
    def _execute_filter(self, filter_data):
        """Führe Filter aus - DIREKT über LinearFilterExecutionManager"""
        try:
            if not self.linear_filter_manager:
                logger.warning("⚠️ LinearFilterExecutionManager nicht verfügbar")
                return
                
            if not filter_data:
                # Leerer Filter = Reset
                self.linear_filter_manager.execute_filter_linear('einfach', {})
                logger.info("🔵 Reset auf Basis-Matrix")
                return
                
            # Filter anwenden - EINFACH
            success = self.linear_filter_manager.execute_filter_linear('einfach', {
                'simple_filters': filter_data,
                'filter_type': 'parameter_simple'
            })
            
            if success:
                logger.info("✅ Filter erfolgreich angewendet")
            else:
                logger.warning("⚠️ Filter-Anwendung fehlgeschlagen")
                
        except Exception as e:
            logger.error(f"❌ Filter-Ausführung fehlgeschlagen: {e}")
    
    def clear_all_filters(self):
        """Lösche alle Filter - EINFACH"""
        logger.info("🗑️ Lösche alle Filter...")
        
        try:
            # UI zurücksetzen
            for widget in self.filter_widgets.values():
                widget.clear()
            
            # Persistent löschen
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            
            if gcs and hasattr(gcs, '_app_db'):
                for field_key in self.filter_widgets.keys():
                    gcs._app_db.set_value(self.view_guid, field_key, None)
            
            # Reset Filter
            if self.linear_filter_manager:
                self.linear_filter_manager.execute_filter_linear('einfach', {})
            
            logger.info("✅ Alle Filter gelöscht")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Löschen: {e}")


def open_simple_search_dialog(view_guid, linear_filter_manager=None, parent=None):
    """Öffne einfachen Search Parameter Dialog"""
    dialog = SimpleSearchParameterDialog(view_guid, linear_filter_manager, parent)
    return dialog.exec_()