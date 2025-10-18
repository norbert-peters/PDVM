# hybrid_filter_dialog.py
# HYBRID FILTER DIALOG - EINFACH + KOMPLEX mit Details

import logging
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QLineEdit, QCheckBox, QFrame, QScrollArea, 
                             QWidget, QComboBox, QGroupBox)
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QFont

logger = logging.getLogger(__name__)

class FieldFilterWidget(QFrame):
    """Widget für ein einzelnes Filter-Feld mit Details"""
    
    def __init__(self, field_key, field_label, parent=None):
        super().__init__(parent)
        self.field_key = field_key
        self.field_label = field_label
        self.has_details = False
        
        self.setFrameStyle(QFrame.Box)
        self.setLineWidth(1)
        self.init_ui()
    
    def init_ui(self):
        """Erstelle UI für einzelnes Feld"""
        layout = QVBoxLayout()
        
        # Obere Zeile: Label, Einfach-Input, Details-Button
        top_layout = QHBoxLayout()
        
        # Label
        self.label = QLabel(f"{self.field_label}:")
        self.label.setMinimumWidth(120)
        top_layout.addWidget(self.label)
        
        # Einfacher Input
        self.simple_input = QLineEdit()
        self.simple_input.setPlaceholderText(f"Filter für {self.field_label}...")
        self.simple_input.textChanged.connect(self._on_simple_change)
        top_layout.addWidget(self.simple_input)
        
        # Details Button
        self.details_button = QPushButton("📋 Details")
        self.details_button.setFixedWidth(80)
        self.details_button.clicked.connect(self._toggle_details)
        self.details_button.setStyleSheet("QPushButton { background-color: #f0f0f0; }")
        top_layout.addWidget(self.details_button)
        
        layout.addLayout(top_layout)
        
        # Details-Bereich (initially hidden)
        self.details_frame = QFrame()
        self.details_frame.setVisible(False)
        self.details_frame.setStyleSheet("QFrame { background-color: #f8f8f8; margin: 5px; padding: 5px; }")
        
        details_layout = QVBoxLayout()
        
        # Positiv/Negativ Switch
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Modus:"))
        
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Positiv (enthält)", "Negativ (enthält nicht)"])
        self.mode_combo.currentTextChanged.connect(self._on_details_change)
        mode_layout.addWidget(self.mode_combo)
        mode_layout.addStretch()
        
        details_layout.addLayout(mode_layout)
        
        # Erweiterte Filter-Optionen
        self.operator_combo = QComboBox()
        self.operator_combo.addItems(["enthält", "beginnt mit", "endet mit", "ist gleich", "ist leer"])
        self.operator_combo.currentTextChanged.connect(self._on_details_change)
        
        operator_layout = QHBoxLayout()
        operator_layout.addWidget(QLabel("Operator:"))
        operator_layout.addWidget(self.operator_combo)
        operator_layout.addStretch()
        
        details_layout.addLayout(operator_layout)
        
        # Detail-Wert
        self.detail_input = QLineEdit()
        self.detail_input.setPlaceholderText("Detaillierter Suchbegriff...")
        self.detail_input.textChanged.connect(self._on_details_change)
        
        detail_layout = QHBoxLayout()
        detail_layout.addWidget(QLabel("Wert:"))
        detail_layout.addWidget(self.detail_input)
        
        details_layout.addLayout(detail_layout)
        
        self.details_frame.setLayout(details_layout)
        layout.addWidget(self.details_frame)
        
        self.setLayout(layout)
    
    def _toggle_details(self):
        """Toggle Details-Bereich"""
        self.details_frame.setVisible(not self.details_frame.isVisible())
        
        if self.details_frame.isVisible():
            self.details_button.setText("📋 Details ▼")
            # Kopiere einfachen Wert in Detail-Input falls leer
            if not self.detail_input.text() and self.simple_input.text():
                self.detail_input.setText(self.simple_input.text())
        else:
            self.details_button.setText("📋 Details ►")
    
    def _on_simple_change(self):
        """Aktualisiere Button-Farbe bei einfacher Eingabe"""
        self._update_button_color()
    
    def _on_details_change(self):
        """Aktualisiere Button-Farbe bei Detail-Eingabe"""
        self.has_details = bool(self.detail_input.text().strip())
        self._update_button_color()
    
    def _update_button_color(self):
        """Aktualisiere Button-Farbe basierend auf Inhalt"""
        if self.has_details or self.detail_input.text().strip():
            # Details vorhanden - Orange
            self.details_button.setStyleSheet("QPushButton { background-color: #ffaa00; color: white; font-weight: bold; }")
            self.details_button.setText("📋 Details ●")
        elif self.simple_input.text().strip():
            # Nur einfacher Wert - Hellblau
            self.details_button.setStyleSheet("QPushButton { background-color: #ADD8E6; }")
            self.details_button.setText("📋 Details")
        else:
            # Kein Inhalt - Grau
            self.details_button.setStyleSheet("QPushButton { background-color: #f0f0f0; }")
            self.details_button.setText("📋 Details")
    
    def get_simple_value(self):
        """Hole einfachen Wert"""
        return self.simple_input.text().strip()
    
    def get_detail_data(self):
        """Hole Detail-Daten als Dict"""
        if not self.detail_input.text().strip():
            return None
        
        return {
            'value': self.detail_input.text().strip(),
            'operator': self.operator_combo.currentText(),
            'mode': 'negative' if 'nicht' in self.mode_combo.currentText() else 'positive'
        }
    
    def set_simple_value(self, value):
        """Setze einfachen Wert"""
        self.simple_input.setText(value or '')
        self._update_button_color()
    
    def set_detail_data(self, data):
        """Setze Detail-Daten"""
        if not data:
            return
        
        if isinstance(data, dict):
            self.detail_input.setText(data.get('value', ''))
            
            operator = data.get('operator', 'enthält')
            index = self.operator_combo.findText(operator)
            if index >= 0:
                self.operator_combo.setCurrentIndex(index)
            
            mode = data.get('mode', 'positive')
            mode_text = "Negativ (enthält nicht)" if mode == 'negative' else "Positiv (enthält)"
            index = self.mode_combo.findText(mode_text)
            if index >= 0:
                self.mode_combo.setCurrentIndex(index)
        
        self._update_button_color()


