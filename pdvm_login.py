# login_app.py
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
    QWidget, QLabel, QLineEdit, QPushButton,
    QVBoxLayout, QHBoxLayout, QMessageBox, QCheckBox, QApplication
)
from PyQt5.QtCore import Qt
from pdvm_user_db import PdvmUserDatenbank
from pdvm_benutzer   import PdvmBenutzer

class LoginApp(QWidget):
    def __init__(self, main_app_class):
        super().__init__()
        self.main_app_class = main_app_class
        self.setWindowTitle("PDVM-System – Login")
        self.setFixedSize(320, 180)
        self.setFocusPolicy(Qt.StrongFocus)  # Ensure the window processes focus events
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        # Benutzername
        hl_user = QHBoxLayout()
        hl_user.addWidget(QLabel("Benutzername:"))
        self.username_input = QLineEdit()
        hl_user.addWidget(self.username_input)
        layout.addLayout(hl_user)

        # Passwort
        hl_pw = QHBoxLayout()
        hl_pw.addWidget(QLabel("Passwort:"))
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        hl_pw.addWidget(self.password_input)
        layout.addLayout(hl_pw)

        # Hier die beiden Zeilen ergänzen:
        self.username_input.returnPressed.connect(self._check_login)
        self.password_input.returnPressed.connect(self._check_login)

        # Passwort anzeigen
        self.show_pw_cb = QCheckBox("Passwort anzeigen")
        self.show_pw_cb.stateChanged.connect(self._toggle_password)
        layout.addWidget(self.show_pw_cb)

        # Buttons
        hl_btn = QHBoxLayout()
        btn_login = QPushButton("Anmelden")
        btn_login.clicked.connect(self._check_login)
        btn_login.setDefault(True)  # Set as default button for Enter key
        btn_login.setAutoDefault(True)  # Enable auto default behavior
        self.setFocusPolicy(Qt.StrongFocus) # Ensure the window processes focus events
        btn_quit  = QPushButton("Beenden")
        btn_quit.clicked.connect(self.close)
        hl_btn.addWidget(btn_login)
        hl_btn.addWidget(btn_quit)
        layout.addLayout(hl_btn)

        # Set focus on the username input field
        self.username_input.setFocus()

    def _toggle_password(self):
        if self.show_pw_cb.isChecked():
            self.password_input.setEchoMode(QLineEdit.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.Password)

    def _check_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        db = PdvmUserDatenbank()
        result = db.lesen(username)
        if not result:
            QMessageBox.warning(self, "Login fehlgeschlagen", "Benutzer nicht gefunden.")
            return

        try:
            user = PdvmBenutzer(result[0], result[1], result[2])
        except Exception:
            QMessageBox.critical(self, "Fehler", "Benutzerdaten ungültig.")
            return

        if user.verify_password(result[1], password):
            QMessageBox.information(self, "Erfolg", "Login erfolgreich!")
            # Hier wird die MainApp mit den validierten user_daten gestartet:
            self._open_main_app(result)
        else:
            QMessageBox.critical(self, "Login fehlgeschlagen", "Falsches Passwort.")

    def _open_main_app(self, user_daten):
        self.close()
        # Hier starten wir erst die MainApp mit den validierten user_daten:
        self.main_window = self.main_app_class(user_daten)
        self.main_window.show()


# Falls du direkt nur die LoginApp testen willst:
if __name__ == "__main__":
    app = QApplication(sys.argv)
    login = LoginApp(main_app_class=lambda ud: None)
    login.show()
    sys.exit(app.exec_())
