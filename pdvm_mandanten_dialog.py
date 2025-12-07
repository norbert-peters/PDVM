"""
V2.0 Mandanten-Auswahl Dialog

Zeigt Mandanten-Liste und lässt User einen Mandanten wählen

AUTOR: Norbert Peters
DATUM: 30.10.2025
VERSION: 1.0
"""

import sys
import sqlite3
import json
import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
    QPushButton, QMessageBox, QApplication, QGroupBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

# User-Datenbank und Password-Change-Dialog
from pdvm_user_db import PdvmUserDatenbank
from pdvm_password_change_dialog import PasswordChangeDialog

logger = logging.getLogger(__name__)


class V2MandantenDialog(QDialog):
    """Mandanten-Auswahl Dialog"""
    
    def __init__(self, user_data: dict, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.selected_mandant = None
        self.auth_db_path = "Daten/auth.db"
        self.setup_ui()
    
    def setup_ui(self):
        """UI aufbauen"""
        # 🔐 PHASE 1.3: Passwort-Änderung erzwingen wenn FLAG gesetzt
        user_email = self.user_data.get('email', self.user_data.get('benutzer', ''))
        
        try:
            user_db = PdvmUserDatenbank()
            
            # Prüfen ob Passwort-Änderung erforderlich
            if user_db.check_password_change_required(user_email):
                logger.info(f"🔐 Passwort-Änderung erforderlich für User: {user_email}")
                
                # Passwort-Änderungs-Dialog ERZWINGEN
                pw_dialog = PasswordChangeDialog(
                    benutzer=user_email,  # KORRIGIERT: benutzer statt user_email
                    force_change=True,
                    parent=self
                )
                
                result = pw_dialog.exec_()
                
                if result != QDialog.Accepted:
                    # User hat Abbrechen gedrückt → Login-Vorgang abbrechen
                    logger.warning(f"⚠️ User {user_email} hat Passwort-Änderung abgebrochen")
                    QMessageBox.warning(
                        self,
                        "Passwort-Änderung erforderlich",
                        "Sie müssen Ihr Passwort ändern, bevor Sie fortfahren können.\n\n"
                        "Der Login-Vorgang wird abgebrochen."
                    )
                    self.reject()  # Dialog schließen ohne Mandanten-Auswahl
                    return
                    
                logger.info(f"✅ Passwort erfolgreich geändert für User: {user_email}")
                
        except Exception as e:
            logger.error(f"❌ Fehler bei Passwort-Änderung-Check: {e}")
        
        # Standard-UI aufbauen (nur wenn Passwort OK)
        self.setWindowTitle("Mandant auswählen")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Titel
        title = QLabel(f"Willkommen, {self.user_data['name']}!")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        layout.addSpacing(10)
        
        # Anweisung
        instruction = QLabel("Bitte wählen Sie einen Mandanten:")
        layout.addWidget(instruction)
        
        # Mandanten-Dropdown
        self.combo_mandanten = QComboBox()
        self.combo_mandanten.setMinimumHeight(40)
        
        # Mandanten-Liste aus User-Daten holen
        mandanten_list = self.user_data['daten']['MANDANTEN']['LIST']
        default_mandant = self.user_data['daten']['MANDANTEN'].get('DEFAULT')
        
        if not mandanten_list:
            QMessageBox.warning(
                self,
                "Fehler",
                "Keine Mandanten für diesen Benutzer verfügbar!"
            )
            self.reject()
            return
        
        # Dropdown befüllen
        default_index = 0
        for idx, mandant_guid in enumerate(mandanten_list):
            mandant_info = self._load_mandant_info(mandant_guid)
            
            # Anzeige: "Hauptverwaltung (mandant_001)"
            display_text = f"{mandant_info['name']} ({mandant_info['mandant_id']})"
            self.combo_mandanten.addItem(display_text, mandant_guid)
            
            # Default vormerken
            if mandant_guid == default_mandant:
                default_index = idx
        
        # Default vorauswählen
        self.combo_mandanten.setCurrentIndex(default_index)
        
        layout.addWidget(self.combo_mandanten)
        
        layout.addSpacing(20)
        
        # OK-Button
        ok_button = QPushButton("Mandant auswählen")
        ok_button.setDefault(True)
        ok_button.setMinimumHeight(40)
        ok_button.clicked.connect(self.on_mandant_selected)
        layout.addWidget(ok_button)
        
        # Info-Text
        info_text = f"Verfügbare Mandanten: {len(mandanten_list)}"
        info_label = QLabel(info_text)
        info_label.setStyleSheet("color: gray; font-size: 9pt;")
        info_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(info_label)
        
        self.setLayout(layout)
    
    def _load_mandant_info(self, mandant_guid: str) -> dict:
        """
        Lädt Mandanten-Info aus sys_mandanten (kurze Version)
        
        Args:
            mandant_guid: GUID aus sys_mandanten.uid
        
        Returns:
            {'name': 'Hauptverwaltung', 'mandant_id': 'mandant_001', ...}
        """
        try:
            conn = sqlite3.connect(self.auth_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM sys_mandanten WHERE uid = ?",
                (mandant_guid,)
            )
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                daten = json.loads(row['daten'])
                return {
                    'name': daten['ROOT']['BEZEICHNUNG'],
                    'db_name': daten['ROOT']['DB_NAME'],
                    'mandant_id': daten['METADATEN']['MANDANT_ID'],  # ⭐ Aus Daten!
                    'status': daten['METADATEN']['STATUS'],
                    'country': daten['METADATEN']['COUNTRY']
                }
            else:
                # Fallback wenn Mandant nicht in DB
                return {
                    'name': mandant_guid,
                    'db_name': mandant_guid,
                    'mandant_id': 'unknown',
                    'status': 'unbekannt',
                    'country': 'DEU'
                }
        
        except Exception as e:
            print(f"⚠️ Fehler beim Laden von Mandant {mandant_guid}: {e}")
            return {
                'name': mandant_guid,
                'db_name': mandant_guid,
                'mandant_id': 'error',
                'status': 'fehler',
                'country': 'DEU'
            }
    
    def _load_mandant_data(self, mandant_guid: str) -> dict:
        """
        Lädt KOMPLETTE Mandanten-Daten für GCS
        
        Args:
            mandant_guid: GUID aus sys_mandanten.uid
        
        Returns:
            Komplettes JSON aus sys_mandanten.daten
        """
        try:
            conn = sqlite3.connect(self.auth_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT daten FROM sys_mandanten WHERE uid = ?",
                (mandant_guid,)
            )
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return json.loads(row['daten'])
            else:
                raise ValueError(f"Mandant {mandant_guid} nicht gefunden!")
        
        except Exception as e:
            print(f"❌ Fehler beim Laden von Mandanten-Daten: {e}")
            raise
    
    def on_mandant_selected(self):
        """Mandant wurde ausgewählt"""
        self.selected_mandant = self.combo_mandanten.currentData()
        
        mandant_info = self._load_mandant_info(self.selected_mandant)
        
        print(f"✅ Mandant gewählt: {self.selected_mandant}")
        print(f"   Name: {mandant_info['name']}")
        print(f"   DB-Name: {mandant_info['db_name']}")
        print(f"   Status: {mandant_info['status']}")
        
        self.accept()


# ============================================================================
# TEST
# ============================================================================

def test_mandanten_dialog():
    """Test-Funktion für Mandanten-Dialog"""
    app = QApplication(sys.argv)
    
    # Mock User-Daten (wie von Login-Dialog)
    user_data = {
        'uid': 'test-uid-123',
        'email': 'admin@super.de',
        'name': 'Norbert Peters',
        'daten': {
            'MANDANTEN': {
                'LIST': ['mandant_001', 'mandant_002'],
                'DEFAULT': 'mandant_001'
            },
            'PERMISSIONS': {
                'ROLES': ['admin']
            }
        }
    }
    
    print("\n" + "=" * 70)
    print("🏢 V2.0 MANDANTEN-DIALOG TEST")
    print("=" * 70)
    print(f"\nUser: {user_data['name']}")
    print(f"Verfügbare Mandanten: {user_data['daten']['MANDANTEN']['LIST']}")
    print("")
    
    dialog = V2MandantenDialog(user_data)
    
    if dialog.exec_() == QDialog.Accepted:
        print("\n" + "=" * 70)
        print("✅ MANDANT AUSGEWÄHLT!")
        print("=" * 70)
        print(f"\nMandant-ID: {dialog.selected_mandant}")
    else:
        print("\n❌ Mandanten-Auswahl abgebrochen")
    
    return 0


if __name__ == '__main__':
    sys.exit(test_mandanten_dialog())
