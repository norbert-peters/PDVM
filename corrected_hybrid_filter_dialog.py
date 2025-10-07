# corrected_hybrid_filter_dialog.py
# KORRIGIERTES HYBRID FILTER SYSTEM - GETRENNTE EINFACH/KOMPLEX

import logging
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QLineEdit, QFrame, QScrollArea, 
                             QWidget, QGroupBox)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont

logger = logging.getLogger(__name__)

class SimpleFieldWidget(QFrame):
    """Widget für ein einzelnes EINFACHES Filter-Feld"""
    
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
        
        # Label
        self.label = QLabel(f"{self.field_label}:")
        self.label.setMinimumWidth(120)
        layout.addWidget(self.label)
        
        # Input
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText(f"Filter für {self.field_label}...")
        layout.addWidget(self.input_field)
        
        # +/- Button
        self.toggle_button = QPushButton("✅ +")
        self.toggle_button.setFixedWidth(60)
        self.toggle_button.clicked.connect(self._toggle_mode)
        self._update_button_style()
        layout.addWidget(self.toggle_button)
        
        # Details Button (später)
        self.details_button = QPushButton("📋 Details")
        self.details_button.setFixedWidth(80)
        self.details_button.setEnabled(False)  # Erstmal deaktiviert
        self.details_button.setStyleSheet("QPushButton { background-color: #f0f0f0; color: #999; }")
        layout.addWidget(self.details_button)
        
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
    
    def get_simple_value(self):
        """Hole einfachen Wert"""
        return self.input_field.text().strip()
    
    def get_mode(self):
        """Hole Modus (True = positiv, False = negativ)"""
        return self.is_positive
    
    def set_simple_value(self, value):
        """Setze einfachen Wert"""
        self.input_field.setText(value or '')
    
    def set_mode(self, is_positive):
        """Setze Modus"""
        self.is_positive = is_positive
        self._update_button_style()


class ComplexFieldWidget(QFrame):
    """Widget für ein einzelnes KOMPLEXES Filter-Feld (später implementiert)"""
    
    def __init__(self, field_key, field_label, parent=None):
        super().__init__(parent)
        self.field_key = field_key
        self.field_label = field_label
        
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(1)
        self.init_ui()
    
    def init_ui(self):
        """Erstelle Platzhalter für komplexes Feld"""
        layout = QVBoxLayout()
        
        placeholder = QLabel(f"🔧 {self.field_label} (Komplex - später implementiert)")
        placeholder.setStyleSheet("color: #7f8c8d; font-style: italic; padding: 10px;")
        layout.addWidget(placeholder)
        
        self.setLayout(layout)
    
    def get_complex_data(self):
        """Hole komplexe Daten (Platzhalter)"""
        return None


