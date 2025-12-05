"""
PDVM Input-Type VIEWTABLE

Zeigt einen Auswahl-Button für View-basierte Tabellen-Auswahl.
Öffnet Dialog mit View-Darstellung zur Auswahl eines Datensatzes.

VERANTWORTLICHKEITEN:
- Button-Widget erstellen mit aktuellem Display-Wert
- viewtable_config aus field_config laden
- Auswahl-Dialog öffnen mit View-Pipeline
- Ausgewählte GUID speichern
- Display-Text aus View-Metadaten formatieren

AUTOR: Norbert Peters
DATUM: 25.10.2025
"""

import logging
from PyQt5.QtWidgets import QPushButton, QWidget
from PyQt5.QtCore import pyqtSignal
from pdvm_input_type_base import PdvmInputTypeBase  # ✅ V2-Version!
from pdvm_central_datenbank import PdvmCentralDatenbank
# ✅ V2: GCS wird vom Control durchgereicht (self.control.gcs)

logger = logging.getLogger(__name__)


class PdvmInputTypeViewtable(PdvmInputTypeBase):
    """Input-Type für View-Table-Auswahl (Lookup via View)"""
    
    def __init__(self, parent: QWidget, control_config: dict):
        super().__init__(parent, control_config)
        
        # Viewtable-spezifische Config V3 (aus configs.viewtable)
        configs = self.field_config.get('configs', {})
        viewtable_config = configs.get('viewtable', {})
        
        # V3: key ist die view_guid
        self.viewtable_guid = viewtable_config.get('key', None)
        
        # Display-Wert Cache
        self.display_text = ""
        
        logger.debug(f"    🔍 VIEWTABLE V3-Type erstellt: {self.viewtable_guid[:20] if self.viewtable_guid else 'keine GUID'}...")
    
    def get_target_width(self) -> int:
        """Gibt Breite für Viewtable-Button zurück"""
        # Breiter Button für längere Texte
        return 400
    
    def _format_display_text(self, guid_value):
        """
        Formatiert Display-Text aus GUID
        
        Zeigt vollständige GUID für DB-Verifikation
        """
        if not guid_value:
            return "<Keine Auswahl>"
        
        # Vollständige GUID anzeigen (wichtig für DB-Verifikation!)
        return str(guid_value)
    
    def create_widget(self) -> QWidget:
        """Erstellt Button-Widget für Viewtable-Auswahl"""
        self.widget = QPushButton()
        
        # Initial-Text
        self.display_text = self._format_display_text(self.current_value)
        self.widget.setText(self.display_text)
        
        # Breite setzen
        self.widget.setFixedWidth(self.get_target_width())
        
        # Styling
        if self.read_only:
            self.widget.setEnabled(False)
            self.widget.setStyleSheet("""
                QPushButton {
                    background-color: #ecf0f1;
                    border: 1px solid #bdc3c7;
                    border-radius: 3px;
                    padding: 5px 10px;
                    color: #7f8c8d;
                    text-align: left;
                }
            """)
        else:
            self.widget.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    border: 1px solid #3498db;
                    border-radius: 3px;
                    padding: 5px 10px;
                    color: #2c3e50;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #e8f4f8;
                }
                QPushButton:pressed {
                    background-color: #d0e8f2;
                }
            """)
            # Click-Handler
            self.widget.clicked.connect(self._open_selection_dialog)
        
        return self.widget
    
    def load_value(self, stichtag: float) -> tuple:
        """Lädt GUID-Wert aus DB"""
        if not self.db_instance:
            return (None, None)
        
        try:
            wert, abdatum = self.db_instance.get_value(
                self.gruppe,
                self.feld,
                stichtag
            )
            
            # GUID direkt übernehmen
            self.original_value = wert
            self.current_value = wert
            self.abdatum_wert = abdatum
            
            logger.debug(f"    📊 VIEWTABLE geladen: guid={wert[:20] if wert else 'None'}...")
            return (wert, abdatum)
            
        except Exception as e:
            logger.error(f"    ❌ VIEWTABLE-Fehler beim Laden: {e}")
            return (None, None)
    
    def update_display(self):
        """Aktualisiert Button-Text mit Display-Wert und Styling"""
        if not self.widget:
            return
        
        # Text aktualisieren
        self.display_text = self._format_display_text(self.current_value)
        self.widget.setText(self.display_text)
        
        # Styling basierend auf dirty-Status
        if self._is_dirty:
            # Dirty-Styling (gelb)
            self.widget.setStyleSheet("""
                QPushButton {
                    background-color: #fff9e6;
                    border: 2px solid #f39c12;
                    border-radius: 3px;
                    padding: 5px 10px;
                    color: #2c3e50;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #fef3d6;
                }
            """)
        else:
            # Normal-Styling (weiß)
            self.widget.setStyleSheet("""
                QPushButton {
                    background-color: white;
                    border: 1px solid #3498db;
                    border-radius: 3px;
                    padding: 5px 10px;
                    color: #2c3e50;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #e8f4f8;
                }
                QPushButton:pressed {
                    background-color: #d0e8f2;
                }
            """)
    
    def get_current_value(self):
        """Gibt aktuelle GUID zurück"""
        return self.current_value
    
    def _open_selection_dialog(self):
        """Öffnet Auswahl-Dialog mit AUTONOMER VIEW"""
        logger.info(f"    🔍 Öffne Viewtable-Auswahl: {self.gruppe}.{self.feld}")
        
        try:
            # Prüfe viewtable_guid
            if not self.viewtable_guid:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self.widget,
                    "Fehler",
                    "Keine View-GUID konfiguriert."
                )
                return
            
            # Auswahl-Dialog öffnen (AUTONOME VERSION - ULTRA-EINFACH!)
            from pdvm_input_viewtable_selection_dialog import PdvmInputViewtableSelectionDialog
            
            # ULTRA-EINFACH: Nur viewtable_guid!
            # View holt sich ALLES SELBST aus viewdaten-Tabelle!
            dialog = PdvmInputViewtableSelectionDialog(
                viewtable_guid=self.viewtable_guid,
                current_guid=self.current_value,
                parent=self.widget
            )
            
            result = dialog.exec_()
            
            # Wenn Auswahl getroffen wurde
            if result and dialog.selected_guid:
                new_guid = dialog.selected_guid
                
                # Wert hat sich geändert?
                if new_guid != self.current_value:
                    self.current_value = new_guid
                    self._is_dirty = True
                    
                    # Display aktualisieren (inkl. Dirty-Styling!)
                    self.update_display()
                    
                    logger.info(f"    ✅ Neue Auswahl: {new_guid[:20]}...")
            
        except Exception as e:
            logger.error(f"    ❌ Fehler beim Öffnen des Auswahl-Dialogs: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(
                self.widget,
                "Fehler",
                f"Fehler beim Öffnen der Auswahl:\n{str(e)}"
            )

