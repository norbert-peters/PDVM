# pdvm_modern_view_widget_v3.py
"""
Modernes View-Widget V3 mit korrekter Original/Show-Spalten-Architektur
Implementiert die neue Filter- und Sortierungs-Logik
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

# Import der neuen V3-Manager
from pdvm_view_data_manager import PdvmViewDataManager
from pdvm_filter_manager_v3 import PdvmFilterManagerV3
from pdvm_central_datenbank_extensions import install_extensions

logger = logging.getLogger(__name__)

class PdvmModernViewWidget(QWidget):
    """
    Modernes View-Widget V3 mit korrekter Original/Show-Spalten-Architektur
    
    Neue Architektur:
    1. Zentrale Datenaufbereitung in PdvmCentralDatenbank
    2. Original/Show-Spalten für alle Feldtypen
    3. Spezielle Spalten: Alter, Jahr, Monat, Tag (immer vorhanden)
    4. Filter arbeiten auf Show-Spalten (außer Datum-Zeitraum-Modus)
    5. Sortierung basierend auf sortByOriginal-Parameter
    6. Benutzer-Einstellungen in systemsteuerung
    """
    
    # Signals
    rowSelected = pyqtSignal(dict)
    dataChanged = pyqtSignal()
    
    def __init__(self, view_guid, user_guid=None, parent=None):
        super().__init__(parent)
        
        # Erweiterungen installieren
        install_extensions()
        
        self.view_guid = view_guid
        self.user_guid = user_guid
        
        # V3 Manager-Pattern
        self.data_manager = None
        self.filter_manager = None
        
        # UI State
        self.search_widgets = {}
        self.filter_buttons = {}
        self.current_sort_column = None
        self.current_sort_order = Qt.AscendingOrder
        
        # Search delay timer
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._on_search_timer)
        
        # Initialisierung
        self._initialize_managers()
        self._setup_ui()
        self._initial_load()
    
    def _initialize_managers(self):
        """Initialisiert Data- und Filter-Manager V3"""
        try:
            # Data-Manager V3
            self.data_manager = PdvmViewDataManager(
                view_guid=self.view_guid,
                user_guid=self.user_guid
            )
            
            # Filter-Manager V3
            self.filter_manager = PdvmFilterManagerV3(self.data_manager)
            
            logger.info(f"✅ Manager V3 initialisiert: {self.data_manager.get_table_info()}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Initialisieren der Manager V3: {e}")
            raise
    
    def _setup_ui(self):
        """Erstellt die UI-Struktur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Toolbar
        self._create_toolbar(layout)
        
        # Search Area
        self._create_search_area(layout)
        
        # Filter Area
        self._create_filter_area(layout)
        
        # Main Table
        self._create_table(layout)
        
        # Status Bar
        self._create_status_bar(layout)
    
    def _create_toolbar(self, layout):
        """Erstellt die Toolbar"""
        toolbar_frame = QFrame()
        toolbar_frame.setFrameShape(QFrame.StyledPanel)
        toolbar_layout = QHBoxLayout(toolbar_frame)
        toolbar_layout.setContentsMargins(5, 5, 5, 5)
        
        # Refresh Button
        self.refresh_btn = QPushButton("🔄 Aktualisieren")
        self.refresh_btn.clicked.connect(self.refresh)
        toolbar_layout.addWidget(self.refresh_btn)
        
        # Clear Filters Button
        self.clear_filters_btn = QPushButton("❌ Filter löschen")
        self.clear_filters_btn.clicked.connect(self._clear_all_filters)
        toolbar_layout.addWidget(self.clear_filters_btn)
        
        # Save Settings Button
        self.save_settings_btn = QPushButton("💾 Einstellungen speichern")
        self.save_settings_btn.clicked.connect(self._save_user_settings)
        toolbar_layout.addWidget(self.save_settings_btn)
        
        # Spacer
        toolbar_layout.addStretch()
        
        # Export Button
        self.export_btn = QPushButton("📊 Export")
        self.export_btn.clicked.connect(self._export_data)
        toolbar_layout.addWidget(self.export_btn)
        
        layout.addWidget(toolbar_frame)
    
    def _create_search_area(self, layout):
        """Erstellt den Search-Bereich"""
        search_frame = QFrame()
        search_frame.setFrameShape(QFrame.StyledPanel)
        search_layout = QVBoxLayout(search_frame)
        search_layout.setContentsMargins(5, 5, 5, 5)
        
        # Title
        search_title = QLabel("🔍 Textsuche")
        search_title.setFont(QFont("Arial", 10, QFont.Bold))
        search_layout.addWidget(search_title)
        
        # Search Grid
        search_grid = QHBoxLayout()
        
        # Erstelle Search-Widgets für alle String-Felder
        for field_config in self.data_manager.get_fields_config():
            field_name = field_config.get("feld")
            field_type = field_config.get("type", "string")
            ui_config = field_config.get("ui", {})
            filter_type = ui_config.get("filterType", "contains")
            
            if field_type == "string" and filter_type in ["contains", "exact", "startsWith", "endsWith"]:
                # Label
                label = QLabel(f"{field_config.get('bezeichnung', field_name)}:")
                search_grid.addWidget(label)
                
                # Search Input
                search_input = QLineEdit()
                search_input.setPlaceholderText(f"{filter_type}...")
                search_input.textChanged.connect(
                    lambda text, fn=field_name: self._on_search_text_changed(fn, text)
                )
                self.search_widgets[field_name] = search_input
                search_grid.addWidget(search_input)
        
        search_layout.addLayout(search_grid)
        layout.addWidget(search_frame)
    
    def _create_filter_area(self, layout):
        """Erstellt den Filter-Bereich für Dropdown und DateRange"""
        filter_frame = QFrame()
        filter_frame.setFrameShape(QFrame.StyledPanel)
        filter_layout = QVBoxLayout(filter_frame)
        filter_layout.setContentsMargins(5, 5, 5, 5)
        
        # Title
        filter_title = QLabel("🎛️ Filter")
        filter_title.setFont(QFont("Arial", 10, QFont.Bold))
        filter_layout.addWidget(filter_title)
        
        # Filter Buttons Grid
        filter_grid = QHBoxLayout()
        
        # Erstelle Filter-Buttons für Dropdown und DateRange Felder
        for field_config in self.data_manager.get_fields_config():
            field_name = field_config.get("feld")
            field_type = field_config.get("type", "string")
            ui_config = field_config.get("ui", {})
            filter_type = ui_config.get("filterType")
            
            if filter_type in ["dropdown", "dateRange"]:
                # Filter Button
                filter_btn = QPushButton(f"🎛️ {field_config.get('bezeichnung', field_name)}")
                filter_btn.clicked.connect(
                    lambda checked, fn=field_name: self._open_filter_dialog(fn)
                )
                self.filter_buttons[field_name] = filter_btn
                filter_grid.addWidget(filter_btn)
        
        filter_layout.addLayout(filter_grid)
        layout.addWidget(filter_frame)
    
    def _create_table(self, layout):
        """Erstellt die Haupttabelle"""
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setSortingEnabled(True)
        
        # Header-Klick für Sortierung
        self.table.horizontalHeader().sectionClicked.connect(self._on_header_clicked)
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        
        layout.addWidget(self.table, 1)  # Stretch
    
    def _create_status_bar(self, layout):
        """Erstellt die Status-Leiste"""
        self.status_label = QLabel("Bereit")
        self.status_label.setStyleSheet("padding: 5px; background-color: #f0f0f0;")
        layout.addWidget(self.status_label)
    
    def _initial_load(self):
        """Lädt Initial-Basisdaten und Setup (keine Filter, alle Spalten)"""
        try:
            self._setup_table_columns()
            self._populate_table()
            logger.info("✅ Initial-Load (Basis) abgeschlossen")
        except Exception as e:
            logger.error(f"❌ Fehler beim Initial-Load (Basis): {e}")
    
    def _setup_table_columns(self):
        """Richtet die Tabellen-Spalten für ALLE Basisspalten ein, Header zweizeilig (Anzeigename, interner Name)"""
        try:
            # Hole alle Spaltennamen direkt aus der Basistabelle (keine Filterung)
            if hasattr(self.data_manager, 'original_data') and self.data_manager.original_data:
                all_columns = list(self.data_manager.original_data[0].keys())
            else:
                all_columns = []

            self.table.setColumnCount(len(all_columns))
            headers = []
            for col in all_columns:
                # Anzeigename aus Feldkonfiguration, sonst leer
                field_config = self.data_manager.get_field_config(col.replace('_show',''))
                display = field_config.get('bezeichnung', '') if field_config else ''
                # Zweizeilig: Anzeigename (fett), darunter interner Name
                if display and display != col:
                    header = f"{display}\n[{col}]"
                else:
                    header = col
                headers.append(header)
            self.table.setHorizontalHeaderLabels(headers)
            self.visible_columns = all_columns
            self.table.horizontalHeader().setStretchLastSection(True)
            logger.info(f"✅ Tabellen-Spalten (Basis) eingerichtet: {len(all_columns)} Spalten")
        except Exception as e:
            logger.error(f"❌ Fehler beim Einrichten der Basis-Tabellen-Spalten: {e}")
    
    def _populate_table(self):
        """Befüllt die Tabelle mit ALLEN Basisdaten (keine Filterung)"""
        try:
            if hasattr(self.data_manager, 'original_data'):
                all_data = self.data_manager.original_data
            else:
                all_data = []
            visible_columns = self.visible_columns
            self.table.setRowCount(0)
            self.table.setSortingEnabled(False)
            if self.table.columnCount() != len(visible_columns):
                self._setup_table_columns()
            for row_idx, record in enumerate(all_data):
                self.table.insertRow(row_idx)
                for col_idx, column_name in enumerate(visible_columns):
                    value = record.get(column_name, "")
                    display_value = str(value) if value is not None else ""
                    item = QTableWidgetItem(display_value)
                    if col_idx == 0:
                        item.setData(Qt.UserRole, record.get("_guid"))
                    self.table.setItem(row_idx, col_idx, item)
            self.table.setSortingEnabled(True)
            logger.debug(f"✅ Tabelle (Basis) befüllt: {len(all_data)} Zeilen, {len(visible_columns)} Spalten")
        except Exception as e:
            logger.error(f"❌ Fehler beim Befüllen der Basistabelle: {e}")
    
    def _update_ui_from_filter_manager(self):
        """Aktualisiert komplette UI basierend auf Filter-Manager"""
        try:
            # Filter-Buttons aktualisieren
            self._update_filter_button_states()
            
            # Tabelle befüllen
            self._populate_table()
            
            # Status aktualisieren
            self._update_status()
            
        except Exception as e:
            logger.error(f"❌ Fehler beim UI-Update: {e}")
    
    def _update_filter_button_states(self):
        """Aktualisiert die Zustände der Filter-Buttons"""
        for field_name, button in self.filter_buttons.items():
            is_active = self.filter_manager.is_filter_active(field_name)
            
            if is_active:
                button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
            else:
                button.setStyleSheet("")
    
    def _update_status(self):
        """Aktualisiert die Status-Leiste"""
        try:
            original_count = len(self.filter_manager.original_data)
            filtered_count = len(self.filter_manager.get_filtered_data())
            active_filters = self.filter_manager.get_active_filter_count()
            
            status = f"📊 {filtered_count} von {original_count} Datensätzen"
            if active_filters > 0:
                status += f" | 🎛️ {active_filters} Filter aktiv"
            
            self.status_label.setText(status)
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Status-Update: {e}")
    
    # Event Handlers
    
    def _on_search_text_changed(self, field_name: str, text: str):
        """Behandelt Textsuche-Änderungen"""
        # Timer für verzögerte Suche
        self.search_timer.stop()
        self._pending_search = (field_name, text)
        self.search_timer.start(300)  # 300ms Verzögerung
    
    def _on_search_timer(self):
        """Führt verzögerte Textsuche aus"""
        if hasattr(self, '_pending_search'):
            field_name, text = self._pending_search
            
            # Filter setzen
            self.filter_manager.set_text_filter(field_name, text)
            
            # Filter anwenden und UI aktualisieren
            self.filter_manager.apply_all_filters()
            self._update_ui_from_filter_manager()
    
    def _on_header_clicked(self, logical_index: int):
        """Behandelt Spalten-Header-Klicks für Sortierung"""
        try:
            if logical_index >= len(self.visible_columns):
                return
            
            column_name = self.visible_columns[logical_index]
            
            # Sortierreihenfolge bestimmen
            if self.current_sort_column == column_name:
                # Toggle sort order
                self.current_sort_order = (Qt.DescendingOrder 
                                         if self.current_sort_order == Qt.AscendingOrder 
                                         else Qt.AscendingOrder)
            else:
                # Neue Spalte: Aufsteigend starten
                self.current_sort_column = column_name
                self.current_sort_order = Qt.AscendingOrder
            
            # Sortierung anwenden
            self._sort_filtered_data()
            
            # Tabelle neu befüllen
            self._populate_table()
            
            logger.info(f"🔄 Sortiert nach {column_name} ({'aufsteigend' if self.current_sort_order == Qt.AscendingOrder else 'absteigend'})")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Spalten-Sortierung: {e}")
    
    def _sort_filtered_data(self):
        """Sortiert die gefilterten Daten"""
        if not self.current_sort_column:
            return
        
        try:
            reverse = (self.current_sort_order == Qt.DescendingOrder)
            
            def sort_key(record):
                value = record.get(self.current_sort_column)
                
                # Spezialbehandlung für verschiedene Spaltentypen
                if "_Jahr" in self.current_sort_column or "_Monat" in self.current_sort_column or "_Tag" in self.current_sort_column:
                    # Jahr/Monat/Tag: Numerisch sortieren
                    return int(value) if value is not None else 0
                elif "_Alter" in self.current_sort_column:
                    # Alter: Numerisch sortieren
                    return int(value) if value is not None else 0
                elif self.current_sort_column.endswith("_original") and "date" in str(value):
                    # Original-Datumsspalten: Als Float sortieren
                    try:
                        return float(value) if value else 0
                    except (ValueError, TypeError):
                        return 0
                else:
                    # Standard: String-Sortierung
                    return str(value).lower() if value is not None else ""
            
            # Daten sortieren
            self.filter_manager.filtered_data.sort(key=sort_key, reverse=reverse)
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Sortieren: {e}")
    
    def _on_selection_changed(self):
        """Behandelt Zeilen-Auswahl-Änderungen"""
        try:
            current_row = self.table.currentRow()
            if current_row >= 0:
                # GUID aus erster Spalte holen
                guid_item = self.table.item(current_row, 0)
                if guid_item:
                    guid = guid_item.data(Qt.UserRole)
                    
                    # Vollständigen Datensatz finden
                    filtered_data = self.filter_manager.get_filtered_data()
                    if current_row < len(filtered_data):
                        selected_record = filtered_data[current_row]
                        self.rowSelected.emit(selected_record)
                        
                        logger.debug(f"🔘 Zeile ausgewählt: {guid}")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Zeilen-Auswahl: {e}")
    
    def _open_filter_dialog(self, field_name: str):
        """Öffnet Filter-Dialog für ein Feld"""
        try:
            field_config = self.data_manager.get_field_config(field_name)
            filter_type = field_config.get("ui", {}).get("filterType")
            
            if filter_type == "dropdown":
                self._open_dropdown_filter_dialog(field_name)
            elif filter_type == "dateRange":
                self._open_date_range_filter_dialog(field_name)
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Öffnen des Filter-Dialogs für {field_name}: {e}")
    
    def _open_dropdown_filter_dialog(self, field_name: str):
        """Öffnet Dropdown-Filter-Dialog"""
        try:
            from pdvm_dropdown_filter_dialog_v3 import PdvmDropdownFilterDialogV3
            
            # Dropdown-Optionen holen
            options = self.data_manager.get_dropdown_options(field_name)
            
            # Aktueller Filter-Zustand
            filter_state = self.filter_manager.get_filter_state(field_name)
            
            # Dialog öffnen
            dialog = PdvmDropdownFilterDialogV3(
                field_name=field_name,
                options=options,
                current_state=filter_state,
                parent=self
            )
            
            if dialog.exec_() == QDialog.Accepted:
                # Filter-Einstellungen übernehmen
                selected_keys, show_empty = dialog.get_filter_settings()
                self.filter_manager.set_dropdown_filter(field_name, selected_keys, show_empty)
                
                # Filter anwenden
                self.filter_manager.apply_all_filters()
                self._update_ui_from_filter_manager()
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Dropdown-Filter-Dialog: {e}")
    
    def _open_date_range_filter_dialog(self, field_name: str):
        """Öffnet DateRange-Filter-Dialog"""
        try:
            from pdvm_date_range_filter_dialog_v3 import PdvmDateRangeFilterDialogV3
            
            # Aktueller Filter-Zustand
            filter_state = self.filter_manager.get_filter_state(field_name)
            
            # Dialog öffnen
            dialog = PdvmDateRangeFilterDialogV3(
                field_name=field_name,
                current_state=filter_state,
                parent=self
            )
            
            if dialog.exec_() == QDialog.Accepted:
                # Filter-Einstellungen übernehmen
                range_data = dialog.get_filter_settings()
                self.filter_manager.set_date_range_filter(field_name, range_data)
                
                # Filter anwenden
                self.filter_manager.apply_all_filters()
                self._update_ui_from_filter_manager()
                
        except Exception as e:
            logger.error(f"❌ Fehler beim DateRange-Filter-Dialog: {e}")
    
    # Public Methods
    
    def refresh(self):
        """Lädt Daten neu und behält Filter bei"""
        try:
            logger.info("🔄 View wird aktualisiert...")
            
            # Daten neu laden
            self.data_manager.refresh()
            self.filter_manager.load_original_data()
            
            # Filter beibehalten und anwenden
            self.filter_manager.apply_all_filters()
            self._update_ui_from_filter_manager()
            
            logger.info("✅ View aktualisiert")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktualisieren: {e}")
            QMessageBox.warning(self, "Fehler", f"Fehler beim Aktualisieren: {e}")
    
    def _clear_all_filters(self):
        """Löscht alle Filter"""
        try:
            # Filter löschen
            self.filter_manager.clear_all_filters()
            
            # Search-Widgets leeren
            for search_widget in self.search_widgets.values():
                search_widget.clear()
            
            # Filter anwenden (= alle Daten anzeigen)
            self.filter_manager.apply_all_filters()
            self._update_ui_from_filter_manager()
            
            logger.info("✅ Alle Filter gelöscht")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Löschen der Filter: {e}")
    
    def _save_user_settings(self):
        """Speichert Benutzer-Einstellungen"""
        try:
            self.filter_manager.save_filter_settings()
            QMessageBox.information(self, "Gespeichert", "Einstellungen wurden gespeichert.")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern der Einstellungen: {e}")
            QMessageBox.warning(self, "Fehler", f"Fehler beim Speichern: {e}")
    
    def _export_data(self):
        """Exportiert die aktuell angezeigten Daten"""
        try:
            # TODO: Export-Funktionalität implementieren
            QMessageBox.information(self, "Export", "Export-Funktionalität folgt in der nächsten Version.")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Export: {e}")
    
    def get_selected_record(self) -> Dict[str, Any]:
        """Gibt den aktuell ausgewählten Datensatz zurück"""
        try:
            current_row = self.table.currentRow()
            if current_row >= 0:
                filtered_data = self.filter_manager.get_filtered_data()
                if current_row < len(filtered_data):
                    return filtered_data[current_row]
            return {}
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Abrufen des ausgewählten Datensatzes: {e}")
            return {}