class CorrectedHybridFilterDialog(QDialog):
    """
    KORRIGIERTES HYBRID FILTER DIALOG
    
    GETRENNTE EINFACH/KOMPLEX SYSTEM:
    - Separate UI-Bereiche
    - Separate Persistierung 
    - Separate Such-String Erstellung
    - Separate Ausführungsbuttons
    """
    
    def __init__(self, view_guid, parent=None):
        super().__init__(parent)
        self.view_guid = view_guid
        self.simple_widgets = {}
        self.complex_widgets = {}
        
        self.setWindowTitle("🔍 Korrigiertes Hybrid Filter-System")
        self.setModal(True)
        self.resize(800, 700)
        
        self.init_ui()
        self.load_persistent_data()
    
    def init_ui(self):
        """Erstelle korrigierte Hybrid UI"""
        layout = QVBoxLayout()
        
        # Titel
        title = QLabel("🔍 Hybrid Filter-System (Korrigiert)")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px; color: #2c3e50;")
        layout.addWidget(title)
        
        # Info
        info = QLabel("💡 Einfach und Komplex sind vollständig getrennt - eigene Parameter, eigene Persistierung")
        info.setStyleSheet("color: #7f8c8d; font-size: 11px; margin-bottom: 10px;")
        layout.addWidget(info)
        
        # EINFACH-Bereich
        simple_group = QGroupBox("🔍 EINFACHER FILTER")
        simple_group.setStyleSheet("""
            QGroupBox { 
                font-weight: bold; 
                border: 2px solid #3498db; 
                border-radius: 5px; 
                margin: 5px; 
                padding-top: 10px;
            }
            QGroupBox::title { 
                subcontrol-origin: margin; 
                left: 10px; 
                padding: 0 5px 0 5px; 
            }
        """)
        simple_layout = QVBoxLayout()
        
        # Einfach Info
        simple_info = QLabel("✅ Direkte Feldwerte mit +/- Umschaltung pro Feld")
        simple_info.setStyleSheet("color: #2980b9; font-size: 10px; margin: 5px;")
        simple_layout.addWidget(simple_info)
        
        # Einfache Filter-Felder
        self.create_simple_fields(simple_layout)
        
        # Einfach Buttons
        simple_button_layout = QHBoxLayout()
        
        self.simple_execute_button = QPushButton("🔍 EINFACHES FILTER AUSFÜHREN")
        self.simple_execute_button.setStyleSheet("""
            QPushButton { 
                background-color: #3498db; 
                color: white; 
                font-weight: bold; 
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        self.simple_execute_button.clicked.connect(self.execute_simple_filter)
        
        simple_clear_button = QPushButton("🗑️ Einfach löschen")
        simple_clear_button.clicked.connect(self.clear_simple_filters)
        
        simple_button_layout.addWidget(simple_clear_button)
        simple_button_layout.addStretch()
        simple_button_layout.addWidget(self.simple_execute_button)
        
        simple_layout.addLayout(simple_button_layout)
        simple_group.setLayout(simple_layout)
        layout.addWidget(simple_group)
        
        # KOMPLEX-Bereich
        complex_group = QGroupBox("⚙️ KOMPLEXER FILTER")
        complex_group.setStyleSheet("""
            QGroupBox { 
                font-weight: bold; 
                border: 2px solid #e67e22; 
                border-radius: 5px; 
                margin: 5px; 
                padding-top: 10px;
            }
            QGroupBox::title { 
                subcontrol-origin: margin; 
                left: 10px; 
                padding: 0 5px 0 5px; 
            }
        """)
        complex_layout = QVBoxLayout()
        
        # Komplex Info
        complex_info = QLabel("⚙️ Erweiterte Optionen mit Details (später implementiert)")
        complex_info.setStyleSheet("color: #d68910; font-size: 10px; margin: 5px;")
        complex_layout.addWidget(complex_info)
        
        # Komplexe Filter-Felder (Platzhalter)
        self.create_complex_fields(complex_layout)
        
        # Komplex Buttons
        complex_button_layout = QHBoxLayout()
        
        self.complex_execute_button = QPushButton("⚙️ KOMPLEXES FILTER AUSFÜHREN")
        self.complex_execute_button.setStyleSheet("""
            QPushButton { 
                background-color: #e67e22; 
                color: white; 
                font-weight: bold; 
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #d35400; }
        """)
        self.complex_execute_button.clicked.connect(self.execute_complex_filter)
        self.complex_execute_button.setEnabled(False)  # Erstmal deaktiviert
        
        complex_clear_button = QPushButton("🗑️ Komplex löschen")
        complex_clear_button.clicked.connect(self.clear_complex_filters)
        complex_clear_button.setEnabled(False)  # Erstmal deaktiviert
        
        complex_button_layout.addWidget(complex_clear_button)
        complex_button_layout.addStretch()
        complex_button_layout.addWidget(self.complex_execute_button)
        
        complex_layout.addLayout(complex_button_layout)
        complex_group.setLayout(complex_layout)
        layout.addWidget(complex_group)
        
        # Allgemeine Buttons
        general_button_layout = QHBoxLayout()
        
        cancel_button = QPushButton("❌ Abbrechen")
        cancel_button.clicked.connect(self.reject)
        
        general_button_layout.addWidget(cancel_button)
        general_button_layout.addStretch()
        
        layout.addLayout(general_button_layout)
        
        self.setLayout(layout)
    
    def create_simple_fields(self, layout):
        """Erstelle einfache Filter-Felder"""
        # Standard Felder
        standard_fields = [
            ('familienname_show', 'Familienname'),
            ('vorname_show', 'Vorname'),
            ('anrede_show', 'Anrede'),
            ('geburtsdatum_show', 'Geburtsdatum'),
            ('email_show', 'E-Mail'),
            ('telefon_show', 'Telefon'),
            ('strasse_show', 'Straße'),
            ('plz_show', 'PLZ'),
            ('ort_show', 'Ort')
        ]
        
        for field_key, field_label in standard_fields:
            widget = SimpleFieldWidget(field_key, field_label)
            layout.addWidget(widget)
            self.simple_widgets[field_key] = widget
    
    def create_complex_fields(self, layout):
        """Erstelle komplexe Filter-Felder (Platzhalter)"""
        # Standard Felder (Platzhalter)
        standard_fields = [
            ('familienname_show', 'Familienname'),
            ('vorname_show', 'Vorname'),
            ('anrede_show', 'Anrede')  # Nur wenige für Platzhalter
        ]
        
        for field_key, field_label in standard_fields:
            widget = ComplexFieldWidget(field_key, field_label)
            layout.addWidget(widget)
            self.complex_widgets[field_key] = widget
    
    def load_persistent_data(self):
        """Lade GETRENNTE persistente Filter-Daten"""
        logger.info("📂 Lade getrennte persistente Filter-Daten...")
        
        try:
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            
            if not gcs or not hasattr(gcs, '_app_db'):
                logger.warning("⚠️ GCS nicht verfügbar für persistente Daten")
                return
            
            # EINFACHE Filter laden
            simple_loaded = 0
            for field_key, widget in self.simple_widgets.items():
                try:
                    # Wert laden
                    value_key = f"simple_{field_key}_value"
                    value_data, _ = gcs._app_db.get_value(self.view_guid, value_key) or ('', None)
                    if value_data:
                        widget.set_simple_value(value_data)
                        simple_loaded += 1
                    
                    # Modus laden
                    mode_key = f"simple_{field_key}_mode"
                    mode_data, _ = gcs._app_db.get_value(self.view_guid, mode_key) or (True, None)
                    widget.set_mode(mode_data)
                        
                except Exception as e:
                    logger.warning(f"⚠️ Fehler beim Laden einfacher Filter {field_key}: {e}")
            
            # KOMPLEXE Filter laden (später)
            complex_loaded = 0
            
            logger.info(f"✅ {simple_loaded} einfache, {complex_loaded} komplexe Filter geladen")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden persistenter Daten: {e}")
    
    def save_simple_persistent_data(self, simple_filters):
        """Speichere EINFACHE persistente Filter-Daten"""
        logger.info("💾 Speichere einfache persistente Filter-Daten...")
        
        try:
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            
            if not gcs or not hasattr(gcs, '_app_db'):
                logger.warning("⚠️ GCS nicht verfügbar für Persistierung")
                return
            
            saved_count = 0
            
            # Speichere einfache Werte und Modi
            for field_key, widget in self.simple_widgets.items():
                # Wert speichern
                value = widget.get_simple_value()
                value_key = f"simple_{field_key}_value"
                gcs._app_db.set_value(self.view_guid, value_key, value)
                
                # Modus speichern
                mode = widget.get_mode()
                mode_key = f"simple_{field_key}_mode"
                gcs._app_db.set_value(self.view_guid, mode_key, mode)
                
                saved_count += 2
            
            logger.info(f"✅ {saved_count} einfache Filter-Werte persistent gespeichert")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern einfacher persistenter Daten: {e}")
    
    def collect_simple_filters(self):
        """Sammle EINFACHE Filter-Werte"""
        simple_filters = {}
        
        for field_key, widget in self.simple_widgets.items():
            value = widget.get_simple_value()
            mode = widget.get_mode()
            
            if value:  # Nur wenn Wert eingegeben
                simple_filters[field_key] = {
                    'value': value,
                    'is_positive': mode
                }
                logger.info(f"🔍 Einfach: {field_key} = '{value}' ({'positiv' if mode else 'negativ'})")
        
        return simple_filters
    
    def execute_simple_filter(self):
        """METHODE 1: Ausführung EINFACHES Filter - KOMPLETT GETRENNT"""
        logger.info("🔍 === EINFACHES FILTER AUSFÜHRUNG (GETRENNT) ===")
        
        try:
            # Sammle NUR einfache Filter
            simple_filters = self.collect_simple_filters()
            
            if not simple_filters:
                logger.warning("⚠️ Keine einfachen Filter-Werte eingegeben")
                return
            
            # Erstelle EINFACHEN Such-String
            positive_parts = []
            negative_parts = []
            
            for field_key, data in simple_filters.items():
                clean_field = field_key.replace('_show', '')
                value = data['value']
                is_positive = data['is_positive']
                
                filter_part = f"{clean_field}:{value}"
                
                if is_positive:
                    positive_parts.append(filter_part)
                else:
                    negative_parts.append(f"NOT({filter_part})")
            
            # Kombiniere: Positive mit UND, Negative mit UND
            search_parts = positive_parts + negative_parts
            search_string = " AND ".join(search_parts)
            
            logger.info(f"🎯 EINFACHER Such-String: '{search_string}'")
            
            # Persistiere NUR einfache Daten
            self.save_simple_persistent_data(simple_filters)
            
            # Führe einfachen Filter aus
            self._execute_unified_filter(search_string, 'simple')
            
            logger.info("✅ Einfaches Filter erfolgreich ausgeführt")
            
        except Exception as e:
            logger.error(f"❌ FEHLER bei einfachem Filter: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def execute_complex_filter(self):
        """METHODE 2: Ausführung KOMPLEXES Filter - KOMPLETT GETRENNT (später)"""
        logger.info("⚙️ === KOMPLEXES FILTER AUSFÜHRUNG (GETRENNT) ===")
        logger.info("⚠️ Komplexer Filter noch nicht implementiert")
    
    def _execute_unified_filter(self, search_string, filter_type):
        """EINHEITLICHE Filter-Ausführung"""
        logger.info(f"🎯 Führe {filter_type} Filter aus: '{search_string}'")
        
        try:
            # Hole LinearFilterExecutionManager
            from linear_filter_execution_manager import get_linear_filter_manager
            manager = get_linear_filter_manager(self.view_guid)
            
            if not manager:
                raise RuntimeError("LinearFilterExecutionManager nicht verfügbar!")
            
            # Führe Filter linear aus
            result = manager.execute_filter_linear('search_string', {
                'search_string': search_string,
                'filter_type': filter_type
            })
            
            if result:
                logger.info(f"✅ {filter_type.title()} Filter erfolgreich angewendet")
                self.accept()  # Dialog schließen
            else:
                raise RuntimeError(f"{filter_type.title()} Filter konnte nicht angewendet werden!")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Filter-Ausführung: {e}")
            raise
    
    def clear_simple_filters(self):
        """Lösche NUR einfache Filter-Eingaben"""
        logger.info("🗑️ Lösche einfache Filter-Eingaben...")
        
        for widget in self.simple_widgets.values():
            widget.set_simple_value('')
            widget.set_mode(True)  # Zurück zu positiv
        
        logger.info("✅ Einfache Filter-Eingaben gelöscht")
    
    def clear_complex_filters(self):
        """Lösche NUR komplexe Filter-Eingaben (später)"""
        logger.info("🗑️ Lösche komplexe Filter-Eingaben...")
        logger.info("⚠️ Komplexer Clear noch nicht implementiert")


def show_corrected_hybrid_filter_dialog(parent, view_guid):
    """Zeige Korrigierten Hybrid Filter Dialog"""
    dialog = CorrectedHybridFilterDialog(view_guid, parent)
    return dialog.exec_() == QDialog.Accepted