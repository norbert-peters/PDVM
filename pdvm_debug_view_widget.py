# pdvm_debug_view_widget.py
"""
DEBUG-Version des modernen View-Widgets für Basis-Tabellen-Überprüfung
Zeigt ALLE verfügbaren Spalten mit ihren internen Namen als Überschriften an
"""

import logging
from typing import Dict, Any, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, 
    QLineEdit, QHeaderView, QPushButton, QLabel, QFrame, QMessageBox,
    QComboBox, QSpinBox, QCheckBox, QDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont

logger = logging.getLogger(__name__)

class PdvmDebugViewWidget(QWidget):
    """
    DEBUG-Version: Zeigt ALLE Spalten der Basis-Tabelle mit internen Namen als Überschriften
    Für Entwicklungsphase zur Überprüfung der Datenbeschaffung
    """
    
    # Signals
    rowSelected = pyqtSignal(dict)
    
    def __init__(self, view_guid, user_guid=None, parent=None):
        super().__init__(parent)
        self.view_guid = view_guid
        self.user_guid = user_guid
        # Daten
        self.raw_data = []
        self.table = None
        self.show_source_table = False  # Flag für Quelltabelle
        # Setup
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self):
        """Erstellt die einfache Debug-UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Debug-Info und Steuerung
        control_layout = QHBoxLayout()
        
        info_label = QLabel("🔧 DEBUG-Modus: Basis-Tabellen-Überprüfung")
        info_label.setStyleSheet("font-weight: bold; color: #FF6600; padding: 5px;")
        control_layout.addWidget(info_label)
        
        # Spaltenfilter-Schalter
        control_layout.addStretch()  # Platz zwischen Info und Schaltern
        
        filter_label = QLabel("📊 Spalten-Filter:")
        control_layout.addWidget(filter_label)
        
        # Quelltabelle-Schalter
        self.source_table_checkbox = QCheckBox("Quelltabelle anzeigen")
        self.source_table_checkbox.setChecked(False)
        self.source_table_checkbox.stateChanged.connect(self._toggle_source_table)
        control_layout.addWidget(self.source_table_checkbox)
        
        self.show_all_columns = QCheckBox("Alle Spalten anzeigen")
        self.show_all_columns.setChecked(True)  # Default: Alle anzeigen (Debug-Modus)
        self.show_all_columns.stateChanged.connect(self._toggle_column_display)
        control_layout.addWidget(self.show_all_columns)
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems([
            "Alle Spalten",
            "Nur System-Spalten (uid_*)",
            "Nur Original-Spalten (*_original)",
            "Nur Show-Spalten (*_show)",
            "Nur Datum-Original (*_datum_*_original)",
            "Nur Datum-Show (*_datum_*_show)",
            "Nur Basis-Spalten (ohne automatische)"
        ])
        self.filter_combo.currentTextChanged.connect(self._apply_column_filter)
        control_layout.addWidget(self.filter_combo)
        
        layout.addLayout(control_layout)
        
        # Status-Bereich
        self.status_label = QLabel("📊 Lade Daten...")
        layout.addWidget(self.status_label)
        
        # Refresh-Button
        refresh_button = QPushButton("🔄 Daten neu laden")
        refresh_button.clicked.connect(self._load_data)
        layout.addWidget(refresh_button)
        
        # Tabelle
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSortingEnabled(True)
        
        # Header konfigurieren
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.sectionClicked.connect(self._on_header_clicked)
        
        # Row-Selection-Handler
        self.table.itemSelectionChanged.connect(self._on_row_selected)
        
        layout.addWidget(self.table)
    
    def _load_data(self):
        """Lädt EXAKT die gleichen Daten wie get_value_view - 1:1 Basis-Tabelle"""
        try:
            from pdvm_central_datenbank import PdvmCentralDatenbank
            
            self.status_label.setText("📊 Lade view_config...")
            
            # 1. View-Konfiguration laden
            viewdaten_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name="viewdaten",
                guid=self.view_guid
            )
            
            view_config = viewdaten_db.lesen()
            if not view_config:
                raise ValueError(f"Keine view_config für GUID {self.view_guid} gefunden")
            
            target_table = view_config["ROOT"]["view_table"]
            
            data_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name=target_table,
                guid=self.user_guid
            )
            
            if self.show_source_table:
                self.status_label.setText("📊 Zeige komplette Quelltabelle (Rohdaten)...")
                # Quelltabelle: alle Zeilen und Felder wie in der DB
                self.raw_data = data_db.lesen_alle() or []
                if not self.raw_data:
                    logger.warning("⚠️ Quelltabelle leer")
                    self.status_label.setText("⚠️ Keine Daten in Quelltabelle")
                    return
                # Alle Keys sammeln
                all_columns = set()
                for record in self.raw_data:
                    all_columns.update(record.keys())
                
                sorted_columns = sorted(all_columns)
                
                # 4. DEBUG-Tabelle mit ALLEN get_value_view-Spalten einrichten
                self._setup_debug_table(sorted_columns)
                
                # 5. EXAKT die get_value_view-Daten in Tabelle einfügen
                self._populate_debug_table(sorted_columns)
                
                self.status_label.setText(f"✅ QUELLTABELLE: {len(self.raw_data)} Zeilen, {len(sorted_columns)} Spalten (DB-Rohdaten)")
                
                logger.info(f"🔧 Quelltabelle: {len(self.raw_data)} Zeilen, {len(sorted_columns)} Spalten")
            else:
                self.status_label.setText("📊 Lade komplette Basis-Tabelle über get_value_view...")
                
                # NEUE ARCHITEKTUR: get_value_view() gibt jetzt IMMER die komplette ungefilterte Tabelle zurück
                self.raw_data = data_db.get_value_view(view_config)
                
                if not self.raw_data:
                    logger.warning("⚠️ get_value_view lieferte keine Daten")
                    self.status_label.setText("⚠️ Keine Daten von get_value_view")
                    return
                
                # 3. ALLE Spalten der Basis-Tabelle sammeln (was get_value_view tatsächlich liefert)
                all_columns = set()
                for record in self.raw_data:
                    all_columns.update(record.keys())
                
                # Nach Spalten-Art sortieren: System, dann _original, dann _show, dann Spezial
                system_cols = [col for col in all_columns if col in ["uid", "_guid"]]
                original_cols = sorted([col for col in all_columns if col.endswith("_original")])
                show_cols = sorted([col for col in all_columns if col.endswith("_show")])
                date_cols = sorted([col for col in all_columns if any(suffix in col for suffix in ["_jahr", "_monat", "_tag", "_alter"])] )
                regular_cols = sorted([col for col in all_columns if col not in system_cols + original_cols + show_cols + date_cols])
                
                # Logische Reihenfolge: System → Original → Show → Regular → Date
                sorted_columns = system_cols + original_cols + show_cols + regular_cols + date_cols
                
                # 4. DEBUG-Tabelle mit ALLEN get_value_view-Spalten einrichten
                self._setup_debug_table(sorted_columns)
                
                # 5. EXAKT die get_value_view-Daten in Tabelle einfügen
                self._populate_debug_table(sorted_columns)
                
                # Status aktualisieren
                self.status_label.setText(f"✅ DEBUG: {len(self.raw_data)} Datensätze, {len(sorted_columns)} Spalten (get_value_view 1:1)")
                
                logger.info(f"🔧 DEBUG-Daten DIREKT von get_value_view: {len(self.raw_data)} Datensätze")
                logger.info(f"🔧 ALLE get_value_view Spalten: {sorted_columns}")
                logger.info("📊 NEUE ARCHITEKTUR: get_value_view() liefert jetzt vollständige ungefilterte Tabelle")
            
        except Exception as e:
            logger.error(f"❌ DEBUG-Fehler beim Laden der get_value_view-Daten: {e}")
            self.status_label.setText(f"❌ Fehler: {str(e)}")
    
    def _setup_debug_table(self, columns):
        """Richtet DEBUG-Tabelle mit ALLEN get_value_view Spalten ein (1:1 Basis-Tabelle)"""
        try:
            # Spalten-Anzahl setzen
            self.table.setColumnCount(len(columns))
            
            # DEBUGGING: Interne Spaltennamen als Header verwenden (genau wie get_value_view sie liefert)
            headers = []
            for col in columns:
                # Spalten-Typ erkennen und markieren
                if col in ["uid", "_guid"]:
                    headers.append(f"🔧 {col}")  # System-Spalten
                elif col.endswith("_original"):
                    headers.append(f"📊 {col}")  # Original-Spalten
                elif col.endswith("_show"):
                    headers.append(f"👁️ {col}")  # Show-Spalten  
                elif any(suffix in col for suffix in ["_jahr", "_monat", "_tag", "_alter"]):
                    headers.append(f"📅 {col}")  # Datums-Spalten
                else:
                    headers.append(f"📋 {col}")  # Regular-Spalten
            
            self.table.setHorizontalHeaderLabels(headers)
            
            # Spalten-Zuordnung speichern
            self.debug_columns = columns
            
            # Spalten-Breiten automatisch anpassen
            header = self.table.horizontalHeader()
            header.setStretchLastSection(False)
            for i in range(len(columns)):
                header.resizeSection(i, 120)  # Feste Breite für bessere Lesbarkeit
            
            logger.info(f"🔧 DEBUG-Tabelle 1:1 eingerichtet: {len(columns)} Spalten")
            logger.info(f"🔧 Spalten-Header mit Typ-Markierung: {headers}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Einrichten der DEBUG-Tabelle: {e}")
    
    def _populate_debug_table(self, columns):
        """Befüllt Tabelle mit EXAKT den get_value_view-Daten (1:1 Basis-Tabelle)"""
        try:
            # Tabelle leeren
            self.table.setRowCount(0)
            self.table.setSortingEnabled(False)
            
            # Zeilen hinzufügen - EXAKT wie get_value_view sie liefert
            for row_idx, record in enumerate(self.raw_data):
                self.table.insertRow(row_idx)
                
                for col_idx, column_name in enumerate(columns):
                    # DIREKTER Wert aus get_value_view Record (ohne weitere Verarbeitung)
                    raw_value = record.get(column_name)
                    
                    # DEBUG: Typ-spezifische Darstellung
                    if raw_value is None:
                        display_value = "[NULL]"
                        bg_color = Qt.lightGray
                    elif raw_value == "":
                        display_value = "[LEER]"
                        bg_color = Qt.yellow
                    else:
                        # Bei langen Strings/Werten kürzen für bessere Darstellung
                        str_value = str(raw_value)
                        if len(str_value) > 80:
                            display_value = str_value[:77] + "..."
                        else:
                            display_value = str_value
                        bg_color = Qt.white
                    
                    # Table Item erstellen mit Typ-Info
                    item = QTableWidgetItem(display_value)
                    
                    # Typ-spezifische Markierung
                    if column_name.endswith("_original"):
                        item.setToolTip(f"Original-Wert für {column_name[:-9]}")
                    elif column_name.endswith("_show"):
                        item.setToolTip(f"Display-Wert für {column_name[:-5]}")
                    elif any(suffix in column_name for suffix in ["_jahr", "_monat", "_tag", "_alter"]):
                        item.setToolTip(f"Datums-Extrakt: {column_name}")
                    elif column_name in ["uid", "_guid"]:
                        item.setToolTip(f"System-Spalte: {column_name}")
                        # GUID für Row-Selection speichern
                        item.setData(Qt.UserRole, raw_value)
                    else:
                        item.setToolTip(f"Standard-Feld: {column_name}")
                    
                    # Hintergrundfarbe setzen
                    item.setBackground(bg_color)
                    
                    self.table.setItem(row_idx, col_idx, item)
            
            # Sortierung wieder aktivieren
            self.table.setSortingEnabled(True)
            
            logger.info(f"🔧 DEBUG-Tabelle 1:1 befüllt: {len(self.raw_data)} Zeilen, {len(columns)} Spalten")
            logger.debug(f"✅ Erste Zeile Beispiel-Daten: {dict(list(self.raw_data[0].items())[:5]) if self.raw_data else 'Keine Daten'}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Befüllen der DEBUG-Tabelle: {e}")
            
            # Sortierung aktivieren
            self.table.setSortingEnabled(True)
            
            logger.info(f"🔧 DEBUG-Tabelle 1:1 befüllt: {len(self.raw_data)} Zeilen, {len(columns)} Spalten")
            logger.debug(f"✅ Erste Zeile Beispiel-Daten: {dict(list(self.raw_data[0].items())[:5]) if self.raw_data else 'Keine Daten'}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Befüllen der DEBUG-Tabelle: {e}")

    def _toggle_column_display(self, state):
        """Schaltet zwischen allen Spalten und gefilterter Ansicht um"""
        if state == Qt.Checked:
            # Alle Spalten anzeigen
            self.filter_combo.setCurrentText("Alle Spalten")
        else:
            # Auf Basis-Spalten filtern
            self.filter_combo.setCurrentText("Nur Basis-Spalten (ohne automatische)")
        
    def _apply_column_filter(self, filter_text):
        """Wendet den gewählten Spaltenfilter an"""
        try:
            if not hasattr(self, 'debug_columns') or not self.debug_columns:
                return
                
            # Alle Spalten zunächst einblenden
            for i in range(self.table.columnCount()):
                self.table.setColumnHidden(i, False)
            
            # Filter anwenden
            if filter_text == "Alle Spalten":
                # Alle Spalten anzeigen (bereits gemacht)
                pass
                
            elif filter_text == "Nur System-Spalten (uid_*)":
                # Nur System-Spalten anzeigen
                for i, col in enumerate(self.debug_columns):
                    if not (col.startswith("uid") or col == "_guid"):
                        self.table.setColumnHidden(i, True)
                        
            elif filter_text == "Nur Original-Spalten (*_original)":
                # Nur Original-Spalten anzeigen
                for i, col in enumerate(self.debug_columns):
                    if not (col.endswith("_original") or col.startswith("uid") or col == "_guid"):
                        self.table.setColumnHidden(i, True)
                        
            elif filter_text == "Nur Show-Spalten (*_show)":
                # Nur Show-Spalten anzeigen
                for i, col in enumerate(self.debug_columns):
                    if not (col.endswith("_show") or col.startswith("uid") or col == "_guid"):
                        self.table.setColumnHidden(i, True)
                        
            elif filter_text == "Nur Datum-Original (*_datum_*_original)":
                # Nur Original-Datum-Spalten anzeigen
                for i, col in enumerate(self.debug_columns):
                    is_date_original = (col.endswith("_original") and 
                                      any(date_part in col for date_part in ["_jahr", "_monat", "_tag", "_alter", "datum"]))
                    is_system = col.startswith("uid") or col == "_guid"
                    if not (is_date_original or is_system):
                        self.table.setColumnHidden(i, True)
                        
            elif filter_text == "Nur Datum-Show (*_datum_*_show)":
                # Nur Show-Datum-Spalten anzeigen
                for i, col in enumerate(self.debug_columns):
                    is_date_show = (col.endswith("_show") and 
                                  any(date_part in col for date_part in ["_jahr", "_monat", "_tag", "_alter", "datum"]))
                    is_system = col.startswith("uid") or col == "_guid"
                    if not (is_date_show or is_system):
                        self.table.setColumnHidden(i, True)
                        
            elif filter_text == "Nur Basis-Spalten (ohne automatische)":
                # Nur Basis-Spalten ohne automatische Datums-Spalten
                for i, col in enumerate(self.debug_columns):
                    is_automatic = any(auto_part in col for auto_part in ["_jahr", "_monat", "_tag", "_alter"])
                    is_system = col.startswith("uid") or col == "_guid"
                    is_base = (col.endswith("_original") or col.endswith("_show")) and not is_automatic
                    if not (is_system or is_base):
                        self.table.setColumnHidden(i, True)
            
            # Tabelle neu zeichnen
            self.table.resizeColumnsToContents()
            
            # Status aktualisieren
            visible_cols = sum(1 for i in range(self.table.columnCount()) if not self.table.isColumnHidden(i))
            self.status_label.setText(f"✅ DEBUG: {len(self.raw_data)} Datensätze, {visible_cols}/{len(self.debug_columns)} Spalten sichtbar - Filter: {filter_text}")
            
            logger.info(f"📊 Spaltenfilter angewendet: {filter_text} - {visible_cols}/{len(self.debug_columns)} Spalten sichtbar")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Anwenden des Spaltenfilters: {e}")
    
    def _on_header_clicked(self, logical_index):
        """Header-Klick für Sortierung"""
        try:
            column_name = self.debug_columns[logical_index]
            
            # Toggle Sortierreihenfolge
            if self.table.horizontalHeader().sortIndicatorSection() == logical_index:
                if self.table.horizontalHeader().sortIndicatorOrder() == Qt.AscendingOrder:
                    self.table.sortItems(logical_index, Qt.DescendingOrder)
                else:
                    self.table.sortItems(logical_index, Qt.AscendingOrder)
            else:
                self.table.sortItems(logical_index, Qt.AscendingOrder)
            
            logger.debug(f"🔧 DEBUG-Sortierung: Spalte {column_name}")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Header-Klick: {e}")
    
    def _on_row_selected(self):
        """Row-Selection-Handler"""
        try:
            current_row = self.table.currentRow()
            if current_row >= 0 and current_row < len(self.raw_data):
                record = self.raw_data[current_row]
                
                # Signal emittieren
                self.rowSelected.emit(record)
                
                # DEBUG-Info
                guid = record.get("_guid", record.get("uid", "Unbekannt"))
                logger.info(f"🔧 DEBUG-Row ausgewählt: {guid}")
                
                # Erste paar Felder anzeigen
                preview_fields = ["FAMILIENNAME", "VORNAME", "GEBURTSDATUM", "ANREDE"]
                preview_info = []
                for field in preview_fields:
                    if field in record:
                        value = record[field]
                        if value not in [None, ""]:
                            preview_info.append(f"{field}: {value}")
                
                if preview_info:
                    logger.info(f"   Preview: {', '.join(preview_info)}")
                
        except Exception as e:
            logger.error(f"❌ Fehler bei Row-Selection: {e}")
    
    def refresh(self):
        """Daten neu laden"""
        self._load_data()
    
    def _toggle_source_table(self, state):
        # Dummy-Implementierung, damit kein Fehler entsteht
        # TODO: Implementiere Quelltabelle-Umschaltung, falls benötigt
        pass
