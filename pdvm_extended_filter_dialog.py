# pdvm_extended_filter_dialog.py
"""
PDVM Erweiterter Filter-Dialog - KORREKTE ARCHITEKTUR

STRUKTUR:
- Globaler Filter: Bereits in View vorhanden
- Erweiterter Filter: Zwei Filter NEBENEINANDER pro Spaltenzeile

LAYOUT PRO ZEILE (eine pro Spalte):
┌──────────────┬─────────────────────────────┬──────────────────────────────┐
│ Spaltenname  │ EINFACHER FILTER            │ KOMPLEXER FILTER             │
│              │ [Eingabe] [+/-]             │ [Details] [UND/ODER]         │
└──────────────┴─────────────────────────────┴────────────────────            # Speichere in App-DB unter Gruppe=view_guid, Feld='einfach'
            if simple_filters:
                gcs._app_db.set_value(self.view_guid, 'einfach', simple_filters)
                logger.info(f"💾 Einfache Filter gespeichert: {len(simple_filters)} Einträge")
                logger.info(f"📋 Gespeicherte Daten: {simple_filters}")
            else:
                # Lösche gespeicherte Daten wenn keine Filter aktiv
                gcs._app_db.set_value(self.view_guid, 'einfach', [])
                logger.info("💾 Einfache Filter gelöscht (keine aktiven Filter)")
            
            # KRITISCH: Persistiere in Datenbank!
            gcs._app_db.save_all_values()
            logger.info("✅ Filter-Daten in Datenbank persistiert")
            
            # DEBUG: Prüfe ob Daten sofort lesbar sind
            try:
                test_load = gcs._app_db.get_static_value(self.view_guid, 'einfach')
                logger.info(f"🔍 DEBUG Nach Speichern gelesen: {test_load}")
            except Exception as read_error:
                logger.warning(f"⚠️ DEBUG Konnte nach Speichern nicht lesen: {read_error}")
            
            # TODO: Später komplexe Filter speichern unter Feld 'komplex'
            # gcs._app_db.set_value(self.view_guid, 'komplex', complex_filters)
            # gcs._app_db.save_all_values()
            
        except Exception as e:
EINFACHER FILTER:
- Eingabefeld für Suchwert
- +/- Button (Standard: +) → negiert Bedingung
- Operator: Immer "enthält"
- Generiert search_string für 'einzeln' Filter-Typ

KOMPLEXER FILTER:
- Details-Button → erweitert Zeile für Operator-Auswahl
- UND/ODER Button → Verknüpfung zwischen Spalten (Stufe 2)
- Operatoren: enthält, gleich, beginnt mit, endet mit, größer, kleiner (Stufe 2)

PERSISTIERUNG:
- GCS App-DB: Gruppe = view_guid, Feld = 'einfach'/'komplex'
- Strukturierte Daten: Liste von Filter-Objekten
- Format: {"column": "...", "value": "...", "include": true/false, "operator": "enthält"}

SEARCH-STRING FORMAT:
- Einfach: "column1:value1 AND column2:value2"
- Mit NOT: "column1:value1 AND NOT column2:value2"
- Operator immer "enthält" (wird von PdvmMatrixManager interpretiert)
"""

import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QScrollArea, QWidget, QFrame, QGridLayout, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

logger = logging.getLogger(__name__)


