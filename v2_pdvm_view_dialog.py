# -*- coding: utf-8 -*-
"""
V2 PDVM View Dialog - Angepasst für V2-Architektur
==================================================
View-Dialog für V2-System mit GCS-Integration

Autor: PDVM V2.0
Datum: 04.11.2025
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QHBoxLayout,
    QLabel, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QScrollArea
)
from PyQt5.QtCore import Qt
import logging

logger = logging.getLogger(__name__)


class V2PdvmViewDialog(QWidget):
    """
    V2-View-Dialog für PDVM-System
    
    Zeigt tabellarische Daten mit Filter- und Such-Funktionen
    Verwendet V2-GCS aus v2_central_systemsteuerung
    """
    
    def __init__(self, call_daten: dict, parent=None):
        """
        Initialisiert V2-View-Dialog
        
        Args:
            call_daten: {
                'view_guid': str,
                'title': str,
                'first_call': bool,
                'reset': bool
            }
            parent: Parent-Widget
        """
        super().__init__(parent)
        
        self.call_daten = call_daten
        self.view_guid = call_daten.get('view_guid')
        self.title = call_daten.get('title', 'Unbekannte Ansicht')
        self.first_call = call_daten.get('first_call', False)
        self.reset = call_daten.get('reset', False)
        
        # V2-GCS importieren
        from v2_central_systemsteuerung import get_gcs
        self.gcs = get_gcs()
        
        if not self.gcs:
            logger.error("❌ GCS nicht verfügbar in V2-View-Dialog")
            QMessageBox.critical(self, "Fehler", "GCS nicht initialisiert!")
            return
        
        if not self.view_guid:
            logger.error("❌ Keine view_guid in call_daten")
            QMessageBox.critical(self, "Fehler", "Keine View-GUID angegeben!")
            return
        
        logger.info(f"🔹 V2-View-Dialog gestartet: {self.view_guid}")
        
        # UI aufbauen
        self._init_ui()
        self._load_view_data()
    
    def _init_ui(self):
        """Initialisiert UI-Layout"""
        layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel(f"<h2>{self.title}</h2>")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Refresh-Button
        btn_refresh = QPushButton("🔄 Aktualisieren")
        btn_refresh.clicked.connect(self._load_view_data)
        header_layout.addWidget(btn_refresh)
        
        layout.addLayout(header_layout)
        
        # Info-Bereich
        self.info_label = QLabel()
        layout.addWidget(self.info_label)
        
        # Tabelle für Daten
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        layout.addWidget(self.table)
        
        # Button-Leiste
        button_layout = QHBoxLayout()
        
        btn_close = QPushButton("❌ Schließen")
        btn_close.clicked.connect(self.close)
        button_layout.addStretch()
        button_layout.addWidget(btn_close)
        
        layout.addLayout(button_layout)
        
        logger.info("✅ V2-View-Dialog UI initialisiert")
    
    def _load_view_data(self):
        """Lädt View-Daten und zeigt sie an"""
        try:
            from pdvm_central_datenbank import PdvmCentralDatenbank
            
            logger.info(f"📂 Lade View-Daten für {self.view_guid}")
            
            # V2: ViewDaten aus sys_viewdaten DB laden
            view_db = PdvmCentralDatenbank('sys_viewdaten', self.view_guid)
            view_data = view_db.get_all_values()
            
            if not view_data:
                logger.warning(f"⚠️ Keine ViewDaten für {self.view_guid}")
                self.info_label.setText(
                    "<b>⚠️ View-Konfiguration fehlt</b><br>"
                    "Diese Ansicht ist noch nicht in sys_viewdaten definiert."
                )
                return
            
            # Controls aus viewdaten extrahieren
            controls_data = view_db.get_value('controls', 'all_controls')
            
            if not controls_data:
                logger.warning(f"⚠️ Keine Controls für View {self.view_guid} in sys_viewdaten")
                self.info_label.setText(
                    f"<b>View-GUID:</b> {self.view_guid}<br>"
                    "<b>Status:</b> Keine Controls definiert"
                )
                return
            
            # Info aktualisieren
            self.info_label.setText(
                f"<b>View-GUID:</b> {self.view_guid}<br>"
                f"<b>Controls:</b> {len(controls_data) if isinstance(controls_data, (list, dict)) else '?'}"
            )
            
            # Tabelle mit Dummy-Daten füllen (später: echte Daten aus Matrix)
            self._populate_table_dummy(controls_data)
            
            logger.info(f"✅ View-Daten geladen")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der View-Daten: {e}")
            import traceback
            traceback.print_exc()
            
            self.info_label.setText(f"<b>❌ Fehler:</b> {str(e)}")
    
    def _populate_table_dummy(self, controls_data):
        """Füllt Tabelle mit Dummy-Daten"""
        try:
            # Spalten-Namen aus Controls extrahieren
            if isinstance(controls_data, dict):
                columns = list(controls_data.keys())[:10]  # Max 10 Spalten
            elif isinstance(controls_data, list):
                columns = [f"Spalte {i+1}" for i in range(min(5, len(controls_data)))]
            else:
                columns = ["Spalte 1", "Spalte 2", "Spalte 3"]
            
            self.table.setColumnCount(len(columns))
            self.table.setHorizontalHeaderLabels(columns)
            
            # Dummy-Daten (3 Zeilen)
            self.table.setRowCount(3)
            for row in range(3):
                for col in range(len(columns)):
                    item = QTableWidgetItem(f"Dummy-Wert {row+1}/{col+1}")
                    self.table.setItem(row, col, item)
            
            # Spaltenbreiten anpassen
            self.table.resizeColumnsToContents()
            
            logger.info(f"✅ Tabelle gefüllt: {len(columns)} Spalten, 3 Zeilen (Dummy)")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Füllen der Tabelle: {e}")


# =============================================================================
# KOMPATIBILITÄTS-KLASSE FÜR ALTE AUFRUFE
# =============================================================================

class PdvmViewDialog(QWidget):
    """Kompatibilitäts-Klasse für alte View-Dialog-Aufrufe"""
    
    def __init__(self, call_daten: dict, parent=None, view_manager=None):
        super().__init__(parent)
        logger.info("🔹 PdvmViewDialog (Kompatibilitätsmodus → V2)")
        
        # Erstelle V2-View-Dialog
        layout = QVBoxLayout(self)
        self.v2_view = V2PdvmViewDialog(call_daten, self)
        layout.addWidget(self.v2_view)
