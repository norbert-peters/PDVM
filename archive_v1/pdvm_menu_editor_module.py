#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🎯 PDVM MENÜ-EDITOR MODULE - Wrapper für Generellen Dialog

Integriert den bestehenden Menü-Editor (pdvm_menu_editor.py) in den
Generellen Dialog als Edit-Modul.

ARCHITEKTUR:
- Wrapper-Klasse für Integration in edit_modules Registry
- Verwendet bestehenden PdvmMenuEditor
- GUID des Datensatzes = Menü-GUID (menu_type)
- Keine Controls, sondern direkter Menü-Editor

VERWENDUNG:
```python
# In pdvm_genereller_dialog.py Registry:
self.edit_modules = {
    'menu_editor': 'pdvm_menu_editor_module.PdvmMenuEditorModule',
    ...
}
```

FRAMEDATEN KONFIGURATION:
- ROOT_TABLE: 'menue' (oder entsprechende Menü-Tabelle)
- VIEW_GUID: View mit allen Menüs
- EDIT_TYPE: 'menu_editor'
- DIALOG_GUID: Eindeutige GUID für diesen Dialog

Autor: Norbert Peters
Datum: 28.10.2025
Version: 1.0 (Initiale Integration)
"""

import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from PyQt5.QtCore import pyqtSignal

from global_gcs import gcs

logger = logging.getLogger(__name__)


class PdvmMenuEditorModule(QWidget):
    """
    Wrapper-Modul für Menü-Editor Integration
    
    EINFACHE API (wie bei PdvmInputControlsManager):
    - __init__(framedaten_db, selected_guid)
    - get_widget() → gibt Widget zurück
    - Signale: refresh_requested, save_completed
    """
    
    # Signale (Kompatibilität mit Generellem Dialog)
    refresh_requested = pyqtSignal()
    save_completed = pyqtSignal()
    
    def __init__(self, framedaten_db, selected_guid, main_app=None, parent=None):
        """
        Initialisiert Menü-Editor Modul
        
        Args:
            framedaten_db: PdvmCentralDatenbank-Instanz mit Framedaten
            selected_guid: GUID des ausgewählten Menüs (= menu_type)
            main_app: Referenz zur MainAppComplete (ERFORDERLICH für menu_handler.menu)
            parent: Parent-Widget (optional)
        """
        super().__init__(parent)
        
        logger.info("🎯 === MENÜ-EDITOR MODULE - INITIALISIERUNG ===")
        logger.info(f"📋 Selected GUID (Menu-Type): {selected_guid}")
        
        # GCS-Zugriff prüfen
        if not gcs or not gcs.is_initialized:
            raise RuntimeError("❌ GCS muss initialisiert sein!")
        
        self.framedaten_db = framedaten_db
        self.selected_guid = selected_guid  # = menu_type
        self.main_app = main_app  # ✅ Direkt gespeichert statt Widget-Hierarchie!
        self.gcs = gcs
        
        logger.info(f"  🔗 MainApp-Referenz: {'✅ Verfügbar' if self.main_app else '❌ Fehlt'}")
        
        # Menü-Editor Widget (wird in _init_editor erstellt)
        self.menu_editor = None
        
        # Initialisierung
        try:
            self._init_editor()
            logger.info("✅ Menü-Editor Module erfolgreich initialisiert")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Menü-Editor-Initialisierung: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    def _init_editor(self):
        """Initialisiert den Menü-Editor"""
        logger.info("🔧 Initialisiere Menü-Editor...")
        
        try:
            # Lazy Import des bestehenden Menü-Editors
            from pdvm_menu_editor import PdvmMenuEditor
            from pdvm_central_datenbank import PdvmCentralDatenbank
            import json
            
            # ✅ main_app DIREKT verwenden (statt Widget-Hierarchie!)
            if not self.main_app:
                logger.error("❌ main_app nicht übergeben!")
                raise RuntimeError("main_app fehlt - Dialog muss main_app Parameter übergeben")
            
            logger.info(f"  ✅ main_app vorhanden: {type(self.main_app).__name__}")
            
            # 🎯 KORRIGIERT: Verwende PdvmMenu (verarbeitet Templates automatisch!)
            logger.info(f"  🔧 Lade Menü mit Template-Verarbeitung: {self.selected_guid}")
            
            from pdvm_menu import PdvmMenu
            
            # PdvmMenu lädt Daten UND verarbeitet Templates automatisch
            menu_instance = PdvmMenu(self.selected_guid)
            logger.info(f"  ✅ PdvmMenu erfolgreich geladen (mit Template-Verarbeitung)")
            
            # Layout für Widget
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            
            # Bestehenden PdvmMenuEditor einbetten mit PdvmMenu-Instanz
            self.menu_editor = PdvmMenuEditor(
                parent=self,
                menu_instance=menu_instance,
                menu_type='ROOT',  # ✅ WORKAROUND: Einfacher Pfad statt GUID
                main_app=self.main_app,
                call_path=None
            )
            
            layout.addWidget(self.menu_editor)
            
            logger.info("  ✅ PdvmMenuEditor erfolgreich eingebettet (WORKAROUND aktiv)")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Editor-Initialisierung: {e}")
            import traceback
            logger.error(traceback.format_exc())
            raise
    
    def get_widget(self):
        """
        Gibt das Widget für Anzeige im Dialog zurück
        
        Returns:
            QWidget: Menü-Editor Widget
        """
        logger.info("📦 get_widget() aufgerufen")
        return self
    
    def refresh(self):
        """
        Refresht den Menü-Editor (z.B. nach Speicherung)
        
        WICHTIG: Wird vom Generellen Dialog aufgerufen wenn
                 refresh_requested Signal emittiert wurde
        """
        logger.info("🔄 refresh() aufgerufen")
        
        # TODO: Menü-Editor neu laden
        logger.warning("⚠️ TODO: Menü-Editor refresh() implementieren")
    
    def save(self):
        """
        Speichert Menü-Änderungen
        
        HINWEIS: Der bestehende PdvmMenuEditor hat eigenen Save-Button
                 Diese Methode ist optional für externen Save-Trigger
        """
        logger.info("💾 save() aufgerufen")
        
        # TODO: Save-Logik des bestehenden Editors aufrufen
        # oder über dessen save_changes() Methode
        logger.warning("⚠️ TODO: Menü-Editor save() implementieren")
        
        # Nach erfolgreichem Speichern:
        # self.save_completed.emit()
