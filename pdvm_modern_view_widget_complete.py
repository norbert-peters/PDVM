#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VOLLSTÄNDIGES VIEW-WIDGET mit Steuerungselementen für den exakten ViewManager
Kompakte Version mit allen wichtigen Funktionen
"""

import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QPushButton, QCheckBox, QComboBox, QLineEdit, QGroupBox,
    QScrollArea, QFrame, QSplitter, QHeaderView
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

logger = logging.getLogger(__name__)

class PdvmModernViewWidget(QWidget):
    """
    Vollständiges modernes View-Widget mit allen Steuerungselementen
    Arbeitet mit dem exakten ViewManager nach USER-SPEZIFIKATION
    """
    
    # Signals für externe Kommunikation
    rowSelected = pyqtSignal(dict)  # Zeile ausgewählt
    dataChanged = pyqtSignal()      # Daten geändert
    
    def __init__(self, view_manager, parent=None, mode=None):
        super().__init__(parent)
        self.view_manager = view_manager
        self.mode = mode  # 'admin' für Expert-Mode Zugang
        self.current_expert_mode = False
        
        self.init_ui()
        self.load_initial_data()
        
        logger.info(f"🎨 Vollständiges View-Widget initialisiert (Mode: {mode})")
    
    def init_ui(self):
        """Initialisiert die vollständige Benutzeroberfläche"""
        # Haupt-Layout
        main_layout = QVBoxLayout(self)
        
        # Header-Bereich
        header_widget = self.create_header_widget()
        main_layout.addWidget(header_widget)
        
        # Splitter für Steuerung und Tabelle
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter, 1)
        
        # Linke Seite: Steuerungselemente
        control_widget = self.create_control_widget()
        splitter.addWidget(control_widget)
        
        # Rechte Seite: Tabelle
        table_widget = self.create_table_widget()
        splitter.addWidget(table_widget)
        
        # Splitter-Verhältnis: 25% Steuerung, 75% Tabelle
        splitter.setSizes([250, 750])
        
        # Status-Leiste
        status_widget = self.create_status_widget()
        main_layout.addWidget(status_widget)
    
    def create_header_widget(self):
        """Erstellt den Header-Bereich mit Titel und Hauptaktionen"""
        header = QWidget()
        header.setStyleSheet("background-color: #e8f4fd; padding: 10px; border-bottom: 1px solid #ccc;")
        layout = QHBoxLayout(header)
        
        # Titel
        title_label = QLabel("🎯 EXAKTER ViewManager - Moderne Tabellenansicht")
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        layout.addStretch()
        
        # Expert-Modus Toggle (nur im Admin-Mode verfügbar)
        if self.mode == 'admin':
            self.expert_button = QPushButton("👥 Expert-Modus")
            self.expert_button.setCheckable(True)
            self.expert_button.clicked.connect(self.toggle_expert_mode)
            self.expert_button.setStyleSheet("""
                QPushButton {
                    padding: 8px 16px;
                    border: 2px solid #007acc;
                    border-radius: 4px;
                    background-color: white;
                }
                QPushButton:checked {
                    background-color: #007acc;
                    color: white;
                }
            """)
            layout.addWidget(self.expert_button)
        else:
            self.expert_button = None  # Kein Expert-Button im User-Mode
        
        # Reset-Button
        reset_button = QPushButton("🔄 Reset")
        reset_button.clicked.connect(self.reset_view)
        reset_button.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                border: 2px solid #ff6b6b;
                border-radius: 4px;
                background-color: white;
                color: #ff6b6b;
            }
            QPushButton:hover {
                background-color: #ff6b6b;
                color: white;
            }
        """)
        layout.addWidget(reset_button)
        
        return header
    
    def create_control_widget(self):
        """Erstellt das Steuerungspanel"""
        control_frame = QFrame()
        control_frame.setFrameStyle(QFrame.StyledPanel)
        control_frame.setStyleSheet("background-color: #f8f9fa; padding: 10px;")
        
        layout = QVBoxLayout(control_frame)
        
        # Spalten-Steuerung
        columns_group = self.create_columns_control()
        layout.addWidget(columns_group)
        
        # Filter-Steuerung
        filter_group = self.create_filter_control()
        layout.addWidget(filter_group)
        
        layout.addStretch()
        
        return control_frame
    
    def create_columns_control(self):
        """Erstellt die Spalten-Steuerung"""
        group = QGroupBox("📋 Spalten-Anzeige")
        layout = QVBoxLayout(group)
        
        # Scroll-Bereich für viele Spalten
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMaximumHeight(300)
        
        scroll_widget = QWidget()
        self.columns_layout = QVBoxLayout(scroll_widget)
        
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # Aktionen
        actions_layout = QHBoxLayout()
        
        all_button = QPushButton("Alle")
        all_button.clicked.connect(self.select_all_columns)
        actions_layout.addWidget(all_button)
        
        none_button = QPushButton("Keine")
        none_button.clicked.connect(self.select_no_columns)
        actions_layout.addWidget(none_button)
        
        layout.addLayout(actions_layout)
        
        return group
    
    def create_filter_control(self):
        """Erstellt die Filter-Steuerung"""
        group = QGroupBox("🔍 Filter")
        layout = QVBoxLayout(group)
        
        # Such-Filter
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Suche in allen Spalten...")
        self.search_input.textChanged.connect(self.apply_search_filter)
        layout.addWidget(self.search_input)
        
        return group
    
    def create_table_widget(self):
        """Erstellt das Tabellen-Widget"""
        self.table = QTableWidget()
        
        # Tabellen-Eigenschaften
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        
        # Signal-Verbindungen
        self.table.itemSelectionChanged.connect(self.on_row_selected)
        
        # Styling
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #e0e0e0;
                background-color: white;
                alternate-background-color: #f5f5f5;
            }
            QTableWidget::item:selected {
                background-color: #007acc;
                color: white;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 8px;
                border: 1px solid #d0d0d0;
                font-weight: bold;
            }
        """)
        
        return self.table
    
    def create_status_widget(self):
        """Erstellt die Status-Leiste"""
        status = QWidget()
        status.setStyleSheet("background-color: #f0f0f0; padding: 5px; border-top: 1px solid #ccc;")
        layout = QHBoxLayout(status)
        
        self.status_label = QLabel("Bereit")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        self.rows_label = QLabel("0 Zeilen")
        layout.addWidget(self.rows_label)
        
        self.columns_label = QLabel("0 Spalten")
        layout.addWidget(self.columns_label)
        
        return status
    
    def load_initial_data(self):
        """Lädt die initialen Daten"""
        try:
            # Daten vom ViewManager holen
            self.update_table_data()
            self.update_columns_control()
            
            self.status_label.setText("✅ Daten geladen")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der initialen Daten: {e}")
            self.status_label.setText(f"❌ Fehler: {e}")
    
    def update_table_data(self):
        """Aktualisiert die Tabellendaten"""
        try:
            aktuelle_tabelle = self.view_manager.get_aktuelle_tabelle()
            sichtbare_spalten = self.view_manager.get_sichtbare_spalten()
            
            # Tabelle konfigurieren
            self.table.setRowCount(len(aktuelle_tabelle))
            self.table.setColumnCount(len(sichtbare_spalten))
            self.table.setHorizontalHeaderLabels(sichtbare_spalten)
            
            # Daten einfügen
            for row_idx, row_data in enumerate(aktuelle_tabelle):
                for col_idx, col_name in enumerate(sichtbare_spalten):
                    value = str(row_data.get(col_name, ""))
                    item = QTableWidgetItem(value)
                    self.table.setItem(row_idx, col_idx, item)
            
            # Spalten automatisch anpassen
            self.table.resizeColumnsToContents()
            
            # Status aktualisieren
            self.rows_label.setText(f"{len(aktuelle_tabelle)} Zeilen")
            self.columns_label.setText(f"{len(sichtbare_spalten)} Spalten")
            
            logger.info(f"📊 Tabelle aktualisiert: {len(aktuelle_tabelle)} Zeilen, {len(sichtbare_spalten)} Spalten")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktualisieren der Tabellendaten: {e}")
            self.status_label.setText(f"❌ Fehler beim Aktualisieren: {e}")
    
    def update_columns_control(self):
        """Aktualisiert die Spalten-Steuerung"""
        try:
            # Alte Checkboxen entfernen
            for i in reversed(range(self.columns_layout.count())):
                child = self.columns_layout.itemAt(i).widget()
                if child:
                    child.setParent(None)
            
            # Neue Checkboxen erstellen
            self.column_checkboxes = {}
            
            if hasattr(self.view_manager, 'display_view_control') and self.view_manager.display_view_control:
                for column in self.view_manager.display_view_control.columns:
                    # Prüfe Expert-Modus-Sichtbarkeit
                    if column.get('expert', False) and not self.current_expert_mode:
                        continue
                    
                    checkbox = QCheckBox(column.get('anzeige', column.get('name', 'Unbekannt')))
                    checkbox.setChecked(column.get('show', False))
                    checkbox.stateChanged.connect(lambda state, col_name=column.get('name'): 
                                                 self.on_column_visibility_changed(col_name, state == Qt.Checked))
                    
                    self.columns_layout.addWidget(checkbox)
                    self.column_checkboxes[column.get('name')] = checkbox
            
            logger.info(f"📋 Spalten-Steuerung aktualisiert: {len(self.column_checkboxes)} Spalten")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktualisieren der Spalten-Steuerung: {e}")
    
    def toggle_expert_mode(self):
        """Schaltet den Expert-Modus um (nur im Admin-Mode verfügbar)"""
        if self.mode != 'admin':
            logger.warning("⚠️ Expert-Mode nur im Admin-Mode verfügbar")
            return
            
        try:
            self.current_expert_mode = not self.current_expert_mode
            
            # ViewManager Expert-Modus umschalten
            self.view_manager.aenderung_expert_umschalten()
            
            # UI aktualisieren
            self.update_table_data()
            self.update_columns_control()
            
            mode_text = "AN" if self.current_expert_mode else "AUS"
            if self.expert_button:  # Prüfen ob Button existiert
                self.expert_button.setText(f"👥 Expert: {mode_text}")
            self.status_label.setText(f"🔄 Expert-Modus: {mode_text}")
            
            logger.info(f"👥 Expert-Modus umgeschaltet: {mode_text}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Umschalten des Expert-Modus: {e}")
            self.status_label.setText(f"❌ Fehler Expert-Modus: {e}")
    
    def reset_view(self):
        """Setzt die View auf Standardwerte zurück"""
        try:
            self.view_manager.aenderung_reset()
            
            # Expert-Modus zurücksetzen
            self.current_expert_mode = False
            self.expert_button.setChecked(False)
            self.expert_button.setText("👥 Expert-Modus")
            
            # Such-Filter zurücksetzen
            self.search_input.clear()
            
            # UI aktualisieren
            self.update_table_data()
            self.update_columns_control()
            
            self.status_label.setText("🔄 View zurückgesetzt")
            logger.info("🔄 View auf Standardwerte zurückgesetzt")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Zurücksetzen der View: {e}")
            self.status_label.setText(f"❌ Reset-Fehler: {e}")
    
    def on_column_visibility_changed(self, column_name, visible):
        """Callback wenn Spalten-Sichtbarkeit geändert wird"""
        try:
            self.view_manager.aenderung_spalten_auswahl(column_name, visible)
            self.update_table_data()
            
            action = "eingeblendet" if visible else "ausgeblendet"
            self.status_label.setText(f"📋 Spalte '{column_name}' {action}")
            
            # Signal emittieren
            self.dataChanged.emit()
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Ändern der Spalten-Sichtbarkeit: {e}")
            self.status_label.setText(f"❌ Fehler Spalte: {e}")
    
    def select_all_columns(self):
        """Wählt alle Spalten aus"""
        for checkbox in self.column_checkboxes.values():
            if not checkbox.isChecked():
                checkbox.setChecked(True)
    
    def select_no_columns(self):
        """Wählt keine Spalten aus"""
        for checkbox in self.column_checkboxes.values():
            if checkbox.isChecked():
                checkbox.setChecked(False)
    
    def apply_search_filter(self):
        """Wendet den Such-Filter an"""
        search_text = self.search_input.text().lower()
        
        for row in range(self.table.rowCount()):
            show_row = False
            if not search_text:
                show_row = True
            else:
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if item and search_text in item.text().lower():
                        show_row = True
                        break
            
            self.table.setRowHidden(row, not show_row)
        
        # Sichtbare Zeilen zählen
        visible_rows = sum(1 for row in range(self.table.rowCount()) 
                          if not self.table.isRowHidden(row))
        self.rows_label.setText(f"{visible_rows} Zeilen (gefiltert)")
    
    def on_row_selected(self):
        """Callback wenn eine Zeile ausgewählt wird"""
        try:
            current_row = self.table.currentRow()
            if current_row >= 0:
                # Zeilen-Daten sammeln
                row_data = {}
                for col in range(self.table.columnCount()):
                    header = self.table.horizontalHeaderItem(col).text()
                    item = self.table.item(current_row, col)
                    row_data[header] = item.text() if item else ""
                
                # Signal emittieren
                self.rowSelected.emit(row_data)
                
                # Status aktualisieren
                self.status_label.setText(f"📍 Zeile {current_row + 1} ausgewählt")
                
        except Exception as e:
            logger.error(f"❌ Fehler bei Zeilen-Auswahl: {e}")
    
    def refresh_data(self):
        """Aktualisiert alle Daten (öffentliche Methode)"""
        self.load_initial_data()
