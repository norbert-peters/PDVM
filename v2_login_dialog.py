"""
V2.0 Login-Dialog

Login mit Email/Passwort und bcrypt-Verifikation
User-Daten werden einmalig geladen und weitergegeben

AUTOR: Norbert Peters
DATUM: 30.10.2025
VERSION: 1.0
"""

import sys
import sqlite3
import json
import bcrypt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QMessageBox, QApplication
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon


class V2LoginDialog(QDialog):
    """Login-Dialog für V2.0 Authentication"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.user_data = None  # ⭐ User-Daten für Weitergabe
        self.auth_db_path = "Daten/auth.db"
        self.setup_ui()
    
    def setup_ui(self):
        """UI aufbauen"""
        self.setWindowTitle("PDVM V2.0 - Login")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Titel
        title = QLabel("PDVM V2.0")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel("Anmeldung")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)
        
        layout.addSpacing(20)
        
        # Email
        email_label = QLabel("E-Mail:")
        layout.addWidget(email_label)
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("admin@super.de")
        self.email_input.returnPressed.connect(self.on_login_clicked)
        layout.addWidget(self.email_input)
        
        # Passwort
        password_label = QLabel("Passwort:")
        layout.addWidget(password_label)
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Passwort eingeben")
        self.password_input.returnPressed.connect(self.on_login_clicked)
        layout.addWidget(self.password_input)
        
        layout.addSpacing(20)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.login_button = QPushButton("Anmelden")
        self.login_button.setDefault(True)
        self.login_button.clicked.connect(self.on_login_clicked)
        button_layout.addWidget(self.login_button)
        
        cancel_button = QPushButton("Abbrechen")
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(button_layout)
        
        # Info-Text
        layout.addSpacing(20)
        info_label = QLabel(
            "Test-Zugänge:\n"
            "• Admin: admin@super.de / admin\n"
            "• User: user@super.de / user"
        )
        info_label.setStyleSheet("color: gray; font-size: 9pt;")
        layout.addWidget(info_label)
        
        self.setLayout(layout)
        
        # Focus auf Email-Feld
        self.email_input.setFocus()
    
    def on_login_clicked(self):
        """Login-Button geklickt"""
        email = self.email_input.text().strip()
        password = self.password_input.text()
        
        # Validierung
        if not email:
            QMessageBox.warning(self, "Fehler", "Bitte E-Mail eingeben!")
            self.email_input.setFocus()
            return
        
        if not password:
            QMessageBox.warning(self, "Fehler", "Bitte Passwort eingeben!")
            self.password_input.setFocus()
            return
        
        # User-Datenbank öffnen (EINMALIG!)
        try:
            conn = sqlite3.connect(self.auth_db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT * FROM sys_benutzer WHERE benutzer = ?",
                (email,)
            )
            
            user_row = cursor.fetchone()
            conn.close()
            
            if not user_row:
                QMessageBox.warning(
                    self, 
                    "Fehler", 
                    f"Benutzer '{email}' nicht gefunden!"
                )
                self.password_input.clear()
                self.email_input.setFocus()
                return
            
            # Passwort prüfen (bcrypt)
            if not self._verify_password(password, user_row['passwort']):
                QMessageBox.warning(
                    self, 
                    "Fehler", 
                    "Falsches Passwort!"
                )
                self.password_input.clear()
                self.password_input.setFocus()
                return
            
            # ✅ LOGIN ERFOLGREICH!
            # User-Daten parsen und aufbereiten
            self.user_data = {
                'uid': user_row['uid'],
                'email': email,
                'name': user_row['name'],
                'daten': json.loads(user_row['daten'])  # ⭐ JSON parsen!
            }
            
            print(f"✅ Login erfolgreich: {self.user_data['name']} ({email})")
            print(f"   Rollen: {self.user_data['daten']['PERMISSIONS']['ROLES']}")
            print(f"   Mandanten: {self.user_data['daten']['MANDANTEN']['LIST']}")
            
            # Dialog schließen (Daten bleiben in self.user_data)
            self.accept()
            
        except sqlite3.Error as e:
            QMessageBox.critical(
                self, 
                "Datenbank-Fehler", 
                f"Fehler beim Zugriff auf auth.db:\n{e}"
            )
        except Exception as e:
            QMessageBox.critical(
                self, 
                "Fehler", 
                f"Unerwarteter Fehler beim Login:\n{e}"
            )
    
    def _verify_password(self, password: str, hashed: str) -> bool:
        """
        Passwort mit bcrypt verifizieren
        
        Args:
            password: Klartext-Passwort
            hashed: bcrypt-Hash aus Datenbank
        
        Returns:
            True wenn Passwort korrekt
        """
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'), 
                hashed.encode('utf-8')
            )
        except Exception as e:
            print(f"❌ Fehler bei Passwort-Verifikation: {e}")
            return False


# ============================================================================
# TEST
# ============================================================================

def test_login_dialog():
    """Test-Funktion für Login-Dialog"""
    app = QApplication(sys.argv)
    
    print("\n" + "=" * 70)
    print("🔐 V2.0 LOGIN-DIALOG TEST")
    print("=" * 70)
    print("\nTest-Zugänge:")
    print("  • Admin: admin@super.de / admin")
    print("  • User:  user@super.de  / user")
    print("")
    
    dialog = V2LoginDialog()
    
    if dialog.exec_() == QDialog.Accepted:
        print("\n" + "=" * 70)
        print("✅ LOGIN ERFOLGREICH!")
        print("=" * 70)
        print(f"\n👤 User: {dialog.user_data['name']}")
        print(f"📧 Email: {dialog.user_data['email']}")
        print(f"🆔 UID: {dialog.user_data['uid']}")
        print(f"\n📋 Daten:")
        print(json.dumps(dialog.user_data['daten'], indent=2, ensure_ascii=False))
    else:
        print("\n❌ Login abgebrochen")
    
    return 0


if __name__ == '__main__':
    sys.exit(test_login_dialog())
