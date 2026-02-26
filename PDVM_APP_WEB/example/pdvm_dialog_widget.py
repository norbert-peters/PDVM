# -*- coding: utf-8 -*-
"""
V2 PDVM Dialog Widget - Angepasst für V2-Architektur
=====================================================
Minimale Dialog-Implementation für V2-System mit GCS-Integration

Autor: PDVM V2.0
Datum: 04.11.2025
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QHBoxLayout, 
    QLabel, QMessageBox, QScrollArea
)
from PyQt5.QtCore import Qt
import logging

logger = logging.getLogger(__name__)


class V2PdvmDialogWidget(QWidget):
    """
    Minimaler V2-Dialog für PDVM-System
    
    Verwendet V2-GCS aus v2_central_systemsteuerung
    """
    
    def __init__(self, dialog_guid: str, dialog_mode: int = 0, parent=None):
        """
        Initialisiert V2-Dialog
        
        Args:
            dialog_guid: GUID des Dialogs aus framedaten
            dialog_mode: Modus (0=neu, 1=bearbeiten, etc.)
            parent: Parent-Widget
        """
        super().__init__(parent)
        
        self.dialog_guid = dialog_guid
        self.dialog_mode = dialog_mode
        
        # V2-GCS importieren
        from pdvm_central_systemsteuerung import get_gcs
        self.gcs = get_gcs()
        
        if not self.gcs:
            logger.error("❌ GCS nicht verfügbar in V2-Dialog")
            QMessageBox.critical(self, "Fehler", "GCS nicht initialisiert!")
            return
        
        logger.info(f"🔹 V2-Dialog gestartet: {dialog_guid}, Mode: {dialog_mode}")
        
        # Dialog-Konfiguration (als Widget, nicht Modal!)
        # Kein resize() - wird vom Parent-Layout gesteuert
        
        # UI aufbauen
        self._init_ui()
        self._load_dialog_config()
    
    def _init_ui(self):
        """Initialisiert UI-Layout"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)  # Keine Ränder für Widget im Arbeitsbereich
        
        # Header
        header_label = QLabel(f"<h2>Dialog: {self.dialog_guid}</h2>")
        layout.addWidget(header_label)
        
        # Info-Bereich
        info_label = QLabel(
            f"<b>Modus:</b> {self.dialog_mode}<br>"
            f"<b>User-GUID:</b> {self.gcs.user_guid}"
        )
        layout.addWidget(info_label)
        
        # Content-Bereich (ScrollArea für zukünftige Controls)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        scroll.setWidget(self.content_widget)
        layout.addWidget(scroll)
        
        # Button-Leiste
        button_layout = QHBoxLayout()
        
        btn_save = QPushButton("💾 Speichern")
        btn_save.clicked.connect(self._on_save)
        button_layout.addWidget(btn_save)
        
        btn_cancel = QPushButton("❌ Schließen")
        btn_cancel.clicked.connect(self._on_close)
        button_layout.addWidget(btn_cancel)
        
        layout.addLayout(button_layout)
        
        logger.info("✅ V2-Dialog UI initialisiert")
    
    def _load_dialog_config(self):
        """Lädt Dialog-Konfiguration aus sys_framedaten (V2)"""
        try:
            from pdvm_central_datenbank import PdvmCentralDatenbank
            
            # V2: sys_framedaten für Dialog laden (NICHT historisch!)
            frame_db = PdvmCentralDatenbank('sys_framedaten', self.dialog_guid)
            frame_data = frame_db.get_all_values()
            
            if not frame_data:
                logger.warning(f"⚠️ Keine sys_framedaten für Dialog {self.dialog_guid}")
                info_label = QLabel(
                    "<b>⚠️ Dialog-Konfiguration fehlt</b><br>"
                    "Dieser Dialog ist noch nicht in sys_framedaten definiert.<br>"
                    "Bitte konfigurieren Sie den Dialog in der Verwaltung."
                )
                self.content_layout.addWidget(info_label)
                return
            
            # Dialog-Titel aus ROOT.title - NICHT historisch, verwende get_static_value()
            title = frame_db.get_static_value('ROOT', 'title')
            if title:
                self.setWindowTitle(str(title))
            
            # View-GUID für Daten-View - NICHT historisch
            view_guid = frame_db.get_static_value('ROOT', 'view_guid')
            
            logger.info(f"✅ Dialog-Konfiguration geladen: title={title}, view_guid={view_guid}")
            
            # Placeholder für zukünftige Control-Integration
            config_label = QLabel(
                f"<b>Dialog-Konfiguration:</b><br>"
                f"View-GUID: {view_guid}<br>"
                f"<i>Controls werden hier geladen...</i>"
            )
            self.content_layout.addWidget(config_label)
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Dialog-Konfiguration: {e}")
            import traceback
            traceback.print_exc()
            
            error_label = QLabel(f"<b>❌ Fehler:</b> {str(e)}")
            self.content_layout.addWidget(error_label)
    
    def _on_save(self):
        """Speichert Dialog-Daten"""
        try:
            logger.info(f"💾 Speichere Dialog-Daten für {self.dialog_guid}")
            
            # TODO: Hier werden später die Control-Werte gespeichert
            
            QMessageBox.information(
                self, 
                "Erfolg", 
                f"Dialog-Daten wurden gespeichert."
            )
            
            # Kein accept() mehr - Widget bleibt offen
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern: {e}")
            QMessageBox.critical(
                self,
                "Fehler",
                f"Fehler beim Speichern:\n{str(e)}"
            )
    
    def _on_close(self):
        """Schließt den Dialog (entfernt Widget aus Parent)"""
        try:
            logger.info(f"🔒 Schließe Dialog: {self.dialog_guid}")
            # Signalisiere Parent, dass Dialog geschlossen werden soll
            self.hide()
            if self.parent():
                self.parent().remove_dialog_widget()
        except Exception as e:
            logger.error(f"❌ Fehler beim Schließen: {e}")


# =============================================================================
# KOMPATIBILITÄTS-KLASSE FÜR ALTE AUFRUFE
# =============================================================================

class PdvmDialogManager:
    """Kompatibilitäts-Klasse für alte Dialog-Aufrufe"""
    
    def __init__(self, base_call: dict):
        logger.info("🔹 V2-PdvmDialogManager (Kompatibilitätsmodus)")
        self.base_call = base_call
        self.frame_guid = base_call.get('frame_guid')
        self.mode = base_call.get('mode', 0)
        
        from pdvm_central_systemsteuerung import get_gcs
        self.gcs = get_gcs()
    
    def get_call(self, root_guid=None, stichtag_inst=None):
        """Gibt Call-Daten zurück"""
        return {
            'frame_guid': self.frame_guid,
            'mode': self.mode,
            'root_guid': root_guid,
            'stichtag_inst': stichtag_inst or self.gcs.st_inst,
        }


class PdvmDialogWidget(QWidget):
    """Kompatibilitäts-Widget für alte Aufrufe"""
    
    def __init__(self, call_data: dict, parent=None):
        super().__init__(parent)
        logger.info("🔹 V2-PdvmDialogWidget (Kompatibilitätsmodus)")
        
        frame_guid = call_data.get('frame_guid')
        mode = call_data.get('mode', 0)
        
        # Erstelle neuen V2-Dialog
        self.dialog = V2PdvmDialogWidget(frame_guid, mode, parent)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.dialog)
    
    def show_dialog(self):
        """Zeigt Dialog an"""
        return self.dialog.exec_()
