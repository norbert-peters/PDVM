# pdvm_input_controls_module.py
# -*- coding: utf-8 -*-
"""
🎯 PDVM INPUT CONTROLS MODULE - Erstes Edit-Modul für GenerellerDialog

MODULARER ANSATZ:
- Einfache API: __init__(framedaten_db, selected_guid)
- Eigenständiges Widget mit get_widget()
- Linear und übersichtlich
- GCS via globalen Import (nicht als Parameter!)

VERANTWORTLICHKEITEN:
- Header anzeigen
- GUID anzeigen
- Später: Input-Controls aufbauen

Version: 1.0.0 (Neu - Modularer Ansatz)
"""

import logging
from typing import Optional
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame
from PyQt5.QtCore import Qt

from global_gcs import gcs  # ← Globaler GCS-Import!

logger = logging.getLogger(__name__)


class PdvmInputControlsModule:
    """
    Input-Controls Modul für GenerellerDialog
    
    EINFACHE API:
    - __init__(framedaten_db, selected_guid)
    - get_widget() → QWidget
    - GCS via globalen Import
    
    PHASE 1: Header + GUID anzeigen
    PHASE 2: Input-Controls aufbauen (später)
    """
    
    def __init__(self, framedaten_db, selected_guid: str):
        """
        Initialisiert Input-Controls Modul
        
        Args:
            framedaten_db: PdvmCentralDatenbank Instanz für Framedaten
            selected_guid: GUID des ausgewählten Datensatzes
        """
        logger.info("🎯 === PDVM INPUT CONTROLS MODULE INITIALISIERUNG ===")
        logger.info(f"  📋 Selected GUID: {selected_guid}")
        
        self.framedaten_db = framedaten_db
        self.selected_guid = selected_guid
        # gcs via globalen Import verfügbar!
        
        # Header-Text aus Framedaten laden
        self._load_header()
        
        logger.info("✅ InputControlsModule initialisiert")
    
    def _load_header(self):
        """Lädt Header-Text aus Framedaten"""
        try:
            self.header_text, _ = self.framedaten_db.get_value('ROOT', 'HEADER_TEXT')
            
            # Fallback falls nicht gefunden
            if not self.header_text:
                logger.warning("  ⚠️ HEADER_TEXT nicht gefunden, versuche Fallback...")
                self.header_text, _ = self.framedaten_db.get_value('ROOT', 'header_text')
            
            # Default falls immer noch nichts
            if not self.header_text:
                self.header_text = "Edit-Bereich"
                logger.warning("  ⚠️ Kein Header gefunden, verwende Default")
            
            logger.info(f"  📋 Header: {self.header_text}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden des Headers: {e}")
            self.header_text = "Edit-Bereich"
    
    def get_widget(self) -> QWidget:
        """
        Gibt Widget mit Input-Controls zurück
        
        PHASE 1: Header + GUID
        PHASE 2: Input-Controls (später)
        
        Returns:
            QWidget mit vollständigem Edit-Bereich
        """
        logger.info("🎨 Erstelle Input-Controls Widget...")
        
        try:
            # Haupt-Container
            container = QWidget()
            layout = QVBoxLayout(container)
            layout.setContentsMargins(20, 20, 20, 20)
            layout.setSpacing(15)
            
            # === HEADER ===
            header_label = QLabel(self.header_text)
            header_label.setStyleSheet("""
                QLabel {
                    font-size: 18px;
                    font-weight: bold;
                    color: #2c3e50;
                    padding: 10px;
                    background-color: #ecf0f1;
                    border-radius: 5px;
                }
            """)
            header_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(header_label)
            
            # === TRENNLINIE ===
            separator = QFrame()
            separator.setFrameShape(QFrame.HLine)
            separator.setFrameShadow(QFrame.Sunken)
            separator.setStyleSheet("background-color: #bdc3c7;")
            layout.addWidget(separator)
            
            # === GUID ANZEIGE ===
            guid_container = QWidget()
            guid_layout = QVBoxLayout(guid_container)
            guid_layout.setContentsMargins(10, 10, 10, 10)
            guid_layout.setSpacing(5)
            
            guid_label_header = QLabel("📋 Ausgewählter Datensatz:")
            guid_label_header.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    font-weight: bold;
                    color: #34495e;
                }
            """)
            guid_layout.addWidget(guid_label_header)
            
            guid_label_value = QLabel(self.selected_guid)
            guid_label_value.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    color: #7f8c8d;
                    font-family: 'Courier New', monospace;
                    padding: 10px;
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 3px;
                }
            """)
            guid_label_value.setTextInteractionFlags(Qt.TextSelectableByMouse)
            guid_layout.addWidget(guid_label_value)
            
            layout.addWidget(guid_container)
            
            # === PLATZHALTER FÜR INPUT-CONTROLS ===
            placeholder = QLabel(
                "⚙️ Input-Controls werden hier angezeigt\n\n"
                "Phase 1: Header + GUID ✅\n"
                "Phase 2: Input-Controls (in Arbeit...)"
            )
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    color: #95a5a6;
                    font-style: italic;
                    padding: 40px;
                    background-color: #fafafa;
                    border: 2px dashed #dee2e6;
                    border-radius: 5px;
                }
            """)
            layout.addWidget(placeholder)
            
            # Stretch am Ende
            layout.addStretch()
            
            logger.info("✅ Input-Controls Widget erstellt (Phase 1: Header + GUID)")
            return container
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen des Widgets: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Fallback: Error-Widget
            error_widget = QWidget()
            error_layout = QVBoxLayout(error_widget)
            error_label = QLabel(f"❌ Fehler beim Laden des Edit-Bereichs:\n{str(e)}")
            error_label.setStyleSheet("color: red; padding: 20px;")
            error_layout.addWidget(error_label)
            return error_widget