class FilterRowWidget(QWidget):
    """
    Widget für EINE Spaltenzeile mit BEIDEN Filtern NEBENEINANDER
    
    Layout:
    [Spaltenname (150px)] | [Einfacher Filter: Eingabe + +/-] | [Komplexer Filter: Details + UND/ODER]
    """
    
    def __init__(self, column_name, column_display_name, parent=None):
        super().__init__(parent)
        self.column_name = column_name
        self.column_display_name = column_display_name
        
        # Status
        self.simple_include = True  # True = +, False = -
        self.complex_active = False  # Komplexer Filter zunächst inaktiv
        
        # Komplexe Filter-Daten
        self.complex_conditions = []  # Liste von Bedingungen
        self.complex_logic = 'UND'  # 'UND' oder 'ODER'
        
        self._init_ui()
    
    def _init_ui(self):
        """Initialisiert kompakte Zeilen-UI"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(10)
        
        # 1. SPALTENNAME (150px, links)
        name_label = QLabel(self.column_display_name)
        name_label.setMinimumWidth(150)
        name_label.setMaximumWidth(150)
        name_label.setFont(QFont("Arial", 9, QFont.Bold))
        layout.addWidget(name_label)
        
        # Trennlinie
        separator1 = QFrame()
        separator1.setFrameShape(QFrame.VLine)
        separator1.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator1)
        
        # 2. EINFACHER FILTER (Eingabe + +/-)
        simple_layout = QHBoxLayout()
        simple_layout.setSpacing(5)
        
        # Eingabefeld
        self.simple_input = QLineEdit()
        self.simple_input.setPlaceholderText("Suchwert (enthält)...")
        self.simple_input.setMinimumWidth(200)
        simple_layout.addWidget(self.simple_input)
        
        # +/- Toggle Button
        self.simple_toggle_btn = QPushButton("✅ +")
        self.simple_toggle_btn.setFixedSize(50, 28)
        self.simple_toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.simple_toggle_btn.clicked.connect(self._toggle_simple_include)
        simple_layout.addWidget(self.simple_toggle_btn)
        
        layout.addLayout(simple_layout)
        
        # Trennlinie
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.VLine)
        separator2.setFrameShadow(QFrame.Sunken)
        layout.addWidget(separator2)
        
        # 3. KOMPLEXER FILTER (Details + UND/ODER) - JETZT AKTIV
        complex_layout = QHBoxLayout()
        complex_layout.setSpacing(5)
        
        # Details Button (AKTIV)
        self.details_btn = QPushButton("Details")
        self.details_btn.setFixedSize(80, 28)
        self.details_btn.setEnabled(True)
        self.details_btn.setStyleSheet("""
            QPushButton {
                background-color: #9E9E9E;
                color: white;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #757575;
            }
        """)
        self.details_btn.clicked.connect(self._open_detail_dialog)
        complex_layout.addWidget(self.details_btn)
        
        # UND/ODER Anzeige (zeigt Logik an, nicht klickbar hier)
        self.logic_btn = QPushButton("UND")
        self.logic_btn.setFixedSize(70, 28)
        self.logic_btn.setEnabled(False)
        self.logic_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                border-radius: 4px;
            }
        """)
        complex_layout.addWidget(self.logic_btn)
        
        layout.addLayout(complex_layout)
        layout.addStretch()
    
    def _toggle_simple_include(self):
        """Toggle zwischen + (include) und - (exclude)"""
        self.simple_include = not self.simple_include
        self._update_toggle_button()
    
    def _update_toggle_button(self):
        """
        Aktualisiert die Toggle-Button Darstellung basierend auf simple_include
        (OHNE den Zustand zu ändern - für programmatisches Laden)
        """
        if self.simple_include:
            self.simple_toggle_btn.setText("✅ +")
            self.simple_toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    font-weight: bold;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
        else:
            self.simple_toggle_btn.setText("❌ -")
            self.simple_toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    font-weight: bold;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #da190b;
                }
            """)
    
    def get_simple_filter_data(self):
        """
        Gibt Daten für einfachen Filter zurück
        
        Returns:
            dict oder None: {'column': str, 'value': str, 'include': bool}
        """
        value = self.simple_input.text().strip()
        if not value:
            return None
        
        return {
            'column': self.column_name,
            'value': value,
            'include': self.simple_include,
            'operator': 'enthält'  # Immer "enthält" für einfachen Filter
        }
    
    def load_simple_data(self, data):
        """Lädt gespeicherte Daten für einfachen Filter"""
        if not data:
            return
        
        self.simple_input.setText(data.get('value', ''))
        self.simple_include = data.get('include', True)
        
        # Update +/- Button
        if not self.simple_include:
            self._toggle_simple_include()
    
    def _open_detail_dialog(self):
        """Öffnet Detail-Dialog für komplexe Bedingungen"""
        from pdvm_complex_filter_detail_dialog import PdvmComplexFilterDetailDialog
        
        dialog = PdvmComplexFilterDetailDialog(
            parent=self,
            column_name=self.column_name,
            column_display_name=self.column_display_name,
            existing_conditions=self.complex_conditions,
            logic_mode=self.complex_logic
        )
        
        if dialog.exec_() == dialog.Accepted:
            # Speichere Ergebnis
            result = dialog.get_result_data()
            self.complex_conditions = result['conditions']
            self.complex_logic = result['logic']
            
            # Update UI
            self._update_complex_ui()
            
            logger.info(f"✅ Detail-Dialog für {self.column_display_name} gespeichert: {len(self.complex_conditions)} Bedingungen")
    
    def _update_complex_ui(self):
        """Aktualisiert UI basierend auf komplexen Filter-Daten"""
        has_conditions = len(self.complex_conditions) > 0
        
        # Details-Button Farbe + Text
        if has_conditions:
            self.details_btn.setText(f"Details ({len(self.complex_conditions)})")
            self.details_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            
            # Tooltip mit Bedingungen
            tooltip_parts = []
            for cond in self.complex_conditions:
                not_prefix = "NOT " if cond.get('not', False) else ""
                op_display = cond.get('operator_display', cond.get('operator', '?'))
                value = cond.get('value', '')
                tooltip_parts.append(f"{not_prefix}{op_display} '{value}'")
            
            separator = f" {self.complex_logic} "
            tooltip_text = f"{self.column_display_name}:\n{separator.join(tooltip_parts)}"
            self.details_btn.setToolTip(tooltip_text)
            
            # Logik-Button Update
            self.logic_btn.setText(self.complex_logic)
            if self.complex_logic == 'UND':
                self.logic_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #2196F3;
                        color: white;
                        font-weight: bold;
                        border-radius: 4px;
                    }
                """)
            else:  # ODER
                self.logic_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #FF9800;
                        color: white;
                        font-weight: bold;
                        border-radius: 4px;
                    }
                """)
        else:
            # Keine Bedingungen - Grau
            self.details_btn.setText("Details")
            self.details_btn.setStyleSheet("""
                QPushButton {
                    background-color: #9E9E9E;
                    color: white;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #757575;
                }
            """)
            self.details_btn.setToolTip("Keine Bedingungen definiert")
            
            # Logik-Button zurücksetzen
            self.logic_btn.setText("UND")
            self.logic_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    font-weight: bold;
                    border-radius: 4px;
                }
            """)
    
    def get_complex_filter_data(self):
        """
        Gibt Daten für komplexen Filter zurück
        
        Returns:
            dict oder None: {
                'column': str,
                'conditions': list,
                'logic': str
            }
        """
        if not self.complex_conditions:
            return None
        
        return {
            'column': self.column_name,
            'column_display': self.column_display_name,
            'conditions': self.complex_conditions,
            'logic': self.complex_logic
        }
    
    def load_complex_data(self, data):
        """Lädt gespeicherte Daten für komplexen Filter"""
        if not data:
            return
        
        self.complex_conditions = data.get('conditions', [])
        self.complex_logic = data.get('logic', 'UND')
        self._update_complex_ui()
    
    def reset_complex_filter(self):
        """Setzt komplexen Filter zurück"""
        self.complex_conditions = []
        self.complex_logic = 'UND'
        self._update_complex_ui()


