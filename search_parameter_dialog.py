"""
MODAL-DIALOG: SEARCH-PARAMETER
==============================

Blockierendes Fenster für Search-Parameter mit aktueller Sicht
"""

import sys
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QLineEdit, QComboBox, QCheckBox,
                             QDialogButtonBox, QFrame, QScrollArea, QWidget,
                             QMessageBox, QGroupBox, QGridLayout, QFormLayout,
                             QDateEdit, QSpinBox, QRadioButton, QButtonGroup)
from PyQt5.QtCore import Qt, pyqtSignal, QDate
from PyQt5.QtGui import QFont, QIcon
import logging
from global_gcs import gcs  # Globaler Zugriff auf GCS
from extended_filter_engine import extended_filter_engine  # Extended Filter Engine

# V3 Filter-System
from pdvm_einfach_filter_manager import EinfachFilterManager
from pdvm_komplex_filter_manager import KomplexFilterManager

logger = logging.getLogger(__name__)

class SearchParameterDialog(QDialog):
    """
    Modal-Dialog für Search-Parameter.
    
    Öffnet mit aktueller Sicht (Standard/Expert), blockiert bis OK/Abbrechen.
    Benutzer kann Such-Filter für alle verfügbaren Spalten setzen.
    """
    
    # Signale
    filter_changed = pyqtSignal()  # Signal für Filter-Änderungen
    search_changed = pyqtSignal(dict)  # Neue Search-Parameter
    
    def __init__(self, parent, view_guid, controls_config, current_filters=None, matrix_manager=None):
        """
        Args:
            parent: Parent-Widget
            view_guid: GUID der View für Controls
            controls_config: Dictionary mit Controls direkt vom Dialog
            current_filters: Dict mit aktuellen Filter-Werten
            matrix_manager: Matrix Manager für Filter-Ausführung (V3)
        """
        super().__init__(parent)
        
        self.view_guid = view_guid
        self.controls_config = controls_config  # Direkt vom Dialog erhalten
        self.current_filters = current_filters or {}
        self.matrix_manager = matrix_manager  # V3: Für Filter-Manager
        
        # WICHTIG: Backup der ursprünglichen Filter für Cancel-Behandlung
        self.original_filters = self.current_filters.copy()
        
        # Dialog-Ergebnis
        self.result_filters = None
        self.result_filter_string = ""  # NEU: Einheitlicher Filterstring
        self.was_accepted = False
        
        # EINFACHER MODE-SCHALTER: Einfach/Komplex/Aktiv
        self.filter_mode = "EINFACH"  # Standard: normale Suche
        
        # Extended Filter Bedingungen (für Kompatibilität)
        self.extended_filter_conditions = {}
        
        # Filterfeld-Widgets
        self.filter_widgets = {}
        
        # GCS Key für persistente Speicherung der Suchparameter
        self.gcs_filters_key = f"search_parameters_{view_guid}"
        
        # V3 Filter-Manager initialisieren
        if self.matrix_manager:
            self.einfach_filter_manager = EinfachFilterManager(
                view_guid=self.view_guid,
                matrix_manager=self.matrix_manager
            )
            self.komplex_filter_manager = KomplexFilterManager(
                view_guid=self.view_guid,
                matrix_manager=self.matrix_manager
            )
            logger.info("✅ V3 Filter-Manager im SearchParameterDialog initialisiert")
        else:
            logger.warning("⚠️ Kein Matrix Manager - V3 Filter deaktiviert")
            self.einfach_filter_manager = None
            self.komplex_filter_manager = None
        
        self.setup_ui()
        self.load_persistent_filters()  # Lade persistente Filter
        self.load_current_filters()
    
    def _load_field_extended_filters(self, field_key: str):
        """Lade Extended Filter für ein Feld"""
        return self.extended_filter_conditions.get(field_key, [])
    
    def _save_field_extended_filters(self, field_key: str, conditions):
        """Speichere Extended Filter für ein Feld"""
        if conditions:
            self.extended_filter_conditions[field_key] = conditions
        else:
            self.extended_filter_conditions.pop(field_key, None)
    
    def create_mode_toggle(self, layout):
        """
        Erstelle MODE-SCHALTER für Einfach/Komplex-Filter
        🟢 EINFACH = Normale Suchfelder  
        🔵 KOMPLEX = Extended Filter  
        🟠 AKTIV = Extended Filter gefüllt
        """
        mode_frame = QFrame()
        mode_frame.setFrameStyle(QFrame.Box)
        mode_frame.setStyleSheet("QFrame { border: 1px solid #ccc; background-color: #f9f9f9; }")
        
        mode_layout = QHBoxLayout(mode_frame)
        
        # Mode-Info Label
        mode_info = QLabel("🎛️ Filter-Modus:")
        mode_info.setFont(QFont("Segoe UI", 10, QFont.Bold))
        mode_layout.addWidget(mode_info)
        
        # Mode-Schalter Button
        self.mode_button = QPushButton()
        self.mode_button.setFixedSize(120, 30)
        self.mode_button.clicked.connect(self.toggle_filter_mode)
        mode_layout.addWidget(self.mode_button)
        
        mode_layout.addStretch()
        
        # Status-Label
        self.mode_status_label = QLabel()
        self.mode_status_label.setFont(QFont("Segoe UI", 9))
        mode_layout.addWidget(self.mode_status_label)
        
        layout.addWidget(mode_frame)
        
        # Initial Mode setzen
        self.update_mode_display()
    
    def toggle_filter_mode(self):
        """Schalte zwischen Einfach und Komplex um"""
        if self.filter_mode == "EINFACH":
            self.filter_mode = "KOMPLEX"
        else:
            self.filter_mode = "EINFACH"
            
        self.update_mode_display()
        self.update_widgets_for_mode()
        
        logger.info(f"🎛️ Filter-Modus gewechselt zu: {self.filter_mode}")
    
    def update_mode_display(self):
        """Aktualisiere Mode-Button und Status"""
        has_extended_filters = any(
            conditions for conditions in self.extended_filter_conditions.values()
        )
        
        if has_extended_filters:
            # AKTIV-Modus: Extended Filter sind vorhanden
            self.mode_button.setText("🟠 AKTIV")
            self.mode_button.setStyleSheet("""
                QPushButton { 
                    background-color: #FF9800; 
                    color: white; 
                    border: 2px solid #F57C00;
                    border-radius: 5px; 
                    font-weight: bold;
                }
            """)
            self.mode_status_label.setText("Extended Filter sind aktiv")
            # Im AKTIV-Modus ist KOMPLEX erzwungen
            self.filter_mode = "KOMPLEX"
            
        elif self.filter_mode == "EINFACH":
            # EINFACH-Modus: Normale Suche
            self.mode_button.setText("🟢 EINFACH")
            self.mode_button.setStyleSheet("""
                QPushButton { 
                    background-color: #4CAF50; 
                    color: white; 
                    border: 2px solid #388E3C;
                    border-radius: 5px; 
                    font-weight: bold;
                }
            """)
            self.mode_status_label.setText("Normale Suchfelder aktiv")
            
        else:  # KOMPLEX
            # KOMPLEX-Modus: Extended Filter verfügbar
            self.mode_button.setText("🔵 KOMPLEX")
            self.mode_button.setStyleSheet("""
                QPushButton { 
                    background-color: #2196F3; 
                    color: white; 
                    border: 2px solid #1976D2;
                    border-radius: 5px; 
                    font-weight: bold;
                }
            """)
            self.mode_status_label.setText("Extended Filter verfügbar")
    
    def update_widgets_for_mode(self):
        """Aktiviere/Deaktiviere Widgets basierend auf Modus"""
        is_simple_mode = (self.filter_mode == "EINFACH")
        
        for field_key, widget_dict in self.filter_widgets.items():
            # Normale Felder
            normal_widget = widget_dict['widget']
            # Details-Button  
            details_button = widget_dict['details_button']
            # Negativ-Button
            negative_button = widget_dict['negative_button']
            # Container
            container = widget_dict['container']
            
            if is_simple_mode:
                # EINFACH: Normale Felder sichtbar, Details-Button verfügbar
                normal_widget.setVisible(True)
                normal_widget.setEnabled(True)
                negative_button.setVisible(True)
                details_button.setEnabled(True)
                details_button.setStyleSheet("""
                    QPushButton { 
                        background-color: #2196F3; 
                        color: white; 
                        border: 2px solid #1976D2;
                        border-radius: 3px; 
                        font-weight: bold;
                    }
                """)
                container.setStyleSheet("QFrame { background-color: white; }")
                
            else:
                # KOMPLEX: Normale Felder ausblenden, nur Details-Button aktiv
                normal_widget.setVisible(False)  # Felder komplett ausblenden
                normal_widget.setEnabled(False)
                negative_button.setVisible(False)  # Auch Negativ-Button ausblenden
                details_button.setEnabled(True)
                details_button.setStyleSheet("""
                    QPushButton { 
                        background-color: #FF9800; 
                        color: white; 
                        border: 2px solid #F57C00;
                        border-radius: 3px; 
                        font-weight: bold;
                    }
                """)
                container.setStyleSheet("QFrame { background-color: #f0f0f0; }")
                # Normale Felder leeren im Komplex-Modus
                if hasattr(normal_widget, 'setText'):
                    normal_widget.setText("")
    
    def setup_ui(self):
        """UI setup"""
        self.setWindowTitle("Suchparameter verwalten")
        self.setModal(True)
        self.resize(500, 600)
        
        layout = QVBoxLayout(self)
        
        # Header
        header_label = QLabel("Filter-Parameter für Suche definieren")
        header_font = QFont("Segoe UI", 12, QFont.Bold)
        header_label.setFont(header_font)
        layout.addWidget(header_label)
        
        # MODE-SCHALTER: Einfach/Komplex
        self.create_mode_toggle(layout)
        
        # Scroll-Bereich für Filter
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Container für Filter-Parameter
        self.filter_container = QWidget()
        self.filter_layout = QFormLayout(self.filter_container)
        
        scroll_area.setWidget(self.filter_container)
        layout.addWidget(scroll_area)
        
        # Reset-Button Bereich
        reset_layout = QHBoxLayout()
        reset_button = QPushButton("🗑️ Alle Filter zurücksetzen")
        reset_button.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #f57c00;
            }
        """)
        reset_button.clicked.connect(self.reset_all_filters)
        reset_layout.addStretch()
        reset_layout.addWidget(reset_button)
        layout.addLayout(reset_layout)
        
        # Button-Bereich
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel,
            Qt.Horizontal,
            self
        )
        
        button_box.accepted.connect(self.accept_changes)
        button_box.rejected.connect(self.cancel_changes)
        
        # Button-Texte ändern
        ok_button = button_box.button(QDialogButtonBox.Ok)
        cancel_button = button_box.button(QDialogButtonBox.Cancel)
        if cancel_button:
            cancel_button.setText("Abbrechen")
        
        layout.addWidget(button_box)
        
        logger.info("✅ SearchParameterDialog UI erstellt")
    
    def reset_all_filters(self):
        """ZENTRAL: Löscht ALLE Filter für neue Suche (außer Gesamtfilter)"""
        try:
            from central_filter_reset import reset_all_filters_for_view
            
            logger.info("🔄 STARTE: Kompletter Filter-Reset für neue Suche")
            
            # 1. Zentrale Filter-Reset-Funktion aufrufen
            success = reset_all_filters_for_view(self.view_guid, preserve_gesamtfilter=True)
            
            if success:
                # 2. Dialog-interne Filter zurücksetzen
                self.current_filters.clear()
                self.original_filters.clear()
                
                # 3. UI-Elemente zurücksetzen
                if hasattr(self, 'filter_inputs'):
                    for input_widget in self.filter_inputs.values():
                        if hasattr(input_widget, 'clear'):
                            input_widget.clear()
                        elif hasattr(input_widget, 'setText'):
                            input_widget.setText('')
                
                # 4. Extended Filter Engine Reset (falls Instanz existiert)
                if hasattr(self, 'extended_engine') and self.extended_engine:
                    if hasattr(self.extended_engine, 'extended_conditions'):
                        self.extended_engine.extended_conditions.clear()
                
                logger.info("✅ Kompletter Filter-Reset erfolgreich")
                return True
            else:
                logger.warning("⚠️ Zentraler Filter-Reset hatte Probleme")
                return False
                
        except Exception as e:
            logger.error(f"❌ Filter-Reset fehlgeschlagen: {e}")
            return False
        """Lade persistent gespeicherte Filter aus anwendungsdaten - KORRIGIERT: über self._app_db"""
        try:
            if gcs and hasattr(gcs, '_app_db') and gcs._app_db:
                loaded_filters = {}
                
                # KORREKT: Lade aus anwendungsdaten über self._app_db
                possible_fields = ['familienname_show', 'vorname_show', 'anrede_show', 'geburtsdatum_show', 'geburtsdatum_alter_show', 'uid_show']
                
                for field_key in possible_fields:
                    field_data, _ = gcs._app_db.get_value(self.view_guid, field_key) or (None, None)
                    if field_data and isinstance(field_data, dict):
                        # Neue Struktur: {"simple_search": "wert", "conditions": [...]}
                        simple_search = field_data.get('simple_search')
                        if simple_search:
                            loaded_filters[field_key] = simple_search
                            logger.info(f"📥 APP-DB geladen: {field_key} = '{simple_search}'")
                    elif field_data:  # Alt-Format: direkter String-Wert
                        loaded_filters[field_key] = field_data
                        logger.info(f"📥 APP-DB ALT-Format geladen: {field_key} = '{field_data}'")
                
                if loaded_filters:
                    self.current_filters.update(loaded_filters)
                    # WICHTIG: Original Filter aktualisieren für korrekte Cancel-Behandlung
                    self.original_filters = self.current_filters.copy()
                    logger.info(f"✅ {len(loaded_filters)} persistente Filter aus ANWENDUNGSDATEN geladen")
                else:
                    logger.info("ℹ️ Keine persistenten Filter in anwendungsdaten gefunden")
                    
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Laden persistenter Filter: {e}")
    
    def save_persistent_filters(self, filters):
        """Speichere Filter persistent in anwendungsdaten - KORRIGIERT: über self._app_db"""
        try:
            if gcs and hasattr(gcs, '_app_db') and gcs._app_db:
                # KORREKT: Nutze anwendungsdaten über self._app_db
                for field_key, field_value in filters.items():
                    if not field_key.startswith('EXTENDED:'):  # Normale einfache Filter
                        # Aktuelle Spalten-Daten laden (falls vorhanden)
                        current_data, _ = gcs._app_db.get_value(self.view_guid, field_key) or ({}, None)
                        if not isinstance(current_data, dict):
                            current_data = {}
                        
                        # Simple_search setzen
                        current_data['simple_search'] = field_value
                        
                        # Conditions beibehalten falls vorhanden
                        if 'conditions' not in current_data:
                            current_data['conditions'] = []
                        
                        # Zurück speichern in ANWENDUNGSDATEN
                        gcs._app_db.set_value(self.view_guid, field_key, current_data)
                        logger.info(f"💾 APP-DB gespeichert: {field_key} = {{'simple_search': '{field_value}', 'conditions': {len(current_data['conditions'])} items}}")
                
                # Alles in anwendungsdaten speichern
                gcs._app_db.save_all_values()
                logger.info(f"✅ {len(filters)} Filter persistent in ANWENDUNGSDATEN gespeichert")
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Speichern persistenter Filter: {e}")
    
    def _save_search_string_to_gcs(self, new_filters, extended_summary):
        """
        🆕 V2: Speichert search_string in GCS für autonome Pipeline
        
        Konvertiert Filter-Parameter zu search_string und speichert beides:
        - Parameter unter 'einfach' (für Dialog-Anzeige)
        - search_string unter 'search_string' (für Pipeline)
        """
        try:
            if not gcs or not hasattr(gcs, '_app_db'):
                logger.warning("⚠️ GCS nicht verfügbar für search_string Speicherung")
                return
            
            # Erstelle search_string aus Filtern
            search_parts = []
            
            if extended_summary and len(extended_summary) > 0:
                # KOMPLEX-Filter
                logger.info(f"🔵 Erstelle search_string für KOMPLEX-Filter")
                for field_key, summary in extended_summary.items():
                    search_parts.append(f"EXTENDED:{field_key}:{summary}")
            else:
                # EINFACH-Filter
                logger.info(f"🟢 Erstelle search_string für EINFACH-Filter")
                for field_key, value in new_filters.items():
                    if not field_key.startswith('EXTENDED:'):
                        search_parts.append(f"{field_key}:{value}")
            
            search_string = "||".join(search_parts) if search_parts else None
            
            # Speichere search_string
            gcs._app_db.set_value(self.view_guid, 'search_string', search_string)
            gcs._app_db.save_all_values()  # 💾 CRITICAL!
            
            if search_string:
                logger.info(f"💾 search_string gespeichert: '{search_string[:100]}...'")
            else:
                logger.info(f"💾 search_string gelöscht (keine Filter)")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern search_string: {e}")

    def load_persistent_filters(self):
        """Lade persistent gespeicherte Filter aus anwendungsdaten - KORRIGIERT: über self._app_db"""
        try:
            logger.info(f"🔍 === DEBUG LOAD PERSISTENT FILTERS ===")
            logger.info(f"📂 View-GUID: {self.view_guid}")
            logger.info(f"🔧 GCS verfügbar: {gcs is not None}")
            
            if gcs:
                logger.info(f"🔧 GCS._app_db verfügbar: {hasattr(gcs, '_app_db') and gcs._app_db}")
            
            if gcs and hasattr(gcs, '_app_db') and gcs._app_db:
                loaded_filters = {}
                
                # KORREKT: Lade aus anwendungsdaten über self._app_db
                possible_fields = ['familienname_show', 'vorname_show', 'anrede_show', 'geburtsdatum_show', 'geburtsdatum_alter_show', 'uid_show']
                logger.info(f"🔍 Prüfe Felder: {possible_fields}")
                
                for field_key in possible_fields:
                    logger.info(f"  🔍 Prüfe Feld: {field_key}")
                    field_data, timestamp = gcs._app_db.get_value(self.view_guid, field_key) or (None, None)
                    logger.info(f"    📊 Raw Data: {field_data} (Timestamp: {timestamp})")
                    
                    if field_data and isinstance(field_data, dict):
                        logger.info(f"    📋 Dict-Format erkannt: {field_data}")
                        # Neue Struktur: {"simple_search": "wert", "conditions": [...]}
                        simple_search = field_data.get('simple_search')
                        if simple_search:
                            loaded_filters[field_key] = simple_search
                            logger.info(f"📥 APP-DB geladen: {field_key} = '{simple_search}'")
                        else:
                            logger.info(f"    ❌ Kein simple_search in Dict")
                    elif field_data:  # Alt-Format: direkter String-Wert
                        logger.info(f"    📋 String-Format erkannt: {field_data}")
                        loaded_filters[field_key] = field_data
                        logger.info(f"📥 APP-DB ALT-Format geladen: {field_key} = '{field_data}'")
                    else:
                        logger.info(f"    ❌ Keine Daten für {field_key}")
                
                logger.info(f"🎯 Gefundene Filter: {loaded_filters}")
                
                if loaded_filters:
                    self.current_filters.update(loaded_filters)
                    # WICHTIG: Original Filter aktualisieren für korrekte Cancel-Behandlung
                    self.original_filters = self.current_filters.copy()
                    logger.info(f"✅ {len(loaded_filters)} persistente Filter aus ANWENDUNGSDATEN geladen")
                else:
                    logger.info("ℹ️ Keine persistenten Filter in anwendungsdaten gefunden")
            else:
                logger.warning("⚠️ GCS oder APP-DB nicht verfügbar für Persistierung")
                    
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Laden persistenter Filter: {e}")
            import traceback
            logger.warning(traceback.format_exc())
    
    def reset_all_filters(self):
        """Setze alle Filter zurück"""
        try:
            # Alle Widgets zurücksetzen
            for control_key, widget_dict in self.filter_widgets.items():
                widget = widget_dict['widget']
                negative_button = widget_dict['negative_button']
                
                # Widget leeren
                if isinstance(widget, QLineEdit):
                    widget.clear()
                elif isinstance(widget, QComboBox):
                    widget.setCurrentIndex(0)  # Erste (leere) Option
                
                # Negative Button zurücksetzen
                if hasattr(negative_button, '_is_negative'):
                    negative_button._is_negative = False
                    negative_button.setText("➕")
                    negative_button.setStyleSheet("""
                        QPushButton { 
                            background-color: #4CAF50; 
                            color: white; 
                            border: none; 
                            border-radius: 3px; 
                            font-weight: bold;
                            font-size: 12px;
                        }
                        QPushButton:hover { 
                            background-color: #45a049; 
                        }
                    """)
                    negative_button.setToolTip("Normale Suche (einschließen)\nKlicken für Negativ-Suche (ausschließen)")
                    
                    # Placeholder zurücksetzen
                    if isinstance(widget, QLineEdit):
                        current_placeholder = widget.placeholderText()
                        widget.setPlaceholderText(current_placeholder.replace("Ausschließen", "Filter für"))
            
            # Interne Filter zurücksetzen (nur temporär!)
            self.current_filters.clear()
            
            # Extended Filter Engine zurücksetzen
            extended_filter_engine.clear_all_conditions()
            
            # Erweiterte Filter aus GCS löschen
            for field_key in self.filter_widgets.keys():
                try:
                    gcs.save_extended_filters(self.view_guid, field_key, {'conditions': []})
                except Exception as e:
                    logger.warning(f"⚠️ Fehler beim Löschen erweiterter Filter für {field_key}: {e}")
            
            # Details-Button-Zustände aktualisieren
            self._update_all_details_button_states()
            
            # NICHT sofort persistent speichern - das passiert nur bei OK!
            # Bei Cancel werden die original Filter wiederhergestellt
            
            logger.info("✅ Alle Filter zurückgesetzt")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Zurücksetzen der Filter: {e}")
            QMessageBox.warning(self, "Fehler", f"Filter konnten nicht zurückgesetzt werden:\n{e}")
    
    
    def load_current_filters(self):
        """Lade verfügbare Felder für Filter direkt aus GCS-Projektion (NEUE EINFACHE ARCHITEKTUR)"""
        try:
            # GCS direkt verwenden für zentrale Daten
            if not gcs:
                QMessageBox.warning(self, "Fehler", "GCS nicht verfügbar")
                return
            
            # STATISCHE PROJEKTION für Search je nach Expert Mode
            if gcs.expert_mode:
                visible_columns = gcs.get_projection_table(self.view_guid, 'search_expert')
            else:
                visible_columns = gcs.get_projection_table(self.view_guid, 'search_standard')
            if not visible_columns:
                logger.warning(f"⚠️ Keine durchsuchbaren Spalten verfügbar")
                return
            
            # Controls-Konfiguration direkt aus GCS holen
            all_controls, _ = gcs.db.get_value(self.view_guid, "controls")
            if not all_controls:
                QMessageBox.warning(self, "Fehler", "Keine Controls-Konfiguration verfügbar")
                return
            
            # Nur Filter für sichtbare Spalten erstellen
            searchable_controls = []
            for column_key in visible_columns:
                if column_key in all_controls:
                    config = all_controls[column_key]
                    searchable_controls.append((column_key, config))
            
            # Filter-UI erstellen - nur für sichtbare Spalten
            self._create_filter_fields(searchable_controls)
            
            # Lade persistente Filter (LINEAR - einmalig aus GCS)  
            self.load_persistent_filters()
            
            # UI mit geladenen Daten aktualisieren (LINEAR - ersetzt Details-Button-Update)
            self._update_ui_with_current_data()
            
            mode_info = "Expert" if gcs.expert_mode else "Standard"
            logger.info(f"✅ Filter-Felder ({mode_info}) erstellt für {len(searchable_controls)} sichtbare Spalten")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Filter-Felder: {e}")
            QMessageBox.warning(self, "Fehler", f"Filter-Felder konnten nicht geladen werden:\n{e}")
    
    def _create_filter_fields(self, controls):
        """Erstelle Filter-Felder für verfügbare Controls"""
        for control_key, control_config in controls:
            try:
                # Label für das Feld
                field_name = control_config.get('name', control_key)
                field_type = control_config.get('type', 'string')
                
                # Widget basierend auf Typ erstellen
                if field_type == 'date':
                    widget = self._create_date_filter(control_key, field_name)
                elif field_type == 'dropdown':
                    widget = self._create_dropdown_filter(control_key, field_name, control_config)
                elif field_type in ['int', 'float', 'number']:
                    widget = self._create_number_filter(control_key, field_name)
                else:  # string, text
                    widget = self._create_text_filter(control_key, field_name)
                
                if widget:
                    # Container für Widget + Negativ-Button
                    widget_container = QWidget()
                    widget_layout = QHBoxLayout(widget_container)
                    widget_layout.setContentsMargins(0, 0, 0, 0)
                    widget_layout.setSpacing(5)
                    
                    # Hauptfilter-Widget
                    widget_layout.addWidget(widget)
                    
                    # Details-Button für erweiterte Suchoptionen
                    details_button = QPushButton("Details...")
                    details_button.setFixedSize(60, 25)
                    details_button.setToolTip(f"Erweiterte Suchoptionen für {field_name}\nAND/OR/NOT Logik, mehrere Bedingungen")
                    details_button.setStyleSheet("""
                        QPushButton { 
                            background-color: #2196F3; 
                            color: white; 
                            border: none; 
                            border-radius: 3px; 
                            font-weight: bold;
                            font-size: 10px;
                        }
                        QPushButton:hover { 
                            background-color: #1976D2; 
                        }
                    """)
                    
                    # Details-Button-Funktion
                    def create_details_func(field_key, field_name):
                        def show_details():
                            self._show_field_details_dialog(field_key, field_name)
                        return show_details
                    
                    details_button.clicked.connect(create_details_func(control_key, field_name))
                    widget_layout.addWidget(details_button)
                    
                    # Negativ-Button
                    negative_button = QPushButton("➕")
                    negative_button.setFixedSize(25, 25)
                    negative_button.setToolTip("Normale Suche (einschließen)\nKlicken für Negativ-Suche (ausschließen)")
                    negative_button.setStyleSheet("""
                        QPushButton { 
                            background-color: #4CAF50; 
                            color: white; 
                            border: none; 
                            border-radius: 3px; 
                            font-weight: bold;
                            font-size: 12px;
                        }
                        QPushButton:hover { 
                            background-color: #45a049; 
                        }
                    """)
                    
                    # Toggle-Funktion für den Button
                    def create_toggle_func(btn, edit_widget):
                        def toggle():
                            is_negative = hasattr(btn, '_is_negative') and btn._is_negative
                            btn._is_negative = not is_negative
                            
                            if btn._is_negative:
                                btn.setText("➖")
                                btn.setToolTip("Negativ-Suche (ausschließen)\nKlicken für normale Suche (einschließen)")
                                btn.setStyleSheet("""
                                    QPushButton { 
                                        background-color: #f44336; 
                                        color: white; 
                                        border: none; 
                                        border-radius: 3px; 
                                        font-weight: bold;
                                        font-size: 12px;
                                    }
                                    QPushButton:hover { 
                                        background-color: #da190b; 
                                    }
                                """)
                                if isinstance(edit_widget, QLineEdit):
                                    current_placeholder = edit_widget.placeholderText()
                                    edit_widget.setPlaceholderText(current_placeholder.replace("Filter für", "Ausschließen"))
                            else:
                                btn.setText("➕")
                                btn.setToolTip("Normale Suche (einschließen)\nKlicken für Negativ-Suche (ausschließen)")
                                btn.setStyleSheet("""
                                    QPushButton { 
                                        background-color: #4CAF50; 
                                        color: white; 
                                        border: none; 
                                        border-radius: 3px; 
                                        font-weight: bold;
                                        font-size: 12px;
                                    }
                                    QPushButton:hover { 
                                        background-color: #45a049; 
                                    }
                                """)
                                if isinstance(edit_widget, QLineEdit):
                                    current_placeholder = edit_widget.placeholderText()
                                    edit_widget.setPlaceholderText(current_placeholder.replace("Ausschließen", "Filter für"))
                        return toggle
                    
                    # Toggle-Funktion für den Button - Korrigierte Signatur
                    def create_toggle_func(btn, edit_widget):
                        def toggle():
                            is_negative = hasattr(btn, '_is_negative') and btn._is_negative
                            btn._is_negative = not is_negative
                            
                            if btn._is_negative:
                                btn.setText("➖")
                                btn.setToolTip("Negativ-Suche (ausschließen)\\nKlicken für normale Suche (einschließen)")
                                btn.setStyleSheet("""
                                    QPushButton { 
                                        background-color: #f44336; 
                                        color: white; 
                                        border: none; 
                                        border-radius: 3px; 
                                        font-weight: bold;
                                        font-size: 12px;
                                    }
                                    QPushButton:hover { 
                                        background-color: #da190b; 
                                    }
                                """)
                                if isinstance(edit_widget, QLineEdit):
                                    current_placeholder = edit_widget.placeholderText()
                                    edit_widget.setPlaceholderText(current_placeholder.replace("Filter für", "Ausschließen"))
                            else:
                                btn.setText("➕")
                                btn.setToolTip("Normale Suche (einschließen)\\nKlicken für Negativ-Suche (ausschließen)")
                                btn.setStyleSheet("""
                                    QPushButton { 
                                        background-color: #4CAF50; 
                                        color: white; 
                                        border: none; 
                                        border-radius: 3px; 
                                        font-weight: bold;
                                        font-size: 12px;
                                    }
                                    QPushButton:hover { 
                                        background-color: #45a049; 
                                    }
                                """)
                                if isinstance(edit_widget, QLineEdit):
                                    current_placeholder = edit_widget.placeholderText()
                                    edit_widget.setPlaceholderText(current_placeholder.replace("Ausschließen", "Filter für"))
                        return toggle
                    
                    negative_button.clicked.connect(create_toggle_func(negative_button, widget))
                    negative_button._is_negative = False  # Initial state
                    
                    widget_layout.addWidget(negative_button)
                    
                    # Container zur Form hinzufügen
                    self.filter_layout.addRow(f"{field_name}:", widget_container)
                    self.filter_widgets[control_key] = {
                        'widget': widget,
                        'details_button': details_button,
                        'negative_button': negative_button,
                        'container': widget_container
                    }
                    
                    # Aktueller Wert setzen wenn vorhanden
                    current_value = self.current_filters.get(control_key)
                    if current_value:
                        # Prüfe ob Wert mit NOT: beginnt (negativer Filter)
                        if current_value.startswith("NOT:"):
                            actual_value = current_value[4:]  # "NOT:" entfernen
                            self._set_widget_value(widget, actual_value, field_type)
                            # Negative Button aktivieren
                            if hasattr(negative_button, '_is_negative'):
                                negative_button._is_negative = True
                                negative_button.setText("➖")
                                negative_button.setStyleSheet("""
                                    QPushButton { 
                                        background-color: #f44336; 
                                        color: white; 
                                        border: none; 
                                        border-radius: 3px; 
                                        font-weight: bold;
                                        font-size: 12px;
                                    }
                                    QPushButton:hover { 
                                        background-color: #da190b; 
                                    }
                                """)
                                if isinstance(widget, QLineEdit):
                                    current_placeholder = widget.placeholderText()
                                    widget.setPlaceholderText(current_placeholder.replace("Filter für", "Ausschließen"))
                        else:
                            self._set_widget_value(widget, current_value, field_type)
                        
            except Exception as e:
                logger.warning(f"⚠️ Fehler beim Erstellen des Filter-Feldes {control_key}: {e}")
    
    def _create_text_filter(self, key, name):
        """Erstelle Text-Filter Widget mit linearer Synchronisation"""
        widget = QLineEdit()
        widget.setPlaceholderText(f"Filter für {name}...")
        
        # LINEARE PROGRAMMIERUNG: Text-Änderungen synchronisieren mit Detail-Filter
        widget.textChanged.connect(lambda text: self._on_field_text_changed(key, widget))
        
        return widget
    
    def _create_number_filter(self, key, name):
        """Erstelle Zahlen-Filter Widget mit linearer Synchronisation"""
        widget = QLineEdit()
        widget.setPlaceholderText(f"Zahlen-Filter für {name}...")
        
        # LINEARE PROGRAMMIERUNG: Text-Änderungen synchronisieren mit Detail-Filter
        widget.textChanged.connect(lambda text: self._on_field_text_changed(key, widget))
        
        return widget
    
    def _create_date_filter(self, key, name):
        """Erstelle Datum-Filter Widget mit linearer Synchronisation"""
        widget = QLineEdit()
        widget.setPlaceholderText(f"Datum-Filter für {name} (TT.MM.JJJJ)...")
        
        # LINEARE PROGRAMMIERUNG: Text-Änderungen synchronisieren mit Detail-Filter
        widget.textChanged.connect(lambda text: self._on_field_text_changed(key, widget))
        
        return widget
    
    def _on_field_text_changed(self, field_key: str, widget):
        """
        EINFACHE MODE-BASIERTE Behandlung von Text-Änderungen
        """
        try:
            text = widget.text().strip()
            logger.info(f"📝 Eingabe in '{field_key}': '{text}' (Modus: {self.filter_mode})")
            
            # Nur im EINFACH-Modus normale Filterung
            if self.filter_mode == "EINFACH":
                self.filter_changed.emit()
                
        except Exception as e:
            logger.error(f"❌ Fehler bei Text-Änderung für '{field_key}': {e}")

    def _create_dropdown_filter(self, key, name, config):
        """Erstelle Dropdown-Filter Widget"""
        widget = QComboBox()
        widget.setEditable(True)
        widget.addItem("")  # Leerer Eintrag
        widget.setPlaceholderText(f"Dropdown-Filter für {name}...")
        return widget
    
    def _set_widget_value(self, widget, value, field_type):
        """Setze Wert in Widget basierend auf Typ"""
        try:
            if isinstance(widget, QLineEdit):
                widget.setText(str(value))
            elif isinstance(widget, QComboBox):
                # Versuche den Wert in der ComboBox zu setzen
                index = widget.findText(str(value))
                if index >= 0:
                    widget.setCurrentIndex(index)
                else:
                    widget.setEditText(str(value))
                    
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Setzen des Widget-Werts: {e}")
    
    def _update_ui_with_current_data(self):
        """LINEAR: Aktualisiere UI mit bereits geladenen Daten"""
        try:
            logger.info("🔄 LINEAR: UI mit aktuellen Daten aktualisieren...")
            
            # 1. Einfache Filter in Widgets laden
            for field_key, value in self.current_filters.items():
                if field_key in self.filter_widgets:
                    widget_info = self.filter_widgets[field_key]
                    widget = widget_info['widget']
                    field_type = widget_info.get('type', 'text')
                    self._set_widget_value(widget, value, field_type)
                    logger.info(f"� UI gesetzt: {field_key} = '{value}'")
            
            # 2. Details-Button-Zustände aktualisieren (BEIDE Modi)
            self._update_all_details_button_states_linear()
            
            logger.info("✅ UI linear aktualisiert")
            
        except Exception as e:
            logger.warning(f"⚠️ Fehler bei linearer UI-Aktualisierung: {e}")
    
    def _update_all_details_button_states_linear(self):
        """LINEAR: Aktualisiere Details-Button-Zustände für BEIDE Modi"""
        try:
            from extended_filter_engine import extended_filter_engine
            
            for field_key in self.filter_widgets.keys():
                # DIREKT aus Extended Filter Engine abfragen - EINFACH
                has_conditions = bool(extended_filter_engine.extended_conditions.get(field_key, []))
                self._update_details_button_state(field_key, has_conditions)
                
                if has_conditions:
                    logger.info(f"🟢 Grüner Button: {field_key} hat erweiterte Bedingungen")
                    
            logger.info("✅ Details-Button-Zustände linear aktualisiert")
            
        except Exception as e:
            logger.warning(f"⚠️ Fehler bei Details-Button-Aktualisierung: {e}")
    
    def accept_changes(self):
        """VEREINFACHTER ABLAUF: Sammle alle Filter-Werte und generiere Filterstring"""
        try:
            logger.info("🎯 === VEREINFACHTER FILTER-DIALOG: OK GEDRÜCKT ===")
            
            # SCHRITT 1: Sammle alle Filter-Werte aus den UI-Widgets
            logger.info("� Sammle alle Filter-Werte aus UI")
            collected_filters = {}
            
            for field_key, widget_dict in self.filter_widgets.items():
                # Hole Wert aus normalem Widget
                simple_value = self._get_widget_value(widget_dict)
                
                # Prüfe ob Extended Conditions für dieses Feld existieren
                extended_conditions = self.extended_filter_conditions.get(field_key, [])
                
                if extended_conditions:
                    # Komplexer Filter für dieses Feld
                    logger.info(f"🔧 Komplexer Filter für {field_key}: {len(extended_conditions)} Bedingungen")
                    collected_filters[field_key] = {
                        'type': 'complex',
                        'simple_value': simple_value,
                        'conditions': extended_conditions
                    }
                elif simple_value and simple_value.strip():
                    # Einfacher Filter für dieses Feld
                    logger.info(f"� Einfacher Filter für {field_key}: '{simple_value}'")
                    collected_filters[field_key] = {
                        'type': 'simple',
                        'simple_value': simple_value.strip()
                    }
            
            logger.info(f"📊 Gesammelte Filter: {len(collected_filters)} Felder")
            
            # SCHRITT 2: Sammle alle einfachen Filter-Werte aus Widgets
            logger.info("🟢 Sammle EINFACH-Filter aus normalen Suchfeldern")
            new_filters = {}
            for control_key, widget_dict in self.filter_widgets.items():
                value = self._get_widget_value(widget_dict)
                if value and value.strip():  # Nur nicht-leere Werte
                    new_filters[control_key] = value.strip()

            # SCHRITT 3: Extended Filter zu new_filters hinzufügen (falls vorhanden)
            # HOTFIX: extended_summary definieren für Rückwärtskompatibilität
            extended_summary = {}
            try:
                from extended_filter_engine import extended_filter_engine
                if hasattr(extended_filter_engine, 'get_active_conditions_summary'):
                    extended_summary = extended_filter_engine.get_active_conditions_summary()
            except:
                extended_summary = {}
                
            if extended_summary:
                logger.info("� Füge KOMPLEX-Filter zu Gesamtfiltern hinzu")
                for field_key, summary in extended_summary.items():
                    extended_key = f"EXTENDED:{field_key}"
                    new_filters[extended_key] = summary
                    logger.info(f"� Extended Filter hinzugefügt: {field_key} = {summary}")

            # SCHRITT 4: JETZT ERST Filter-Reset (nachdem ALLES ausgelesen wurde)
            logger.info("🔄 Starte Filter-Reset NACH dem Sammeln aller Bedingungen")
            from central_filter_reset import CentralFilterResetManager
            reset_manager = CentralFilterResetManager(self.view_guid)
            
            # Reset Extended Filter Engine und Caches (aber nicht die aktuell zu setzenden Filter)
            reset_manager._reset_extended_filter_engine()
            reset_manager._reset_filter_caches()

            # V2 EINFACH: Dialog ist AUTONOM!
            # 1. Speichere Parameter unter 'einfach' oder 'komplex'
            filter_type = 'komplex' if (extended_summary and len(extended_summary) > 0) else 'einfach'
            self.save_persistent_filters(new_filters)
            logger.info(f"💾 {len(new_filters)} Filter-Parameter unter '{filter_type}' gespeichert")
            
            # 2. Baue search_string aus Parametern
            search_parts = []
            
            if extended_summary and len(extended_summary) > 0:
                # KOMPLEX: "EXTENDED:field:summary"
                logger.info(f"🔵 KOMPLEX-Filter: {len(extended_summary)} Felder")
                for field_key, summary in extended_summary.items():
                    search_parts.append(f"EXTENDED:{field_key}:{summary}")
            else:
                # EINFACH: "field:value"
                logger.info(f"🟢 EINFACH-Filter: {len(new_filters)} Felder")
                for field_key, value in new_filters.items():
                    if not field_key.startswith('EXTENDED:'):
                        search_parts.append(f"{field_key}:{value}")
            
            search_string = "||".join(search_parts) if search_parts else None
            
            # 3. V3 FILTER-SYSTEM: Verwende richtige Manager
            if extended_summary and len(extended_summary) > 0:
                # KOMPLEX-Filter → KomplexFilterManager
                if self.komplex_filter_manager:
                    # Baue field_conditions Dict für Manager
                    field_conditions = {}
                    for field_key, conditions in self.extended_filter_conditions.items():
                        if conditions:
                            field_conditions[field_key] = conditions
                    
                    success = self.komplex_filter_manager.execute_komplex_filter(field_conditions)
                    if success:
                        logger.info(f"✅ V3 KOMPLEX-Filter angewendet: {len(field_conditions)} Felder")
                    else:
                        logger.error(f"❌ V3 KOMPLEX-Filter fehlgeschlagen")
                else:
                    logger.error("❌ KomplexFilterManager nicht verfügbar")
            elif new_filters:
                # EINFACH-Filter → EinfachFilterManager
                if self.einfach_filter_manager:
                    # Entferne EXTENDED: Prefix für Manager
                    clean_filters = {k: v for k, v in new_filters.items() if not k.startswith('EXTENDED:')}
                    
                    success = self.einfach_filter_manager.execute_einfach_filter(clean_filters)
                    if success:
                        logger.info(f"✅ V3 EINFACH-Filter angewendet: {len(clean_filters)} Felder")
                    else:
                        logger.error(f"❌ V3 EINFACH-Filter fehlgeschlagen")
                else:
                    logger.error("❌ EinfachFilterManager nicht verfügbar")
            else:
                logger.info("ℹ️ Keine Filter - überspringe Ausführung")
            
            # SCHRITT 6: Ergebnis setzen - TRENNUNG UI/VERARBEITUNG
            self.result_filters = new_filters
            self.was_accepted = True
            
            # WICHTIG: Gesamtfilter SOFORT löschen beim Anwenden der Filter
            if new_filters:
                try:
                    # Sofortiges Löschen der Gesamtsuche
                    self._clear_global_search()
                    # Zusätzlich verzögert für Sicherheit
                    from PyQt5.QtCore import QTimer
                    QTimer.singleShot(100, self._clear_global_search)
                    logger.info("✅ Gesamtsuche sofort und verzögert geleert da Spaltenfilter aktiv")
                except Exception as e:
                    logger.warning(f"⚠️ Konnte Gesamtsuche nicht löschen: {e}")
            
            logger.info(f"✅ Filter-Parameter aktualisiert: {len(new_filters)} aktive Filter")
            logger.info("✅ Erweiterte Suchparameter angewendet")
            
            # Dialog schließen
            self.accept()
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Sammeln der Filter-Werte: {e}")
            QMessageBox.warning(self, "Fehler", f"Filter-Werte konnten nicht gespeichert werden:\n{e}")
    
    def cancel_changes(self):
        """EINFACHER LINEARER ABLAUF: Abbrechen - Original Filter beibehalten"""
        try:
            logger.info("🚫 === EINFACHER LINEARER ABLAUF: ABBRECHEN GEDRÜCKT ===")
            
            # Original Filter wiederherstellen
            self.result_filters = self.original_filters.copy()
            self.was_accepted = False
            
            logger.info(f"✅ Original Filter beibehalten: {len(self.original_filters)} Filter")
            
            # Dialog schließen
            self.reject()
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Abbrechen: {e}")
            self.reject()
    
    def restore_original_filters(self):
        """Stelle ursprüngliche Filter in den Widgets wieder her"""
        try:
            # Erst alle Widgets zurücksetzen
            self.reset_all_filters()
            
            # Dann ursprüngliche Werte wiederherstellen
            for control_key, filter_value in self.original_filters.items():
                if control_key in self.filter_widgets:
                    widget_dict = self.filter_widgets[control_key]
                    widget = widget_dict['widget']
                    
                    # Bestimme Feldtyp aus Controls-Config
                    field_type = 'text'  # Default
                    if control_key in self.controls_config:
                        field_type = self.controls_config[control_key].get('type', 'text')
                    
                    self._set_widget_value(widget, filter_value, field_type)
            
            logger.info(f"✅ Ursprüngliche Filter in Widgets wiederhergestellt: {len(self.original_filters)} Filter")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Wiederherstellen der ursprünglichen Filter: {e}")
    
    def _clear_global_search(self):
        """Lösche die globale Suche verzögert"""
        try:
            # Hole parent Dialog (pdvm_view_dialog) und lösche Gesamtsuche
            parent = self.parent()
            while parent and not hasattr(parent, 'search_input'):
                parent = parent.parent()
            
            if parent and hasattr(parent, 'search_input'):
                parent.search_input.clear()
                logger.info("✅ Gesamtsuche verzögert geleert da Spaltenfilter aktiv")
        except Exception as e:
            logger.warning(f"⚠️ Konnte Gesamtsuche nicht löschen: {e}")
    
    def _sync_normal_field_to_first_condition(self, field_key: str, widget_dict):
        """
        LINEARE PROGRAMMIERUNG: Synchronisiert normales Suchfeld mit erster Detail-Bedingung
        
        Das normale Suchfeld ist immer die erste (nicht löschbare) Bedingung im Detail-Filter.
        Dies eliminiert die Komplexität von zwei separaten Filter-Systemen.
        """
        try:
            # Hole aktuelle erweiterte Bedingungen für dieses Feld
            extended_conditions = self.extended_filter_conditions.get(field_key, [])
            
            # Erstelle oder aktualisiere erste Bedingung basierend auf normalem Feld
            normal_value = self._get_widget_value(widget_dict)
            
            if normal_value.strip():
                # Normale Eingabe vorhanden -> erste Bedingung erstellen/aktualisieren
                first_condition = {
                    'operator': None,  # Erste Bedingung hat keinen Operator (wie bisher)
                    'field': field_key,
                    'comparison': 'enthält',
                    'value': normal_value,
                    'case_sensitive': False,
                    'is_first_condition': True  # Markierung für UI
                }
                
                if extended_conditions:
                    # Erste Bedingung ersetzen
                    extended_conditions[0] = first_condition
                else:
                    # Erste Bedingung hinzufügen
                    extended_conditions = [first_condition]
                    
            else:
                # Normale Eingabe leer -> nur erste Bedingung entfernen (andere behalten)
                if extended_conditions and len(extended_conditions) > 1:
                    # Behalte nur Bedingungen ab Index 1
                    extended_conditions = extended_conditions[1:]
                else:
                    # Alle Bedingungen löschen
                    extended_conditions = []
            
            # Aktualisiere erweiterte Bedingungen
            self.extended_filter_conditions[field_key] = extended_conditions
            
            # Synchronisiere mit Extended Filter Engine
            extended_filter_engine.set_field_conditions(field_key, extended_conditions)
            
            # UI-Status aktualisieren
            self._update_field_activation_state(field_key)
            
            logger.info(f"🔄 LINEARE SYNC: '{field_key}' normal→detail, {len(extended_conditions)} Bedingungen total")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei linearer Synchronisation für '{field_key}': {e}")

    def _update_field_activation_state(self, field_key: str):
        """
        LINEARE PROGRAMMIERUNG: Aktualisiert Aktivierungszustand basierend auf Anzahl Bedingungen
        
        KORREKTE REGEL: 
        - Normal-Feld immer aktiv (außer bei ≥2 Bedingungen)
        - Details-Button nur optisch aktiv bei ≥2 Bedingungen
        - Bei 1 Bedingung: Normal-Feld aktiv, Details-Button nicht aktiv markiert
        """
        try:
            conditions = self.extended_filter_conditions.get(field_key, [])
            condition_count = len(conditions)
            
            # Normal-Feld ist aktiv außer bei ≥2 Bedingungen
            field_active = condition_count < 2
            
            # Details-Button ist nur optisch aktiv bei ≥2 Bedingungen
            details_active = condition_count >= 2
            
            # Widget finden und Zustand setzen
            if field_key in self.filter_widgets:
                widget_dict = self.filter_widgets[field_key]
                widget = widget_dict['widget']
                container = widget_dict['container']
                details_button = widget_dict['details_button']
                
                # Normal-Widget aktivieren/deaktivieren
                widget.setEnabled(field_active)
                
                # Visuelles Feedback für Container
                if field_active:
                    container.setStyleSheet("QFrame { background-color: white; }")
                else:
                    container.setStyleSheet("QFrame { background-color: #f0f0f0; }")
                
                # Details-Button visuell anpassen
                if details_active:
                    details_button.setStyleSheet("""
                        QPushButton { 
                            background-color: #2196F3; 
                            color: white; 
                            border: 2px solid #1976D2;
                            border-radius: 3px; 
                            font-weight: bold;
                        }
                    """)
                    details_button.setText("📋 Details*")
                    details_button.setToolTip(f"Erweiterte Bedingungen aktiv ({condition_count} Bedingungen)")
                else:
                    details_button.setStyleSheet("""
                        QPushButton { 
                            background-color: #f0f0f0; 
                            color: #666; 
                            border: 1px solid #ccc;
                            border-radius: 3px; 
                        }
                    """)
                    details_button.setText("📋 Details")
                    details_button.setToolTip("Erweiterte Suchoptionen")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Öffnen des Details-Dialogs für '{field_key}': {e}")

    def _create_dropdown_filter(self, key, name, config):
        """Erstelle Dropdown-Filter (Platzhalter)"""
        # TODO: Implementierung falls benötigt
        pass

    def _get_widget_value(self, widget_dict):
        """Hole Wert aus Widget (jetzt Dictionary mit widget, negative_button, container)"""
        try:
            if isinstance(widget_dict, dict):
                widget = widget_dict['widget']
                negative_button = widget_dict['negative_button']
                
                if isinstance(widget, QLineEdit):
                    value = widget.text()
                elif isinstance(widget, QComboBox):
                    value = widget.currentText()
                else:
                    value = ""
                
                # Wenn negativ-Modus aktiv ist, Wert mit NOT markieren
                if hasattr(negative_button, '_is_negative') and negative_button._is_negative:
                    value = f"NOT:{value}" if value.strip() else ""
                
                return value
            else:
                # Fallback für altes Format (sollte nicht vorkommen)
                logger.warning("⚠️ Altes Widget-Format erkannt")
                return ""
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Lesen des Widget-Werts: {e}")
            return ""
    
    def get_result(self):
        """Ergebnis abrufen"""
        return self.result_filters if self.was_accepted else None
    
    def _show_field_details_dialog(self, field_key: str, field_name: str):
        """
        EINFACHE MODE-BASIERTE Details-Dialog
        """
        from field_search_detail_dialog import FieldSearchDetailDialog
        
        try:
            # Automatisch zu KOMPLEX-Modus wechseln wenn Details geöffnet werden
            if self.filter_mode == "EINFACH":
                logger.info(f"🔄 Auto-Wechsel zu KOMPLEX-Modus für Details-Dialog '{field_key}'")
                self.filter_mode = "KOMPLEX"
                self.update_mode_display()
                self.update_widgets_for_mode()
                
            logger.info(f"🔧 Öffne Details-Dialog für '{field_key}' (Modus: {self.filter_mode})")
            
            # Aktuelle erweiterte Filter für dieses Feld laden
            current_extended = self._load_field_extended_filters(field_key)
            
            # Details-Dialog öffnen (NEUE Signatur)
            dialog = FieldSearchDetailDialog(
                field_name=field_name,
                current_conditions=current_extended,
                parent=self
            )
            
            if dialog.exec_() == QDialog.Accepted:
                # Erweiterte Filter-Bedingungen vom Dialog erhalten
                extended_conditions = dialog.get_conditions()
                
                # Speichere erweiterte Filter für dieses Feld
                self._save_field_extended_filters(field_key, extended_conditions)
                
                # WICHTIG: Sofort in Extended Filter Engine laden
                extended_filter_engine.reload_extended_conditions()
                logger.info(f"🔄 Extended Filter Engine nach Details-Dialog für '{field_key}' aktualisiert")
                
                # Mode-Anzeige aktualisieren (wird AKTIV wenn Bedingungen da sind)
                self.update_mode_display()
                self.update_widgets_for_mode()
                
                # Filter anwenden
                self.filter_changed.emit()
                
                logger.info(f"✅ Details-Dialog für '{field_key}' gespeichert: {len(extended_conditions)} Bedingungen")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Öffnen des Details-Dialogs für '{field_key}': {e}")

    def _load_field_extended_filters(self, field_key: str) -> list:
        """Lade erweiterte Filter für ein Feld - konvertiert Dictionaries zu SearchCondition-Objekten"""
        try:
            # Lade aus GCS anwendungsdaten
            extended_filters = gcs.load_extended_filters(self.view_guid, field_key)
            conditions_data = extended_filters.get('conditions', [])
            
            # Konvertiere Dictionaries zurück zu SearchCondition-Objekten
            from field_search_detail_dialog import SearchCondition
            conditions = []
            for condition_data in conditions_data:
                if isinstance(condition_data, dict):
                    condition = SearchCondition.from_dict(condition_data)
                    conditions.append(condition)
                else:
                    # Fallback für bereits konvertierte Objekte
                    conditions.append(condition_data)
            
            return conditions
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Laden erweiterter Filter für {field_key}: {e}")
            return []
    
    def _save_field_extended_filters(self, field_key: str, conditions: list):
        """Speichere erweiterte Filter für ein Feld"""
        try:
            # Konvertiere SearchCondition-Objekte zu Dictionaries für JSON-Serialisierung
            conditions_dicts = []
            for condition in conditions:
                if hasattr(condition, 'to_dict'):
                    conditions_dicts.append(condition.to_dict())
                else:
                    # Fallback für dictionary-Objekte
                    conditions_dicts.append(condition)
            
            # Speichere in GCS anwendungsdaten
            filter_config = {
                'field_key': field_key,
                'conditions': conditions_dicts,  # Verwende Dictionaries statt Objekte
                'created_at': str(QDate.currentDate().toString('yyyy-MM-dd'))
            }
            gcs.save_extended_filters(self.view_guid, field_key, filter_config)
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern erweiterter Filter für {field_key}: {e}")
    
    def _update_details_button_state(self, field_key: str, has_conditions: bool):
        """Aktualisiere visuellen Zustand des Details-Buttons - EINFACH"""
        try:
            if field_key in self.filter_widgets:
                widget_info = self.filter_widgets[field_key]
                # EINFACH: Erwarte dict-Struktur, fallback bei Problemen
                container = widget_info.get('container') if isinstance(widget_info, dict) else None
                if not container:
                    return
                    
                layout = container.layout()
                
                # Tooltip-Text erstellen falls Bedingungen vorhanden
                tooltip_text = self._create_conditions_tooltip(field_key) if has_conditions else "Erweiterte Filteroptionen öffnen"
                
                # 1. Details-Button aktualisieren
                for i in range(layout.count()):
                    widget = layout.itemAt(i).widget()
                    if isinstance(widget, QPushButton) and widget.text() == "Details...":
                        # Tooltip setzen
                        widget.setToolTip(tooltip_text)
                        
                        if has_conditions:
                            # Aktiv-Zustand: Grüne Hervorhebung (konsistent mit EINFACH-Modus)
                            widget.setStyleSheet("""
                                QPushButton { 
                                    background-color: #4CAF50; 
                                    color: white; 
                                    border: none; 
                                    border-radius: 3px; 
                                    font-weight: bold;
                                    font-size: 10px;
                                }
                                QPushButton:hover { 
                                    background-color: #45a049; 
                                }
                            """)
                        else:
                            # Standard-Zustand: Blau
                            widget.setStyleSheet("""
                                QPushButton { 
                                    background-color: #2196F3; 
                                    color: white; 
                                    border: none; 
                                    border-radius: 3px; 
                                    font-weight: bold;
                                    font-size: 10px;
                                }
                                QPushButton:hover { 
                                    background-color: #1976D2; 
                                }
                            """)
                        break
                
                # 2. Normale Suchfelder aktivieren/deaktivieren
                search_widget = widget_info['widget']
                if has_conditions:
                    # Deaktiviere normale Suchfelder wenn erweiterte Bedingungen aktiv sind
                    search_widget.setEnabled(False)
                    if isinstance(search_widget, QLineEdit):
                        search_widget.setPlaceholderText("Erweiterte Suche aktiv - verwenden Sie 'Details...'")
                        search_widget.setStyleSheet("background-color: #f0f0f0; color: #888;")
                        search_widget.clear()  # Inhalt löschen
                    elif isinstance(search_widget, QComboBox):
                        search_widget.setStyleSheet("background-color: #f0f0f0; color: #888;")
                        search_widget.setCurrentIndex(0)  # Zurücksetzen
                else:
                    # Aktiviere normale Suchfelder wenn keine erweiterten Bedingungen
                    search_widget.setEnabled(True)
                    if isinstance(search_widget, QLineEdit):
                        search_widget.setPlaceholderText("Filter eingeben...")
                        search_widget.setStyleSheet("")  # Standard-Style
                    elif isinstance(search_widget, QComboBox):
                        search_widget.setStyleSheet("")  # Standard-Style
                        
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Aktualisieren des Details-Button-Zustands: {e}")
    
    def _update_all_details_button_states(self):
        """Aktualisiere alle Details-Button-Zustände basierend auf gespeicherten erweiterten Filtern"""
        try:
            for field_key in self.filter_widgets.keys():
                # Prüfe ob erweiterte Filter für dieses Feld existieren
                extended_conditions = self._load_field_extended_filters(field_key)
                has_conditions = bool(extended_conditions)
                self._update_details_button_state(field_key, has_conditions)
                
            logger.info("✅ Alle Details-Button-Zustände aktualisiert")
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Aktualisieren aller Details-Button-Zustände: {e}")
    
    def _create_conditions_tooltip(self, field_key: str) -> str:
        """Erstelle Tooltip-Text mit aktuellen Filtereinstellungen"""
        try:
            extended_conditions = self._load_field_extended_filters(field_key)
            if not extended_conditions:
                return "Erweiterte Filteroptionen öffnen"
            
            tooltip_parts = []
            tooltip_parts.append(f"Erweiterte Filter für {field_key.replace('_show', '').replace('_', ' ').title()}:")
            tooltip_parts.append("")
            
            for i, condition in enumerate(extended_conditions, 1):
                # Erstelle lesbaren Text für jede Bedingung
                logic = condition.logic_operator if hasattr(condition, 'logic_operator') else 'AND'
                negation = condition.negation if hasattr(condition, 'negation') else 'IS'
                operator = condition.operator_type if hasattr(condition, 'operator_type') else 'enthält'
                value = condition.value if hasattr(condition, 'value') else ''
                
                if i == 1 and logic == 'FIRST':
                    logic_text = ""
                else:
                    logic_text = f"{logic} "
                
                negation_text = "NICHT " if negation == 'NOT' else ""
                condition_text = f"{logic_text}{negation_text}{operator} '{value}'"
                tooltip_parts.append(f"{i}. {condition_text}")
            
            return "\n".join(tooltip_parts)
            
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Erstellen des Condition-Tooltips: {e}")
            return "Erweiterte Filteroptionen (Fehler beim Laden der Details)"
    
    def _initialize_extended_filter_engine(self):
        """Initialisiere Extended Filter Engine - VEREINFACHT ohne view_guid Abhängigkeit"""
        try:
            # Extended Filter Engine zurücksetzen
            extended_filter_engine.clear_all_conditions()
            
            # VEREINFACHT: Keine view_guid mehr nötig - wird als Parameter übergeben
            logger.info("✅ Extended Filter Engine zurückgesetzt")
            
            # Alle Felder mit gespeicherten erweiterten Bedingungen laden
            for field_key in self.filter_widgets.keys():
                extended_conditions = self._load_field_extended_filters(field_key)
                if extended_conditions:
                    extended_filter_engine.set_field_conditions(field_key, extended_conditions)
                    
            logger.info("✅ Extended Filter Engine initialisiert")
        except Exception as e:
            logger.warning(f"⚠️ Fehler bei Extended Filter Engine-Initialisierung: {e}")

    def get_filter_string(self):
        """
        ZENTRALE METHODE: Erstellt einheitlichen Filterstring
        
        Returns:
            str: Einheitlicher Filterstring für die Tabellen-Filterung
        """
        try:
            filter_parts = []
            
            # 1. EINFACHE FILTER: Sammle normale Suchfeld-Filter
            if self.filter_mode == "EINFACH":
                logger.info("🟢 Erstelle EINFACH-Filterstring aus normalen Suchfeldern")
                
                for control_key, widget_dict in self.filter_widgets.items():
                    value = self._get_widget_value(widget_dict)
                    if value and value.strip():
                        # Format: "feldname:wert"
                        filter_parts.append(f"{control_key}:{value.strip()}")
                        
            else:
                # 2. KOMPLEXE FILTER: Sammle erweiterte Filter-Bedingungen
                logger.info("🔵 Erstelle KOMPLEX-Filterstring aus erweiterten Bedingungen")
                
                # VEREINFACHT: Erweiterte Bedingungen NEU LADEN mit view_guid Parameter
                try:
                    extended_filter_engine.reload_extended_conditions(self.view_guid)
                    logger.info("🔄 Erweiterte Bedingungen neu geladen für Filterstring-Erstellung")
                except Exception as e:
                    logger.warning(f"⚠️ Fehler beim Neuladen der erweiterten Bedingungen: {e}")
                
                extended_summary = extended_filter_engine.get_active_conditions_summary()
                logger.info(f"🔍 DEBUG: Extended Summary enthält {len(extended_summary)} Felder: {list(extended_summary.keys())}")
                
                for field_key, summary in extended_summary.items():
                    # Format: "EXTENDED:feldname:bedingungen"
                    filter_parts.append(f"EXTENDED:{field_key}:{summary}")
                    logger.info(f"🔍 DEBUG: Filter hinzugefügt für {field_key}: {summary}")
            
            # 3. Erstelle finalen Filterstring
            if not filter_parts:
                filter_string = ""
                logger.info("📝 Kein Filterstring - alle Zeilen anzeigen")
            else:
                filter_string = "||".join(filter_parts)  # Trennzeichen zwischen Filtern
                logger.info(f"📝 Filterstring erstellt: {len(filter_parts)} Filter")
            
            return filter_string
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen des Filterstrings: {e}")
            return ""



    def apply_filters_LINEAR(self, filters_dict):
        """🎯 NEUE LINEARE FILTER-ANWENDUNG - Ersetzt alte apply_filters Methoden"""
        logger.info("🎯 LINEARE FILTER-ANWENDUNG gestartet")
        logger.info(f"📂 View-GUID: {self.view_guid}")
        logger.info(f"🔧 Filter-Dict: {filters_dict}")
        
        try:
            # LinearFilterExecutionManager holen
            manager = get_linear_filter_manager(self.view_guid)
            
            # Konvertiere filters_dict zu Filter-Konfiguration
            if not filters_dict:
                # Leere Filter = alle löschen
                success = manager.clear_all_filters()
                logger.info(f"🧹 Alle Filter gelöscht: {'✅' if success else '❌'}")
                return success
            
            # Bestimme Filter-Type basierend auf filters_dict
            if len(filters_dict) == 1 and 'global' in filters_dict:
                # Gesamtfilter
                filter_config = {'search_text': filters_dict['global']}
                success = manager.execute_filter_linear('gesamtfilter', filter_config)
                logger.info(f"🌐 Gesamtfilter angewendet: {'✅' if success else '❌'}")
                return success
            else:
                # Einfacher Filter (aus erweiterten Filterdaten) - nur ersten verwenden (linear = nur ein Filter!)
                first_field = list(filters_dict.keys())[0]
                first_value = filters_dict[first_field]
                
                filter_config = {
                    'field_name': first_field,
                    'search_value': first_value,
                    'operator': 'enthält'
                }
                
                success = manager.execute_filter_linear('einfach', filter_config)
                logger.info(f"🔍 Einfacher Filter angewendet: {'✅' if success else '❌'}")
                
                # Warnung bei mehreren Filtern - diese werden als komplexer Filter behandelt
                if len(filters_dict) > 1:
                    logger.info(f"🔧 Mehrere Filter erkannt - verwende komplexen Filter")
                    # Erstelle komplexen Filter aus allen Bedingungen
                    conditions = []
                    for field_name, search_value in filters_dict.items():
                        conditions.append({
                            'field': field_name,
                            'operator': 'enthält',
                            'value': search_value
                        })
                    
                    complex_filter_config = {
                        'conditions': conditions,
                        'logical_operator': 'AND'
                    }
                    
                    success = manager.execute_filter_linear('komplex', complex_filter_config)
                    logger.info(f"🔧 Komplexer Filter angewendet: {'✅' if success else '❌'}")
                
                return success
                
        except Exception as e:
            logger.error(f"❌ Fehler bei linearer Filter-Anwendung: {e}")
            return False


def show_search_parameter_dialog(parent, view_guid, controls_config, current_filters=None, matrix_manager=None):
    """
    Zeige Modal-Dialog für Search-Parameter.
    
    Args:
        parent: Parent-Widget
        view_guid: GUID der View für Controls
        controls_config: Dictionary mit Controls direkt vom Dialog
        current_filters: Dict mit aktuellen Filter-Werten
        matrix_manager: Matrix Manager für V3 Filter-System
        
    Returns:
        dict: Neue Filter-Parameter (bei OK) oder ursprüngliche Filter (bei Abbruch)
    """
    dialog = SearchParameterDialog(parent, view_guid, controls_config, current_filters, matrix_manager)
    
    # Modal ausführen (blockiert!)
    result = dialog.exec_()
    
    if result == QDialog.Accepted:
        # OK gedrückt - neue Filter anwenden
        return dialog.get_result()
    else:
        # Abgebrochen - ursprüngliche Filter beibehalten
        # WICHTIG: Bei Abbruch die result_filters nutzen (enthalten die original Filter)
        return dialog.result_filters

# NEUE VEREINFACHTE HILFSMETHODEN (am Ende der Datei)
def save_persistent_filters_unified(view_guid, collected_filters):
    """Speichere alle Filter einheitlich"""
    from filter_helper_methods import save_persistent_filters_unified
    return save_persistent_filters_unified(view_guid, collected_filters)

def generate_filter_string(collected_filters):
    """Generiere Filterstring"""
    from filter_helper_methods import generate_filter_string
    return generate_filter_string(collected_filters)