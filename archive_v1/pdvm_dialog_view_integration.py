# pdvm_dialog_view_integration.py
"""
Integration des modernen View-Widgets in das Dialog-System
Lädt automatisch die view_guid aus den framedaten
"""

import logging
import json
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSplitter
from PyQt5.QtCore import Qt, pyqtSignal

from pdvm_central_datenbank import PdvmCentralDatenbank
from pdvm_modern_view_widget import PdvmModernViewWidget

logger = logging.getLogger(__name__)

class PdvmDialogViewWidget(QWidget):
    """
    Dialog-integrierte Version des modernen View-Widgets
    Lädt automatisch die view_guid aus den framedaten
    """
    
    # Signals
    rowSelected = pyqtSignal(dict)  # Wenn eine Zeile ausgewählt wird
    editRequested = pyqtSignal(dict)  # Wenn Bearbeitung angefordert wird
    newRequested = pyqtSignal()     # Wenn neuer Datensatz angefordert wird
    
    def __init__(self, frame_guid, user_guid=None, parent=None):
        super().__init__(parent)
        
        self.frame_guid = frame_guid
        self.user_guid = user_guid
        self.frame_data = None
        self.view_guid = None
        self.root_table = None
        self.view_widget = None
        
        self._load_frame_configuration()
        self._setup_ui()
        
    def _load_frame_configuration(self):
        """Lädt die Frame-Konfiguration und extrahiert view_guid und root_table"""
        try:
            # Framedaten laden
            db = PdvmCentralDatenbank(
                db_name="PdvmManager.db", 
                table_name="framedaten",
                guid=self.frame_guid
            )
            
            raw_data = db.lesen()
            if not raw_data:
                logger.error(f"❌ Keine framedaten für GUID {self.frame_guid} gefunden")
                return False
            
            self.frame_data = raw_data
            
            # Nur view_guid und root_table aus framedaten extrahieren
            if isinstance(self.frame_data, dict):
                self.view_guid = (
                    self.frame_data.get("view_guid") or
                    self.frame_data.get("viewguid")
                )
                
                self.root_table = (
                    self.frame_data.get("root_table") or
                    self.frame_data.get("table_name") or
                    self.frame_data.get("table")
                )
            
            if self.view_guid:
                logger.info(f"✅ View-GUID aus framedaten geladen: {self.view_guid}")
                if self.root_table:
                    logger.info(f"✅ Root-Tabelle aus framedaten geladen: {self.root_table}")
                return True
            else:
                logger.warning(f"⚠️ Keine view_guid in framedaten {self.frame_guid} gefunden")
                logger.debug(f"Verfügbare Schlüssel in framedaten: {list(self.frame_data.keys()) if isinstance(self.frame_data, dict) else 'Nicht-Dict-Struktur'}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Frame-Konfiguration: {e}")
            return False
    
    def _setup_ui(self):
        """Erstellt die Benutzeroberfläche"""
        layout = QVBoxLayout(self)
        
        # Header mit Titel und Aktions-Buttons
        header_layout = QHBoxLayout()
        
        # Titel aus viewdaten laden (falls verfügbar), sonst Standard
        title = "Datenansicht"
        if self.view_guid:
            try:
                from pdvm_central_datenbank import PdvmCentralDatenbank
                view_db = PdvmCentralDatenbank(
                    db_name="PdvmManager.db",
                    table_name="viewdaten",
                    guid=self.view_guid
                )
                view_data = view_db.lesen()
                if view_data and isinstance(view_data, dict):
                    title = (
                        view_data.get("title") or 
                        view_data.get("name") or 
                        view_data.get("view_title") or
                        f"Ansicht: {self.root_table}" if self.root_table else "Datenansicht"
                    )
            except Exception as e:
                logger.debug(f"Titel aus viewdaten nicht verfügbar: {e}")
                title = f"Ansicht: {self.root_table}" if self.root_table else "Datenansicht"
        
        title_label = QLabel(f"📊 {title}")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50; padding: 10px;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Action Buttons
        self.btn_new = QPushButton("➕ Neu")
        self.btn_new.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        self.btn_new.clicked.connect(self._on_new_clicked)
        header_layout.addWidget(self.btn_new)
        
        self.btn_edit = QPushButton("✏️ Bearbeiten")
        self.btn_edit.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
            }
        """)
        self.btn_edit.clicked.connect(self._on_edit_clicked)
        self.btn_edit.setEnabled(False)  # Erst nach Selektion aktivieren
        header_layout.addWidget(self.btn_edit)
        
        layout.addLayout(header_layout)
        
        # View-Widget einbetten (falls view_guid verfügbar)
        if self.view_guid:
            try:
                self.view_widget = PdvmModernViewWidget(
                    view_guid=self.view_guid,
                    user_guid=self.user_guid,
                    parent=self
                )
                
                # Signal-Verbindungen
                self.view_widget.rowSelected.connect(self._on_row_selected)
                
                layout.addWidget(self.view_widget, 1)
                
                logger.info(f"✅ Modernes View-Widget für Frame {self.frame_guid} geladen")
                logger.info(f"🔗 Verknüpft mit view_guid: {self.view_guid}")
                if self.root_table:
                    logger.info(f"📋 Root-Tabelle: {self.root_table}")
                
            except Exception as e:
                logger.error(f"❌ Fehler beim Laden des View-Widgets: {e}")
                self._show_error_message(f"Fehler beim Laden der Datenansicht: {str(e)}")
        else:
            self._show_error_message("Keine View-GUID in den Framedaten gefunden")
    
    def _show_error_message(self, message):
        """Zeigt eine Fehlermeldung an"""
        error_label = QLabel(f"❌ {message}")
        error_label.setStyleSheet("""
            color: #e74c3c;
            font-size: 14px;
            padding: 20px;
            border: 2px dashed #e74c3c;
            border-radius: 8px;
            background-color: #fdeaea;
        """)
        error_label.setAlignment(Qt.AlignCenter)
        self.layout().addWidget(error_label)
    
    def _on_row_selected(self, record):
        """Wird aufgerufen wenn eine Zeile im View-Widget ausgewählt wird"""
        logger.info(f"🔘 Datensatz in Dialog-View ausgewählt: {record.get('_guid', 'Unbekannt')}")
        
        # Edit-Button aktivieren
        self.btn_edit.setEnabled(True)
        
        # Signal weiterleiten
        self.rowSelected.emit(record)
    
    def _on_new_clicked(self):
        """Wird aufgerufen wenn 'Neu' geklickt wird"""
        logger.info("➕ Neuer Datensatz angefordert")
        self.newRequested.emit()
    
    def _on_edit_clicked(self):
        """Wird aufgerufen wenn 'Bearbeiten' geklickt wird"""
        if self.view_widget and hasattr(self.view_widget, 'get_selected_record'):
            selected = self.view_widget.get_selected_record()
            if selected:
                logger.info(f"✏️ Bearbeitung angefordert für: {selected.get('_guid', 'Unbekannt')}")
                self.editRequested.emit(selected)
        else:
            logger.warning("⚠️ Kein Datensatz für Bearbeitung ausgewählt")
    
    def refresh_data(self):
        """Aktualisiert die Datenansicht"""
        if self.view_widget:
            self.view_widget._load_data()
            logger.info("🔄 Datenansicht aktualisiert")
    
    def get_frame_guid(self):
        """Gibt die Frame-GUID zurück"""
        return self.frame_guid
    
    def get_view_guid(self):
        """Gibt die View-GUID zurück"""
        return self.view_guid


def integrate_view_into_dialog(frame_guid, user_guid=None):
    """
    Hilfsfunktion zur Integration des View-Widgets in bestehende Dialoge
    Kann in pdvm_dialog() verwendet werden
    """
    try:
        dialog_view = PdvmDialogViewWidget(
            frame_guid=frame_guid,
            user_guid=user_guid
        )
        
        logger.info(f"✅ Dialog-View-Integration erfolgreich für Frame: {frame_guid}")
        return dialog_view
        
    except Exception as e:
        logger.error(f"❌ Fehler bei Dialog-View-Integration: {e}")
        return None


if __name__ == "__main__":
    # Test der Dialog-View-Integration
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Test mit Standard-Frame
    test_frame_guid = "4078079f-4028-45ed-879c-3c779ecf3d0d"
    
    widget = PdvmDialogViewWidget(
        frame_guid=test_frame_guid,
        user_guid="test-user"
    )
    
    widget.setWindowTitle("🔗 Dialog-View Integration Test")
    widget.resize(1000, 700)
    widget.show()
    
    sys.exit(app.exec_())
