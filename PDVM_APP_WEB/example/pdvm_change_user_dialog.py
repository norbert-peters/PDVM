# -*- coding: utf-8 -*-
"""
Change User Dialog - Benutzerverwaltung

Frame-Dialog zum Bearbeiten von Benutzerdaten mit 3 Tabs:
- Tab 1: USER + SECURITY (Name, Rollen, Account-Status)
- Tab 2: SETTINGS + MANDANTEN + PERMISSIONS (Theme, Mandanten-Zuordnung)
- Tab 3: MEINEAPPS + ANWENDUNGEN (App-Berechtigungen)

Übernehmen/Sichern Pattern für Datenänderungen

AUTOR: Norbert Peters
DATUM: 07.12.2025
VERSION: 1.0
"""
import sys
import logging
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTabWidget, QWidget, QFormLayout, QComboBox, QCheckBox, QMessageBox,
    QGroupBox, QListWidget, QTextEdit, QApplication
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from pdvm_user_db import PdvmUserDatenbank

logger = logging.getLogger(__name__)


class ChangeUserDialog(QDialog):
    """Frame-Dialog zum Bearbeiten von Benutzerdaten"""
    
    def __init__(self, benutzer_email, user_db=None, parent=None, user_guid=None):
        """
        Initialisiert den Dialog
        
        Args:
            benutzer_email (str): Email des zu bearbeitenden Benutzers
            user_db (PdvmUserDatenbank): Datenbank-Instanz (optional)
            parent (QWidget): Parent-Widget
            user_guid (str): UID des Benutzers (für Email-Update)
        """
        super().__init__(parent)
        
        self.benutzer_email = benutzer_email
        self.user_guid = user_guid
        self.user_db = user_db if user_db else PdvmUserDatenbank()
        
        logger.info(f"🔍 ChangeUserDialog für: {benutzer_email}")
        
        # Originaldaten laden
        self.original_data = self.user_db.get_all_data(benutzer_email)
        
        logger.info(f"   Geladene Daten: {self.original_data}")
        
        if not self.original_data:
            QMessageBox.critical(
                self,
                "Fehler",
                f"Benutzer '{benutzer_email}' nicht gefunden!"
            )
            self.reject()
            return
        
        # Arbeitskopie für Änderungen
        self.work_data = self.original_data.copy()
        
        self.setWindowTitle(f"Benutzer bearbeiten: {benutzer_email}")
        self.setModal(True)
        self.setMinimumSize(800, 600)
        
        self._init_ui()
        self._load_data()
    
    def _init_ui(self):
        """UI aufbauen"""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header mit User-Info
        header = QLabel(f"📝 Benutzerdaten bearbeiten")
        header_font = QFont()
        header_font.setPointSize(14)
        header_font.setBold(True)
        header.setFont(header_font)
        layout.addWidget(header)
        
        info_label = QLabel(f"Email: {self.benutzer_email}")
        info_label.setStyleSheet("color: gray; font-size: 10pt;")
        layout.addWidget(info_label)
        
        layout.addSpacing(10)
        
        # Tab-Widget
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_tab_user_security(), "👤 Benutzer & Sicherheit")
        self.tabs.addTab(self._create_tab_settings_mandanten(), "⚙️ Einstellungen & Mandanten")
        self.tabs.addTab(self._create_tab_apps(), "📱 Anwendungen")
        
        layout.addWidget(self.tabs)
        
        layout.addSpacing(10)
        
        # Button-Leiste (Übernehmen/Sichern Pattern)
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.btn_cancel = QPushButton("Abbrechen")
        self.btn_cancel.clicked.connect(self._on_cancel)
        button_layout.addWidget(self.btn_cancel)
        
        self.btn_apply = QPushButton("Übernehmen")
        self.btn_apply.clicked.connect(self._on_apply)
        self.btn_apply.setToolTip("Änderungen übernehmen (Dialog bleibt offen)")
        button_layout.addWidget(self.btn_apply)
        
        self.btn_save = QPushButton("Sichern")
        self.btn_save.clicked.connect(self._on_save)
        self.btn_save.setToolTip("Änderungen sichern und Dialog schließen")
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                padding: 8px 20px;
                border: none;
                border-radius: 3px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #229954;
            }
        """)
        button_layout.addWidget(self.btn_save)
        
        layout.addLayout(button_layout)
    
    def _create_tab_user_security(self):
        """Tab 1: USER + SECURITY"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # === GROUP: USER ===
        user_group = QGroupBox("👤 Benutzerdaten")
        user_layout = QFormLayout()
        
        self.input_anrede = QComboBox()
        self.input_anrede.addItems(["Herr", "Frau", "Divers"])
        user_layout.addRow("Anrede:", self.input_anrede)
        
        self.input_vorname = QLineEdit()
        self.input_vorname.setPlaceholderText("Vorname des Benutzers")
        user_layout.addRow("Vorname:", self.input_vorname)
        
        self.input_name = QLineEdit()
        self.input_name.setPlaceholderText("Nachname des Benutzers")
        user_layout.addRow("Name:", self.input_name)
        
        self.input_email = QLineEdit()
        self.input_email.setPlaceholderText("Email-Adresse des Benutzers")
        user_layout.addRow("Email:", self.input_email)
        
        user_group.setLayout(user_layout)
        layout.addWidget(user_group)
        
        # === GROUP: SECURITY ===
        security_group = QGroupBox("🔐 Sicherheit & Rollen")
        security_layout = QVBoxLayout()
        
        # Rollen-Liste
        roles_label = QLabel("Rollen:")
        security_layout.addWidget(roles_label)
        
        self.list_roles = QListWidget()
        self.list_roles.setMaximumHeight(100)
        self.list_roles.setSelectionMode(QListWidget.MultiSelection)
        # Standard-Rollen
        for role in ["admin", "user", "viewer", "editor"]:
            self.list_roles.addItem(role)
        security_layout.addWidget(self.list_roles)
        
        # Account-Status
        status_layout = QHBoxLayout()
        
        self.check_account_locked = QCheckBox("Account gesperrt")
        self.check_account_locked.setToolTip("Account ist für Login gesperrt")
        status_layout.addWidget(self.check_account_locked)
        
        self.check_password_change = QCheckBox("Passwort-Änderung erforderlich")
        self.check_password_change.setToolTip("User muss bei nächstem Login Passwort ändern")
        status_layout.addWidget(self.check_password_change)
        
        status_layout.addStretch()
        security_layout.addLayout(status_layout)
        
        # Passwort-Buttons
        password_layout = QHBoxLayout()
        password_layout.addStretch()
        
        self.btn_set_password = QPushButton("🔑 Startpasswort setzen")
        self.btn_set_password.clicked.connect(self._on_set_password)
        self.btn_set_password.setToolTip("Neues Passwort für Benutzer setzen (z.B. bei Erstanlage oder Passwort vergessen)")
        self.btn_set_password.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                padding: 6px 12px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
        """)
        password_layout.addWidget(self.btn_set_password)
        
        self.btn_reset_password = QPushButton("🔄 Passwort zurücksetzen")
        self.btn_reset_password.clicked.connect(self._on_reset_password)
        self.btn_reset_password.setToolTip("Passwort zurücksetzen (öffnet gleichen Dialog wie 'Startpasswort setzen')")
        self.btn_reset_password.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                padding: 6px 12px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        password_layout.addWidget(self.btn_reset_password)
        
        security_layout.addLayout(password_layout)
        
        security_group.setLayout(security_layout)
        layout.addWidget(security_group)
        
        layout.addStretch()
        return tab
    
    def _create_tab_settings_mandanten(self):
        """Tab 2: SETTINGS + MANDANTEN + PERMISSIONS"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # === GROUP: SETTINGS ===
        settings_group = QGroupBox("⚙️ Einstellungen")
        settings_layout = QFormLayout()
        
        self.input_theme = QComboBox()
        self.input_theme.addItems(["light", "dark", "auto"])
        settings_layout.addRow("Theme:", self.input_theme)
        
        self.input_language = QComboBox()
        self.input_language.addItems(["DEU", "ENG", "USA"])
        settings_layout.addRow("Sprache:", self.input_language)
        
        self.check_expert_mode = QCheckBox("Expert-Modus aktiviert")
        settings_layout.addRow("", self.check_expert_mode)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # === GROUP: MANDANTEN ===
        mandanten_group = QGroupBox("🏢 Mandanten-Zuordnung")
        mandanten_layout = QVBoxLayout()
        
        mandanten_label = QLabel("Zugeordnete Mandanten:")
        mandanten_layout.addWidget(mandanten_label)
        
        self.list_mandanten = QListWidget()
        self.list_mandanten.setMaximumHeight(120)
        mandanten_layout.addWidget(self.list_mandanten)
        
        mandanten_buttons = QHBoxLayout()
        mandanten_buttons.addStretch()
        
        btn_add_mandant = QPushButton("➕ Mandant hinzufügen")
        btn_add_mandant.clicked.connect(self._on_add_mandant)
        mandanten_buttons.addWidget(btn_add_mandant)
        
        btn_remove_mandant = QPushButton("➖ Mandant entfernen")
        btn_remove_mandant.clicked.connect(self._on_remove_mandant)
        mandanten_buttons.addWidget(btn_remove_mandant)
        
        mandanten_layout.addLayout(mandanten_buttons)
        
        mandanten_group.setLayout(mandanten_layout)
        layout.addWidget(mandanten_group)
        
        layout.addStretch()
        return tab
    
    def _create_tab_apps(self):
        """Tab 3: MEINEAPPS + ANWENDUNGEN"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # === GROUP: MEINEAPPS ===
        apps_group = QGroupBox("📱 Meine Anwendungen")
        apps_layout = QVBoxLayout()
        
        apps_label = QLabel("Freigeschaltete Anwendungen:")
        apps_layout.addWidget(apps_label)
        
        self.list_apps = QListWidget()
        self.list_apps.setMaximumHeight(150)
        apps_layout.addWidget(self.list_apps)
        
        apps_buttons = QHBoxLayout()
        apps_buttons.addStretch()
        
        btn_add_app = QPushButton("➕ App freischalten")
        btn_add_app.clicked.connect(self._on_add_app)
        apps_buttons.addWidget(btn_add_app)
        
        btn_remove_app = QPushButton("➖ App entfernen")
        btn_remove_app.clicked.connect(self._on_remove_app)
        apps_buttons.addWidget(btn_remove_app)
        
        apps_layout.addLayout(apps_buttons)
        
        apps_group.setLayout(apps_layout)
        layout.addWidget(apps_group)
        
        # === INFO: Anwendungen ===
        info_group = QGroupBox("ℹ️ Verfügbare Anwendungen")
        info_layout = QVBoxLayout()
        
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setMaximumHeight(150)
        info_text.setPlainText(
            "Verfügbare Anwendungen im System:\n\n"
            "• PDVM-Personen: Personenverwaltung\n"
            "• PDVM-Finanzen: Finanzverwaltung\n"
            "• PDVM-Dokumente: Dokumentenverwaltung\n"
            "• PDVM-Reports: Berichtswesen\n"
        )
        info_layout.addWidget(info_text)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        layout.addStretch()
        return tab
    
    def _load_data(self):
        """Lädt Daten in UI-Felder"""
        # Tab 1: USER
        user_data = self.work_data.get('USER', {})
        
        anrede = user_data.get('ANREDE', 'Herr')
        index = self.input_anrede.findText(anrede)
        if index >= 0:
            self.input_anrede.setCurrentIndex(index)
        
        self.input_vorname.setText(user_data.get('VORNAME', ''))
        self.input_name.setText(user_data.get('NAME', ''))
        # Email aus work_data laden (falls bereits geändert), sonst aktuelle Email
        self.input_email.setText(user_data.get('EMAIL', self.benutzer_email))
        
        # Tab 1: SECURITY
        security_data = self.work_data.get('SECURITY', {})
        
        roles = self.work_data.get('PERMISSIONS', {}).get('ROLES', [])
        for i in range(self.list_roles.count()):
            item = self.list_roles.item(i)
            if item.text() in roles:
                item.setSelected(True)
        
        self.check_account_locked.setChecked(security_data.get('ACCOUNT_LOCKED', False))
        self.check_password_change.setChecked(security_data.get('PASSWORD_CHANGE_REQUIRED', False))
        
        # Tab 2: SETTINGS
        settings_data = self.work_data.get('SETTINGS', {})
        
        theme = settings_data.get('THEME', 'light')
        index = self.input_theme.findText(theme)
        if index >= 0:
            self.input_theme.setCurrentIndex(index)
        
        language = settings_data.get('LANGUAGE', 'DEU')
        index = self.input_language.findText(language)
        if index >= 0:
            self.input_language.setCurrentIndex(index)
        
        self.check_expert_mode.setChecked(settings_data.get('EXPERT_MODE', False))
        
        # Tab 2: MANDANTEN
        mandanten_list = self.work_data.get('MANDANTEN', {}).get('LIST', [])
        self.list_mandanten.clear()
        for mandant in mandanten_list:
            self.list_mandanten.addItem(mandant)
        
        # Tab 3: MEINEAPPS
        apps_list = self.work_data.get('MEINEAPPS', {}).get('LIST', [])
        self.list_apps.clear()
        for app in apps_list:
            self.list_apps.addItem(app)
    
    def _save_data_from_ui(self):
        """Speichert UI-Felder in work_data"""
        # Tab 1: USER
        if 'USER' not in self.work_data:
            self.work_data['USER'] = {}
        
        self.work_data['USER']['ANREDE'] = self.input_anrede.currentText()
        self.work_data['USER']['VORNAME'] = self.input_vorname.text().strip()
        self.work_data['USER']['NAME'] = self.input_name.text().strip()
        # Email IMMER in Kleinbuchstaben (case-insensitive)
        self.work_data['USER']['EMAIL'] = self.input_email.text().strip().lower()
        
        # Tab 1: SECURITY
        if 'SECURITY' not in self.work_data:
            self.work_data['SECURITY'] = {}
        
        self.work_data['SECURITY']['ACCOUNT_LOCKED'] = self.check_account_locked.isChecked()
        self.work_data['SECURITY']['PASSWORD_CHANGE_REQUIRED'] = self.check_password_change.isChecked()
        
        # Rollen sammeln
        if 'PERMISSIONS' not in self.work_data:
            self.work_data['PERMISSIONS'] = {}
        
        selected_roles = []
        for i in range(self.list_roles.count()):
            item = self.list_roles.item(i)
            if item.isSelected():
                selected_roles.append(item.text())
        self.work_data['PERMISSIONS']['ROLES'] = selected_roles
        
        # Tab 2: SETTINGS
        if 'SETTINGS' not in self.work_data:
            self.work_data['SETTINGS'] = {}
        
        self.work_data['SETTINGS']['THEME'] = self.input_theme.currentText()
        self.work_data['SETTINGS']['LANGUAGE'] = self.input_language.currentText()
        self.work_data['SETTINGS']['EXPERT_MODE'] = self.check_expert_mode.isChecked()
        
        # Mandanten und Apps werden direkt über Buttons aktualisiert
    
    def _on_apply(self):
        """Übernehmen-Button: Daten speichern, Dialog bleibt offen"""
        self._save_data_from_ui()
        
        # Validierung
        if not self.work_data.get('USER', {}).get('NAME'):
            QMessageBox.warning(self, "Fehler", "Name darf nicht leer sein!")
            return
        
        if not self.work_data.get('USER', {}).get('VORNAME'):
            QMessageBox.warning(self, "Fehler", "Vorname darf nicht leer sein!")
            return
        
        # In DB speichern
        try:
            # 1. Email-Update (falls geändert) via set_spalte()
            neue_email = self.work_data.get('USER', {}).get('EMAIL', '').strip()
            if self.user_guid and neue_email and neue_email != self.benutzer_email:
                # Email hat sich geändert - Update via PdvmDatenbank
                from pdvm_datenbank import PdvmDatenbank
                db = PdvmDatenbank(table_name='sys_benutzer')
                db.set_spalte(self.user_guid, 'benutzer', neue_email)
                logger.info(f"✅ Email aktualisiert: {self.benutzer_email} → {neue_email}")
                # Aktuelle Email aktualisieren
                self.benutzer_email = neue_email
            
            # 2. JSON-Daten speichern
            success = self.user_db.save_all_data(self.benutzer_email, self.work_data)
            if success:
                self.original_data = self.work_data.copy()
                QMessageBox.information(
                    self,
                    "Erfolg",
                    "Änderungen wurden übernommen."
                )
                logger.info(f"✅ User-Daten übernommen für {self.benutzer_email}")
            else:
                QMessageBox.critical(self, "Fehler", "Fehler beim Speichern!")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Speichern:\n{e}")
            logger.error(f"Fehler beim Speichern von User-Daten: {e}")
    
    def _on_save(self):
        """Sichern-Button: Daten speichern und Dialog schließen"""
        self._save_data_from_ui()
        
        # Validierung
        if not self.work_data.get('USER', {}).get('NAME'):
            QMessageBox.warning(self, "Fehler", "Name darf nicht leer sein!")
            return
        
        if not self.work_data.get('USER', {}).get('VORNAME'):
            QMessageBox.warning(self, "Fehler", "Vorname darf nicht leer sein!")
            return
        
        # In DB speichern
        try:
            # 1. Email-Update (falls geändert) via set_spalte()
            neue_email = self.work_data.get('USER', {}).get('EMAIL', '').strip()
            if self.user_guid and neue_email and neue_email != self.benutzer_email:
                # Email hat sich geändert - Update via PdvmDatenbank
                from pdvm_datenbank import PdvmDatenbank
                db = PdvmDatenbank(table_name='sys_benutzer')
                db.set_spalte(self.user_guid, 'benutzer', neue_email)
                logger.info(f"✅ Email aktualisiert: {self.benutzer_email} → {neue_email}")
                # Aktuelle Email aktualisieren
                self.benutzer_email = neue_email
            
            # 2. JSON-Daten speichern
            success = self.user_db.save_all_data(self.benutzer_email, self.work_data)
            if success:
                logger.info(f"✅ User-Daten gesichert für {self.benutzer_email}")
                self.accept()
            else:
                QMessageBox.critical(self, "Fehler", "Fehler beim Speichern!")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Speichern:\n{e}")
            logger.error(f"Fehler beim Speichern von User-Daten: {e}")
    
    def _on_cancel(self):
        """Abbrechen-Button: Änderungen verwerfen"""
        if self.work_data != self.original_data:
            reply = QMessageBox.question(
                self,
                "Änderungen verwerfen?",
                "Es gibt ungespeicherte Änderungen.\n\nMöchten Sie diese verwerfen?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.reject()
        else:
            self.reject()
    
    def _on_set_password(self):
        """Startpasswort setzen (Admin-Funktion) - öffnet Passwort-Dialog"""
        from pdvm_password_dialog import PdvmPasswordDialog
        
        # Benutzer-Name für Anzeige
        user_name = self.work_data.get('USER', {}).get('NAME', 'Unbekannt')
        vorname = self.work_data.get('USER', {}).get('VORNAME', '')
        display_name = f"{vorname} {user_name}".strip()
        
        # Passwort-Dialog öffnen
        dialog = PdvmPasswordDialog(
            benutzer_name=display_name,
            title="Startpasswort setzen",
            parent=self
        )
        
        if dialog.exec_() == QDialog.Accepted:
            password = dialog.get_password()
            require_change = dialog.get_require_change()
            
            if password:
                try:
                    # Passwort via admin_set_password() setzen
                    success, error_msg = self.user_db.admin_set_password(
                        self.benutzer_email, 
                        password, 
                        require_change
                    )
                    
                    if success:
                        QMessageBox.information(
                            self,
                            "Erfolg",
                            f"Passwort erfolgreich gesetzt für {display_name}.\n\n"
                            f"Passwort-Änderung beim Login: {'Ja' if require_change else 'Nein'}"
                        )
                        
                        # Checkbox aktualisieren
                        self.check_password_change.setChecked(require_change)
                        
                        logger.info(f"✅ Startpasswort gesetzt für {self.benutzer_email}")
                    else:
                        QMessageBox.critical(
                            self,
                            "Fehler",
                            f"Fehler beim Setzen des Passworts:\n{error_msg}"
                        )
                except Exception as e:
                    QMessageBox.critical(
                        self,
                        "Fehler",
                        f"Fehler beim Setzen des Passworts:\n{e}"
                    )
                    logger.error(f"Fehler beim Setzen des Passworts: {e}")
    
    def _on_reset_password(self):
        """Passwort zurücksetzen (Admin-Funktion) - nutzt gleichen Dialog"""
        # Gleiche Funktion wie _on_set_password()
        self._on_set_password()
    
    def _on_add_mandant(self):
        """Mandant hinzufügen"""
        # TODO: Mandanten-Auswahl-Dialog
        QMessageBox.information(self, "Info", "Mandanten-Auswahl wird implementiert")
    
    def _on_remove_mandant(self):
        """Mandant entfernen"""
        current_item = self.list_mandanten.currentItem()
        if current_item:
            mandant = current_item.text()
            reply = QMessageBox.question(
                self,
                "Mandant entfernen?",
                f"Möchten Sie den Mandanten '{mandant}' wirklich entfernen?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                row = self.list_mandanten.row(current_item)
                self.list_mandanten.takeItem(row)
                
                # work_data aktualisieren
                if 'MANDANTEN' not in self.work_data:
                    self.work_data['MANDANTEN'] = {}
                if 'LIST' not in self.work_data['MANDANTEN']:
                    self.work_data['MANDANTEN']['LIST'] = []
                
                if mandant in self.work_data['MANDANTEN']['LIST']:
                    self.work_data['MANDANTEN']['LIST'].remove(mandant)
    
    def _on_add_app(self):
        """App freischalten"""
        # TODO: App-Auswahl-Dialog
        QMessageBox.information(self, "Info", "App-Auswahl wird implementiert")
    
    def _on_remove_app(self):
        """App entfernen"""
        current_item = self.list_apps.currentItem()
        if current_item:
            app = current_item.text()
            reply = QMessageBox.question(
                self,
                "App entfernen?",
                f"Möchten Sie die App '{app}' wirklich entfernen?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                row = self.list_apps.row(current_item)
                self.list_apps.takeItem(row)
                
                # work_data aktualisieren
                if 'MEINEAPPS' not in self.work_data:
                    self.work_data['MEINEAPPS'] = {}
                if 'LIST' not in self.work_data['MEINEAPPS']:
                    self.work_data['MEINEAPPS']['LIST'] = []
                
                if app in self.work_data['MEINEAPPS']['LIST']:
                    self.work_data['MEINEAPPS']['LIST'].remove(app)


# ============================================================================
# TEST
# ============================================================================

def test_change_user_dialog():
    """Test-Funktion für Change-User-Dialog"""
    app = QApplication(sys.argv)
    
    print("\n" + "=" * 70)
    print("📝 CHANGE USER DIALOG TEST")
    print("=" * 70)
    
    # Dialog öffnen
    dialog = ChangeUserDialog("admin@super.de")
    
    if dialog.exec_() == QDialog.Accepted:
        print("\n✅ Änderungen gespeichert")
    else:
        print("\n❌ Abgebrochen")
    
    return 0


if __name__ == '__main__':
    sys.exit(test_change_user_dialog())
