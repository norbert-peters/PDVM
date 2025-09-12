# pdvm_login.py - SICHERE LOGIN-LOGIK mit moderner Oberfläche
import sys, os, logging
# Erzwinge UTF-8 für alle IO
os.environ['PYTHONIOENCODING'] = 'utf-8'
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
# Logger-Setup noch VOR allen anderen Imports!
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("pdvm_app.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger(__name__)
logger.info("🔹 Login gestartet")

from PyQt5.QtWidgets import (
    QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, 
    QMessageBox, QCheckBox, QApplication, QDialog, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon
from pdvm_user_db import PdvmUserDatenbank
from pdvm_benutzer import PdvmBenutzer


class LoginDialog(QDialog):
    """
    SICHERER LOGIN-DIALOG mit moderner Oberfläche
    - Sichere Trennung der Login-Logik
    - Schöne Optik mit Demo-Button
    - Passwort sichtbar machen möglich
    """
    
    def __init__(self, main_app_class=None):
        super().__init__()
        self.main_app_class = main_app_class
        self.username = ""
        self.password = ""
        self.user_data = None
        self.setup_ui()
        
    def setup_ui(self):
        """UI-Setup für modernen Login-Dialog"""
        self.setWindowTitle("PDVM System - Sichere Anmeldung")
        self.setFixedSize(470, 300)
        self.setModal(True)
        
        # WICHTIG: Fenster-Flags für Vordergrund
        self.setWindowFlags(Qt.Dialog | Qt.WindowStaysOnTopHint | Qt.WindowSystemMenuHint)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Titel
        title_label = QLabel("🔐 PDVM System - Sichere Anmeldung")
        title_font = QFont("Segoe UI", 16, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                padding: 10px;
                background-color: #ecf0f1;
                border-radius: 8px;
                border: 2px solid #3498db;
            }
        """)
        layout.addWidget(title_label)
        
        # Benutzername
        user_frame = QFrame()
        user_layout = QHBoxLayout(user_frame)
        user_layout.setContentsMargins(0, 0, 0, 0)
        
        user_label = QLabel("Benutzername:")
        user_label.setMinimumWidth(100)
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Benutzername eingeben...")
        user_layout.addWidget(user_label)
        user_layout.addWidget(self.username_input)
        layout.addWidget(user_frame)
        
        # Passwort
        pass_frame = QFrame()
        pass_layout = QHBoxLayout(pass_frame)
        pass_layout.setContentsMargins(0, 0, 0, 0)
        
        pass_label = QLabel("Passwort:")
        pass_label.setMinimumWidth(100)
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Passwort eingeben...")
        pass_layout.addWidget(pass_label)
        pass_layout.addWidget(self.password_input)
        layout.addWidget(pass_frame)
        
        # Passwort anzeigen Checkbox
        self.show_password_cb = QCheckBox("👁️ Passwort anzeigen")
        self.show_password_cb.stateChanged.connect(self._toggle_password)
        layout.addWidget(self.show_password_cb)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.cancel_button = QPushButton("Abbrechen")
        self.cancel_button.clicked.connect(self.reject)
        
        self.demo_button = QPushButton("🧪 Demo Login")
        self.demo_button.clicked.connect(self.handle_demo_login)
        self.demo_button.setToolTip("Schneller Test-Login: demo/demo")
        
        self.login_button = QPushButton("🔑 Anmeldung")
        self.login_button.clicked.connect(self.handle_secure_login)
        self.login_button.setDefault(True)
        
        # Button-Styling
        button_style = """
            QPushButton {
                padding: 8px 16px;
                font-size: 11pt;
                border-radius: 6px;
                border: 1px solid #bdc3c7;
            }
            QPushButton:hover {
                background-color: #ecf0f1;
            }
        """
        self.cancel_button.setStyleSheet(button_style)
        self.demo_button.setStyleSheet(button_style + """
            QPushButton {
                background-color: #f39c12;
                color: white;
                border: 1px solid #e67e22;
            }
            QPushButton:hover {
                background-color: #e67e22;
            }
        """)
        self.login_button.setStyleSheet(button_style + """
            QPushButton {
                background-color: #27ae60;
                color: white;
                border: 1px solid #229954;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.demo_button)
        button_layout.addWidget(self.login_button)
        layout.addLayout(button_layout)
        
        # Enter-Taste für Login
        self.password_input.returnPressed.connect(self.handle_secure_login)
        self.username_input.returnPressed.connect(self.password_input.setFocus)
        
        # Focus auf Username
        self.username_input.setFocus()
        
    def _toggle_password(self):
        """Passwort sichtbar/unsichtbar umschalten"""
        if self.show_password_cb.isChecked():
            self.password_input.setEchoMode(QLineEdit.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
    
    def handle_demo_login(self):
        """Demo-Login für schnelle Tests"""
        self.username_input.setText("admin@super.de")
        self.password_input.setText("Polari$55")
        
        reply = QMessageBox.question(self, "Demo Login", 
                                   "Demo-Login verwenden?\n\nUser: demo\nPassword: demo",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            self.handle_secure_login()
    
    def handle_secure_login(self):
        """SICHERE LOGIN-VALIDIERUNG - Getrennte Logik"""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username:
            QMessageBox.warning(self, "Eingabe fehlt", "Bitte Benutzername eingeben!")
            self.username_input.setFocus()
            return
            
        if not password:
            QMessageBox.warning(self, "Eingabe fehlt", "Bitte Passwort eingeben!")
            self.password_input.setFocus()
            return
        
        # SICHERE LOGIN-VALIDIERUNG
        try:
            logger.info(f"🔐 Sichere Login-Validierung für User: {username}")
            
            # User-Datenbank laden
            db = PdvmUserDatenbank()
            result = db.lesen(username)
            
            if not result:
                QMessageBox.warning(self, "Login fehlgeschlagen", 
                                  "Benutzer nicht gefunden!")
                logger.warning(f"❌ Benutzer nicht gefunden: {username}")
                return
            
            # PdvmBenutzer erstellen und validieren
            try:
                user = PdvmBenutzer(result[0], result[1], result[2])
            except Exception as e:
                QMessageBox.critical(self, "Fehler", 
                                   "Benutzerdaten ungültig!")
                logger.error(f"❌ Benutzerdaten ungültig für {username}: {e}")
                return
            
            # Passwort-Validierung
            if user.verify_password(result[1], password):
                logger.info(f"✅ Sichere Login erfolgreich für User: {username}")
                
                # User-Daten für Rückgabe speichern - EINFACH und LINEAR
                self.user_data = {
                    'user_guid': result[3],  # [email, password, user_json, guid]
                    'user_json': result[2],  # Daten aus Spalte 'daten' 
                }
                
                QMessageBox.information(self, "Erfolg", 
                                      f"Login erfolgreich!\n\nWillkommen {username}")
                
                # Dialog erfolgreich schließen
                self.accept()
                
            else:
                QMessageBox.critical(self, "Login fehlgeschlagen", 
                                   "Falsches Passwort!")
                logger.warning(f"❌ Falsches Passwort für User: {username}")
                self.password_input.clear()
                self.password_input.setFocus()
                
        except Exception as e:
            logger.error(f"❌ Fehler bei sicherer Login-Validierung: {e}")
            QMessageBox.critical(self, "System-Fehler", 
                               f"Login-System Fehler:\n{e}")
            
    def get_login_data(self):
        """Sichere Login-Daten zurückgeben"""
        return self.user_data
        
    def showEvent(self, event):
        """Beim Anzeigen: Ins Zentrum und in Vordergrund"""
        super().showEvent(event)
        self.center_on_screen()
        self.raise_()
        self.activateWindow()
        
    def center_on_screen(self):
        """Dialog in Bildschirmmitte zentrieren"""
        from PyQt5.QtWidgets import QDesktopWidget
        screen = QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move(
            (screen.width() - size.width()) // 2,
            (screen.height() - size.height()) // 2
        )


# LEGACY SUPPORT: Alte LoginApp für Kompatibilität
class LoginApp(LoginDialog):
    """Legacy-Wrapper für bestehenden Code"""
    
    def __init__(self, main_app_class):
        super().__init__(main_app_class)
        self.setWindowTitle("PDVM-System – Login (Legacy)")


# Falls direkt getestet wird:
if __name__ == "__main__":
    app = QApplication(sys.argv)
    login = LoginDialog()
    
    if login.exec_() == QDialog.Accepted:
        user_data = login.get_login_data()
        print(f"✅ Login erfolgreich: {user_data}")
    else:
        print("❌ Login abgebrochen")
    
    sys.exit(0)
