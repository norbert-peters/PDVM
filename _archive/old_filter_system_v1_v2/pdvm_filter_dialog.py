# pdvm_filter_dialog.py
# ECHTES PDVM FILTER-SYSTEM - Original Design

"""
PDVM Filter-Dialog mit ursprünglichem Design:

1. EINFACHER FILTER: Globale Suche über alle Felder
2. KOMPLEXER FILTER: Feldspezifische Filter mit Details
3. +/- Buttons: Einschließen/Ausschließen pro Feld
4. Details Button: Erweiterte Optionen (Operator, Regex, etc.)
5. ZWEI getrennte Ausführungsbuttons für verschiedene Such-String Generierung
"""

import logging
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QLineEdit, QFrame, QScrollArea, 
                             QWidget, QGroupBox, QComboBox, QCheckBox)
from PyQt5.QtCore import Qt

logger = logging.getLogger(__name__)


class FilterFieldWidget(QFrame):
    """Widget für ein einzelnes Filter-Feld mit +/- Toggle und Details"""
    
    def __init__(self, field_key, field_label, parent=None):
        super().__init__(parent)
        self.field_key = field_key
        self.field_label = field_label
        self.is_positive = True  # True = + (einschließen), False = - (ausschließen)
        self.show_details = False
        
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(1)
        self.init_ui()
    
    def init_ui(self):
        """Erstelle UI für Filter-Feld"""
        layout = QVBoxLayout()
        
        # Haupt-Zeile mit Feld, Wert, +/- und Details
        main_layout = QHBoxLayout()
        
        # Label
        self.label = QLabel(f"{self.field_label}:")
        self.label.setMinimumWidth(120)
        main_layout.addWidget(self.label)
        
        # Input
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText(f"Wert für {self.field_label}...")
        main_layout.addWidget(self.input_field)
        
        # +/- Button
        self.toggle_button = QPushButton("✅ +")
        self.toggle_button.setFixedWidth(60)
        self.toggle_button.clicked.connect(self._toggle_mode)
        self._update_button_style()
        main_layout.addWidget(self.toggle_button)
        
        # Details Button
        self.details_button = QPushButton("🔽 Details")
        self.details_button.setFixedWidth(90)
        self.details_button.clicked.connect(self._toggle_details)
        self._update_details_button()
        main_layout.addWidget(self.details_button)
        
        layout.addLayout(main_layout)
        
        # Details-Bereich (anfangs versteckt)
        self.details_widget = QWidget()
        self.details_layout = QVBoxLayout()
        
        # Operator Auswahl
        op_layout = QHBoxLayout()
        op_layout.addWidget(QLabel("Operator:"))
        self.operator_combo = QComboBox()
        self.operator_combo.addItems([
            "enthält", "gleich", "beginnt mit", "endet mit", 
            "größer als", "kleiner als", "zwischen"
        ])
        op_layout.addWidget(self.operator_combo)
        op_layout.addStretch()
        self.details_layout.addLayout(op_layout)
        
        # Case Sensitive
        self.case_sensitive = QCheckBox("Groß-/Kleinschreibung beachten")
        self.details_layout.addWidget(self.case_sensitive)
        
        # Regex Option
        self.regex_mode = QCheckBox("Regulärer Ausdruck")
        self.details_layout.addWidget(self.regex_mode)
        
        self.details_widget.setLayout(self.details_layout)
        self.details_widget.setVisible(False)
        layout.addWidget(self.details_widget)
        
        self.setLayout(layout)
    
    def _toggle_mode(self):
        """Schalte zwischen + (einschließen) und - (ausschließen) um"""
        self.is_positive = not self.is_positive
        self._update_button_style()
    
    def _update_button_style(self):
        """Aktualisiere +/- Button-Style"""
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
    
    def _toggle_details(self):
        """Schalte Details-Bereich um"""
        self.show_details = not self.show_details
        self.details_widget.setVisible(self.show_details)
        self._update_details_button()
    
    def _update_details_button(self):
        """Aktualisiere Details-Button"""
        if self.show_details:
            self.details_button.setText("🔼 Details")
            self.details_button.setStyleSheet("""
                QPushButton { 
                    background-color: #3498db; 
                    color: white; 
                }
                QPushButton:hover { background-color: #2980b9; }
            """)
        else:
            self.details_button.setText("🔽 Details")
            self.details_button.setStyleSheet("""
                QPushButton { 
                    background-color: #95a5a6; 
                    color: white; 
                }
                QPushButton:hover { background-color: #7f8c8d; }
            """)
    
    def get_value(self):
        """Hole Eingabewert"""
        return self.input_field.text().strip()
    
    def get_mode(self):
        """Hole Modus (True = positiv/einschließen, False = negativ/ausschließen)"""
        return self.is_positive
    
    def get_details(self):
        """Hole Detail-Einstellungen"""
        return {
            'operator': self.operator_combo.currentText(),
            'case_sensitive': self.case_sensitive.isChecked(),
            'regex_mode': self.regex_mode.isChecked()
        }
    
    def set_value(self, value):
        """Setze Eingabewert"""
        self.input_field.setText(value or '')
    
    def set_mode(self, is_positive):
        """Setze Modus"""
        self.is_positive = is_positive
        self._update_button_style()
    
    def set_details(self, details):
        """Setze Detail-Einstellungen"""
        if details:
            if 'operator' in details:
                index = self.operator_combo.findText(details['operator'])
                if index >= 0:
                    self.operator_combo.setCurrentIndex(index)
            
            self.case_sensitive.setChecked(details.get('case_sensitive', False))
            self.regex_mode.setChecked(details.get('regex_mode', False))


