# pdvm_simple_table_widget.py
"""
Einfaches PDVM Table Widget - NUR Tabelle + Menü
===============================================

Widget mit minimaler Ausstattung:
- QTableWidget 
- QMenu mit Spalten-Parameter und Expert-Mode Toggle
- KEIN Filter-Panel
- KEIN Button-Layout
"""

import logging
from typing import Dict, Any, Optional
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, 
    QHeaderView, QPushButton, QMenu, QAction
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from pdvm_central_systemsteuerung import is_expert_mode_available

logger = logging.getLogger(__name__)

class PdvmSimpleTableWidget(QWidget):
    """
    Einfaches PDVM Table Widget mit nur Tabelle + Menü
    
    Features:
    - Reine Tabellen-Darstellung
    - Menü für Spalten-Parameter und Expert-Mode
    - Direkte ViewManager-Integration
    - Keine Filter-Buttons oder komplexe UI
    """
    
    # Signals
    settings_requested = pyqtSignal()
    expert_mode_toggled = pyqtSignal(bool)
    
    def __init__(self, view_manager, view_guid=None, mode='normal', parent=None):
        super().__init__(parent)
        
        self.view_manager = view_manager
        self.view_guid = view_guid
        self.mode = mode
        self.expert_mode_active = False
        
        self.setup_ui()
        self.setup_signals()
        
        # Initial load
        if self.view_manager:
            self.refresh_data()
    
    def setup_ui(self):
        """Minimal UI Setup: Nur Tabelle + Menü"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Header mit Menü-Button
        header_layout = QVBoxLayout()
        
        # Menü-Button
        self.menu_button = QPushButton("⚙️ PDVM Menü")
        self.menu_button.setMaximumWidth(150)
        
        # Menü erstellen
        self.menu = QMenu(self)
        
        # Spalten-Parameter
        spalten_action = QAction("📋 Spalten-Parameter", self)
        spalten_action.triggered.connect(self.settings_requested.emit)
        self.menu.addAction(spalten_action)
        
        # Expert-Mode Toggle (nur bei Admin-Mode verfügbar)
        if is_expert_mode_available():
            self.menu.addSeparator()
            self.expert_action = QAction("👥 Expert-Mode umschalten", self)
            self.expert_action.triggered.connect(self._toggle_expert_mode)
            self.menu.addAction(self.expert_action)
        
        self.menu_button.setMenu(self.menu)
        header_layout.addWidget(self.menu_button)
        layout.addLayout(header_layout)
        
        # Tabelle
        self.table = QTableWidget()
        self.table.setSortingEnabled(True)
        
        # Header-Stil
        header = self.table.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignCenter)
        header.setStyleSheet("""
            QHeaderView::section {
                background-color: #f0f0f0;
                border: 1px solid #d0d0d0;
                padding: 8px;
                font-weight: bold;
            }
        """)
        
        layout.addWidget(self.table)
        
        self.setStyleSheet("""
            PdvmSimpleTableWidget {
                background-color: #ffffff;
                border: 1px solid #d0d0d0;
                border-radius: 5px;
            }
            QPushButton {
                background-color: #e7f3ff;
                border: 1px solid #b3d9ff;
                border-radius: 3px;
                padding: 5px 10px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #d0ebff;
            }
        """)
    
    def setup_signals(self):
        """Signal-Verbindungen"""
        # Header-Klicks für Sortierung
        if hasattr(self.table.horizontalHeader(), 'sectionClicked'):
            self.table.horizontalHeader().sectionClicked.connect(self._on_header_clicked)
    
    def _on_header_clicked(self, logical_index):
        """Handler für Header-Klicks (Sortierung)"""
        try:
            if self.view_manager and hasattr(self.view_manager, 'handle_header_click'):
                self.view_manager.handle_header_click(logical_index)
                self.refresh_data()
        except Exception as e:
            logger.error(f"❌ Header-Click Fehler: {e}")
    
    def _toggle_expert_mode(self):
        """Expert-Mode umschalten"""
        try:
            if self.view_manager and hasattr(self.view_manager, 'aenderung_expert_umschalten'):
                self.view_manager.aenderung_expert_umschalten()
                self.expert_mode_active = self.view_manager.is_expert_mode_active()
                self.expert_mode_toggled.emit(self.expert_mode_active)
                
                # UI aktualisieren
                self.refresh_data()
                
                mode_text = "EIN" if self.expert_mode_active else "AUS"
                logger.info(f"🔧 Expert-Mode {mode_text}")
                
        except Exception as e:
            logger.error(f"❌ Expert-Mode Toggle Fehler: {e}")
    
    def refresh_data(self):
        """Tabelle mit aktuellen Daten füllen"""
        try:
            if not self.view_manager:
                return
            
            # Daten vom ViewManager abrufen
            if hasattr(self.view_manager, 'get_table_data'):
                data = self.view_manager.get_table_data()
            elif hasattr(self.view_manager, 'vollstaendige_basistabelle'):
                data = self.view_manager.vollstaendige_basistabelle or []
            else:
                data = []
            
            # Spalten-Konfiguration abrufen
            if hasattr(self.view_manager, 'get_visible_columns'):
                columns = self.view_manager.get_visible_columns()
            elif hasattr(self.view_manager, 'display_view_control') and self.view_manager.display_view_control:
                columns = []
                for col in self.view_manager.display_view_control.columns:
                    if col.get('show', False):
                        columns.append({
                            'name': col['name'],
                            'title': col.get('title', col['name']),
                        })
                # Nach aktueller Sortier-Logik sortieren
                columns.sort(key=lambda x: self.view_manager._get_order_for_mode(x['name'], self.expert_mode_active))
            else:
                columns = []
            
            # Tabelle konfigurieren
            self.table.setRowCount(len(data))
            self.table.setColumnCount(len(columns))
            
            # Header setzen
            headers = [col.get('title', col['name']) for col in columns]
            self.table.setHorizontalHeaderLabels(headers)
            
            # Daten einfügen
            for row_idx, row_data in enumerate(data):
                for col_idx, col in enumerate(columns):
                    field_name = col['name']
                    value = row_data.get(field_name, '')
                    
                    item = QTableWidgetItem(str(value))
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Read-only
                    self.table.setItem(row_idx, col_idx, item)
            
            # Auto-Resize
            self.table.resizeColumnsToContents()
            
            logger.info(f"✅ Tabelle aktualisiert: {len(data)} Zeilen, {len(columns)} Spalten")
            
        except Exception as e:
            logger.error(f"❌ Refresh-Data Fehler: {e}")
            # Fallback: Leere Tabelle
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
