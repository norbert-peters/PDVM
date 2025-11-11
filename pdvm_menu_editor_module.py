"""
🎯 PDVM Menu-Editor Modul
==========================

ZWECK: Plugin-Modul für generellen Dialog (EDIT_TYPE='menu_editor')

KONZEPT:
- Wird vom generellen Dialog dynamisch geladen
- IDENTISCHE API wie PdvmInputControlsManager
- get_widget() Methode für Dialog-Integration
- Vollständig gekapselt

API (wie input_controls):
- __init__(framedaten_db, selected_guid, main_app=None, gcs=None)
- get_widget() → QWidget
- save_data() → bool (optional)
- has_unsaved_changes() → bool (optional)

LINEAR:
1. Dialog erstellt PdvmMenuEditorModule(framedaten_db, selected_guid, ...)
2. Dialog ruft get_widget()
3. Widget wird in Tab eingefügt
"""

import logging
from typing import Optional
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QMessageBox
from PyQt5.QtCore import QObject, pyqtSignal

# Import des eigentlichen Menu-Editor-Widgets
from pdvm_menu_editor_widget import PdvmMenuEditorWidget

# GCS global
from pdvm_central_systemsteuerung import get_gcs

logger = logging.getLogger(__name__)


class PdvmMenuEditorModule(QObject):
    """
    🎯 Menu-Editor Modul (Plugin für generellen Dialog)
    
    IDENTISCHE API wie PdvmInputControlsManager:
    - Erbt von QObject (nicht QWidget!)
    - __init__(framedaten_db, selected_guid, main_app=None, gcs=None)
    - get_widget() → QWidget
    - Signals: refresh_requested, save_completed
    """
    
    refresh_requested = pyqtSignal()
    save_completed = pyqtSignal()
    
    def __init__(self, framedaten_db, selected_guid: str, main_app=None, gcs=None):
        """
        Initialisiert Menu-Editor Modul
        
        Args:
            framedaten_db: Framedaten-DB (für Metadaten - wird bei menu_editor nicht genutzt)
            selected_guid: GUID des ausgewählten Menüs (aus View)
            main_app: OPTIONAL - Referenz zur MainApp
            gcs: OPTIONAL - GCS-Instanz (wenn None, wird get_gcs() verwendet)
        """
        super().__init__()
        
        logger.info("🎯 === MENU-EDITOR MODUL (Plugin für Dialog) ===")
        
        self.framedaten_db = framedaten_db  # Kompatibilität (ungenutzt)
        self.selected_guid = selected_guid
        self.main_app = main_app
        
        # GCS holen (entweder als Parameter oder via get_gcs)
        self.gcs = gcs if gcs is not None else get_gcs()
        if not self.gcs:
            raise RuntimeError("❌ GCS nicht initialisiert!")
        
        logger.info(f"  📋 Selected-GUID (Menü): {self.selected_guid}")
        
        # Widget-Instanz (wird in get_widget() erstellt)
        self.editor_widget: Optional[PdvmMenuEditorWidget] = None
        self.main_widget: Optional[QWidget] = None
    
    def get_widget(self) -> QWidget:
        """
        🎨 Erstellt und gibt das Haupt-Widget zurück
        
        WICHTIG: Identische API wie PdvmInputControlsManager!
        
        Returns:
            QWidget: Haupt-Widget mit Menu-Editor
        """
        logger.info("🎨 Erstelle Menu-Editor Widget...")
        
        # Haupt-Widget erstellen
        self.main_widget = QWidget()
        layout = QVBoxLayout(self.main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        try:
            # Menu-Editor-Widget erstellen und einbetten
            self.editor_widget = PdvmMenuEditorWidget(
                menu_guid=self.selected_guid,
                parent=self.main_widget
            )
            
            # Signals weiterleiten
            if hasattr(self.editor_widget, 'data_changed'):
                self.editor_widget.data_changed.connect(self._on_data_changed)
            
            layout.addWidget(self.editor_widget)
            
            logger.info("✅ Menu-Editor Widget erfolgreich erstellt")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen des Menu-Editors: {e}", exc_info=True)
            
            # Fehler-Widget anzeigen
            from PyQt5.QtWidgets import QLabel
            from PyQt5.QtCore import Qt
            
            error_label = QLabel()
            error_label.setWordWrap(True)
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setStyleSheet("""
                QLabel {
                    background-color: #f8d7da;
                    border: 2px solid #dc3545;
                    border-radius: 5px;
                    padding: 30px;
                    font-size: 12pt;
                    color: #721c24;
                }
            """)
            error_label.setText(
                f"❌ FEHLER BEIM LADEN DES MENU-EDITORS\n\n"
                f"Fehler: {str(e)}\n\n"
                f"GUID: {self.selected_guid}\n\n"
                f"Bitte prüfen Sie die Log-Datei für Details."
            )
            
            layout.addWidget(error_label)
        
        return self.main_widget
    
    def _on_data_changed(self):
        """Handler für data_changed Signal vom Widget"""
        logger.debug("📝 Daten geändert im Menu-Editor")
    
    def save_data(self) -> bool:
        """
        Speichert Daten (wird vom Dialog beim Speichern aufgerufen)
        
        Returns:
            bool: True bei Erfolg
        """
        if not self.editor_widget:
            logger.warning("⚠️ Kein Editor-Widget vorhanden")
            return False
        
        try:
            success = self.editor_widget.save_data()
            
            if success:
                logger.info("✅ Menu-Editor Daten gespeichert")
            else:
                logger.warning("⚠️ Speichern fehlgeschlagen oder abgebrochen")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Fehler beim Speichern",
                f"Daten konnten nicht gespeichert werden:\n{str(e)}"
            )
            return False
    
    def has_unsaved_changes(self) -> bool:
        """
        Prüft ob ungespeicherte Änderungen vorhanden
        
        Returns:
            bool: True wenn Änderungen vorhanden
        """
        if not self.editor_widget:
            return False
        
        return self.editor_widget.has_unsaved_changes()
    
    def undo_changes(self):
        """Verwirft alle Änderungen"""
        if self.editor_widget:
            self.editor_widget.undo_changes()


# ============================================================================
# Modul-Info für dynamisches Laden
# ============================================================================

MODULE_INFO = {
    'name': 'Menu-Editor',
    'version': '1.0.0',
    'description': 'Editor für PDVM Menüstrukturen (Vertikal/Grund/Zusatz)',
    'edit_type': 'menu_editor',
    'requires_selection': True,
    'supports_save': True,
    'supports_undo': True
}
