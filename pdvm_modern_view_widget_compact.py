#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PdvmModernViewWidget - KOMPAKTE VERSION mit Filter-Panel
Umgestaltung nach User-Anforderungen:
- Kompakte Hauptansicht nur mit Tabelle
- Filter-Button öffnet separates Filter-Panel
- Spalten-Parameter über Menü zugänglich
- Expert-Modus Integration
"""

import logging
from typing import Optional, List, Dict, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QLabel, QPushButton, QLineEdit, QCheckBox, QScrollArea,
    QFrame, QSplitter, QMenu, QAction, QGroupBox, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor, QBrush

logger = logging.getLogger(__name__)

class PdvmModernViewWidget(QWidget):
    """
    Kompaktes View-Widget mit ausklappbarem Filter-Panel.
    Hauptbereich: nur Tabelle
    Filter-Panel: bei Bedarf links einblendbar
    Spalten-Parameter: über Menü zugänglich
    """
    
    # Signale
    settings_requested = pyqtSignal()
    
    def __init__(self, view_manager, view_guid, mode=None):
        super().__init__()
        self.view_manager = view_manager
        self.view_guid = view_guid
        self.mode = mode  # 'admin' für Expert-Mode Zugang
        self.current_table_data = []
        self.current_columns = []  # Für Sortierungs-Features
        self.expert_mode = False
        
        # Sortierungs-Persistenz Manager
        try:
            from pdvm_sorting_persistence_manager import PdvmSortingPersistenceManager
            
            self.sorting_manager = PdvmSortingPersistenceManager(self.view_manager, view_guid)
            logger.info("📊 Sortierungs-Persistenz Manager initialisiert")
        except Exception as e:
            logger.warning(f"⚠️ Sortierungs-Persistenz Manager nicht verfügbar: {e}")
            self.sorting_manager = None
        
        self.filter_shown = False
        self.init_ui()
        
        # Daten laden
        try:
            self.load_data()
            # Gespeicherte Sortierung nach dem Laden der Daten anwenden
            if self.sorting_manager:
                try:
                    QTimer.singleShot(100, self._apply_saved_sorting)
                except Exception as e:
                    logger.warning(f"⚠️ Fehler beim Anwenden der gespeicherten Sortierung: {e}")
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Daten: {e}")
            
    def init_ui(self):
        """Initialisiert die Benutzeroberfläche"""
        # Haupt-Layout
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Filter-Panel initialisieren (versteckt)
        self._setup_filter_panel()
        
        # Hauptbereich mit Tabelle
        self._setup_main_area()
        
        # Filter-Panel ist standardmäßig versteckt
        self.filter_panel.hide()
        
    def _setup_filter_panel(self):
        """Erstellt das Filter-Panel"""
        # Scroll-Area für das Filter-Panel
        self.filter_scroll = QScrollArea()
        self.filter_scroll.setFixedWidth(320)
        self.filter_scroll.setWidgetResizable(True)
        self.filter_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.filter_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Filter-Panel Container
        self.filter_panel = QFrame()
        self.filter_panel.setObjectName("FilterPanel")
        self.filter_panel.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.filter_panel.setLineWidth(1)
        
        filter_layout = QVBoxLayout(self.filter_panel)
        filter_layout.setContentsMargins(10, 10, 10, 10)
        filter_layout.setSpacing(10)
        
        # Header
        filter_header = QLabel("🔍 Filter")
        filter_header.setFont(QFont("Arial", 12, QFont.Bold))
        filter_header.setAlignment(Qt.AlignCenter)
        filter_layout.addWidget(filter_header)
        
        # Allgemeine Suche
        search_group = QGroupBox("Allgemeine Suche")
        search_layout = QVBoxLayout(search_group)
        
        self.search_filter = QLineEdit()
        self.search_filter.setPlaceholderText("🔍 Text in allen Spalten suchen...")
        self.search_filter.textChanged.connect(self._on_search_changed)
        search_layout.addWidget(self.search_filter)
        
        # Negativ-Filter Checkbox
        self.negative_filter_checkbox = QCheckBox("❌ Negativ-Filter (gefundene Zeilen ausschließen)")
        self.negative_filter_checkbox.toggled.connect(self._on_search_changed)
        search_layout.addWidget(self.negative_filter_checkbox)
        
        filter_layout.addWidget(search_group)
        
        # Placeholder für zukünftige Filter
        future_filters = QLabel("🔧 Spalten-Filter\n(folgen später)")
        future_filters.setAlignment(Qt.AlignCenter)
        future_filters.setStyleSheet("color: #666; font-style: italic;")
        filter_layout.addWidget(future_filters)
        
        # Spacer
        filter_layout.addStretch()
        
        # Schließen-Button
        close_button = QPushButton("Filter schließen")
        close_button.clicked.connect(self.hide_filter_panel)
        filter_layout.addWidget(close_button)
        
        # Scroll-Area konfigurieren
        self.filter_scroll.setWidget(self.filter_panel)
        
        # Styling
        self.setStyleSheet(self._get_stylesheet())
        
    def _setup_main_area(self):
        """Erstellt den Hauptbereich mit Tabelle"""
        # Hauptbereich Container
        main_container = QWidget()
        main_layout = QVBoxLayout(main_container)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Header-Bereich
        header_layout = QHBoxLayout()
        
        # Titel
        self.title_label = QLabel("📊 View-Tabelle")
        self.title_label.setFont(QFont("Arial", 12, QFont.Bold))
        header_layout.addWidget(self.title_label)
        
        # Menü-Button mit Dropdown
        self.menu_button = QPushButton("⚙️ Menü")
        self.menu = QMenu(self)
        
        # Spalten-Parameter Aktion
        spalten_action = QAction("📋 Spalten-Parameter", self)
        spalten_action.triggered.connect(self.settings_requested.emit)
        self.menu.addAction(spalten_action)
        
        # Expert-Mode Umschaltung (nur im Admin-Mode)
        if self.mode == 'admin':
            self.menu.addSeparator()
            self.expert_action = QAction("👥 Expert-Mode umschalten", self)
            self.expert_action.triggered.connect(self._toggle_expert_mode)
            self.menu.addAction(self.expert_action)
        
        self.menu_button.setMenu(self.menu)
        
        # Filter-Button (funktioniert schon)
        self.filter_button = QPushButton("🔍 Filter")
        self.filter_button.clicked.connect(self.toggle_filter_panel)
        
        header_layout.addWidget(self.menu_button)
        header_layout.addWidget(self.filter_button)
        
        main_layout.addLayout(header_layout)
        
        # Tabelle konfigurieren
        self.table = QTableWidget()
        self.table.setSortingEnabled(True)
        
        # Header-Stil für bessere Darstellung
        header = self.table.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignCenter)
        
        # Event-Handler für Sortierung und Header-Interaktion
        if self.sorting_manager:
            try:
                header.sectionClicked.connect(self._on_header_clicked)
                logger.debug("📊 Header-Click Event für Sortierungs-Persistenz verbunden")
            except Exception as e:
                logger.warning(f"⚠️ Fehler beim Verbinden des Header-Click Events: {e}")
        
        main_layout.addWidget(self.table)
        
        # Layouts zusammensetzen
        self.main_layout.addWidget(self.filter_scroll)  # Filter-Panel links
        self.main_layout.addWidget(main_container)      # Hauptbereich rechts
        
    def _get_stylesheet(self):
        """Gibt das Stylesheet für das Widget zurück"""
        return """
            QFrame#FilterPanel {
                background-color: #f5f5f5;
                border: 1px solid #ddd;
                border-radius: 4px;
            }
            
            QGroupBox {
                font-weight: bold;
                border: 2px solid #ddd;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 5px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            
            QLineEdit {
                padding: 4px;
                border: 1px solid #ddd;
                border-radius: 3px;
            }
            
            QPushButton {
                padding: 6px 12px;
                border: 1px solid #ddd;
                border-radius: 3px;
                background-color: white;
            }
            
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """
        
    def toggle_filter_panel(self):
        """Schaltet die Sichtbarkeit des Filter-Panels um"""
        if self.filter_shown:
            self.hide_filter_panel()
        else:
            self.show_filter_panel()
            
    def show_filter_panel(self):
        """Zeigt das Filter-Panel an"""
        self.filter_panel.show()
        self.filter_scroll.show()
        self.filter_shown = True
        self.filter_button.setText("🔍 Filter schließen")
        
    def hide_filter_panel(self):
        """Versteckt das Filter-Panel"""
        self.filter_panel.hide()
        self.filter_scroll.hide()
        self.filter_shown = False
        self.filter_button.setText("🔍 Filter")
        
    def _on_search_changed(self):
        """Wird aufgerufen, wenn sich der Suchtext ändert"""
        search_text = self.search_filter.text().strip().lower()
        is_negative = self.negative_filter_checkbox.isChecked()
        
        if not search_text:
            # Zeige alle Zeilen wenn kein Suchtext
            for i in range(self.table.rowCount()):
                self.table.setRowHidden(i, False)
            return
            
        # Filtere Zeilen basierend auf Suchtext
        for row in range(self.table.rowCount()):
            row_text = ""
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item:
                    row_text += item.text().lower() + " "
            
            contains_text = search_text in row_text
            
            # Bei Negativ-Filter: verstecke gefundene Zeilen, zeige nicht-gefundene
            # Bei Normal-Filter: zeige gefundene Zeilen, verstecke nicht-gefundene  
            should_hide = contains_text if is_negative else not contains_text
            self.table.setRowHidden(row, should_hide)
            
    def load_data(self):
        """Lädt die Daten in die Tabelle"""
        try:
            # Daten vom View Manager holen
            data_result = self.view_manager.get_data_and_columns_for_view(self.view_guid)
            
            if not data_result:
                logger.warning("❌ Keine Daten vom ViewManager erhalten")
                return
                
            table_data = data_result.get('data', [])
            column_info = data_result.get('columns', [])
            
            logger.info(f"📊 Lade {len(table_data)} Zeilen und {len(column_info)} Spalten")
            
            # Aktuelle Daten für Filter speichern
            self.current_table_data = table_data
            
            if not table_data or not column_info:
                logger.warning("⚠️ Keine Tabellendaten oder Spalten-Informationen vorhanden")
                return
            
            # Expert-Modus Status ermitteln: Admin-Mode ODER sichtbare Expert-Spalten
            expert_spalten_sichtbar = any(
                col.get('show', False) for col in column_info 
                if col.get('expert', False)
            )
            
            # Admin-Mode erzwingt Expert-Funktionalität, auch wenn keine Expert-Spalten sichtbar
            admin_mode_aktiv = (self.mode == 'admin')
            expert_mode_aktiv = admin_mode_aktiv or expert_spalten_sichtbar
            
            if expert_mode_aktiv:
                # EXPERT-MODUS: Verwendet 'show' und 'order'
                visible_columns = [col for col in column_info if col.get('show', False)]
                # Sortierung nach 'order' Feld
                visible_columns.sort(key=lambda x: x.get('order', 999))
                logger.debug(f"🔧 Expert-Modus: Zeige {len(visible_columns)} Spalten (show=True), sortiert nach 'order' (Admin={admin_mode_aktiv})")
            else:
                # NORMAL-MODUS: Verwendet 'show_show' und 'show_order' (komplett getrennt!)
                visible_columns = [col for col in column_info if col.get('show_show', False)]
                # Sortierung nach 'show_order' Feld
                visible_columns.sort(key=lambda x: x.get('show_order', 999))
                logger.debug(f"👤 Normal-Modus: Zeige {len(visible_columns)} Spalten (show_show=True), sortiert nach 'show_order'")
            
            # Expert-Mode Status für Widget aktualisieren
            self.expert_mode = expert_mode_aktiv
            
            # current_columns für die neuen Sortierungs-Features setzen
            self.current_columns = [col['name'] for col in visible_columns]
            
            # Tabelle konfigurieren
            self.table.setRowCount(len(table_data))
            self.table.setColumnCount(len(visible_columns))
            
            # Header setzen - im Expert-Modus mit interner Spaltenbezeichnung
            headers = []
            for col in visible_columns:
                anzeige = col.get('anzeige', col['name'])
                if self.expert_mode:
                    # Expert-Modus: Anzeige + interne Spaltenbezeichnung
                    internal_name = col['name']
                    headers.append(f"{anzeige}\n{internal_name}")
                else:
                    # Normal-Modus: Nur Anzeige-Name
                    headers.append(anzeige)
            
            self.table.setHorizontalHeaderLabels(headers)
            
            # Daten füllen
            for row_idx, row_data in enumerate(table_data):
                for col_idx, col_info in enumerate(visible_columns):
                    col_name = col_info['name']
                    cell_value = str(row_data.get(col_name, ''))
                    
                    item = QTableWidgetItem(cell_value)
                    self.table.setItem(row_idx, col_idx, item)
            
            # Header-Größe anpassen
            header = self.table.horizontalHeader()
            header.setStretchLastSection(True)
            
            # Auto-Resize für bessere Darstellung
            self.table.resizeColumnsToContents()
            
            logger.info(f"✅ Tabelle erfolgreich geladen: {len(table_data)} Zeilen, {len(visible_columns)} sichtbare Spalten")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Daten: {e}")
            import traceback
            traceback.print_exc()
            
    def _apply_saved_sorting(self):
        """Wendet die gespeicherte Sortierung an"""
        try:
            if self.sorting_manager and hasattr(self, 'current_columns'):
                self.sorting_manager.apply_saved_sorting_to_table(self.table, self.current_columns)
                logger.debug("📊 Gespeicherte Sortierung angewendet")
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Anwenden der gespeicherten Sortierung: {e}")
            
    def _on_header_clicked(self, logical_index):
        """Wird aufgerufen, wenn ein Header geklickt wird"""
        try:
            if self.sorting_manager and hasattr(self, 'current_columns'):
                # Sortierung nach einem kurzen Delay persistieren (damit Qt die Sortierung erst durchführt)
                QTimer.singleShot(50, lambda: self._save_current_sorting(logical_index))
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Header-Click: {e}")
            
    def _save_current_sorting(self, logical_index):
        """Speichert die aktuelle Sortierung"""
        try:
            if self.sorting_manager and hasattr(self, 'current_columns'):
                # Aktuelle Sortier-Reihenfolge und -Richtung ermitteln
                sort_column = self.table.horizontalHeader().sortIndicatorSection()
                sort_order = self.table.horizontalHeader().sortIndicatorOrder()
                
                if sort_column >= 0 and sort_column < len(self.current_columns):
                    column_name = self.current_columns[sort_column]
                    self.sorting_manager.save_sorting(column_name, sort_order)
                    logger.debug(f"📊 Sortierung gespeichert: {column_name}, Reihenfolge: {sort_order}")
        except Exception as e:
            logger.warning(f"⚠️ Fehler beim Speichern der Sortierung: {e}")

    def _toggle_expert_mode(self):
        """Schaltet Expert-Mode um (nur im Admin-Mode verfügbar)"""
        if self.mode != 'admin':
            logger.warning("⚠️ Expert-Mode nur im Admin-Mode verfügbar")
            return
            
        try:
            # Expert-Mode in ViewManager umschalten
            if hasattr(self.view_manager, 'aenderung_expert_umschalten'):
                self.view_manager.aenderung_expert_umschalten()
                logger.info("👥 Expert-Mode umgeschaltet über ViewManager")
            else:
                logger.warning("⚠️ ViewManager hat keine aenderung_expert_umschalten Methode")
            
            # Daten neu laden nach Mode-Wechsel
            self.load_data()
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Umschalten des Expert-Modus: {e}")
            import traceback
            traceback.print_exc()
