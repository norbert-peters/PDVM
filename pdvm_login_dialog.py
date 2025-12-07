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

# bcrypt Import mit Fallback
try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    print("⚠️ bcrypt nicht verfügbar - verwende einfachen Hash-Vergleich")
    BCRYPT_AVAILABLE = False

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QMessageBox, QApplication, QCheckBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon, QPixmap

# User-Datenbank für Security-Features
from pdvm_user_db import PdvmUserDatenbank


class V2LoginDialog(QDialog):
    """Login-Dialog für V2.0 Authentication"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.user_data = None  # ⭐ User-Daten für Weitergabe
        self.auth_db_path = "Daten/auth.db"
        self.setup_ui()
    
    def setup_ui(self):
        """UI aufbauen - Alte Optik aus pdvm_login.py"""
        self.setWindowTitle("Anmeldung im PDVM System")
        self.setFixedSize(470, 330)
        self.setModal(True)
        
        # Fenster-Flags für Vordergrund
        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint | Qt.WindowSystemMenuHint)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Titel mit Styling - KOMPAKT
        title = QLabel("🔐 Anmeldung im PDVM System")
        title_font = QFont("Segoe UI", 14, QFont.Bold)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                padding: 29px 10px;
                background-color: #ecf0f1;
                border-radius: 8px;
                border: 2px solid #3498db;
            }
        """)
        layout.addWidget(title)
        
        layout.addSpacing(10)
        
        # Email
        email_label = QLabel("E-Mail:")
        email_label.setMinimumWidth(100)
        layout.addWidget(email_label)
        layout.addSpacing(-10)  # Weniger Abstand zum Feld
        
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("E-Mail eingeben...")
        self.email_input.returnPressed.connect(self.on_login_clicked)
        layout.addWidget(self.email_input)
        
        # Passwort
        password_label = QLabel("Passwort:")
        password_label.setMinimumWidth(100)
        layout.addWidget(password_label)
        layout.addSpacing(-10)  # Weniger Abstand zum Feld
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Passwort eingeben...")
        self.password_input.returnPressed.connect(self.on_login_clicked)
        layout.addWidget(self.password_input)
        
        # Passwort anzeigen Checkbox
        self.show_password_cb = QCheckBox("👁️ Passwort anzeigen")
        self.show_password_cb.stateChanged.connect(self._toggle_password)
        layout.addWidget(self.show_password_cb)
        
        # Passwort-Änderung nach Login Checkbox
        self.change_password_cb = QCheckBox("🔐 Passwort nach dem Login ändern")
        self.change_password_cb.setToolTip(
            "Wenn aktiviert, wird nach erfolgreichem Login ein Dialog zur Passwortänderung angezeigt."
        )
        layout.addWidget(self.change_password_cb)
        
        layout.addSpacing(10)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.cancel_button = QPushButton("Abbrechen")
        self.cancel_button.clicked.connect(self.reject)
        
        self.demo_button = QPushButton("🧪 Demo Login")
        self.demo_button.clicked.connect(self.handle_demo_login)
        self.demo_button.setToolTip("Schneller Admin-Login: admin@super.de")
        
        self.login_button = QPushButton("🔑 Anmeldung")
        self.login_button.setDefault(True)
        self.login_button.clicked.connect(self.on_login_clicked)
        
        # Button-Styling - VEREINFACHT (keine festen Höhen, System-Standard)
        self.cancel_button.setMinimumHeight(35)
        self.demo_button.setMinimumHeight(35)
        self.login_button.setMinimumHeight(35)
        
        # Nur Farben setzen, keine Rahmen/Padding die Größe beeinflussen
        self.demo_button.setStyleSheet("""
            QPushButton {
                background-color: #f39c12;
                color: white;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)
        self.login_button.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.demo_button)
        button_layout.addWidget(self.login_button)
        
        layout.addLayout(button_layout)
        
        # Focus auf Email-Feld
        self.email_input.setFocus()
    
    def _toggle_password(self, state):
        """Passwort-Sichtbarkeit umschalten"""
        if state == Qt.Checked:
            self.password_input.setEchoMode(QLineEdit.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
    
    def handle_demo_login(self):
        """Demo-Login: Automatisch als Admin einloggen"""
        self.email_input.setText("admin@super.de")
        self.password_input.setText("@Pdvm2025")
        self.on_login_clicked()
    
    def on_login_clicked(self):
        """Login-Button geklickt"""
        email = self.email_input.text().strip()
        password = self.password_input.text()
        
        # 🔍 DEBUG
        print(f"\n🔍 LOGIN-VERSUCH:")
        print(f"   Email: {email}")
        print(f"   Passwort: '{password}'")
        print(f"   Passwort-Länge: {len(password)}")
        print(f"   Passwort repr(): {repr(password)}")
        
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
            
            # ✅ SECURITY CHECK: Account gesperrt?
            try:
                user_db = PdvmUserDatenbank()
                if user_db.is_account_locked(email):
                    QMessageBox.critical(
                        self,
                        "Account gesperrt",
                        "Ihr Account wurde aufgrund zu vieler Fehlversuche gesperrt.\n\n"
                        "Bitte kontaktieren Sie einen Administrator."
                    )
                    self.password_input.clear()
                    return
            except Exception as e:
                print(f"   ⚠️ Account-Lock Check fehlgeschlagen: {e}")
            
            # 🔍 DEBUG
            print(f"✅ Benutzer gefunden: {user_row['name']}")
            print(f"   Gespeicherter Hash: {user_row['passwort']}")
            print(f"   Hash-Länge: {len(user_row['passwort'])}")
            
            # Passwort prüfen (bcrypt)
            verify_result = self._verify_password(password, user_row['passwort'])
            print(f"   Verifizierungs-Ergebnis: {verify_result}")
            
            if not verify_result:
                # ✅ UPDATE: Failed-Login Counter erhöhen
                try:
                    user_db = PdvmUserDatenbank()
                    failed_count = user_db.increment_failed_login(email)
                    print(f"   Failed-Login Count: {failed_count}")
                    
                    if failed_count >= 5:
                        QMessageBox.critical(
                            self,
                            "Account gesperrt",
                            f"Ihr Account wurde nach {failed_count} Fehlversuchen gesperrt.\n\n"
                            "Bitte kontaktieren Sie einen Administrator."
                        )
                    else:
                        QMessageBox.warning(
                            self, 
                            "Fehler", 
                            f"Falsches Passwort!\n\nVerbleibende Versuche: {5 - failed_count}"
                        )
                except Exception as e:
                    print(f"   ⚠️ Failed-Login Update fehlgeschlagen: {e}")
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
            
            # ✅ UPDATE: Last-Login Timestamp + Failed-Attempts zurücksetzen
            try:
                user_db = PdvmUserDatenbank()
                user_db.update_last_login(email)
                print(f"   Last-Login aktualisiert für {email}")
                
                # 🔐 PHASE 1.3: Passwort-Änderungs-Flag setzen wenn Checkbox aktiviert
                if self.change_password_cb.isChecked():
                    user_db.set_password_change_required(email, True)
                    print(f"   🔐 Passwort-Änderungs-Flag gesetzt für {email}")
                    
            except Exception as e:
                print(f"   ⚠️ Last-Login Update fehlgeschlagen: {e}")
            
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
        Passwort mit bcrypt verifizieren (oder einfacher Vergleich als Fallback)
        
        Args:
            password: Klartext-Passwort
            hashed: bcrypt-Hash aus Datenbank
        
        Returns:
            True wenn Passwort korrekt
        """
        try:
            print(f"\n🔍 _verify_password() aufgerufen:")
            print(f"   BCRYPT_AVAILABLE: {BCRYPT_AVAILABLE}")
            print(f"   password: '{password}'")
            print(f"   hashed: {hashed}")
            
            if BCRYPT_AVAILABLE:
                result = bcrypt.checkpw(
                    password.encode('utf-8'), 
                    hashed.encode('utf-8')
                )
                print(f"   bcrypt.checkpw() Result: {result}")
                return result
            else:
                # Fallback: Einfacher String-Vergleich (nur für Demo!)
                result = password == hashed
                print(f"   String-Vergleich Result: {result}")
                return result
        except Exception as e:
            print(f"❌ Fehler bei Passwort-Verifikation: {e}")
            import traceback
            traceback.print_exc()
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
