"""
PDVM Input-Control Historie-Dialog

Zeigt alle historischen Werte eines Feldes an und ermöglicht Bearbeitung.

ARCHITEKTUR:
- Modal Dialog (blockiert Parent bis geschlossen)
- Tabellarische Anzeige: Abdatum (formatiert) + Wert
- EDITIERBAR: Werte können direkt bearbeitet werden
- Abdatum ist READ-ONLY
- Speichern: set_value() für geänderte Zeilen mit jeweiligem Abdatum
- Sortiert nach Abdatum (neueste zuerst)

AUTOR: Norbert Peters
DATUM: 22.10.2025 (Erweitert: 23.10.2025)
"""

import logging
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QLabel, QTableWidget, 
                              QTableWidgetItem, QPushButton, QHBoxLayout,
                              QHeaderView, QMessageBox, QComboBox, QWidget)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont

from pdvm_datetime import Pdvm_DateTime
from global_gcs import gcs

logger = logging.getLogger(__name__)


class PdvmInputControlHistoryDialog(QDialog):
    """
    Dialog zur Anzeige und Bearbeitung der Historie eines Input-Controls
    
    Zeigt alle historischen Werte tabellarisch an:
    - Spalte 1: Abdatum (formatiert, READ-ONLY)
    - Spalte 2: Wert (EDITIERBAR)
    
    Speichern-Button: Speichert geänderte Werte mit jeweiligem Abdatum
    """
    
    def __init__(self, label: str, gruppe: str, feld: str, 
                 db_instance, control_type='text', display_val=None, field_config=None, parent=None):
        """
        Args:
            label: Anzeige-Label des Controls (z.B. "Familienname")
            gruppe: DB-Gruppe (z.B. "PERSDATEN")
            feld: DB-Feld (z.B. "FAMILIENNAME")
            db_instance: PdvmCentralDatenbank Instanz
            control_type: Type des Controls ('text' oder 'datetime')
            display_val: Display-Format für Datum
            parent: Parent-Widget
        """
        super().__init__(parent)
        
        self.label = label
        self.gruppe = gruppe
        self.feld = feld
        self.db_instance = db_instance
        self.control_type = control_type
        self.display_val = display_val
        # Optional field_config (contains dropdown_config etc.)
        self.field_config = field_config or {}
        
        # Tracking für Änderungen
        self.original_data = {}  # {row: (abdatum, original_value)}
        
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
        """Erstellt UI mit Header + Tabelle + Buttons"""
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
        
        # Spaltenanzahl abhängig von control_type
        if self.control_type == 'viewtable':
            self.table.setColumnCount(3)
            self.table.setHorizontalHeaderLabels(["Abdatum", "GUID", "Name"])
        else:
            self.table.setColumnCount(2)
            self.table.setHorizontalHeaderLabels(["Abdatum", "Wert"])
        
        # Spalten-Breite
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        if self.control_type == 'viewtable':
            header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # GUID
            header.setSectionResizeMode(2, QHeaderView.Stretch)  # Name
        else:
            header.setSectionResizeMode(1, QHeaderView.Stretch)
        
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
        """Lädt historische Werte aus DB und zeigt sie in Tabelle an"""
        try:
            logger.info(f"📜 Lade Historie: {self.gruppe}.{self.feld}")
            
            # get_field() holt ALLE historischen Werte
            history_data = self.db_instance.get_field(self.gruppe, self.feld)
            
            if not history_data:
                logger.warning("    ⚠️ Keine historischen Daten gefunden")
                self._show_no_data()
                return
            
            logger.info(f"    ✅ {len(history_data)} historische Einträge gefunden")
            
            # 🆕 OPTIMIERUNG: DB-Instanz für viewtable einmal am Anfang erstellen
            viewtable_db = None
            if self.control_type == 'viewtable':
                viewtable_db = self._create_viewtable_db_instance()
                if viewtable_db:
                    logger.info(f"    ✅ ViewTable DB-Instanz erstellt für Tabelle: {viewtable_db.table_name}")
                else:
                    logger.warning("    ⚠️ ViewTable DB-Instanz konnte nicht erstellt werden")
            
            # Tabelle befüllen
            self.table.setRowCount(len(history_data))
            
            row = 0
            for timestamp, wert in history_data.items():
                # Timestamp formatieren
                dt = Pdvm_DateTime(gcs.field_value('country'))
                try:
                    dt.PdvmDateTime = float(timestamp)
                    formatted_date = dt.FormTimeStamp
                except:
                    formatted_date = str(timestamp)
                
                # Wert formatieren (abhängig von control_type)
                viewtable_name = None  # Nur für viewtable relevant
                
                if wert is None:
                    formatted_value = ""
                    original_raw_value = None
                elif self.control_type == 'datetime':
                    # Datum: Float → formatiertes Datum (Pdvm_DateTime macht Formatierung)
                    dt_val = Pdvm_DateTime(gcs.field_value('country'))
                    try:
                        dt_val.PdvmDateTime = float(wert)
                        # display_val bestimmt Format automatisch über Pdvm_DateTime
                        formatted_value = dt_val.FormTimeStamp  # Immer vollständig anzeigen
                        original_raw_value = float(wert)  # Rohdatum für Vergleich
                    except:
                        formatted_value = str(wert)
                        original_raw_value = wert
                elif self.control_type == 'dropdown':
                    # Dropdown: wert ist der gespeicherte KEY (z.B. 'm')
                    # Wir versuchen, dropdown_config aus field_config zu laden
                    formatted_value = str(wert)
                    original_raw_value = wert
                elif self.control_type == 'viewtable':
                    # Viewtable: wert ist eine GUID
                    # Speichere GUID und Name separat für 3-Spalten-Anzeige
                    if wert:
                        guid_str = str(wert)
                        # 🆕 OPTIMIERT: Verwende einmal erstellte DB-Instanz
                        if viewtable_db:
                            name_str = viewtable_db.get_name(guid_str)
                        else:
                            name_str = None
                        
                        # formatted_value wird für GUID-Spalte verwendet
                        formatted_value = guid_str[:8] + "..."  # Gekürzte GUID
                        # Name wird in separater Variable gespeichert
                        # FILTER: 'None' String und leere Strings als ungültig behandeln
                        if name_str and name_str not in ('None', 'none', 'NONE'):
                            viewtable_name = name_str
                        else:
                            viewtable_name = "<Kein Name>"
                    else:
                        formatted_value = "<Keine Auswahl>"
                        viewtable_name = ""
                    original_raw_value = wert
                else:
                    # Text: Direkt als String
                    formatted_value = str(wert)
                    original_raw_value = wert
                
                # Original-Daten speichern (Rohdaten für Änderungs-Tracking)
                self.original_data[row] = (float(timestamp), original_raw_value)
                
                # Zeile befüllen
                # Spalte 1: Abdatum (READ-ONLY)
                date_item = QTableWidgetItem(formatted_date)
                date_item.setFlags(date_item.flags() & ~Qt.ItemIsEditable)
                date_item.setData(Qt.UserRole, float(timestamp))  # Rohdatum speichern
                
                # Spalte 2: Wert (EDITIERBAR)
                if self.control_type == 'datetime':
                    # DateTime: PdvmDateTimePicker als Custom-Widget
                    from pdvm_date_time_picker import PdvmDateTimePicker
                    
                    # Pdvm_DateTime Instanz für Picker erstellen
                    value_dt = Pdvm_DateTime(gcs.field_value('country'))
                    if original_raw_value is not None:
                        value_dt.PdvmDateTime = float(original_raw_value)
                    
                    # Display-Mode bestimmen (aus config oder default 'all')
                    display_mode = self.display_val if self.display_val else "all"
                    
                    # Picker erstellen
                    date_picker = PdvmDateTimePicker(
                        parent=self.table,
                        pdvm_datetime=value_dt,
                        display=display_mode
                    )
                    
                    # Als Cell-Widget setzen
                    self.table.setCellWidget(row, 1, date_picker)
                    
                    # Original-Daten anpassen: Picker-Referenz speichern für späteren Abruf
                    self.original_data[row] = (float(timestamp), original_raw_value, date_picker)
                elif self.control_type == 'dropdown':
                    # Render a QComboBox with display texts, but store keys as itemData
                    try:
                        from pdvm_input_type_dropdown import PdvmInputTypeDropdown
                        # Build a lightweight dropdown helper to get mapping
                        dropdown_config = self.field_config.get('dropdown_config', {}) if self.field_config else {}

                        key_to_display = {}
                        display_to_key = {}

                        if dropdown_config:
                            table = dropdown_config.get('table', '')
                            key_field = dropdown_config.get('key', '')
                            value_field = dropdown_config.get('value', '')
                            if table and key_field and value_field:
                                from pdvm_central_datenbank import PdvmCentralDatenbank
                                try:
                                    dd_inst = PdvmCentralDatenbank(table, key_field)
                                    # language from user settings
                                    try:
                                        language = gcs._u_db.get_static_value(gcs.user_guid, 'language')
                                        if not language:
                                            language = 'de-de'
                                    except:
                                        language = 'de-de'

                                    json_data = dd_inst.get_static_value(value_field, language)
                                    if json_data:
                                        import json as _json
                                        parsed = _json.loads(json_data) if isinstance(json_data, str) else json_data
                                        # parsed: {key: display_text}
                                        for k, v in parsed.items():
                                            key_to_display[k] = v
                                            display_to_key[v] = k
                                except Exception:
                                    logger.exception("Fehler beim Laden der Dropdown-Daten für Historie")

                        # Build combobox
                        from PyQt5.QtWidgets import QComboBox
                        combo = QComboBox()
                        # If we have mapping, add in display order
                        if key_to_display:
                            for k, v in key_to_display.items():
                                combo.addItem(v, k)
                        else:
                            # Fallback: show the raw key as single entry
                            combo.addItem(str(original_raw_value), original_raw_value)

                        # Select current key if present
                        if original_raw_value is not None:
                            for i in range(combo.count()):
                                if combo.itemData(i) == original_raw_value:
                                    combo.setCurrentIndex(i)
                                    break

                        # Disable editing if db is read-only in context
                        if hasattr(self.db_instance, 'read_only') and getattr(self.db_instance, 'read_only'):
                            combo.setEnabled(False)

                        self.table.setCellWidget(row, 1, combo)
                        # Store original data with combobox reference
                        self.original_data[row] = (float(timestamp), original_raw_value, combo)
                    except Exception:
                        # Fallback to editable text cell
                        value_item = QTableWidgetItem(formatted_value)
                        value_item.setFlags(value_item.flags() | Qt.ItemIsEditable)
                        self.table.setItem(row, 1, value_item)
                elif self.control_type == 'viewtable':
                    # 🆕 Viewtable: GUID + Name mit Änderungs-Möglichkeit via Doppelklick
                    
                    # Spalte 1 (Index 1): GUID (VOLLSTÄNDIG!)
                    guid_item = QTableWidgetItem(str(original_raw_value) if original_raw_value else "")
                    guid_item.setFlags(guid_item.flags() & ~Qt.ItemIsEditable)  # Nicht direkt editierbar
                    guid_item.setForeground(QColor('#2c3e50'))
                    self.table.setItem(row, 1, guid_item)
                    
                    # Spalte 2 (Index 2): Name (READ-ONLY Anzeige)
                    name_item = QTableWidgetItem(viewtable_name)
                    name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
                    name_item.setForeground(QColor('#2c3e50'))
                    self.table.setItem(row, 2, name_item)
                    
                    # 🎯 EINFACH WIE TEXT: original_data speichern!
                    # Format: (abdatum, original_guid) - GENAU WIE TEXT!
                    self.original_data[row] = (float(timestamp), str(original_raw_value) if original_raw_value else "")
                else:
                    # Text: QTableWidgetItem wie bisher
                    value_item = QTableWidgetItem(formatted_value)
                    value_item.setFlags(value_item.flags() | Qt.ItemIsEditable)
                    self.table.setItem(row, 1, value_item)
                
                self.table.setItem(row, 0, date_item)
                
                row += 1
            
            # Zeilen-Höhe anpassen (wichtig für DateTime-Picker Widgets!)
            if self.control_type == 'datetime':
                # DateTimePicker braucht mehr Platz
                for i in range(self.table.rowCount()):
                    self.table.setRowHeight(i, 40)
            else:
                # Text: Standard-Höhe
                self.table.resizeRowsToContents()
            
            logger.info("    ✅ Tabelle befüllt (editierbar)")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Historie: {e}")
            import traceback
            logger.error(traceback.format_exc())
            self._show_error()
    
    def _get_name_for_viewtable_guid(self, guid):
        """
        Holt den 'name' Wert für eine GUID aus der referenzierten Tabelle.
        
        Tabelle wird aus Control-Key extrahiert:
        - Control-Key Format: TABELLE_GRUPPE_FELD
        - Bei viewtable: FELD = TABELLE-GRUPPE
        - Beispiel: PERSONDATEN_FINANZDATEN_FINANZDATEN-FINANZDATEN
          → Feld = FINANZDATEN-FINANZDATEN → Split "-" → FINANZDATEN → lowercase
        
        Args:
            guid (str): GUID des referenzierten Datensatzes
            
        Returns:
            str|None: Name-Wert oder None wenn nicht gefunden/nicht verfügbar
        """
        try:
            # Extrahiere Tabelle aus Feld (Format: TABELLE-GRUPPE)
            if not self.feld:
                logger.warning("⚠️ Kein Feld vorhanden für Name-Extraktion")
                return None
            
            # Feld Format: TABELLE-GRUPPE (z.B. FINANZDATEN-FINANZDATEN)
            feld_parts = self.feld.split('-')
            if len(feld_parts) < 1:
                logger.warning(f"⚠️ Feld '{self.feld}' hat ungültiges Format (erwartet: TABELLE-GRUPPE)")
                return None
            
            # Erste Stelle = Tabelle (GROSSBUCHSTABEN → lowercase)
            table_name = feld_parts[0].lower()
            
            logger.debug(f"🔍 Tabelle aus Feld '{self.feld}' extrahiert: '{table_name}'")
            
            # Erstelle Datenbank-Instanz für referenzierte Tabelle (OHNE guid im Constructor!)
            from pdvm_central_datenbank import PdvmCentralDatenbank
            ref_db = PdvmCentralDatenbank(table_name=table_name)
            
            # Hole Name aus DB (mit guid als Parameter!)
            name = ref_db.get_name(guid)
            
            if name:
                logger.debug(f"🔍 Name für GUID {guid[:8]}...: '{name}'")
                return name
            else:
                logger.debug(f"⚠️ Kein Name für GUID {guid[:8]}... gefunden")
                return None
                
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Holen des Namens für GUID {guid}: {e}")
            return None
    
    def _create_viewtable_db_instance(self):
        """
        Erstellt EINMALIG eine DB-Instanz für viewtable Name-Lookups.
        
        Extrahiert Tabellen-Name aus Feld (Format: TABELLE-GRUPPE):
        - Beispiel: FINANZDATEN-FINANZDATEN → finanzdaten
        
        Returns:
            PdvmCentralDatenbank|None: DB-Instanz oder None bei Fehler
        """
        try:
            # Extrahiere Tabelle aus Feld (Format: TABELLE-GRUPPE)
            if not self.feld:
                logger.warning("⚠️ Kein Feld vorhanden für DB-Instanz-Erstellung")
                return None
            
            # Feld Format: TABELLE-GRUPPE (z.B. FINANZDATEN-FINANZDATEN)
            feld_parts = self.feld.split('-')
            if len(feld_parts) < 1:
                logger.warning(f"⚠️ Feld '{self.feld}' hat ungültiges Format (erwartet: TABELLE-GRUPPE)")
                return None
            
            # Erste Stelle = Tabelle (GROSSBUCHSTABEN → lowercase)
            table_name = feld_parts[0].lower()
            
            logger.debug(f"🔍 Tabelle aus Feld '{self.feld}' extrahiert: '{table_name}'")
            
            # Erstelle Datenbank-Instanz für referenzierte Tabelle (OHNE guid im Constructor!)
            from pdvm_central_datenbank import PdvmCentralDatenbank
            db_instance = PdvmCentralDatenbank(table_name=table_name)
            
            return db_instance
            
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Erstellen der ViewTable DB-Instanz: {e}")
            return None
    
    def _open_viewtable_selection(self, row, old_guid):
        """
        Öffnet View-Dialog zur Auswahl einer neuen GUID für ViewTable-Feld.
        
        Args:
            row (int): Zeile in der Historie-Tabelle
            old_guid (str): Aktuelle GUID (vor Änderung)
        """
        try:
            logger.info(f"📋 Öffne ViewTable-Auswahl für Zeile {row} (alte GUID: {old_guid[:8] if old_guid else 'None'}...)")
            
            # 🎯 KRITISCH: view_guid aus field_config['viewtable_config']['guid'] holen
            if not self.field_config:
                QMessageBox.warning(self, "Fehler", "Keine Feld-Konfiguration verfügbar")
                return
            
            viewtable_config = self.field_config.get('viewtable_config', {})
            if not viewtable_config:
                QMessageBox.warning(self, "Fehler", "Keine ViewTable-Konfiguration gefunden")
                return
            
            # PRIMÄR: 'guid' (wie in pdvm_input_type_viewtable.py verwendet)
            view_guid = viewtable_config.get('guid')
            
            # FALLBACK: 'view_guid' (falls abweichend benannt)
            if not view_guid:
                view_guid = viewtable_config.get('view_guid')
            
            if not view_guid:
                QMessageBox.warning(self, "Fehler", 
                    f"Keine View-GUID in viewtable_config gefunden!\n\nConfig: {viewtable_config}")
                return
            
            logger.info(f"  ✅ View-GUID gefunden: {view_guid}")
            
            # 🆕 ULTRA-EINFACH: Verwende existierenden ViewTable-Dialog!
            from pdvm_input_viewtable_selection_dialog import PdvmInputViewtableSelectionDialog
            
            dialog = PdvmInputViewtableSelectionDialog(
                viewtable_guid=view_guid,
                current_guid=old_guid,  # Aktuelle Auswahl vormarkieren
                parent=self
            )
            
            result = dialog.exec_()
            
            if result == QDialog.Accepted:
                # Benutzer hat neue GUID ausgewählt
                new_guid = dialog.selected_guid
                
                if new_guid and new_guid != old_guid:
                    logger.info(f"  ✅ Neue GUID gewählt: {new_guid[:8]}...")
                    
                    # Aktualisiere Anzeige in Historie-Tabelle
                    self._update_viewtable_row(row, new_guid)
                    
                    # 🎯 EINFACH WIE TEXT: Aktualisiere QTableWidgetItem mit neuer GUID!
                    guid_item = self.table.item(row, 1)
                    if guid_item:
                        guid_item.setText(str(new_guid))
                        logger.info(f"  ✅ GUID in Tabelle aktualisiert (Zeile {row})")
                else:
                    logger.info("  ℹ️ Keine Änderung (gleiche GUID gewählt)")
            else:
                logger.info("  ℹ️ Auswahl abgebrochen")
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Öffnen der ViewTable-Auswahl: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Fehler", f"Fehler beim Öffnen der Auswahl:\n{e}")
    
    def _on_viewtable_double_click(self, item):
        """
        Handler für Doppelklick auf ViewTable-Zeile.
        Öffnet View-Dialog zur Auswahl einer neuen GUID.
        
        Args:
            item: QTableWidgetItem das doppelgeklickt wurde
        """
        row = item.row()
        
        # Hole aktuelle GUID aus Spalte 1
        guid_item = self.table.item(row, 1)
        if not guid_item:
            return
        
        old_guid = guid_item.text()
        
        logger.info(f"🖱️ Doppelklick auf ViewTable-Zeile {row}")
        
        # Öffne Auswahl-Dialog
        self._open_viewtable_selection(row, old_guid)
    
    def _update_viewtable_row(self, row, new_guid):
        """
        Aktualisiert Anzeige einer ViewTable-Zeile nach GUID-Änderung.
        
        Args:
            row (int): Zeile in der Historie-Tabelle
            new_guid (str): Neue GUID
        """
        try:
            # Hole Namen für neue GUID
            viewtable_db = self._create_viewtable_db_instance()
            if viewtable_db:
                new_name = viewtable_db.get_name(new_guid)
                if not new_name or new_name in ('None', 'none', 'NONE'):
                    new_name = "<Kein Name>"
            else:
                new_name = "<Name nicht verfügbar>"
            
            # Aktualisiere GUID in Spalte 1 (kein Widget mehr, nur Item!)
            guid_item = self.table.item(row, 1)
            if guid_item:
                guid_item.setText(str(new_guid))  # Vollständige GUID
            
            # Aktualisiere Name in Spalte 2
            name_item = self.table.item(row, 2)
            if name_item:
                name_item.setText(new_name)
            
            logger.info(f"  ✅ Zeile {row} aktualisiert: {new_guid} → {new_name}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktualisieren der Zeile {row}: {e}")
    
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
    
    def _save_changes(self):
        """
        Speichert alle geänderten Werte
        
        ABLAUF:
        1. Geänderte Zeilen identifizieren
        2. Für jede geänderte Zeile: set_value() mit Abdatum aus Zeile
        3. save_all_values() aufrufen
        4. Bestätigungsfenster anzeigen
        5. Mit OK beide Fenster schließen
        """
        try:
            logger.info(f"💾 Speichere Historie-Änderungen: {self.gruppe}.{self.feld}")
            
            changes = []
            
            # [1] Geänderte Zeilen identifizieren
            for row in range(self.table.rowCount()):
                # Original-Wert holen
                if row not in self.original_data:
                    continue
                
                # Wert abholen (unterschiedlich je nach control_type)
                if self.control_type == 'datetime':
                    # DateTime: Wert aus Picker-Widget holen
                    date_picker = self.table.cellWidget(row, 1)
                    if not date_picker:
                        continue
                    
                    # Picker speichern → committed Wert
                    date_picker.save()
                    
                    # Current-Value als Float
                    current_value = date_picker.pdvm_datetime.PdvmDateTime
                    
                    # Original-Daten haben jetzt 3 Elemente (abdatum, original_value, picker)
                    abdatum, original_value, _ = self.original_data[row]
                    
                    # Änderung prüfen (Float-Vergleich)
                    is_changed = (current_value != original_value)
                    
                elif self.control_type == 'dropdown':
                    # Dropdown: QComboBox in der Zelle
                    combo = self.table.cellWidget(row, 1)
                    if not combo:
                        continue

                    # current key stored in itemData
                    idx = combo.currentIndex()
                    current_value = combo.itemData(idx) if idx >= 0 else None

                    # Original-Daten haben jetzt 3 Elemente (abdatum, original_key, combo)
                    abdatum, original_value, _ = self.original_data[row]

                    # Änderung prüfen (Key-Vergleich)
                    is_changed = (current_value != original_value)

                elif self.control_type == 'viewtable':
                    # 🎯 EINFACH WIE TEXT: Wert aus QTableWidgetItem holen!
                    value_item = self.table.item(row, 1)
                    if not value_item:
                        continue

                    current_value = value_item.text()  # Neue GUID als String

                    # Original-Daten haben 2 Elemente (abdatum, original_value) - WIE TEXT!
                    abdatum, original_value = self.original_data[row]

                    # Änderung prüfen (String-Vergleich) - WIE TEXT!
                    is_changed = (str(current_value) != str(original_value))

                else:
                    # Text: Wert aus QTableWidgetItem
                    value_item = self.table.item(row, 1)
                    if not value_item:
                        continue

                    current_value = value_item.text()

                    # Original-Daten haben 2 Elemente (abdatum, original_value)
                    abdatum, original_value = self.original_data[row]

                    # Änderung prüfen (String-Vergleich)
                    is_changed = (str(current_value) != str(original_value))
                
                # Bei Änderung: Zur Liste hinzufügen
                if is_changed:
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
            
            # [2] Änderungen speichern (set_value für jede Zeile mit abdatum als float)
            for change in changes:
                abdatum_float = change['abdatum']
                new_value = change['new_value']
                
                # Wert konvertieren (abhängig von control_type)
                if self.control_type == 'datetime':
                    # DateTime: new_value ist bereits Float vom Picker!
                    # Keine Konvertierung nötig
                    pass
                elif self.control_type == 'dropdown':
                    # Dropdown: new_value is the key (string) or None
                    if new_value == "":
                        new_value = None
                else:
                    # Text: Leere Strings → None
                    if new_value == "":
                        new_value = None
                
                logger.info(f"    💾 set_value({self.gruppe}, {self.feld}, {new_value}, ab_zeit={abdatum_float})")
                self.db_instance.set_value(
                    self.gruppe, 
                    self.feld, 
                    new_value,
                    ab_zeit=abdatum_float  # Float direkt übergeben
                )
            
            # [3] save_all_values
            logger.info("    💾 save_all_values()")
            self.db_instance.save_all_values()
            
            # [4] Bestätigungsfenster
            logger.info("    ✅ Änderungen gespeichert")
            QMessageBox.information(
                self,
                "Gespeichert",
                f"{len(changes)} Änderung(en) erfolgreich gespeichert."
            )
            
            # [5] Dialog schließen (accept = OK)
            self.accept()
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern der Änderungen: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            QMessageBox.critical(
                self,
                "Fehler",
                f"Fehler beim Speichern:\n{str(e)}"
            )

