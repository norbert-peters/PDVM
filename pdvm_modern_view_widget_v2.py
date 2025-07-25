# pdvm_modern_view_widget_v2.py
"""
Moderne View-Widget V2 mit separatem Filter-Manager
Klare Trennung: UI ↔ Filter-Manager ↔ Data-Manager
"""

import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, 
    QLineEdit, QHeaderView, QPushButton, QLabel, QFrame, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont

from pdvm_filter_manager import PdvmFilterManager, PdvmDropdownFilterWidget, PdvmDateRangeFilterWidget

logger = logging.getLogger(__name__)

class PdvmModernViewWidgetV2(QWidget):
    """
    Moderne View-Widget V2 mit neuer Filter-Architektur
    
    Architektur:
    - Original-Daten nur bei refresh() neu geladen
    - Filter-Manager verwaltet alle Filter-States
    - UI zeigt nur gefilterte Daten an
    - Klare Trennung aller Komponenten
    """
    
    # Signals
    rowSelected = pyqtSignal(dict)
    dataChanged = pyqtSignal()
    
    def __init__(self, view_guid, user_guid=None, parent=None):
        super().__init__(parent)
        
        self.view_guid = view_guid
        self.user_guid = user_guid
        
        # Manager-Pattern
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
        """Initialisiert Data- und Filter-Manager"""
        try:
            from pdvm_view_data_manager import PdvmViewDataManager
            
            # Data-Manager
            self.data_manager = PdvmViewDataManager(
                view_guid=self.view_guid,
                user_guid=self.user_guid
            )
            
            # Filter-Manager
            self.filter_manager = PdvmFilterManager(self.data_manager)
            
            logger.info(f"✅ Manager initialisiert: {self.data_manager.get_table_info()}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Initialisieren der Manager: {e}")
            raise
    
    def _setup_ui(self):
        """Erstellt die UI-Struktur"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Toolbar
        self._create_toolbar(layout)
        
        # Search-Bereich
        self._create_search_area(layout)
        
        # Tabelle
        self._create_table(layout)
        
        # Status-Bereich
        self._create_status_bar(layout)
    
    def _create_toolbar(self, layout):
        """Erstellt die Toolbar"""
        toolbar = QFrame()
        toolbar.setStyleSheet("QFrame { background-color: #f8f9fa; border-bottom: 1px solid #dee2e6; }")
        toolbar_layout = QHBoxLayout(toolbar)
        
        # Titel
        title_label = QLabel("📊 Moderne Datenansicht V2")
        title_label.setFont(QFont("Arial", 12, QFont.Bold))
        toolbar_layout.addWidget(title_label)
        
        toolbar_layout.addStretch()
        
        # Aktualisieren Button
        refresh_btn = QPushButton("🔄 Aktualisieren")
        refresh_btn.setToolTip("Daten neu laden und Filter beibehalten")
        refresh_btn.clicked.connect(self.refresh)
        toolbar_layout.addWidget(refresh_btn)
        
        # Filter Reset Button
        reset_btn = QPushButton("🔄 Filter Reset")
        reset_btn.setToolTip("Alle Filter zurücksetzen")
        reset_btn.clicked.connect(self._reset_all_filters)
        toolbar_layout.addWidget(reset_btn)
        
        layout.addWidget(toolbar)
    
    def _create_search_area(self, layout):
        """Erstellt den Search-Bereich"""
        search_frame = QFrame()
        search_frame.setStyleSheet("QFrame { background-color: #f1f3f4; border-bottom: 1px solid #dadce0; }")
        search_layout = QHBoxLayout(search_frame)
        
        # Search-Widgets für jedes Feld erstellen
        field_names = self.data_manager.get_field_names()
        
        for field_name in field_names:
            field_config = self.data_manager.get_field_config(field_name)
            if not field_config:
                continue
            
            # Prüfe ob Feld suchbar ist
            if not field_config.get("ui", {}).get("search", True):
                continue
                
            self._create_search_widget(search_layout, field_name, field_config)
        
        layout.addWidget(search_frame)
    
    def _create_search_widget(self, layout, field_name, field_config):
        """Erstellt ein Search-Widget für ein Feld"""
        field_label = field_config.get("name", field_name)
        filter_type = field_config.get("ui", {}).get("filterType", "contains")
        
        # Spalten-Container
        col_widget = QWidget()
        col_layout = QVBoxLayout(col_widget)
        col_layout.setContentsMargins(2, 2, 2, 2)
        
        # Label
        label = QLabel(field_label)
        label.setFont(QFont("Arial", 8))
        label.setStyleSheet("color: #5f6368; margin-bottom: 2px;")
        col_layout.addWidget(label)
        
        if filter_type == "dropdown":
            # Dropdown-Filter Button
            filter_btn = QPushButton("🔽 (Alle)")
            filter_btn.setStyleSheet("QPushButton { text-align: left; padding: 4px; font-size: 10px; }")
            filter_btn.setMinimumWidth(80)
            filter_btn.clicked.connect(lambda: self._open_dropdown_filter(field_name))
            
            col_layout.addWidget(filter_btn)
            self.filter_buttons[field_name] = filter_btn
            
        elif filter_type == "dateRange":
            # DateRange-Filter Button
            filter_btn = QPushButton("📅 (Alle)")
            filter_btn.setStyleSheet("QPushButton { text-align: left; padding: 4px; font-size: 10px; }")
            filter_btn.setMinimumWidth(80)
            filter_btn.clicked.connect(lambda: self._open_date_range_filter(field_name))
            
            col_layout.addWidget(filter_btn)
            self.filter_buttons[field_name] = filter_btn
            
        else:
            # Text-Search Widget mit erweiterten Funktionen
            search_container = QWidget()
            search_container_layout = QHBoxLayout(search_container)
            search_container_layout.setContentsMargins(0, 0, 0, 0)
            search_container_layout.setSpacing(2)
            
            # Search-Input mit X-Button (einfacher Ansatz)
            search_edit = QLineEdit()
            search_edit.setPlaceholderText("Suchen...")
            search_edit.setMinimumHeight(24)  # Mindesthöhe für bessere Lesbarkeit
            search_edit.setStyleSheet("""
                QLineEdit { 
                    padding: 4px; 
                    font-size: 12px; 
                    border: 1px solid #ccc; 
                    min-height: 20px;
                }
            """)
            search_edit.textChanged.connect(lambda text, fn=field_name: self._on_text_search_changed(fn, text))
            
            # X-Button zum Löschen (separater Button neben Input)
            clear_btn = QPushButton("✕")
            clear_btn.setFixedSize(24, 24)  # Größer für bessere Bedienung
            clear_btn.setStyleSheet("""
                QPushButton {
                    border: 1px solid #ccc;
                    background-color: #f9f9f9;
                    color: #666;
                    font-size: 10px;
                    font-weight: bold;
                    border-radius: 3px;
                }
                QPushButton:hover {
                    background-color: #f0f0f0;
                    border-color: #999;
                }
                QPushButton:pressed {
                    background-color: #e0e0e0;
                }
            """)
            clear_btn.setToolTip("Filter-Text löschen")
            clear_btn.clicked.connect(lambda: self._clear_text_search(field_name))
            clear_btn.setVisible(False)  # Zunächst versteckt
            
            # Toggle für "Leere ausschließen"
            empty_toggle = QPushButton("∅")
            empty_toggle.setFixedSize(20, 20)
            empty_toggle.setCheckable(True)
            
            # ORIGINAL STYLESHEET DEFINIEREN UND SPEICHERN
            original_empty_style = """
                QPushButton {
                    border: 1px solid #ccc;
                    background-color: #fff;
                    color: #666;
                    font-size: 10px;
                    font-weight: bold;
                    border-radius: 3px;
                }
                QPushButton:checked {
                    background-color: #4CAF50;
                    color: white;
                    border-color: #4CAF50;
                }
                QPushButton:hover {
                    border-color: #999;
                }
            """
            empty_toggle.setStyleSheet(original_empty_style)
            
            # STYLESHEET FÜR RESET SPEICHERN
            empty_toggle._original_stylesheet = original_empty_style  # Custom property für Reset
            
            empty_toggle.setToolTip("Leere Werte ausschließen")
            empty_toggle.clicked.connect(lambda checked, fn=field_name: self._on_empty_filter_toggled(fn, checked))
            
            # Layout zusammenbauen
            search_container_layout.addWidget(search_edit)
            search_container_layout.addWidget(clear_btn)
            search_container_layout.addWidget(empty_toggle)
            
            col_layout.addWidget(search_container)
            
            # Widgets speichern
            self.search_widgets[field_name] = search_edit
            
            # Neue Tracking-Dicts für erweiterte Funktionen
            if not hasattr(self, 'search_clear_buttons'):
                self.search_clear_buttons = {}
            if not hasattr(self, 'empty_filter_toggles'):
                self.empty_filter_toggles = {}
                
            self.search_clear_buttons[field_name] = clear_btn
            self.empty_filter_toggles[field_name] = empty_toggle
            
            # Text-Änderung für X-Button-Sichtbarkeit
            search_edit.textChanged.connect(lambda text: self._update_clear_button_visibility(field_name, text))
        
        layout.addWidget(col_widget)
    
    def _create_table(self, layout):
        """Erstellt die Haupttabelle"""
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        
        # Header-Styling
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.sectionClicked.connect(self._on_header_clicked)
        
        # Row selection
        self.table.itemSelectionChanged.connect(self._on_row_selected)
        
        layout.addWidget(self.table)
    
    def _create_status_bar(self, layout):
        """Erstellt die Status-Leiste"""
        status_frame = QFrame()
        status_frame.setStyleSheet("QFrame { background-color: #f0f0f0; border-top: 1px solid #ccc; }")
        status_layout = QHBoxLayout(status_frame)
        
        self.status_label = QLabel("Bereit")
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        self.row_count_label = QLabel("0 Datensätze")
        status_layout.addWidget(self.row_count_label)
        
        layout.addWidget(status_frame)
    
    def _initial_load(self):
        """Initialer Datenload"""
        try:
            # Original-Daten über Filter-Manager laden
            self.filter_manager.load_original_data()
            
            # Tabelle konfigurieren
            self._setup_table_columns()
            
            # UI aktualisieren
            self._update_ui_from_filter_manager()
            
            logger.info("✅ Initialer Datenload abgeschlossen")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim initialen Datenload: {e}")
    
    def _setup_table_columns(self):
        """Konfiguriert die Tabellenspalten"""
        field_names = self.data_manager.get_field_names()
        
        self.table.setColumnCount(len(field_names))
        headers = []
        
        for field_name in field_names:
            field_config = self.data_manager.get_field_config(field_name)
            if field_config:
                headers.append(field_config["name"])
            else:
                headers.append(field_name)
        
        self.table.setHorizontalHeaderLabels(headers)
        logger.debug(f"🔧 Tabellenspalten konfiguriert: {headers}")
    
    def _on_text_search_changed(self, field_name, text):
        """Callback für Text-Search Änderungen"""
        # Text-Filter im Manager setzen
        self.filter_manager.set_text_filter(field_name, text)
        
        # Search-Timer starten (Debouncing)
        self.search_timer.stop()
        self.search_timer.start(300)  # 300ms Delay
    
    def _clear_text_search(self, field_name):
        """Löscht den Text im Search-Feld"""
        if field_name in self.search_widgets:
            search_edit = self.search_widgets[field_name]
            search_edit.clear()  # Löst automatisch textChanged Signal aus
            search_edit.setFocus()
            logger.debug(f"🗑️ Text-Filter für {field_name} gelöscht")
    
    def _update_clear_button_visibility(self, field_name, text):
        """Zeigt/versteckt X-Button basierend auf Text-Inhalt"""
        if field_name in self.search_clear_buttons:
            clear_btn = self.search_clear_buttons[field_name]
            clear_btn.setVisible(bool(text.strip()))
    
    def _on_empty_filter_toggled(self, field_name, checked):
        """Callback für Empty-Filter Toggle"""
        # Leere-Werte-Filter im Manager setzen
        self.filter_manager.set_empty_filter(field_name, exclude_empty=checked)
        
        # UI sofort aktualisieren
        self._apply_filters_and_update_ui()
        
        logger.debug(f"🔘 Empty-Filter für {field_name}: {'Leere ausschließen' if checked else 'Alle anzeigen'}")
    
    def _reset_all_filters(self):
        """Setzt alle Filter zurück - ERWEITERT für neue Funktionen mit DEBUG"""
        logger.warning("🚨 === RESET FILTER METHODE 1 (ERWEITERT) AUFGERUFEN ===")
        logger.info("🔄 === RESET FILTER GESTARTET ===")
        
        # Filter-Manager zurücksetzen
        self.filter_manager.reset_all_filters()
        logger.debug("✅ Filter-Manager zurückgesetzt")
        
        # Search-Felder leeren
        for field_name, search_edit in self.search_widgets.items():
            search_edit.clear()
        logger.debug("✅ Search-Felder geleert")
        
        # PRÜFUNG: Sind ∅-Buttons vorhanden?
        if hasattr(self, 'empty_filter_toggles'):
            logger.info(f"✅ empty_filter_toggles gefunden: {list(self.empty_filter_toggles.keys())}")
        else:
            logger.error("❌ KEIN empty_filter_toggles Attribut gefunden!")
            logger.error("❌ Das ist der Grund, warum die ∅-Buttons nicht zurückgesetzt werden!")
        
        # Empty-Filter-Toggles - STATUS-BASIERTES RESET mit VOLLSTÄNDIGEM DEBUG
        if hasattr(self, 'empty_filter_toggles'):
            logger.info(f"🔍 DEBUG: Gefundene Empty-Filter-Toggles: {len(self.empty_filter_toggles)}")
            
            for field_name, toggle in self.empty_filter_toggles.items():
                logger.info(f"\n🔍 === DEBUG TOGGLE: {field_name} ===")
                
                # STATUS VOR ÄNDERUNG
                is_currently_checked = toggle.isChecked()
                current_style = toggle.styleSheet()
                current_text = toggle.text()
                
                logger.info(f"🔍 VOR Reset:")
                logger.info(f"   - isChecked(): {is_currently_checked}")
                logger.info(f"   - Text: '{current_text}'")
                logger.info(f"   - StyleSheet: '{current_style[:100]}...' (gekürzt)")
                logger.info(f"   - Widget-Typ: {type(toggle).__name__}")
                logger.info(f"   - Widget-Objekt-ID: {id(toggle)}")
                
                if is_currently_checked:
                    logger.warning(f"⚠️ Toggle {field_name} ist AKTIVIERT - Beginne Reset...")
                    
                    # Signale blockieren für sauberes Reset
                    toggle.blockSignals(True)
                    logger.debug("🔒 Signale blockiert")
                    
                    # EXPLIZIT auf False setzen
                    toggle.setChecked(False)
                    logger.debug("🎯 setChecked(False) ausgeführt")
                    
                    # STATUS NACH setChecked
                    new_checked_state = toggle.isChecked()
                    logger.info(f"🔍 Nach setChecked(False): isChecked() = {new_checked_state}")
                    
                    # KORRIGIERT: Gespeichertes ursprüngliches StyleSheet wiederherstellen
                    if hasattr(toggle, '_original_stylesheet'):
                        toggle.setStyleSheet(toggle._original_stylesheet)
                        logger.debug("🎨 Gespeichertes ursprüngliches StyleSheet wiederhergestellt")
                    else:
                        # Fallback falls das gespeicherte Stylesheet nicht vorhanden ist
                        fallback_style = """
                            QPushButton {
                                border: 1px solid #ccc;
                                background-color: #fff;
                                color: #666;
                                font-size: 10px;
                                font-weight: bold;
                                border-radius: 3px;
                            }
                            QPushButton:checked {
                                background-color: #4CAF50;
                                color: white;
                                border-color: #4CAF50;
                            }
                            QPushButton:hover {
                                border-color: #999;
                            }
                        """
                        toggle.setStyleSheet(fallback_style)
                        logger.debug("🎨 Fallback StyleSheet angewendet")
                    
                    # ZUSÄTZLICH: Force Update durch Widget-State Reset
                    # Dies zwingt PyQt5 den visuellen Zustand komplett neu zu evaluieren
                    toggle.setEnabled(False)
                    toggle.setEnabled(True)
                    logger.debug("🔧 Widget-State-Reset durchgeführt")
                    
                    # Signale wieder aktivieren
                    toggle.blockSignals(False)
                    logger.debug("🔓 Signale wieder aktiviert")
                    
                    # Force Update der Darstellung
                    toggle.update()
                    toggle.repaint()
                    logger.debug("🔄 update() und repaint() ausgeführt")
                    
                    # FINALER STATUS NACH ALLEN ÄNDERUNGEN
                    final_checked_state = toggle.isChecked()
                    final_style = toggle.styleSheet()
                    final_text = toggle.text()
                    
                    logger.info(f"🔍 NACH Reset:")
                    logger.info(f"   - isChecked(): {final_checked_state}")
                    logger.info(f"   - Text: '{final_text}'")
                    logger.info(f"   - StyleSheet: '{final_style}'")
                    
                    if final_checked_state == False:
                        logger.info(f"✅ Toggle {field_name} - STATUS erfolgreich auf False gesetzt")
                    else:
                        logger.error(f"❌ Toggle {field_name} - STATUS IMMER NOCH True! Problem erkannt!")
                        
                else:
                    logger.info(f"ℹ️ Toggle {field_name} war bereits deaktiviert (isChecked={is_currently_checked})")
                
                logger.info(f"🔍 === ENDE DEBUG TOGGLE: {field_name} ===\n")
                
        else:
            logger.warning("⚠️ Keine empty_filter_toggles gefunden!")
        
        # X-Buttons verstecken
        if hasattr(self, 'search_clear_buttons'):
            for field_name, clear_button in self.search_clear_buttons.items():
                clear_button.hide()
        
        # Gefilterte Daten auf Original zurücksetzen
        self._apply_filters_and_update_ui()
        
        logger.info("🔄 === RESET FILTER BEENDET ===")
        logger.info(f"📊 Status nach Reset: {len(self.filter_manager.get_filtered_data())} von {len(self.data_manager.get_data())} Datensätzen angezeigt")
    
    def _on_search_timer(self):
        """Timer-Callback für verzögerte Suche"""
        self._apply_filters_and_update_ui()
    
    def _open_dropdown_filter(self, field_name):
        """Öffnet das Dropdown-Filter-Widget"""
        dialog = PdvmDropdownFilterWidget(field_name, self.filter_manager, self)
        dialog.filterApplied.connect(self._on_dropdown_filter_applied)
        dialog.exec_()
    
    def _open_date_range_filter(self, field_name):
        """Öffnet das DateRange-Filter-Widget"""
        dialog = PdvmDateRangeFilterWidget(field_name, self.filter_manager, self)
        dialog.filterApplied.connect(self._on_date_range_filter_applied)
        dialog.exec_()
    
    def _on_date_range_filter_applied(self, field_name, range_data):
        """Callback für angewendete DateRange-Filter"""
        # Filter im Manager setzen
        self.filter_manager.set_date_range_filter(field_name, range_data)
        
        # Aktualisiere UI und Daten
        self._apply_filters_and_update_ui()
        
        logger.info(f"🗓️ DateRange-Filter angewendet für {field_name}")
    
    def _on_dropdown_filter_applied(self, field_name, selected_keys, show_empty):
        """Callback für angewendete Dropdown-Filter"""
        # Filter im Manager setzen
        self.filter_manager.set_dropdown_filter(field_name, selected_keys, show_empty)
        
        # UI sofort aktualisieren
        self._apply_filters_and_update_ui()
    
    def _apply_filters_and_update_ui(self):
        """Wendet alle Filter an und aktualisiert die UI"""
        # Filter anwenden
        self.filter_manager.apply_all_filters()
        
        # UI aktualisieren
        self._update_ui_from_filter_manager()
    
    def _update_ui_from_filter_manager(self):
        """Aktualisiert komplette UI basierend auf Filter-Manager"""
        # Filter-Buttons aktualisieren (Dropdown und DateRange)
        self._update_dropdown_filter_buttons()
        
        # Sortierung anwenden
        self._sort_filtered_data()
        
        # Tabelle befüllen
        self._populate_table()
        
        # Status aktualisieren
        self._update_status()
    
    def _update_dropdown_filter_buttons(self):
        """Aktualisiert alle Filter-Button-Texte (Dropdown und DateRange)"""
        for field_name, button in self.filter_buttons.items():
            filter_state = self.filter_manager.get_filter_state(field_name)
            
            if filter_state.get("type") == "dropdown":
                self._update_dropdown_button_text(field_name, button, filter_state)
            elif filter_state.get("type") == "dateRange":
                self._update_date_range_button_text(field_name, button, filter_state)
    
    def _update_dropdown_button_text(self, field_name, button, filter_state):
        """Aktualisiert Dropdown-Button-Text"""
        selected_count = len(filter_state.get("selected_keys", set()))
        total_count = len(filter_state.get("all_keys", set()))
        show_empty = filter_state.get("show_empty", True)
        
        if selected_count == 0 and not show_empty:
            button.setText("🔴 Keine")
            button.setStyleSheet("QPushButton { text-align: left; padding: 4px; color: red; font-weight: bold; }")
        elif selected_count == total_count and show_empty:
            button.setText("🔽 (Alle)")
            button.setStyleSheet("QPushButton { text-align: left; padding: 4px; color: black; }")
        else:
            button.setText(f"🔽 ({selected_count})")
            button.setStyleSheet("QPushButton { text-align: left; padding: 4px; color: blue; font-weight: bold; }")
    
    def _update_date_range_button_text(self, field_name, button, filter_state):
        """Aktualisiert DateRange-Button-Text"""
        # Prüfe ob ein Datums-Filter aktiv ist
        has_filter = any([
            filter_state.get("ab_jahr"), filter_state.get("ab_monat"), filter_state.get("ab_tag"),
            filter_state.get("bis_jahr"), filter_state.get("bis_monat"), filter_state.get("bis_tag")
        ])
        
        if not has_filter:
            button.setText("📅 (Alle)")
            button.setStyleSheet("QPushButton { text-align: left; padding: 4px; color: black; }")
        else:
            # Kurze Beschreibung des aktiven Filters
            def format_date_part(jahr, monat, tag):
                parts = []
                if jahr: parts.append(str(jahr))
                if monat: parts.append(f"{monat:02d}")
                if tag: parts.append(f"{tag:02d}")
                return "-".join(parts) if parts else "***"
            
            ab_str = format_date_part(
                filter_state.get("ab_jahr"), 
                filter_state.get("ab_monat"), 
                filter_state.get("ab_tag")
            )
            
            bis_str = format_date_part(
                filter_state.get("bis_jahr"), 
                filter_state.get("bis_monat"), 
                filter_state.get("bis_tag")
            )
            
            if ab_str == bis_str and ab_str != "***":
                button.setText(f"� {ab_str}")
            elif ab_str != "***" or bis_str != "***":
                button.setText(f"📅 {ab_str}-{bis_str}")
            else:
                button.setText("📅 (Filter)")
                
            button.setStyleSheet("QPushButton { text-align: left; padding: 4px; color: blue; font-weight: bold; }")
    
    def _sort_filtered_data(self):
        """Sortiert die gefilterten Daten nach der Original-Spalte (erweitert für YMD/Alter-Spalten)"""
        if self.current_sort_column is None:
            return
        
        # Sortierung über Data-Manager
        field_name = self.data_manager.get_field_name_by_index(self.current_sort_column)
        if not field_name:
            return
        
        filtered_data = self.filter_manager.get_filtered_data()
        
        # Prüfe den Spaltentyp
        field_config = self.data_manager.get_field_config(field_name)
        is_date_field = field_config and field_config.get("type") == "date"
        is_ymd_field = "_Jahr" in field_name or "_Monat" in field_name or "_Tag" in field_name
        is_alter_field = "_Alter" in field_name
        
        try:
            def sort_key(record):
                value = record.get(field_name)
                
                # Für Datumsspalten: Original-Wert als Float für numerische Sortierung
                if is_date_field:
                    try:
                        return float(value) if value else 0
                    except (ValueError, TypeError):
                        return 0
                
                # Für YMD-Spalten (Jahr/Monat/Tag): Numerisch sortieren
                elif is_ymd_field or is_alter_field:
                    try:
                        return int(value) if value is not None else 0
                    except (ValueError, TypeError):
                        return 0
                
                # Für andere Spalten: String-Sortierung
                else:
                    if value is None:
                        return ''
                    return str(value).lower()
            
            filtered_data.sort(
                key=sort_key,
                reverse=self.current_sort_order == Qt.DescendingOrder
            )
            
            # Sortierte Daten zurück in Filter-Manager
            self.filter_manager.filtered_data = filtered_data
            
            sort_type = "Original-Datum" if is_date_field else ("Numerisch" if (is_ymd_field or is_alter_field) else "Text")
            logger.debug(f"📊 Sortierung nach {sort_type}-Spalte: {field_name}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Sortieren: {e}")
    
    def _populate_table(self):
        """Füllt die Tabelle mit gefilterten Daten - WICHTIG: Display-Werte verwenden"""
        filtered_data = self.filter_manager.get_filtered_data()
        field_names = self.data_manager.get_field_names()
        
        self.table.setRowCount(len(filtered_data))
        
        for row_idx, record in enumerate(filtered_data):
            for col_idx, field_name in enumerate(field_names):
                # Raw-Wert aus Daten holen
                raw_value = record.get(field_name, "")
                
                # Display-Wert über Data-Manager konvertieren
                display_value = self.data_manager.get_display_value(field_name, raw_value)
                
                item = QTableWidgetItem(display_value)
                item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                
                # Raw-Wert als userData speichern für Debugging/Sorting
                item.setData(Qt.UserRole, raw_value)
                
                self.table.setItem(row_idx, col_idx, item)
        
        logger.debug(f"📊 Tabelle befüllt: {len(filtered_data)} Zeilen mit Display-Werten")
    
    def _update_status(self):
        """Aktualisiert die Status-Anzeige"""
        filtered_count = len(self.filter_manager.get_filtered_data())
        total_count = len(self.filter_manager.original_data)
        
        # Status-Text
        if self.filter_manager.is_any_filter_active():
            active_filters = self.filter_manager.get_active_filter_summary()
            filter_info = ", ".join(active_filters[:2])  # Nur erste 2 anzeigen
            if len(active_filters) > 2:
                filter_info += f" (+{len(active_filters) - 2} weitere)"
            self.status_label.setText(f"🔍 Filter aktiv: {filter_info}")
        else:
            self.status_label.setText("📊 Alle Daten angezeigt")
        
        # Anzahl
        self.row_count_label.setText(f"{filtered_count} von {total_count} Datensätzen")
    
    def _on_header_clicked(self, logical_index):
        """Header-Click für Sortierung"""
        if logical_index == self.current_sort_column:
            # Toggle sort order
            self.current_sort_order = (
                Qt.DescendingOrder if self.current_sort_order == Qt.AscendingOrder 
                else Qt.AscendingOrder
            )
        else:
            self.current_sort_column = logical_index
            self.current_sort_order = Qt.AscendingOrder
        
        # Sofort neu sortieren und anzeigen
        self._update_ui_from_filter_manager()
    
    def _on_row_selected(self):
        """Row-Selection Handler"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            filtered_data = self.filter_manager.get_filtered_data()
            if current_row < len(filtered_data):
                record = filtered_data[current_row]
                self.rowSelected.emit(record)
    
    def refresh(self):
        """
        Lädt Original-Daten neu und behält Filter bei
        WICHTIG: Das ist die zentrale Refresh-Funktion!
        """
        try:
            # Original-Daten neu laden
            self.filter_manager.load_original_data()
            
            # UI komplett aktualisieren
            self._update_ui_from_filter_manager()
            
            logger.info("🔄 Daten aktualisiert - Filter beibehalten")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktualisieren: {e}")
            QMessageBox.warning(self, "Fehler", f"Fehler beim Aktualisieren der Daten:\n{e}")
