# pdvm_minimal_table_widget.py
"""
Minimal PDVM Table Widget - Genau nach Anforderungen
===================================================

Oberfläche:
- Tabelle im Normal-Mode
- Ein Menü [Einstellungen] mit:
  * Spalten-Parameter
  * Expert-Mode ein/aus  
  * Filter anzeigen/ausblenden
"""

import logging
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, 
    QHeaderView, QPushButton, QMenu, QAction
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

logger = logging.getLogger(__name__)

class PdvmMinimalTableWidget(QWidget):
    """
    Minimal PDVM Table Widget nach exakten Anforderungen
    
    - Nur Tabelle + Menü "Einstellungen"
    - Keine komplexen Filter-Panels
    - Direkte ViewManager-Integration
    """
    
    # Signals
    settings_requested = pyqtSignal()
    expert_mode_toggled = pyqtSignal(bool)
    filter_panel_toggled = pyqtSignal(bool)
    
    def __init__(self, view_manager, view_guid=None, mode='normal', parent=None):
        super().__init__(parent)
        
        self.view_manager = view_manager
        self.view_guid = view_guid
        self.mode = mode
        self.expert_mode_active = False
        self.filter_panel_visible = False
        
        self.setup_ui()
        
        # Initial load
        if self.view_manager:
            self.refresh_data()
    
    def setup_ui(self):
        """UI Setup: Nur Tabelle + Einstellungen-Menü"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Header mit Einstellungen-Menü
        header_layout = QVBoxLayout()
        
        # Einstellungen-Button
        self.settings_button = QPushButton("⚙️ Einstellungen")
        self.settings_button.setMaximumWidth(150)
        
        # Menü erstellen
        self.menu = QMenu(self)
        
        # 1. Spalten-Parameter
        spalten_action = QAction("📋 Spalten-Parameter", self)
        spalten_action.triggered.connect(self.settings_requested.emit)
        self.menu.addAction(spalten_action)
        
        # 2. Expert-Mode ein/aus
        self.expert_action = QAction("👥 Expert-Mode EIN", self)
        self.expert_action.triggered.connect(self._toggle_expert_mode)
        self.menu.addAction(self.expert_action)
        
        # 3. Filter anzeigen/ausblenden
        self.filter_action = QAction("🔍 Filter anzeigen", self)
        self.filter_action.triggered.connect(self._toggle_filter_panel)
        self.menu.addAction(self.filter_action)
        
        self.settings_button.setMenu(self.menu)
        header_layout.addWidget(self.settings_button)
        layout.addLayout(header_layout)
        
        # Tabelle
        self.table = QTableWidget()
        self.table.setSortingEnabled(True)
        
        # Header-Stil
        header = self.table.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignCenter)
        header.setStyleSheet("""
            QHeaderView::section {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                padding: 8px;
                font-weight: bold;
            }
        """)
        
        layout.addWidget(self.table)
        
        # Widget-Stil
        self.setStyleSheet("""
            PdvmMinimalTableWidget {
                background-color: #ffffff;
                border: 1px solid #dee2e6;
                border-radius: 5px;
            }
            QPushButton {
                background-color: #e9ecef;
                border: 1px solid #ced4da;
                border-radius: 4px;
                padding: 6px 12px;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #f8f9fa;
            }
            QTableWidget {
                gridline-color: #dee2e6;
                selection-background-color: #cce5ff;
            }
        """)
    
    def _toggle_expert_mode(self):
        """Expert-Mode umschalten"""
        try:
            if self.view_manager and hasattr(self.view_manager, 'aenderung_expert_umschalten'):
                self.view_manager.aenderung_expert_umschalten()
                self.expert_mode_active = self.view_manager.is_expert_mode_active()
                
                # Menü-Text aktualisieren
                mode_text = "AUS" if self.expert_mode_active else "EIN"
                self.expert_action.setText(f"👥 Expert-Mode {mode_text}")
                
                # UI aktualisieren
                self.refresh_data()
                self.expert_mode_toggled.emit(self.expert_mode_active)
                
                logger.info(f"🔧 Expert-Mode {'EIN' if self.expert_mode_active else 'AUS'}")
                
        except Exception as e:
            logger.error(f"❌ Expert-Mode Toggle Fehler: {e}")
    
    def _toggle_filter_panel(self):
        """Filter-Panel anzeigen/ausblenden"""
        try:
            self.filter_panel_visible = not self.filter_panel_visible
            
            # Menü-Text aktualisieren
            filter_text = "ausblenden" if self.filter_panel_visible else "anzeigen"
            self.filter_action.setText(f"🔍 Filter {filter_text}")
            
            self.filter_panel_toggled.emit(self.filter_panel_visible)
            
            logger.info(f"🔍 Filter-Panel {'angezeigt' if self.filter_panel_visible else 'ausgeblendet'}")
            
        except Exception as e:
            logger.error(f"❌ Filter-Panel Toggle Fehler: {e}")
    
    def refresh_data(self):
        """Tabelle mit aktuellen Daten füllen"""
        try:
            if not self.view_manager:
                return
            
            # Daten vom ViewManager abrufen
            if hasattr(self.view_manager, 'get_aktuelle_tabelle'):
                data = self.view_manager.get_aktuelle_tabelle() or []
            else:
                data = []
            
            # Spalten-Konfiguration abrufen  
            if hasattr(self.view_manager, 'get_sichtbare_spalten'):
                column_names = self.view_manager.get_sichtbare_spalten() or []
            else:
                column_names = []
            
            # Tabelle konfigurieren
            self.table.setRowCount(len(data))
            self.table.setColumnCount(len(column_names))
            
            # Header setzen
            self.table.setHorizontalHeaderLabels(column_names)
            
            # Daten einfügen
            for row_idx, row_data in enumerate(data):
                for col_idx, col_name in enumerate(column_names):
                    value = row_data.get(col_name, '')
                    
                    item = QTableWidgetItem(str(value))
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Read-only
                    self.table.setItem(row_idx, col_idx, item)
            
            # Auto-Resize
            self.table.resizeColumnsToContents()
            
            logger.info(f"✅ Tabelle aktualisiert: {len(data)} Zeilen, {len(column_names)} Spalten")
            
        except Exception as e:
            logger.error(f"❌ Refresh-Data Fehler: {e}")
            # Fallback: Leere Tabelle
            self.table.setRowCount(0)
            self.table.setColumnCount(0)
