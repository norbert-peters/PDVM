"""
PDVM Input-Control Historie-Dialog V2 - REFACTORED

ARCHITEKTUR-PRINZIP (Plugin-Pattern):
- Dialog = RAHMEN (Tabelle, Buttons, Header) - EINHEITLICH für alle Types!
- Type-Widget = LOGIK (Wert-Darstellung, Änderung, Speichern) - TYPE-SPEZIFISCH!

VORTEILE:
✅ DRY: Code nur 1x statt 4x
✅ Konsistenz: Alle Types verhalten sich gleich
✅ Erweiterbar: Neuer Type = 1 kleine Klasse (30 Zeilen)
✅ Wartbar: Bug-Fix 1x statt 4x

AUTOR: Norbert Peters
DATUM: 27.10.2025
VERSION: 2.0 (Refactored mit Type-Widgets)
"""

import logging
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QTableWidget, 
                              QTableWidgetItem, QPushButton, QHBoxLayout,
                              QHeaderView, QMessageBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from pdvm_datetime import Pdvm_DateTime
from global_gcs import gcs

# Type-Widgets importieren
from pdvm_history_value_widget_text import PdvmHistoryValueWidgetText
from pdvm_history_value_widget_datetime import PdvmHistoryValueWidgetDateTime
from pdvm_history_value_widget_dropdown import PdvmHistoryValueWidgetDropdown
from pdvm_history_value_widget_viewtable import PdvmHistoryValueWidgetViewTable

logger = logging.getLogger(__name__)