class PdvmFilterDialog(QDialog):
    """
    PDVM FILTER-DIALOG SYSTEM
    
    Originales Design:
    - EINFACHER FILTER: Eine globale Suche über alle Spalten
    - KOMPLEXER FILTER: Mehrere Felder mit +/- und Details
    - Zwei getrennte Ausführungsbuttons für verschiedene Search-String Generierung
    """
    
    def __init__(self, view_guid, parent=None):
        super().__init__(parent)
        self.view_guid = view_guid
        self.field_widgets = {}
        
        self.setWindowTitle("🔍 PDVM Filter-System")
        self.setModal(True)
        self.resize(900, 800)
        
        self.init_ui()
        self.load_persistent_data()
    
    def init_ui(self):
        """Erstelle das echte Filter-UI"""
        layout = QVBoxLayout()
        
        # Titel
        title = QLabel("🔍 PDVM Filter-System")
        title.setStyleSheet("font-size: 18px; font-weight: bold; margin: 10px; color: #2c3e50;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # EINFACHER FILTER Bereich
        simple_group = QGroupBox("🔍 EINFACHER FILTER")
        simple_group.setStyleSheet("""
            QGroupBox { 
                font-weight: bold; 
                border: 2px solid #3498db; 
                border-radius: 8px; 
                margin: 5px; 
                padding-top: 15px;
                background-color: #f8f9fa;
            }
            QGroupBox::title { 
                subcontrol-origin: margin; 
                left: 15px; 
                padding: 0 8px 0 8px; 
                color: #2980b9;
            }
        """)
        simple_layout = QVBoxLayout()
        
        # Einfach Info
        simple_info = QLabel("💡 Globale Suche über alle Felder - findet Werte in allen Spalten")
        simple_info.setStyleSheet("color: #7f8c8d; font-size: 11px; margin: 5px;")
        simple_layout.addWidget(simple_info)
        
        # Globales Suchfeld
        global_layout = QHBoxLayout()
        global_layout.addWidget(QLabel("Suchen:"))
        self.global_search_field = QLineEdit()
        self.global_search_field.setPlaceholderText("Globale Suche über alle Spalten...")
        global_layout.addWidget(self.global_search_field)
        simple_layout.addLayout(global_layout)
        
        # Einfacher Filter Button
        simple_button_layout = QHBoxLayout()
        self.simple_execute_button = QPushButton("🔍 EINFACHEN FILTER AUSFÜHREN")
        self.simple_execute_button.setStyleSheet("""
            QPushButton { 
                background-color: #3498db; 
                color: white; 
                font-weight: bold; 
                padding: 12px 25px;
                border-radius: 8px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #2980b9; }
            QPushButton:pressed { background-color: #21618c; }
        """)
        self.simple_execute_button.clicked.connect(self.execute_simple_filter)
        
        simple_clear_button = QPushButton("🗑️ Löschen")
        simple_clear_button.clicked.connect(self.clear_simple_filter)
        simple_clear_button.setStyleSheet("""
            QPushButton { 
                background-color: #95a5a6; 
                color: white; 
                padding: 8px 15px;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #7f8c8d; }
        """)
        
        simple_button_layout.addWidget(simple_clear_button)
        simple_button_layout.addStretch()
        simple_button_layout.addWidget(self.simple_execute_button)
        
        simple_layout.addLayout(simple_button_layout)
        simple_group.setLayout(simple_layout)
        layout.addWidget(simple_group)
        
        # KOMPLEXER FILTER Bereich
        complex_group = QGroupBox("⚙️ KOMPLEXER FILTER")
        complex_group.setStyleSheet("""
            QGroupBox { 
                font-weight: bold; 
                border: 2px solid #e67e22; 
                border-radius: 8px; 
                margin: 5px; 
                padding-top: 15px;
                background-color: #fdf2e9;
            }
            QGroupBox::title { 
                subcontrol-origin: margin; 
                left: 15px; 
                padding: 0 8px 0 8px; 
                color: #d35400;
            }
        """)
        complex_layout = QVBoxLayout()
        
        # Komplex Info
        complex_info = QLabel("⚙️ Feldspezifische Filter - +/- für Einschließen/Ausschließen, Details für erweiterte Optionen")
        complex_info.setStyleSheet("color: #7f8c8d; font-size: 11px; margin: 5px;")
        complex_layout.addWidget(complex_info)
        
        # Scroll Area für komplexe Filter
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        self.complex_fields_layout = QVBoxLayout()
        
        # Erstelle komplexe Filter-Felder
        self.create_complex_fields()
        
        scroll_widget.setLayout(self.complex_fields_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(350)
        complex_layout.addWidget(scroll_area)
        
        # Komplexer Filter Button
        complex_button_layout = QHBoxLayout()
        self.complex_execute_button = QPushButton("⚙️ KOMPLEXEN FILTER AUSFÜHREN")
        self.complex_execute_button.setStyleSheet("""
            QPushButton { 
                background-color: #e67e22; 
                color: white; 
                font-weight: bold; 
                padding: 12px 25px;
                border-radius: 8px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #d35400; }
            QPushButton:pressed { background-color: #ba4a00; }
        """)
        self.complex_execute_button.clicked.connect(self.execute_complex_filter)
        
        complex_clear_button = QPushButton("🗑️ Löschen")
        complex_clear_button.clicked.connect(self.clear_complex_filters)
        complex_clear_button.setStyleSheet("""
            QPushButton { 
                background-color: #95a5a6; 
                color: white; 
                padding: 8px 15px;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #7f8c8d; }
        """)
        
        complex_button_layout.addWidget(complex_clear_button)
        complex_button_layout.addStretch()
        complex_button_layout.addWidget(self.complex_execute_button)
        
        complex_layout.addLayout(complex_button_layout)
        complex_group.setLayout(complex_layout)
        layout.addWidget(complex_group)
        
        # Dialog Buttons
        dialog_button_layout = QHBoxLayout()
        
        cancel_button = QPushButton("❌ Schließen")
        cancel_button.clicked.connect(self.reject)
        cancel_button.setStyleSheet("""
            QPushButton { 
                background-color: #bdc3c7; 
                color: #2c3e50; 
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #95a5a6; }
        """)
        
        dialog_button_layout.addWidget(cancel_button)
        dialog_button_layout.addStretch()
        
        layout.addLayout(dialog_button_layout)
        
        self.setLayout(layout)
    
    def create_complex_fields(self):
        """Erstelle komplexe Filter-Felder"""
        # Standard Felder für komplexen Filter
        standard_fields = [
            ('familienname_show', 'Familienname'),
            ('vorname_show', 'Vorname'),
            ('anrede_show', 'Anrede'),
            ('geburtsdatum_show', 'Geburtsdatum'),
            ('geburtsdatum_alter_show', 'Alter'),
            ('geburtsdatum_jahr_show', 'Geburtsjahr'),
            ('email_show', 'E-Mail')
        ]
        
        for field_key, field_label in standard_fields:
            widget = FilterFieldWidget(field_key, field_label)
            self.complex_fields_layout.addWidget(widget)
            self.field_widgets[field_key] = widget
    
    def load_persistent_data(self):
        """Lade persistente Filter-Daten"""
        logger.info("📂 Lade persistente Filter-Daten...")
        
        try:
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            
            if not gcs or not hasattr(gcs, '_app_db'):
                logger.warning("⚠️ GCS nicht verfügbar für persistente Daten")
                return
            
            # Globale Suche laden
            global_data, _ = gcs._app_db.get_value(self.view_guid, "simple_global_search") or ('', None)
            self.global_search_field.setText(global_data)
            
            # Komplexe Filter laden
            complex_loaded = 0
            for field_key, widget in self.field_widgets.items():
                try:
                    # Wert laden
                    value_data, _ = gcs._app_db.get_value(self.view_guid, f"complex_{field_key}_value") or ('', None)
                    widget.set_value(value_data)
                    
                    # Modus laden
                    mode_data, _ = gcs._app_db.get_value(self.view_guid, f"complex_{field_key}_mode") or (True, None)
                    widget.set_mode(mode_data)
                    
                    # Details laden
                    details_data, _ = gcs._app_db.get_value(self.view_guid, f"complex_{field_key}_details") or ({}, None)
                    if details_data:
                        widget.set_details(details_data)
                        complex_loaded += 1
                        
                except Exception as e:
                    logger.warning(f"⚠️ Fehler beim Laden Filter {field_key}: {e}")
            
            logger.info(f"✅ Globale Suche und {complex_loaded} komplexe Filter geladen")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden persistenter Daten: {e}")
    
    def save_persistent_data(self):
        """Speichere persistente Filter-Daten"""
        logger.info("💾 Speichere persistente Filter-Daten...")
        
        try:
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            
            if not gcs or not hasattr(gcs, '_app_db'):
                logger.warning("⚠️ GCS nicht verfügbar für Persistierung")
                return
            
            # Globale Suche speichern
            global_value = self.global_search_field.text().strip()
            gcs._app_db.set_value(self.view_guid, "simple_global_search", global_value)
            
            # Komplexe Filter speichern
            saved_count = 0
            for field_key, widget in self.field_widgets.items():
                # Wert speichern
                value = widget.get_value()
                gcs._app_db.set_value(self.view_guid, f"complex_{field_key}_value", value)
                
                # Modus speichern
                mode = widget.get_mode()
                gcs._app_db.set_value(self.view_guid, f"complex_{field_key}_mode", mode)
                
                # Details speichern
                details = widget.get_details()
                gcs._app_db.set_value(self.view_guid, f"complex_{field_key}_details", details)
                
                saved_count += 3
            
            logger.info(f"✅ Globale Suche und {saved_count} komplexe Filter-Werte persistent gespeichert")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern persistenter Daten: {e}")
    
    def execute_simple_filter(self):
        """METHODE 1: Einfacher Filter - Globale Suche"""
        logger.info("🔍 === EINFACHER FILTER AUSFÜHRUNG ===")
        
        try:
            global_search = self.global_search_field.text().strip()
            
            if not global_search:
                logger.warning("⚠️ Keine globale Suche eingegeben")
                return
            
            logger.info(f"🎯 Globale Suche: '{global_search}'")
            
            # Persistiere Daten
            self.save_persistent_data()
            
            # Führe einfachen Filter aus (Globale Suche)
            self._execute_filter(global_search, 'simple')
            
            logger.info("✅ Einfacher Filter erfolgreich ausgeführt")
            
        except Exception as e:
            logger.error(f"❌ FEHLER bei einfachem Filter: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def execute_complex_filter(self):
        """METHODE 2: Komplexer Filter - Feldspezifisch"""
        logger.info("⚙️ === KOMPLEXER FILTER AUSFÜHRUNG ===")
        
        try:
            # Sammle komplexe Filter
            complex_filters = {}
            
            for field_key, widget in self.field_widgets.items():
                value = widget.get_value()
                mode = widget.get_mode()
                details = widget.get_details()
                
                if value:  # Nur wenn Wert eingegeben
                    complex_filters[field_key] = {
                        'value': value,
                        'is_positive': mode,
                        'details': details
                    }
                    logger.info(f"⚙️ Komplex: {field_key} = '{value}' ({'positiv' if mode else 'negativ'}) - {details['operator']}")
            
            if not complex_filters:
                logger.warning("⚠️ Keine komplexen Filter-Werte eingegeben")
                return
            
            # Erstelle komplexen Such-String
            search_parts = []
            
            for field_key, data in complex_filters.items():
                clean_field = field_key.replace('_show', '')
                value = data['value']
                is_positive = data['is_positive']
                operator = data['details']['operator']
                
                # Erstelle feldspezifischen Filter-Teil
                if operator == "enthält":
                    filter_part = f"{clean_field}:*{value}*"
                elif operator == "gleich":
                    filter_part = f"{clean_field}:{value}"
                elif operator == "beginnt mit":
                    filter_part = f"{clean_field}:{value}*"
                elif operator == "endet mit":
                    filter_part = f"{clean_field}:*{value}"
                else:
                    filter_part = f"{clean_field}:{value}"  # Fallback
                
                # Berücksichtige +/- Modus
                if not is_positive:
                    filter_part = f"NOT({filter_part})"
                
                search_parts.append(filter_part)
            
            # Kombiniere mit UND
            search_string = " AND ".join(search_parts)
            
            logger.info(f"🎯 KOMPLEXER Such-String: '{search_string}'")
            
            # Persistiere Daten
            self.save_persistent_data()
            
            # Führe komplexen Filter aus
            self._execute_filter(search_string, 'complex')
            
            logger.info("✅ Komplexer Filter erfolgreich ausgeführt")
            
        except Exception as e:
            logger.error(f"❌ FEHLER bei komplexem Filter: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _execute_filter(self, search_string, filter_type):
        """Einheitliche Filter-Ausführung"""
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
    
    def clear_simple_filter(self):
        """Lösche einfachen Filter"""
        logger.info("🗑️ Lösche einfachen Filter...")
        self.global_search_field.clear()
        logger.info("✅ Einfacher Filter gelöscht")
    
    def clear_complex_filters(self):
        """Lösche komplexe Filter"""
        logger.info("🗑️ Lösche komplexe Filter...")
        
        for widget in self.field_widgets.values():
            widget.set_value('')
            widget.set_mode(True)  # Zurück zu positiv
        
        logger.info("✅ Komplexe Filter gelöscht")


def show_pdvm_filter_dialog(parent, view_guid):
    """Zeige PDVM Filter Dialog"""
    dialog = PdvmFilterDialog(view_guid, parent)
    return dialog.exec_() == QDialog.Accepted
