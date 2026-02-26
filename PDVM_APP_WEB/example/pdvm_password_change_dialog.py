# -*- coding: utf-8 -*-
"""
Password Change Dialog - Passwortänderung

Ermöglicht Benutzern das Ändern ihres Passworts mit:
- Validierung der Passwort-Komplexität
- Bestätigung des neuen Passworts
- Anzeige der Anforderungen
- Live-Feedback zur Passwortstärke

AUTOR: Norbert Peters
DATUM: 06.12.2025
"""
import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QPushButton, QMessageBox, QGroupBox, QCheckBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from pdvm_user_db import PdvmUserDatenbank

logger = logging.getLogger(__name__)


class PasswordChangeDialog(QDialog):
    """Dialog für Passwortänderung"""
    
    def __init__(self, benutzer, user_db=None, force_change=False, parent=None):
        """
        Initialisiert den Dialog
        
        Args:
            benutzer (str): Email des Benutzers
            user_db (PdvmUserDatenbank): Datenbank-Instanz (optional)
            force_change (bool): True wenn Änderung erzwungen wird (nach Admin-Reset)
            parent (QWidget): Parent-Widget
        """
        super().__init__(parent)
        
        self.benutzer = benutzer
        self.user_db = user_db if user_db else PdvmUserDatenbank()
        self.force_change = force_change
        
        self.setWindowTitle("Passwort ändern")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        # Flag ob Änderung erzwungen wird (Dialog kann nicht abgebrochen werden)
        if self.force_change:
            self.setWindowFlag(Qt.WindowCloseButtonHint, False)
        
        self._init_ui()
    
    def _init_ui(self):
        """UI aufbauen"""
        layout = QVBoxLayout(self)
        
        # Header
        if self.force_change:
            header = QLabel(
                "⚠️ Passwortänderung erforderlich\n\n"
                "Ihr Passwort wurde zurückgesetzt.\n"
                "Bitte wählen Sie ein neues, sicheres Passwort."
            )
            header.setStyleSheet("color: #e74c3c; font-weight: bold; padding: 10px;")
        else:
            header = QLabel(
                f"Passwort ändern für: {self.benutzer}\n\n"
                "Bitte geben Sie Ihr aktuelles und ein neues Passwort ein."
            )
        header.setWordWrap(True)
        layout.addWidget(header)
        
        layout.addSpacing(10)
        
        # Passwort-Eingaben
        fields_layout = QVBoxLayout()
        
        # Altes Passwort (nur wenn nicht erzwungen)
        if not self.force_change:
            old_label = QLabel("Aktuelles Passwort:")
            fields_layout.addWidget(old_label)
            
            self.old_password_input = QLineEdit()
            self.old_password_input.setEchoMode(QLineEdit.Password)
            self.old_password_input.setPlaceholderText("Aktuelles Passwort eingeben")
            fields_layout.addWidget(self.old_password_input)
            
            fields_layout.addSpacing(10)
        else:
            # Dummy-Feld damit Code nicht angepasst werden muss
            self.old_password_input = QLineEdit()
            self.old_password_input.hide()
        
        # Neues Passwort
        new_label = QLabel("Neues Passwort:")
        fields_layout.addWidget(new_label)
        
        self.new_password_input = QLineEdit()
        self.new_password_input.setEchoMode(QLineEdit.Password)
        self.new_password_input.setPlaceholderText("Neues Passwort eingeben")
        self.new_password_input.textChanged.connect(self._validate_password_strength)
        fields_layout.addWidget(self.new_password_input)
        
        # Passwort-Stärke Anzeige
        self.strength_label = QLabel("")
        self.strength_label.setStyleSheet("font-size: 9pt; padding: 5px;")
        fields_layout.addWidget(self.strength_label)
        
        fields_layout.addSpacing(5)
        
        # Neues Passwort bestätigen
        confirm_label = QLabel("Neues Passwort bestätigen:")
        fields_layout.addWidget(confirm_label)
        
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        self.confirm_password_input.setPlaceholderText("Neues Passwort wiederholen")
        self.confirm_password_input.textChanged.connect(self._check_password_match)
        fields_layout.addWidget(self.confirm_password_input)
        
        # Match-Anzeige
        self.match_label = QLabel("")
        self.match_label.setStyleSheet("font-size: 9pt; padding: 5px;")
        fields_layout.addWidget(self.match_label)
        
        layout.addLayout(fields_layout)
        
        layout.addSpacing(10)
        
        # Passwort anzeigen Checkbox
        self.show_password_check = QCheckBox("Passwort anzeigen")
        self.show_password_check.stateChanged.connect(self._toggle_password_visibility)
        layout.addWidget(self.show_password_check)
        
        layout.addSpacing(10)
        
        # Anforderungen Box
        requirements_box = QGroupBox("Passwort-Anforderungen")
        requirements_layout = QVBoxLayout()
        
        requirements = [
            "✓ Mindestens 8 Zeichen",
            "✓ Mindestens 1 Großbuchstabe (A-Z)",
            "✓ Mindestens 1 Kleinbuchstabe (a-z)",
            "✓ Mindestens 1 Zahl (0-9)",
            "✓ Mindestens 1 Sonderzeichen (@$!%*?&)"
        ]
        
        for req in requirements:
            label = QLabel(req)
            label.setStyleSheet("font-size: 9pt; padding: 2px;")
            requirements_layout.addWidget(label)
        
        requirements_box.setLayout(requirements_layout)
        layout.addWidget(requirements_box)
        
        layout.addSpacing(20)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        if not self.force_change:
            cancel_btn = QPushButton("Abbrechen")
            cancel_btn.clicked.connect(self.reject)
            button_layout.addWidget(cancel_btn)
        
        self.change_btn = QPushButton("Passwort ändern")
        self.change_btn.clicked.connect(self._change_password)
        self.change_btn.setEnabled(False)
        self.change_btn.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        button_layout.addWidget(self.change_btn)
        
        layout.addLayout(button_layout)
    
    def _toggle_password_visibility(self, state):
        """Passwort-Sichtbarkeit umschalten"""
        if state == Qt.Checked:
            self.old_password_input.setEchoMode(QLineEdit.Normal)
            self.new_password_input.setEchoMode(QLineEdit.Normal)
            self.confirm_password_input.setEchoMode(QLineEdit.Normal)
        else:
            self.old_password_input.setEchoMode(QLineEdit.Password)
            self.new_password_input.setEchoMode(QLineEdit.Password)
            self.confirm_password_input.setEchoMode(QLineEdit.Password)
    
    def _validate_password_strength(self):
        """Validiert Passwort-Stärke live"""
        password = self.new_password_input.text()
        
        if not password:
            self.strength_label.setText("")
            self._check_can_submit()
            return
        
        valid, error_msg = PdvmUserDatenbank.validate_password_complexity(password)
        
        if valid:
            self.strength_label.setText("✅ Passwort erfüllt alle Anforderungen")
            self.strength_label.setStyleSheet("color: #27ae60; font-size: 9pt; padding: 5px;")
        else:
            self.strength_label.setText(f"❌ {error_msg}")
            self.strength_label.setStyleSheet("color: #e74c3c; font-size: 9pt; padding: 5px;")
        
        self._check_can_submit()
    
    def _check_password_match(self):
        """Prüft ob Passwörter übereinstimmen"""
        new_pw = self.new_password_input.text()
        confirm_pw = self.confirm_password_input.text()
        
        if not confirm_pw:
            self.match_label.setText("")
            self._check_can_submit()
            return
        
        if new_pw == confirm_pw:
            self.match_label.setText("✅ Passwörter stimmen überein")
            self.match_label.setStyleSheet("color: #27ae60; font-size: 9pt; padding: 5px;")
        else:
            self.match_label.setText("❌ Passwörter stimmen nicht überein")
            self.match_label.setStyleSheet("color: #e74c3c; font-size: 9pt; padding: 5px;")
        
        self._check_can_submit()
    
    def _check_can_submit(self):
        """Prüft ob Submit möglich ist"""
        old_pw = self.old_password_input.text()
        new_pw = self.new_password_input.text()
        confirm_pw = self.confirm_password_input.text()
        
        # Altes Passwort nur prüfen wenn nicht erzwungen
        if not self.force_change and not old_pw:
            self.change_btn.setEnabled(False)
            return
        
        # Neues Passwort muss valid sein
        valid, _ = PdvmUserDatenbank.validate_password_complexity(new_pw)
        if not valid:
            self.change_btn.setEnabled(False)
            return
        
        # Passwörter müssen übereinstimmen
        if new_pw != confirm_pw:
            self.change_btn.setEnabled(False)
            return
        
        # Alles OK
        self.change_btn.setEnabled(True)
    
    def _change_password(self):
        """Passwort ändern"""
        old_pw = self.old_password_input.text() if not self.force_change else ""
        new_pw = self.new_password_input.text()
        
        try:
            # Für erzwungene Änderung: direkter Zugriff auf DB
            if self.force_change:
                # Passwort direkt setzen (ohne Verifizierung des alten)
                user_data = self.user_db.lesen(self.benutzer)
                if not user_data:
                    QMessageBox.critical(self, "Fehler", "Benutzer nicht gefunden")
                    return
                
                # Neues Passwort hashen
                new_hash = PdvmUserDatenbank.hash_password(new_pw)
                
                # Daten laden
                import json
                from pd_datetime import Pdvm_DateTime
                # user_data ist ein Tuple mit 11 Spalten: (benutzer, passwort, uid, daten, ...)
                # Wir brauchen nur daten (Index 3)
                daten_json = user_data[3]
                daten = json.loads(daten_json)
                
                # SECURITY-Gruppe aktualisieren
                if 'SECURITY' not in daten:
                    daten['SECURITY'] = {}
                
                dt = Pdvm_DateTime()
                current_timestamp = dt.PdvmDateTime
                
                daten['SECURITY']['PASSWORD_CHANGE_REQUIRED'] = False
                daten['SECURITY']['LAST_PASSWORD_CHANGE'] = current_timestamp
                
                # Speichern
                import sqlite3
                conn = sqlite3.connect(self.user_db.db_name)
                cursor = conn.cursor()
                
                json_daten = json.dumps(daten, ensure_ascii=False)
                update_query = f'UPDATE {self.user_db.table_name} SET passwort = ?, daten = ? WHERE benutzer = ?'
                cursor.execute(update_query, (new_hash, json_daten, self.benutzer))
                
                conn.commit()
                conn.close()
                
                logger.info(f"✅ Passwort zurückgesetzt für {self.benutzer}")
                QMessageBox.information(
                    self,
                    "Erfolg",
                    "Ihr Passwort wurde erfolgreich geändert.\n\n"
                    "Sie können sich jetzt mit dem neuen Passwort anmelden."
                )
                self.accept()
            else:
                # Normale Passwortänderung mit Verifizierung
                success, error_msg = self.user_db.change_password(
                    self.benutzer,
                    old_pw,
                    new_pw
                )
                
                if success:
                    logger.info(f"✅ Passwort geändert für {self.benutzer}")
                    QMessageBox.information(
                        self,
                        "Erfolg",
                        "Ihr Passwort wurde erfolgreich geändert."
                    )
                    self.accept()
                else:
                    QMessageBox.critical(
                        self,
                        "Fehler",
                        f"Passwortänderung fehlgeschlagen:\n\n{error_msg}"
                    )
            
        except Exception as e:
            logger.error(f"Fehler bei Passwortänderung: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            QMessageBox.critical(
                self,
                "Fehler",
                f"Fehler bei der Passwortänderung:\n\n{e}"
            )