class HybridFilterDialog(QDialog):
    """
    HYBRID FILTER DIALOG
    
    Unterstützt:
    1. Einfaches Filter (nur direkte Eingaben)
    2. Komplexes Filter (mit Detail-Einstellungen)
    3. Persistent Speicherung aller Parameter
    """
    
    def __init__(self, view_guid, parent=None):
        super().__init__(parent)
        self.view_guid = view_guid
        self.field_widgets = {}
        
        self.setWindowTitle("🔍 Hybrid Filter-System")
        self.setModal(True)
        self.resize(700, 600)
        
        self.init_ui()
        self.load_persistent_data()
    
    def init_ui(self):
        """Erstelle Hybrid UI"""
        layout = QVBoxLayout()
        
        # Titel
        title = QLabel("🔍 Hybrid Filter-System")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px; color: #2c3e50;")
        layout.addWidget(title)
        
        # Info
        info = QLabel("💡 Einfach: Direkte Eingabe | Komplex: Details mit erweiterten Optionen")
        info.setStyleSheet("color: #7f8c8d; font-size: 11px; margin-bottom: 10px;")
        layout.addWidget(info)
        
        # Scroll-Bereich für Filter-Felder
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout()
        
        # Standard Filter-Felder erstellen
        self.create_filter_fields(scroll_layout)
        
        scroll_widget.setLayout(scroll_layout)
        scroll.setWidget(scroll_widget)
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)
        
        # Button-Bereich
        button_frame = QFrame()
        button_frame.setFrameStyle(QFrame.StyledPanel)
        button_layout = QVBoxLayout()
        
        # Info für Buttons
        button_info = QLabel("🎯 Drei Modi verfügbar:")
        button_info.setStyleSheet("font-weight: bold; margin: 5px;")
        button_layout.addWidget(button_info)
        
        # Button-Zeile 1: Execution Buttons
        exec_layout = QHBoxLayout()
        
        self.simple_button = QPushButton("🔍 Einfaches Filter")
        self.simple_button.setStyleSheet("""
            QPushButton { 
                background-color: #3498db; 
                color: white; 
                font-weight: bold; 
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        self.simple_button.clicked.connect(self.execute_simple_filter)
        
        self.complex_button = QPushButton("⚙️ Komplexes Filter")
        self.complex_button.setStyleSheet("""
            QPushButton { 
                background-color: #e67e22; 
                color: white; 
                font-weight: bold; 
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #d35400; }
        """)
        self.complex_button.clicked.connect(self.execute_complex_filter)
        
        exec_layout.addWidget(self.simple_button)
        exec_layout.addWidget(self.complex_button)
        button_layout.addLayout(exec_layout)
        
        # Button-Zeile 2: Utility Buttons
        util_layout = QHBoxLayout()
        
        clear_button = QPushButton("🗑️ Alle löschen")
        clear_button.clicked.connect(self.clear_all_filters)
        
        cancel_button = QPushButton("❌ Abbrechen")
        cancel_button.clicked.connect(self.reject)
        
        util_layout.addWidget(clear_button)
        util_layout.addStretch()
        util_layout.addWidget(cancel_button)
        
        button_layout.addLayout(util_layout)
        
        button_frame.setLayout(button_layout)
        layout.addWidget(button_frame)
        
        self.setLayout(layout)
    
    def create_filter_fields(self, layout):
        """Erstelle Filter-Felder"""
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
            widget = FieldFilterWidget(field_key, field_label)
            layout.addWidget(widget)
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
            
            loaded_count = 0
            for field_key, widget in self.field_widgets.items():
                try:
                    # Lade einfache Daten
                    simple_key = f"{field_key}_simple"
                    simple_data, _ = gcs._app_db.get_value(self.view_guid, simple_key) or ('', None)
                    if simple_data:
                        widget.set_simple_value(simple_data)
                        loaded_count += 1
                    
                    # Lade Detail-Daten
                    detail_key = f"{field_key}_details"
                    detail_data, _ = gcs._app_db.get_value(self.view_guid, detail_key) or (None, None)
                    if detail_data:
                        widget.set_detail_data(detail_data)
                        loaded_count += 1
                        
                except Exception as e:
                    logger.warning(f"⚠️ Fehler beim Laden von {field_key}: {e}")
            
            logger.info(f"✅ {loaded_count} persistente Filter-Werte geladen")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden persistenter Daten: {e}")
    
    def save_persistent_data(self, simple_filters, complex_filters):
        """Speichere persistente Filter-Daten"""
        logger.info("💾 Speichere persistente Filter-Daten...")
        
        try:
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            
            if not gcs or not hasattr(gcs, '_app_db'):
                logger.warning("⚠️ GCS nicht verfügbar für Persistierung")
                return
            
            saved_count = 0
            
            # Speichere einfache Filter
            for field_key, value in simple_filters.items():
                simple_key = f"{field_key}_simple"
                gcs._app_db.set_value(self.view_guid, simple_key, value)
                saved_count += 1
            
            # Speichere komplexe Filter
            for field_key, data in complex_filters.items():
                detail_key = f"{field_key}_details"
                gcs._app_db.set_value(self.view_guid, detail_key, data)
                saved_count += 1
            
            logger.info(f"✅ {saved_count} Filter-Werte persistent gespeichert")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern persistenter Daten: {e}")
    
    def collect_simple_filters(self):
        """Sammle einfache Filter-Werte"""
        simple_filters = {}
        
        for field_key, widget in self.field_widgets.items():
            value = widget.get_simple_value()
            if value:
                simple_filters[field_key] = value
                logger.info(f"🔍 Einfach: {field_key} = '{value}'")
        
        return simple_filters
    
    def collect_complex_filters(self):
        """Sammle komplexe Filter-Daten"""
        complex_filters = {}
        
        for field_key, widget in self.field_widgets.items():
            detail_data = widget.get_detail_data()
            if detail_data:
                complex_filters[field_key] = detail_data
                logger.info(f"⚙️ Komplex: {field_key} = {detail_data}")
        
        return complex_filters
    
    def execute_simple_filter(self):
        """METHODE 1: Ausführung Einfaches Filter"""
        logger.info("🔍 === EINFACHES FILTER AUSFÜHRUNG ===")
        
        try:
            # Sammle einfache Filter
            simple_filters = self.collect_simple_filters()
            complex_filters = self.collect_complex_filters()  # Für Persistierung
            
            if not simple_filters:
                logger.warning("⚠️ Keine einfachen Filter-Werte eingegeben")
                return
            
            # Erstelle Such-String mit UND-Verknüpfung
            search_parts = []
            for field_key, value in simple_filters.items():
                # Vereinfache field_key für Search-String
                clean_field = field_key.replace('_show', '')
                search_parts.append(f"{clean_field}:{value}")
            
            search_string = " AND ".join(search_parts)
            logger.info(f"🎯 Einfacher Such-String: '{search_string}'")
            
            # Persistiere alle Daten
            self.save_persistent_data(simple_filters, complex_filters)
            
            # Führe Filter aus
            self._execute_unified_filter(search_string, 'simple')
            
            logger.info("✅ Einfaches Filter erfolgreich ausgeführt")
            
        except Exception as e:
            logger.error(f"❌ FEHLER bei einfachem Filter: {e}")
            raise  # Eindeutiger Fehler, kein Fallback
    
    def execute_complex_filter(self):
        """METHODE 2: Ausführung Komplexes Filter"""
        logger.info("⚙️ === KOMPLEXES FILTER AUSFÜHRUNG ===")
        
        try:
            # Sammle komplexe Filter
            complex_filters = self.collect_complex_filters()
            simple_filters = self.collect_simple_filters()  # Für Persistierung
            
            if not complex_filters:
                logger.warning("⚠️ Keine komplexen Filter-Details eingegeben")
                return
            
            # Erstelle Such-String mit UND/ODER-Verknüpfung
            positive_parts = []
            negative_parts = []
            
            for field_key, data in complex_filters.items():
                clean_field = field_key.replace('_show', '')
                value = data['value']
                operator = data['operator']
                mode = data['mode']
                
                # Erstelle Filter-Teil basierend auf Operator
                if operator == 'enthält':
                    filter_part = f"{clean_field}:{value}"
                elif operator == 'beginnt mit':
                    filter_part = f"{clean_field}:{value}*"
                elif operator == 'endet mit':
                    filter_part = f"{clean_field}:*{value}"
                elif operator == 'ist gleich':
                    filter_part = f"{clean_field}:={value}"
                elif operator == 'ist leer':
                    filter_part = f"{clean_field}:EMPTY"
                else:
                    filter_part = f"{clean_field}:{value}"
                
                # Sortiere nach Positiv/Negativ
                if mode == 'positive':
                    positive_parts.append(filter_part)
                else:
                    negative_parts.append(f"NOT({filter_part})")
            
            # Kombiniere: Positive mit UND, Negative mit ODER
            search_parts = []
            
            if positive_parts:
                search_parts.append(" AND ".join(positive_parts))
            
            if negative_parts:
                search_parts.append(" OR ".join(negative_parts))
            
            search_string = " AND ".join(search_parts) if len(search_parts) > 1 else search_parts[0] if search_parts else ""
            
            logger.info(f"⚙️ Komplexer Such-String: '{search_string}'")
            
            # Persistiere alle Daten
            self.save_persistent_data(simple_filters, complex_filters)
            
            # Führe Filter aus
            self._execute_unified_filter(search_string, 'complex')
            
            logger.info("✅ Komplexes Filter erfolgreich ausgeführt")
            
        except Exception as e:
            logger.error(f"❌ FEHLER bei komplexem Filter: {e}")
            raise  # Eindeutiger Fehler, kein Fallback
    
    def _execute_unified_filter(self, search_string, filter_type):
        """EINHEITLICHE Filter-Ausführung für beide Modi"""
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
            raise  # Eindeutiger Fehler
    
    def clear_all_filters(self):
        """Lösche alle Filter-Eingaben"""
        logger.info("🗑️ Lösche alle Filter-Eingaben...")
        
        for widget in self.field_widgets.values():
            widget.set_simple_value('')
            widget.set_detail_data(None)
        
        logger.info("✅ Alle Filter-Eingaben gelöscht")


def show_hybrid_filter_dialog(parent, view_guid):
    """Zeige Hybrid Filter Dialog"""
    dialog = HybridFilterDialog(view_guid, parent)
    return dialog.exec_() == QDialog.Accepted