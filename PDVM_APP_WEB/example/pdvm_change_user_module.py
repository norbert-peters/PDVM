# -*- coding: utf-8 -*-
"""
Change User Editor Module - Plugin für Generellen Dialog

Wrapper-Modul das PdvmChangeUserDialog in die Plugin-API integriert.

API (identisch mit anderen Modulen):
- __init__(framedaten_db, selected_guid, main_app=None, gcs=None)
- get_widget() → QWidget
- Signals: refresh_requested, save_completed

AUTOR: Norbert Peters
DATUM: 07.12.2025
VERSION: 1.0
"""
import logging
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import QObject, pyqtSignal, Qt

from pdvm_change_user_dialog import ChangeUserDialog
from pdvm_user_db import PdvmUserDatenbank

logger = logging.getLogger(__name__)


class PdvmChangeUserModule(QObject):
    """
    Change User Editor Modul (Plugin für generellen Dialog)
    
    IDENTISCHE API wie andere Module:
    - Erbt von QObject
    - get_widget() → QWidget
    - Signals: refresh_requested, save_completed
    """
    
    refresh_requested = pyqtSignal()
    save_completed = pyqtSignal()
    
    def __init__(self, framedaten_db, selected_guid: str, main_app=None, gcs=None):
        """
        Initialisiert das Change User Modul
        
        Args:
            framedaten_db: Frame-Datenbank Instanz (nicht verwendet, für API-Kompatibilität)
            selected_guid: GUID des ausgewählten Benutzers
            main_app: Main Application Referenz
            gcs: Global Central Systemsteuerung (nicht verwendet, für API-Kompatibilität)
        """
        super().__init__()
        
        self.selected_guid = selected_guid
        self.main_app = main_app
        self.user_db = PdvmUserDatenbank()
        
        logger.info(f"🔐 PdvmChangeUserModule initialisiert: {selected_guid}")
        
        # Widget wird lazy erstellt (erst bei get_widget())
        self._widget = None
    
    def get_widget(self) -> QWidget:
        """
        Gibt das Widget für Anzeige im Dialog zurück
        
        Returns:
            QWidget: Change User Editor Widget
        """
        if self._widget is not None:
            logger.info("📦 get_widget(): Widget bereits erstellt")
            return self._widget
        
        logger.info("📦 get_widget(): Erstelle neues Widget")
        
        # Hole Benutzer-Email aus selected_guid via PdvmDatenbank
        from pdvm_datenbank import PdvmDatenbank
        db = PdvmDatenbank(table_name='sys_benutzer')
        benutzer_email = db.get_spalte(self.selected_guid, 'benutzer')
        
        if not benutzer_email:
            logger.error(f"❌ Keine Email für GUID {self.selected_guid} gefunden!")
            # Leeres Widget als Fallback
            widget = QWidget()
            layout = QVBoxLayout(widget)
            layout.addWidget(QLabel(f"❌ Benutzer nicht gefunden: {self.selected_guid}"))
            return widget
        
        # Container-Widget erstellen
        self._widget = QWidget()
        layout = QVBoxLayout(self._widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # ChangeUserDialog als Widget einbetten (ohne Dialog-Rahmen)
        self.editor = ChangeUserDialog(
            benutzer_email, 
            self.user_db, 
            parent=self._widget,
            user_guid=self.selected_guid
        )
        
        # Dialog-Fenster-Flags entfernen (als Widget anzeigen)
        self.editor.setWindowFlags(Qt.Widget)
        
        # Save-Button umbiegen: Nicht schließen, sondern nur speichern
        self.editor.btn_save.clicked.disconnect()
        self.editor.btn_save.clicked.connect(self._on_save_clicked)
        
        # In Layout einfügen
        layout.addWidget(self.editor)
        
        logger.info(f"✅ Change User Widget erstellt für: {benutzer_email}")
        
        return self._widget
    
    def _on_save_clicked(self):
        """Handler für Save-Button - speichert ohne Dialog zu schließen"""
        logger.info("💾 Save-Button geklickt (Modul-Handler)")
        
        # Übernehmen-Aktion ausführen (kopiert UI → work_data)
        self.editor._save_data_from_ui()
        
        # Validierung
        if not self.editor.work_data.get('USER', {}).get('NAME'):
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self._widget, "Fehler", "Name darf nicht leer sein!")
            return
        
        if not self.editor.work_data.get('USER', {}).get('VORNAME'):
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.warning(self._widget, "Fehler", "Vorname darf nicht leer sein!")
            return
        
        # In DB speichern
        try:
            # 1. Email-Update (falls geändert) via set_spalte()
            neue_email = self.editor.work_data.get('USER', {}).get('EMAIL', '').strip()
            if neue_email and neue_email != self.editor.benutzer_email:
                # Email hat sich geändert - Update via PdvmDatenbank
                from pdvm_datenbank import PdvmDatenbank
                db = PdvmDatenbank(table_name='sys_benutzer')
                db.set_spalte(self.selected_guid, 'benutzer', neue_email)
                logger.info(f"✅ Email aktualisiert: {self.editor.benutzer_email} → {neue_email}")
                # Aktuelle Email aktualisieren für save_all_data()
                self.editor.benutzer_email = neue_email
            
            # 2. JSON-Daten speichern (mit aktueller Email)
            success = self.user_db.save_all_data(self.editor.benutzer_email, self.editor.work_data)
            if success:
                logger.info(f"✅ User-Daten gesichert für {self.editor.benutzer_email}")
                
                # Original-Daten aktualisieren (für "Änderungen verworfen")
                self.editor.original_data = self.editor.work_data.copy()
                
                # Signal emittieren
                self.save_completed.emit()
                
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.information(self._widget, "Erfolg", "Änderungen wurden gespeichert!")
            else:
                from PyQt5.QtWidgets import QMessageBox
                QMessageBox.critical(self._widget, "Fehler", "Fehler beim Speichern!")
        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(self._widget, "Fehler", f"Fehler beim Speichern:\n{e}")
    
    def save_data(self) -> bool:
        """
        Speichert Änderungen (optional - wird vom Dialog selbst gemacht)
        
        Returns:
            bool: True wenn erfolgreich
        """
        logger.info("💾 save_data() aufgerufen")
        
        if hasattr(self, 'editor') and self.editor:
            # Editor hat eigenen Save-Mechanismus via "Sichern" Button
            # Hier könnten wir prüfen ob es ungespeicherte Änderungen gibt
            logger.info("✅ Änderungen über Dialog-Button speichern")
            return True
        
        return False
    
    def has_unsaved_changes(self) -> bool:
        """
        Prüft ob es ungespeicherte Änderungen gibt (optional)
        
        Returns:
            bool: True wenn ungespeicherte Änderungen vorhanden
        """
        # TODO: Implementieren wenn Editor has_changes Flag hat
        return False
    
    def undo_changes(self):
        """Verwirft alle Änderungen (optional)"""
        logger.info("↩️ undo_changes() aufgerufen")
        
        if hasattr(self, 'editor') and self.editor:
            # TODO: Editor zurücksetzen
            logger.warning("⚠️ TODO: undo_changes implementieren")


# ============================================================================
# Modul-Info für dynamisches Laden
# ============================================================================

MODULE_INFO = {
    'name': 'Change User',
    'version': '1.0.0',
    'description': 'Benutzerverwaltung (Name, Rollen, Berechtigungen)',
    'edit_type': 'change_user',
    'requires_selection': True,
    'supports_save': True,
    'supports_undo': False
}