class PdvmInputControlHistoryDialog(QDialog):
    """
    Dialog zur Anzeige und Bearbeitung der Historie eines Input-Controls
    
    REFACTORED VERSION mit Type-Widget-Pattern:
    - Rahmen (Tabelle, Buttons) ist identisch für alle Types
    - Type-spezifische Logik in separaten Widget-Klassen
    
    Zeigt alle historischen Werte tabellarisch an:
    - Spalte 0: Abdatum (formatiert, READ-ONLY) - IMMER gleich!
    - Spalte 1: Wert (TYPE-ABHÄNGIG via Widget-Klasse)
    - Spalte 2+: Zusätzliche Spalten (z.B. Name bei ViewTable)
    
    Speichern-Button: Speichert geänderte Werte mit jeweiligem Abdatum
    """
    
    # TYPE-WIDGET MAPPING
    VALUE_WIDGETS = {
        'text': PdvmHistoryValueWidgetText,
        'datetime': PdvmHistoryValueWidgetDateTime,
        'dropdown': PdvmHistoryValueWidgetDropdown,
        'viewtable': PdvmHistoryValueWidgetViewTable,
    }
    
    def __init__(self, label: str, gruppe: str, feld: str, 
                 db_instance, control_type='text', display_val=None, field_config=None, parent=None):
        """
        Args:
            label: Anzeige-Label des Controls (z.B. "Familienname")
            gruppe: DB-Gruppe (z.B. "PERSDATEN")
            feld: DB-Feld (z.B. "FAMILIENNAME")
            db_instance: PdvmCentralDatenbank Instanz
            control_type: Type des Controls ('text', 'datetime', 'dropdown', 'viewtable')
            display_val: Display-Format für Datum (optional)
            field_config: Feld-Konfiguration (für Type-spezifische Settings)
            parent: Parent-Widget
        """
        super().__init__(parent)
        
        self.label = label
        self.gruppe = gruppe
        self.feld = feld
        self.db_instance = db_instance
        self.control_type = control_type
        self.display_val = display_val
        self.field_config = field_config or {}
        
        # 🎯 VIEWTABLE: Tabellen-Name aus feld extrahieren und in field_config speichern
        if self.control_type == 'viewtable' and self.feld:
            # Format: "TABELLE-GRUPPE" → split('-') → erste Teil = Tabelle
            feld_parts = self.feld.split('-')
            if len(feld_parts) >= 1:
                table_name = feld_parts[0].lower()  # z.B. "FINANZDATEN" → "finanzdaten"
                self.field_config['table_name'] = table_name
                logger.info(f"  🎯 ViewTable: Extrahierte Tabelle '{table_name}' aus feld '{self.feld}'")
        
        # Type-Widget instanziieren (wird in _create_ui erstellt)
        self.value_widget = None
        
        # Dialog-Konfiguration
        self.setWindowTitle(f"Historie: {label}")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        # UI erstellen
        self._create_ui()
        
        # Daten laden
        self._load_history()
    
    def _create_ui(self):
        """Erstellt UI mit Header + Tabelle + Buttons (EINHEITLICH für alle Types!)"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # === HEADER ===
        header_label = QLabel(f"📜 Historie: {self.label}")
        header_font = QFont()
        header_font.setPointSize(12)
        header_font.setBold(True)
        header_label.setFont(header_font)
        layout.addWidget(header_label)
        
        # Info-Label
        info_label = QLabel(f"Gruppe: {self.gruppe} | Feld: {self.feld}")
        info_label.setStyleSheet("color: #7f8c8d; font-size: 10pt;")
        layout.addWidget(info_label)
        
        # === TABELLE ===
        self.table = QTableWidget()
        
        # 🎯 TYPE-WIDGET erstellen (Plugin-Pattern!)
        widget_class = self.VALUE_WIDGETS.get(self.control_type, PdvmHistoryValueWidgetText)
        self.value_widget = widget_class(self.table, self.field_config, self.db_instance)
        
        # 🎯 SPALTEN festlegen (Type-abhängig!)
        columns = ["Abdatum", "Wert"] + self.value_widget.get_additional_columns()
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)
        
        # Spalten-Breite
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Abdatum
        
        if len(columns) == 3:  # ViewTable: GUID + Name
            header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # GUID
            header.setSectionResizeMode(2, QHeaderView.Stretch)  # Name
        else:  # Text/DateTime/Dropdown
            header.setSectionResizeMode(1, QHeaderView.Stretch)  # Wert
        
        # Styling
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                alternate-background-color: #f8f9fa;
                gridline-color: #dee2e6;
            }
            QTableWidget::item {
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #3498db;
                color: white;
                font-weight: bold;
                padding: 5px;
                border: none;
            }
        """)
        
        layout.addWidget(self.table)
        
        # 🆕 DOPPELKLICK-HANDLER für ViewTable
        if self.control_type == 'viewtable':
            self.table.itemDoubleClicked.connect(self._on_viewtable_double_click)
        
        # === BUTTONS ===
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # Abbrechen-Button
        cancel_button = QPushButton("Abbrechen")
        cancel_button.clicked.connect(self.reject)
        cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 8px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
        """)
        button_layout.addWidget(cancel_button)
        
        # Speichern-Button
        self.save_button = QPushButton("💾 Speichern")
        self.save_button.clicked.connect(self._save_changes)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 8px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        button_layout.addWidget(self.save_button)
        
        layout.addLayout(button_layout)
    
    def _load_history(self):
        """Lädt historische Daten (EINHEITLICH für alle Types!)"""
        try:
            logger.info(f"📂 Lade Historie: {self.gruppe}.{self.feld} (Type: {self.control_type})")
            
            # Historie aus DB holen
            history_entries = self._load_history_data()
            
            if not history_entries:
                self._show_no_data()
                return
            
            # Tabelle befüllen
            self.table.setRowCount(len(history_entries))
            
            for row, entry in enumerate(history_entries):
                abdatum = entry.get('abdatum')
                wert = entry.get('wert')
                
                # Spalte 0: Abdatum (formatiert) - IMMER gleich!
                formatted_date = self._format_abdatum(abdatum)
                date_item = QTableWidgetItem(formatted_date)
                date_item.setFlags(date_item.flags() & ~Qt.ItemIsEditable)  # READ-ONLY
                self.table.setItem(row, 0, date_item)
                
                # Spalte 1: Wert - TYPE-ABHÄNGIG via Widget!
                self.value_widget.create_value_cell(row, wert, abdatum)
                
                # Spalte 2+: Zusätzliche Spalten (z.B. Name bei ViewTable)
                self.value_widget.create_additional_cells(row, wert)
            
            # Zeilen-Höhe anpassen
            if self.control_type == 'datetime':
                # DateTimePicker braucht mehr Platz
                for i in range(self.table.rowCount()):
                    self.table.setRowHeight(i, 40)
            else:
                self.table.resizeRowsToContents()
            
            logger.info(f"    ✅ {len(history_entries)} Historie-Einträge geladen")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Historie: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self._show_error()
    
    def _load_history_data(self) -> list:
        """
        Lädt Historie-Daten aus DB.
        
        Returns:
            Liste von Dicts: [{'abdatum': float, 'wert': any}, ...]
            Sortiert nach Abdatum (neueste zuerst)
        """
        try:
            # ✅ KORREKT: Verwende get_field() Methode (wie V1!)
            # get_field() gibt Dict zurück: {timestamp: wert, ...}
            history_data = self.db_instance.get_field(self.gruppe, self.feld)
            
            if not history_data:
                logger.info(f"    ℹ️ Keine historischen Daten für {self.gruppe}.{self.feld}")
                return []
            
            # Konvertiere zu Liste von Dicts und sortiere nach Abdatum (neueste zuerst)
            entries = []
            for timestamp, wert in history_data.items():
                entries.append({
                    'abdatum': float(timestamp),
                    'wert': wert
                })
            
            # Sortiere nach Abdatum absteigend (neueste zuerst)
            entries.sort(key=lambda x: x['abdatum'], reverse=True)
            
            return entries
            
        except Exception as e:
            logger.error(f"❌ DB-Fehler beim Laden der Historie: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []
    
    def _format_abdatum(self, abdatum_value) -> str:
        """
        Formatiert Abdatum länderspezifisch.
        
        Args:
            abdatum_value: Float-Wert (PdvmDateTime)
            
        Returns:
            Formatierter String (z.B. "27.10.2025 14:30:00")
        """
        if abdatum_value is None:
            return "Unbekannt"
        
        try:
            if float(abdatum_value) == 1001.0:
                return "01.01.0001 (Default)"
            
            # GCS verwenden (ist bereits importiert)
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            
            dt = Pdvm_DateTime(gcs.country if gcs else 'DEU')
            dt.PdvmDateTime = float(abdatum_value)
            return dt.FormTimeStamp
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Formatieren von Abdatum {abdatum_value}: {e}")
            return str(abdatum_value)
    
    def _save_changes(self):
        """
        Speichert alle geänderten Werte (EINHEITLICH für alle Types!)
        
        ABLAUF:
        1. Type-Widget prüft jede Zeile auf Änderungen
        2. Geänderte Werte sammeln
        3. set_value() für jede Änderung mit jeweiligem Abdatum
        4. save_all_values() aufrufen
        5. Bestätigung anzeigen
        """
        try:
            logger.info(f"💾 Speichere Historie-Änderungen: {self.gruppe}.{self.feld}")
            
            changes = []
            
            # 🎯 TYPE-WIDGET prüft alle Zeilen auf Änderungen!
            for row in range(self.table.rowCount()):
                if self.value_widget.is_value_changed(row):
                    current_value = self.value_widget.get_current_value(row)
                    abdatum, original_value = self.value_widget.get_original_value(row)
                    
                    changes.append({
                        'row': row,
                        'abdatum': abdatum,
                        'old_value': original_value,
                        'new_value': current_value
                    })
                    logger.info(f"    📝 Zeile {row}: '{original_value}' → '{current_value}' (Abdatum: {abdatum})")
            
            # Keine Änderungen?
            if not changes:
                logger.info("    ℹ️ Keine Änderungen gefunden")
                QMessageBox.information(
                    self,
                    "Keine Änderungen",
                    "Es wurden keine Änderungen vorgenommen."
                )
                return
            
            logger.info(f"    ✅ {len(changes)} Änderung(en) gefunden")
            
            # [2] Änderungen speichern
            for change in changes:
                # ✅ KORREKT: Parameter heißt 'ab_zeit' nicht 'abdatum' (wie in V1!)
                self.db_instance.set_value(
                    self.gruppe,
                    self.feld,
                    change['new_value'],
                    ab_zeit=change['abdatum']  # WICHTIG: Abdatum beibehalten!
                )
                logger.info(f"    💾 Gespeichert: Zeile {change['row']}")
            
            # [3] Commit
            self.db_instance.save_all_values()
            logger.info("    ✅ Alle Änderungen committed")
            
            # [4] Bestätigung
            QMessageBox.information(
                self,
                "Erfolgreich gespeichert",
                f"{len(changes)} Änderung(en) wurden gespeichert."
            )
            
            # Dialog mit OK schließen
            self.accept()
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern: {e}")
            import traceback
            logger.error(traceback.format_exc())
            QMessageBox.critical(
                self,
                "Fehler beim Speichern",
                f"Die Änderungen konnten nicht gespeichert werden:\n{e}"
            )
    
    def _on_viewtable_double_click(self, item):
        """
        Handler für Doppelklick auf ViewTable-Zeile.
        Delegiert an ViewTable-Widget.
        
        Args:
            item: QTableWidgetItem das doppelgeklickt wurde
        """
        row = item.row()
        logger.info(f"🖱️ Doppelklick auf ViewTable-Zeile {row}")
        
        # An ViewTable-Widget delegieren
        self.value_widget.open_selection_dialog(row, self)
    
    def _show_no_data(self):
        """Zeigt Nachricht wenn keine Daten vorhanden"""
        self.table.setRowCount(1)
        
        item = QTableWidgetItem("Keine historischen Daten vorhanden")
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        
        self.table.setSpan(0, 0, 1, 2)
        self.table.setItem(0, 0, item)
    
    def _show_error(self):
        """Zeigt Fehlermeldung"""
        self.table.setRowCount(1)
        
        item = QTableWidgetItem("❌ Fehler beim Laden der Historie")
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        
        self.table.setSpan(0, 0, 1, 2)
        self.table.setItem(0, 0, item)