class PdvmExtendedFilterDialog(QDialog):
    """
    Erweiterter Filter-Dialog mit korrekter Architektur
    
    - Globaler Filter: Bereits in View vorhanden
    - Zwei Filter NEBENEINANDER pro Spaltenzeile
    - Einfacher Filter: Eingabe + +/- (enthält-Operator)
    - Komplexer Filter: Details + UND/ODER (Stufe 2, zunächst inaktiv)
    """
    
    def __init__(self, parent, view_guid, visible_columns):
        super().__init__(parent)
        self.parent_view = parent
        self.view_guid = view_guid
        self.visible_columns = visible_columns  # Liste von (column_name, display_name)
        
        self.filter_rows = {}  # column_name -> FilterRowWidget
        
        self._init_ui()
        self._load_persistent_data()
        
        logger.info(f"🔎 Erweiterter Filter-Dialog erstellt für View: {view_guid}")
        logger.info(f"📊 Sichtbare Spalten: {len(visible_columns)}")
    
    def _init_ui(self):
        """Initialisiert Dialog-UI"""
        self.setWindowTitle("Erweiterter Filter (Einfach + Komplex)")
        self.setMinimumSize(900, 600)
        
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(10)
        
        # Header
        header_label = QLabel("📊 ERWEITERTER FILTER - Spalten-basierte Filterung")
        header_label.setFont(QFont("Arial", 12, QFont.Bold))
        header_label.setStyleSheet("color: #2196F3; padding: 10px;")
        main_layout.addWidget(header_label)
        
        # Info-Text
        info_label = QLabel(
            "Einfacher Filter (links): Suchwert eingeben + +/- für Include/Exclude\n"
            "Komplexer Filter (rechts): Details + UND/ODER (Stufe 2, aktuell inaktiv)"
        )
        info_label.setStyleSheet("color: #666666; padding: 5px; font-size: 9pt;")
        main_layout.addWidget(info_label)
        
        # Scroll-Bereich für Filter-Zeilen
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: 1px solid #cccccc;
                background-color: white;
            }
        """)
        
        # Container für alle Filter-Zeilen
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(3)
        scroll_layout.setContentsMargins(10, 10, 10, 10)
        
        # Erstelle Filter-Zeilen für alle sichtbaren Spalten
        for column_name, display_name in self.visible_columns:
            row_widget = FilterRowWidget(column_name, display_name)
            self.filter_rows[column_name] = row_widget
            scroll_layout.addWidget(row_widget)
            
            # Trennlinie nach jeder Zeile
            separator = QFrame()
            separator.setFrameShape(QFrame.HLine)
            separator.setFrameShadow(QFrame.Sunken)
            scroll_layout.addWidget(separator)
        
        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)
        
        # Button-Leiste
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        # EINFACHER FILTER ausführen
        self.simple_execute_btn = QPushButton("🔍 EINFACHEN FILTER AUSFÜHREN")
        self.simple_execute_btn.setFixedHeight(40)
        self.simple_execute_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                font-size: 10pt;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        self.simple_execute_btn.clicked.connect(self._execute_simple_filter)
        button_layout.addWidget(self.simple_execute_btn)
        
        # KOMPLEXER FILTER ausführen (AKTIV)
        self.complex_execute_btn = QPushButton("🔧 KOMPLEXEN FILTER AUSFÜHREN")
        self.complex_execute_btn.setFixedHeight(40)
        self.complex_execute_btn.setEnabled(True)
        self.complex_execute_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-weight: bold;
                font-size: 10pt;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #e68900;
            }
        """)
        self.complex_execute_btn.clicked.connect(self._execute_complex_filter)
        button_layout.addWidget(self.complex_execute_btn)
        
        # Filter zurücksetzen
        reset_btn = QPushButton("🔄 Zurücksetzen")
        reset_btn.setFixedHeight(40)
        reset_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #e68900;
            }
        """)
        reset_btn.clicked.connect(self._reset_filters)
        button_layout.addWidget(reset_btn)
        
        # Abbrechen
        cancel_btn = QPushButton("❌ Abbrechen")
        cancel_btn.setFixedHeight(40)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #9E9E9E;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #757575;
            }
        """)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        main_layout.addLayout(button_layout)
    
    def _execute_simple_filter(self):
        """
        Führt EINFACHEN Filter aus:
        1. Sammelt alle aktiven einfachen Filter (Eingabefeld + +/-)
        2. Generiert search_string im Format für 'einzeln' Filter-Typ
        3. Übergibt an PdvmMatrixManager (allgemeines Filter)
        """
        try:
            logger.info("🔍 Führe EINFACHEN Filter aus...")
            
            # Sammle alle aktiven Filter
            active_filters = []
            for column_name, row_widget in self.filter_rows.items():
                filter_data = row_widget.get_simple_filter_data()
                if filter_data:
                    active_filters.append(filter_data)
            
            if not active_filters:
                logger.warning("⚠️ Keine Filter-Kriterien definiert")
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Keine Filter", "Bitte mindestens ein Filter-Kriterium eingeben!")
                return
            
            logger.info(f"📋 Aktive Filter: {len(active_filters)}")
            
            # Generiere search_string für 'einzeln' Filter-Typ
            search_string = self._generate_search_string(active_filters)
            logger.info(f"🔤 Generierter search_string: {search_string}")
            
            # Speichere Persistenz
            self._save_persistent_data()
            
            # Übergabe an PdvmMatrixManager (allgemeines Filter)
            self._apply_to_matrix_manager(search_string)
            
            logger.info("✅ Einfacher Filter erfolgreich ausgeführt")
            self.accept()
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Ausführen des einfachen Filters: {e}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Filter-Fehler", f"Einfacher Filter konnte nicht ausgeführt werden:\n{e}")
    
    def _execute_complex_filter(self):
        """
        Führt KOMPLEXEN Filter aus:
        1. Sammelt alle komplexen Filter mit Bedingungen
        2. Generiert erweiterten search_string mit Operatoren
        3. Übergibt an PdvmMatrixManager (allgemeines Filter)
        4. Speichert Persistenz
        """
        try:
            logger.info("🔧 Führe KOMPLEXEN Filter aus...")
            
            # Sammle alle aktiven komplexen Filter
            active_complex_filters = []
            for column_name, row_widget in self.filter_rows.items():
                filter_data = row_widget.get_complex_filter_data()
                if filter_data:
                    active_complex_filters.append(filter_data)
            
            if not active_complex_filters:
                logger.warning("⚠️ Keine komplexen Filter-Kriterien definiert")
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(self, "Keine Filter", "Bitte mindestens ein komplexes Filter-Kriterium definieren!\n\nÖffnen Sie den Details-Dialog über den Details-Button.")
                return
            
            logger.info(f"📋 Aktive komplexe Filter: {len(active_complex_filters)}")
            
            # Generiere erweiterten search_string
            search_string = self._generate_complex_search_string(active_complex_filters)
            logger.info(f"🔤 Generierter komplexer search_string: {search_string}")
            
            # Speichere Persistenz (KOMPLEX)
            self._save_complex_persistent_data()
            
            # Übergabe an PdvmMatrixManager (allgemeines Filter)
            self._apply_to_matrix_manager(search_string)
            
            logger.info("✅ Komplexer Filter erfolgreich ausgeführt")
            self.accept()
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Ausführen des komplexen Filters: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Filter-Fehler", f"Komplexer Filter konnte nicht ausgeführt werden:\n{e}")
    
    def _generate_search_string(self, active_filters):
        """
        Generiert search_string für 'einzeln' Filter-Typ
        
        Format: "column1:value1 AND column2:value2" oder "column1:value1 AND NOT column2:value2"
        - Spalte:Wert für include (+)
        - NOT Spalte:Wert für exclude (-)
        - Operator ist immer "enthält" (wird von PdvmMatrixManager interpretiert)
        - IMMER UND-Verknüpfung zwischen mehreren Filtern
        
        Args:
            active_filters: Liste von Filter-Daten Dicts
            
        Returns:
            str: Formatierter search_string mit AND-Verknüpfung
        """
        parts = []
        
        for filter_data in active_filters:
            column = filter_data['column']
            value = filter_data['value']
            include = filter_data['include']
            
            if include:
                # Include: "column:value"
                parts.append(f"{column}:{value}")
            else:
                # Exclude: "NOT column:value" (NOT vor dem Feld!)
                parts.append(f"NOT {column}:{value}")
        
        # KRITISCHE ÄNDERUNG: Verbinde mit " AND " (UND-Verknüpfung zwischen verschiedenen Spalten)
        search_string = " AND ".join(parts)
        
        logger.info(f"🔤 Search-String generiert: '{search_string}'")
        
        return search_string
    
    def _generate_complex_search_string(self, active_complex_filters):
        """
        Generiert erweiterten search_string für komplexe Filter
        
        Format: Jedes Feld hat mehrere Bedingungen, die intern mit UND/ODER verknüpft sind
        Zwischen Feldern: IMMER UND-Verknüpfung
        
        Beispiel:
        vorname: (enthält 'Paul' OR enthält 'Laurenne')
        UND
        familienname: (gleich 'Maier')
        
        Ergibt: "(vorname:contains:Paul OR vorname:contains:Laurenne) AND familienname:equals:Maier"
        
        Args:
            active_complex_filters: Liste von Complex-Filter-Daten Dicts
            
        Returns:
            str: Formatierter erweiterter search_string
        """
        field_parts = []
        
        for field_filter in active_complex_filters:
            column = field_filter['column']
            conditions = field_filter['conditions']
            logic = field_filter['logic']  # 'UND' oder 'ODER'
            
            if not conditions:
                continue
            
            # Baue Bedingungen für dieses Feld
            condition_parts = []
            for cond in conditions:
                operator = cond['operator']  # contains, equals, gt, lt, etc.
                value = cond['value']
                is_not = cond.get('not', False)
                
                # Format: "column:operator:value" oder "NOT column:operator:value"
                cond_str = f"{column}:{operator}:{value}"
                if is_not:
                    cond_str = f"NOT {cond_str}"
                
                condition_parts.append(cond_str)
            
            # Verknüpfe Bedingungen dieses Feldes mit UND oder ODER
            if len(condition_parts) == 1:
                field_str = condition_parts[0]
            else:
                # Mehrere Bedingungen - mit Klammern gruppieren
                logic_connector = " OR " if logic == 'ODER' else " AND "
                field_str = f"({logic_connector.join(condition_parts)})"
            
            field_parts.append(field_str)
        
        # Verknüpfe verschiedene Felder mit AND
        search_string = " AND ".join(field_parts)
        
        logger.info(f"🔧 Komplexer Search-String generiert: '{search_string}'")
        
        return search_string
    
    def _apply_to_matrix_manager(self, search_string):
        """
        Wendet Filter über PdvmMatrixManager an (allgemeines Filter)
        
        Args:
            search_string: Formatierter Filter-String
        """
        try:
            # Hole PdvmMatrixManager über Parent View
            if not hasattr(self.parent_view, 'matrix_manager'):
                raise AttributeError("Parent View hat keinen matrix_manager")
            
            matrix_manager = self.parent_view.matrix_manager
            
            # Wende Filter an (EINHEITLICHE Methode)
            logger.info("🎯 Wende Filter über PdvmMatrixManager an...")
            matrix_manager.apply_filter(search_string)
            
            # Refresh View
            if hasattr(self.parent_view, 'refresh_table_direct'):
                self.parent_view.refresh_table_direct()
                logger.info("🔄 View aktualisiert")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Anwenden über MatrixManager: {e}")
            raise
    
    def _reset_filters(self):
        """Setzt alle Filter zurück und löscht Persistenz"""
        try:
            logger.info("🔄 Setze alle Filter zurück...")
            
            # Leere alle Eingabefelder und setze auf + zurück (EINFACH)
            for row_widget in self.filter_rows.values():
                row_widget.simple_input.clear()
                if not row_widget.simple_include:
                    row_widget._toggle_simple_include()  # Zurück auf +
                
                # Setze komplexe Filter zurück
                row_widget.reset_complex_filter()
            
            # Lösche Persistenz (beide Filter)
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            if gcs and gcs._app_db:
                # Lösche einfache Filter
                gcs._app_db.set_value(self.view_guid, 'einfach', [])
                logger.info("💾 Einfache Filter-Persistenz gelöscht")
                
                # Lösche komplexe Filter
                gcs._app_db.set_value(self.view_guid, 'komplex', [])
                logger.info("💾 Komplexe Filter-Persistenz gelöscht")
                
                # KRITISCH: Persistiere in Datenbank!
                gcs._app_db.save_all_values()
                logger.info("✅ Reset in Datenbank persistiert")
            
            logger.info("✅ Alle Filter zurückgesetzt und Persistenz gelöscht")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Zurücksetzen: {e}")
    
    def _save_persistent_data(self):
        """
        Speichert Filter-Einstellungen in GCS App-DB mit strukturierten Daten
        
        Struktur:
        - Gruppe: view_guid
        - Feld 'einfach': Liste von Filter-Objekten für einfachen Filter
        - Feld 'komplex': Liste von Filter-Objekten für komplexen Filter (später)
        
        Filter-Objekt Format:
        {
            "column": "familienname_show",
            "value": "ma",
            "include": true  # true = +, false = -
        }
        """
        try:
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            
            if not gcs or not gcs._app_db:
                logger.warning("⚠️ GCS nicht verfügbar - keine Persistierung")
                return
            
            # DEBUG: Prüfe _app_db Konfiguration
            logger.info(f"🔍 DEBUG _app_db.table_name: {gcs._app_db.table_name}")
            logger.info(f"🔍 DEBUG _app_db.guid: {gcs._app_db.guid}")
            logger.info(f"🔍 DEBUG view_guid (Gruppe): {self.view_guid}")
            
            # Sammle EINFACHE Filter-Daten (Liste von Dicts)
            simple_filters = []
            for column_name, row_widget in self.filter_rows.items():
                data = row_widget.get_simple_filter_data()
                if data:  # Nur wenn Wert eingegeben wurde
                    simple_filters.append(data)
            
            # Speichere in App-DB unter view_guid, Feld 'einfach'
            if simple_filters:
                gcs._app_db.set_value(self.view_guid, 'einfach', simple_filters)
                logger.info(f"💾 Einfache Filter gespeichert: {len(simple_filters)} Einträge")
                logger.info(f"� Gespeicherte Daten: {simple_filters}")
            else:
                # Lösche gespeicherte Daten wenn keine Filter aktiv
                gcs._app_db.set_value(self.view_guid, 'einfach', [])
                logger.info("💾 Einfache Filter gelöscht (keine aktiven Filter)")
            
            # KRITISCH: Persistiere in Datenbank!
            gcs._app_db.save_all_values()
            logger.info("✅ Filter-Daten in Datenbank persistiert")
            
            # DEBUG: Prüfe ob Daten sofort lesbar sind
            try:
                test_load = gcs._app_db.get_static_value(self.view_guid, 'einfach')
                logger.info(f"🔍 DEBUG Nach Speichern gelesen: {test_load}")
            except Exception as read_error:
                logger.warning(f"⚠️ DEBUG Konnte nach Speichern nicht lesen: {read_error}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern der einfachen Persistenz: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _save_complex_persistent_data(self):
        """
        Speichert KOMPLEXE Filter-Einstellungen in GCS App-DB
        
        Struktur:
        - Gruppe: view_guid
        - Feld 'komplex': Liste von komplexen Filter-Objekten
        
        Komplexes Filter-Objekt Format:
        {
            "column": "vorname_show",
            "column_display": "Vorname",
            "conditions": [
                {"operator": "contains", "operator_display": "enthält", "value": "Paul", "not": false},
                {"operator": "contains", "operator_display": "enthält", "value": "Laurenne", "not": false}
            ],
            "logic": "ODER"
        }
        """
        try:
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            
            if not gcs or not gcs._app_db:
                logger.warning("⚠️ GCS nicht verfügbar - keine Persistierung")
                return
            
            logger.info(f"🔍 DEBUG Komplexe Persistierung für view_guid: {self.view_guid}")
            
            # Sammle KOMPLEXE Filter-Daten
            complex_filters = []
            for column_name, row_widget in self.filter_rows.items():
                data = row_widget.get_complex_filter_data()
                if data:  # Nur wenn Bedingungen definiert wurden
                    complex_filters.append(data)
            
            # Speichere in App-DB unter view_guid, Feld 'komplex'
            if complex_filters:
                gcs._app_db.set_value(self.view_guid, 'komplex', complex_filters)
                logger.info(f"💾 Komplexe Filter gespeichert: {len(complex_filters)} Felder")
                logger.info(f"📋 Gespeicherte Daten: {complex_filters}")
            else:
                # Lösche gespeicherte Daten wenn keine Filter aktiv
                gcs._app_db.set_value(self.view_guid, 'komplex', [])
                logger.info("💾 Komplexe Filter gelöscht (keine aktiven Filter)")
            
            # KRITISCH: Persistiere in Datenbank!
            gcs._app_db.save_all_values()
            logger.info("✅ Komplexe Filter-Daten in Datenbank persistiert")
            
            # DEBUG: Prüfe ob Daten sofort lesbar sind
            try:
                test_load = gcs._app_db.get_static_value(self.view_guid, 'komplex')
                logger.info(f"🔍 DEBUG Nach Speichern gelesen: {test_load}")
            except Exception as read_error:
                logger.warning(f"⚠️ DEBUG Konnte nach Speichern nicht lesen: {read_error}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern der komplexen Persistenz: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
    
    def _load_persistent_data(self):
        """
        Lädt gespeicherte Filter-Einstellungen aus GCS App-DB
        
        Struktur:
        - Gruppe: view_guid
        - Feld 'einfach': Liste von Filter-Objekten
        - Feld 'komplex': Liste von Filter-Objekten (später)
        """
        try:
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            
            if not gcs or not gcs._app_db:
                logger.warning("⚠️ GCS nicht verfügbar - keine Persistenz geladen")
                return
            
            # Lade EINFACHE Filter aus App-DB (Gruppe=view_guid, Feld='einfach')
            try:
                simple_filters = gcs._app_db.get_static_value(self.view_guid, 'einfach')
                logger.info(f"📂 Rohdaten aus DB geladen: {simple_filters}")
            except Exception as load_error:
                logger.info(f"ℹ️ Keine gespeicherten einfachen Filter gefunden: {load_error}")
                return
            
            if not simple_filters:
                logger.info("ℹ️ Keine gespeicherten einfachen Filter (leere Liste)")
                # NICHT returnen - komplexe Filter müssen trotzdem geladen werden!
            elif isinstance(simple_filters, list):
                # Lade einfache Daten in Filter-Zeilen
                loaded_count = 0
                for filter_obj in simple_filters:
                    if not isinstance(filter_obj, dict):
                        logger.warning(f"⚠️ Ungültiges Filter-Objekt: {filter_obj}")
                        continue
                    
                    column_name = filter_obj.get('column')
                    if column_name and column_name in self.filter_rows:
                        # Setze Wert und +/- im FilterRowWidget
                        row_widget = self.filter_rows[column_name]
                        value = filter_obj.get('value', '')
                        include = filter_obj.get('include', True)
                        
                        # Lade Daten in Widget
                        row_widget.simple_input.setText(value)
                        row_widget.simple_include = include
                        row_widget._update_toggle_button()
                        
                        loaded_count += 1
                        logger.info(f"📂 Filter geladen: {column_name} = '{value}' ({'include' if include else 'exclude'})")
                
                logger.info(f"📂 Einfache Filter-Daten geladen: {loaded_count} von {len(simple_filters)} Filter")
            else:
                logger.warning(f"⚠️ Ungültige einfache Datenstruktur: {type(simple_filters)}")
            
            # Lade KOMPLEXE Filter aus App-DB (Gruppe=view_guid, Feld='komplex')
            # IMMER laden, unabhängig davon ob einfache Filter vorhanden sind!
            try:
                complex_filters = gcs._app_db.get_static_value(self.view_guid, 'komplex')
                logger.info(f"📂 Komplexe Rohdaten aus DB geladen: {complex_filters}")
            except Exception as complex_load_error:
                logger.info(f"ℹ️ Keine gespeicherten komplexen Filter gefunden: {complex_load_error}")
                # KEIN return - Methode normal beenden
                complex_filters = None
            
            if not complex_filters:
                logger.info("ℹ️ Keine gespeicherten komplexen Filter (leere Liste)")
                return
            
            # Validiere Datenstruktur
            if not isinstance(complex_filters, list):
                logger.warning(f"⚠️ Ungültige komplexe Datenstruktur: {type(complex_filters)}")
                return
            
            # Lade komplexe Daten in Filter-Zeilen
            complex_loaded_count = 0
            for filter_obj in complex_filters:
                if not isinstance(filter_obj, dict):
                    logger.warning(f"⚠️ Ungültiges komplexes Filter-Objekt: {filter_obj}")
                    continue
                
                column_name = filter_obj.get('column')
                if column_name and column_name in self.filter_rows:
                    row_widget = self.filter_rows[column_name]
                    row_widget.load_complex_data(filter_obj)
                    complex_loaded_count += 1
                    logger.info(f"📂 Komplexer Filter geladen: {column_name} ({len(filter_obj.get('conditions', []))} Bedingungen)")
            
            logger.info(f"📂 Komplexe Filter-Daten geladen: {complex_loaded_count} von {len(complex_filters)} Felder")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Persistenz: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")


def show_pdvm_extended_filter_dialog(parent, view_guid, visible_columns):
    """
    Zeigt erweiterten Filter-Dialog an
    
    Args:
        parent: Parent Widget (View)
        view_guid: GUID der View für Persistierung
        visible_columns: Liste von (column_name, display_name) Tupeln
        
    Returns:
        bool: True wenn Filter angewendet wurde, False bei Abbruch
    """
    try:
        logger.info("🔎 Öffne erweiterten Filter-Dialog...")
        
        dialog = PdvmExtendedFilterDialog(parent, view_guid, visible_columns)
        result = dialog.exec_()
        
        return result == QDialog.Accepted
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Öffnen des erweiterten Filter-Dialogs: {e}")
        from PyQt5.QtWidgets import QMessageBox
        QMessageBox.critical(parent, "Dialog-Fehler", f"Filter-Dialog konnte nicht geöffnet werden:\n{e}")
        return False
