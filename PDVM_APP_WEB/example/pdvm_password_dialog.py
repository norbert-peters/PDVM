# -*- coding: utf-8 -*-
"""
Passwort-Dialog mit Live-Validierung

Dialog zum Setzen/Ändern von Passwörtern mit:
- Live-Validierung der Passwort-Regeln
- Passwort-Bestätigung
- Checkbox "Passwort-Änderung beim nächsten Login"

AUTOR: Norbert Peters
DATUM: 08.12.2025
VERSION: 1.0
"""
import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QCheckBox, QGroupBox, QFormLayout, QWidget
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

logger = logging.getLogger(__name__)


class PdvmPasswordDialog(QDialog):
    """Dialog zum Setzen eines Passworts mit Validierung"""
    
    # Passwort-Regeln (aus pdvm_user_db.py)
    PASSWORD_MIN_LENGTH = 8
    
    def __init__(self, benutzer_name, title="Passwort setzen", parent=None):
        """
        Initialisiert den Dialog
        
        Args:
            benutzer_name (str): Name des Benutzers (für Anzeige)
            title (str): Dialog-Titel
            parent (QWidget): Parent-Widget
        """
        super().__init__(parent)
        
        self.benutzer_name = benutzer_name
        self.password = None  # Wird bei OK gesetzt
        self.require_change = True  # Standard: User muss Passwort ändern
        
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(500)
        
        self._init_ui()
    
    def _init_ui(self):
        """UI aufbauen"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header = QLabel(f"🔑 Passwort setzen für: {self.benutzer_name}")
        header_font = QFont()
        header_font.setPointSize(12)
        header_font.setBold(True)
        header.setFont(header_font)
        layout.addWidget(header)
        
        # Info-Text
        info_label = QLabel(
            "Passwort-Regeln:\n"
            "• Mindestens 8 Zeichen\n"
            "• Mindestens ein Großbuchstabe (A-Z)\n"
            "• Mindestens ein Kleinbuchstabe (a-z)\n"
            "• Mindestens eine Ziffer (0-9)\n"
            "• Mindestens ein Sonderzeichen (@$!%*?&)"
        )
        info_label.setStyleSheet("color: gray; font-size: 9pt; padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
        layout.addWidget(info_label)
        
        # Passwort-Gruppe
        password_group = QGroupBox("Neues Passwort")
        password_layout = QFormLayout()
        
        # Passwort-Feld mit Sichtbarkeits-Toggle
        password_container = QHBoxLayout()
        self.input_password = QLineEdit()
        self.input_password.setEchoMode(QLineEdit.Password)
        self.input_password.setPlaceholderText("Passwort eingeben")
        self.input_password.textChanged.connect(self._validate_password)
        password_container.addWidget(self.input_password)
        
        self.btn_toggle_password = QPushButton("👁")
        self.btn_toggle_password.setFixedWidth(40)
        self.btn_toggle_password.setToolTip("Passwort anzeigen/verbergen")
        self.btn_toggle_password.clicked.connect(self._toggle_password_visibility)
        self.btn_toggle_password.setStyleSheet("""
            QPushButton {
                background-color: #ecf0f1;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #d5dbdb;
            }
        """)
        password_container.addWidget(self.btn_toggle_password)
        
        password_widget = QWidget()
        password_widget.setLayout(password_container)
        password_layout.addRow("Passwort:", password_widget)
        
        # Bestätigungs-Feld mit Sichtbarkeits-Toggle
        confirm_container = QHBoxLayout()
        self.input_password_confirm = QLineEdit()
        self.input_password_confirm.setEchoMode(QLineEdit.Password)
        self.input_password_confirm.setPlaceholderText("Passwort wiederholen")
        self.input_password_confirm.textChanged.connect(self._validate_password)
        confirm_container.addWidget(self.input_password_confirm)
        
        self.btn_toggle_confirm = QPushButton("👁")
        self.btn_toggle_confirm.setFixedWidth(40)
        self.btn_toggle_confirm.setToolTip("Passwort anzeigen/verbergen")
        self.btn_toggle_confirm.clicked.connect(self._toggle_password_visibility)
        self.btn_toggle_confirm.setStyleSheet("""
            QPushButton {
                background-color: #ecf0f1;
                border: 1px solid #bdc3c7;
                border-radius: 3px;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #d5dbdb;
            }
        """)
        confirm_container.addWidget(self.btn_toggle_confirm)
        
        confirm_widget = QWidget()
        confirm_widget.setLayout(confirm_container)
        password_layout.addRow("Bestätigung:", confirm_widget)
        
        password_group.setLayout(password_layout)
        layout.addWidget(password_group)
        
        # Validierungs-Labels
        self.label_length = QLabel("✗ Mindestens 8 Zeichen")
        self.label_length.setStyleSheet("color: red;")
        layout.addWidget(self.label_length)
        
        self.label_uppercase = QLabel("✗ Mindestens ein Großbuchstabe")
        self.label_uppercase.setStyleSheet("color: red;")
        layout.addWidget(self.label_uppercase)
        
        self.label_lowercase = QLabel("✗ Mindestens ein Kleinbuchstabe")
        self.label_lowercase.setStyleSheet("color: red;")
        layout.addWidget(self.label_lowercase)
        
        self.label_digit = QLabel("✗ Mindestens eine Ziffer")
        self.label_digit.setStyleSheet("color: red;")
        layout.addWidget(self.label_digit)
        
        self.label_special = QLabel("✗ Mindestens ein Sonderzeichen (@$!%*?&)")
        self.label_special.setStyleSheet("color: red;")
        layout.addWidget(self.label_special)
        
        self.label_match = QLabel("✗ Passwörter stimmen nicht überein")
        self.label_match.setStyleSheet("color: red;")
        layout.addWidget(self.label_match)
        
        layout.addSpacing(10)
        
        # Checkbox: Passwort-Änderung erforderlich
        self.check_require_change = QCheckBox("Benutzer muss Passwort beim nächsten Login ändern")
        self.check_require_change.setChecked(True)
        self.check_require_change.setToolTip("Nach Login wird Benutzer aufgefordert, das Passwort zu ändern")
        layout.addWidget(self.check_require_change)
        
        layout.addSpacing(10)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.btn_cancel = QPushButton("Abbrechen")
        self.btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(self.btn_cancel)
        
        self.btn_ok = QPushButton("OK - Passwort setzen")
        self.btn_ok.clicked.connect(self._on_ok)
        self.btn_ok.setEnabled(False)  # Initial deaktiviert
        self.btn_ok.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover:enabled {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        button_layout.addWidget(self.btn_ok)
        
        layout.addLayout(button_layout)
    
    def _toggle_password_visibility(self):
        """Toggle Passwort-Sichtbarkeit für beide Felder"""
        # Aktuellen Modus ermitteln
        is_hidden = self.input_password.echoMode() == QLineEdit.Password
        
        if is_hidden:
            # Passwörter anzeigen
            self.input_password.setEchoMode(QLineEdit.Normal)
            self.input_password_confirm.setEchoMode(QLineEdit.Normal)
            self.btn_toggle_password.setText("🙈")
            self.btn_toggle_confirm.setText("🙈")
        else:
            # Passwörter verbergen
            self.input_password.setEchoMode(QLineEdit.Password)
            self.input_password_confirm.setEchoMode(QLineEdit.Password)
            self.btn_toggle_password.setText("👁")
            self.btn_toggle_confirm.setText("👁")
    
    def _validate_password(self):
        """Validiert Passwort live und aktualisiert UI"""
        password = self.input_password.text()
        confirm = self.input_password_confirm.text()
        
        # Validierungen
        is_length_ok = len(password) >= self.PASSWORD_MIN_LENGTH
        is_uppercase_ok = any(c.isupper() for c in password)
        is_lowercase_ok = any(c.islower() for c in password)
        is_digit_ok = any(c.isdigit() for c in password)
        is_special_ok = any(c in '@$!%*?&' for c in password)
        is_match_ok = password == confirm and len(password) > 0
        
        # Labels aktualisieren
        self._update_label(self.label_length, is_length_ok, "Mindestens 8 Zeichen")
        self._update_label(self.label_uppercase, is_uppercase_ok, "Mindestens ein Großbuchstabe")
        self._update_label(self.label_lowercase, is_lowercase_ok, "Mindestens ein Kleinbuchstabe")
        self._update_label(self.label_digit, is_digit_ok, "Mindestens eine Ziffer")
        self._update_label(self.label_special, is_special_ok, "Mindestens ein Sonderzeichen (@$!%*?&)")
        self._update_label(self.label_match, is_match_ok, "Passwörter stimmen überein")
        
        # OK-Button aktivieren wenn alle Validierungen erfolgreich
        all_valid = (is_length_ok and is_uppercase_ok and is_lowercase_ok and 
                     is_digit_ok and is_special_ok and is_match_ok)
        self.btn_ok.setEnabled(all_valid)
    
    def _update_label(self, label, is_valid, text):
        """Aktualisiert Validierungs-Label"""
        if is_valid:
            label.setText(f"✓ {text}")
            label.setStyleSheet("color: green;")
        else:
            label.setText(f"✗ {text}")
            label.setStyleSheet("color: red;")
    
    def _on_ok(self):
        """OK-Button: Passwort übernehmen"""
        self.password = self.input_password.text()
        self.require_change = self.check_require_change.isChecked()
        logger.info(f"✅ Passwort gesetzt (require_change={self.require_change})")
        self.accept()
    
    def get_password(self):
        """
        Gibt gesetztes Passwort zurück
        
        Returns:
            str: Passwort oder None wenn abgebrochen
        """
        return self.password
    
    def get_require_change(self):
        """
        Gibt zurück ob Passwort-Änderung erforderlich ist
        
        Returns:
            bool: True wenn Benutzer Passwort ändern muss
        """
        return self.require_change
