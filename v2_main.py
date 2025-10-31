"""
V2.0 Main Entry Point

Kompletter Login-Flow:
1. Login-Dialog (Email/Passwort)
2. Mandanten-Auswahl
3. Hauptanwendung starten (rudimentär)

AUTOR: Norbert Peters
DATUM: 30.10.2025 
VERSION: 1.0
"""

import sys
from PyQt5.QtWidgets import QApplication, QDialog, QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from v2_login_dialog import V2LoginDialog
from v2_mandanten_dialog import V2MandantenDialog
from v2_gcs import init_gcs, get_gcs, reset_gcs


class V2MainWindow(QMainWindow):
    """
    V2.0 Hauptanwendung (rudimentär für Testing)
    
    Zeigt User-Daten und Mandanten-Info an
    """
    
    def __init__(self, user_data: dict, mandant_guid: str, mandant_info: dict):
        super().__init__()
        
        # ⭐ User-Daten speichern (NICHT erneut laden!)
        self.user_data = user_data
        self.mandant_guid = mandant_guid  # GUID
        self.mandant_id = mandant_info['mandant_id']  # mandant_001, mandant_002
        self.mandant_info = mandant_info
        
        self.setup_ui()
    
    def setup_ui(self):
        """UI aufbauen"""
        self.setWindowTitle(f"PDVM V2.0 - {self.mandant_info['name']}")
        self.setMinimumSize(800, 600)
        
        # Central Widget
        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(50, 50, 50, 50)
        
        # Titel
        title = QLabel("🎉 PDVM V2.0 - LOGIN ERFOLGREICH!")
        title_font = QFont()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        layout.addSpacing(20)
        
        # User-Info
        user_info = QLabel(
            f"👤 <b>Benutzer:</b> {self.user_data['name']}<br>"
            f"📧 <b>Email:</b> {self.user_data['email']}<br>"
            f"🆔 <b>UID:</b> {self.user_data['uid']}<br>"
            f"🔐 <b>Rollen:</b> {', '.join(self.user_data['daten']['PERMISSIONS']['ROLES'])}<br>"
            f"🛡️ <b>Security-Profiles:</b> {', '.join(self.user_data['daten']['PERMISSIONS']['SEC_PROFILES'])}"
        )
        user_info.setStyleSheet("font-size: 12pt; padding: 20px; background-color: #f0f0f0; border-radius: 5px;")
        layout.addWidget(user_info)
        
        # Mandanten-Info
        mandant_info_label = QLabel(
            f"🏢 <b>Mandant:</b> {self.mandant_info['name']}<br>"
            f"🆔 <b>ID:</b> {self.mandant_id}<br>"
            f"💾 <b>DB-Name:</b> {self.mandant_info['db_name']}<br>"
            f"🌍 <b>Land:</b> {self.mandant_info['country']}<br>"
            f"📊 <b>Status:</b> {self.mandant_info['status']}"
        )
        mandant_info_label.setStyleSheet("font-size: 12pt; padding: 20px; background-color: #e8f5e9; border-radius: 5px;")
        layout.addWidget(mandant_info_label)
        
        # Settings-Info
        settings = self.user_data['daten']['SETTINGS']
        settings_info = QLabel(
            f"⚙️ <b>Einstellungen:</b><br>"
            f"🎨 Theme: {settings['THEME']}<br>"
            f"🌐 Language: {settings['LANGUAGE']}<br>"
            f"🌍 Country: {settings['COUNTRY']}<br>"
            f"🔧 Mode: {settings['MODE']}<br>"
            f"📅 Stichtag: {settings['STICHTAG']}"
        )
        settings_info.setStyleSheet("font-size: 11pt; padding: 20px; background-color: #fff3e0; border-radius: 5px;")
        layout.addWidget(settings_info)
        
        # MeineApps-Info
        meineapps = self.user_data['daten'].get('MEINEAPPS', {})
        start_menu = meineapps.get('START', 'Nicht definiert')
        
        apps_info = QLabel(
            f"📱 <b>Meine Apps:</b><br>"
            f"🚀 Start-Menü: {start_menu}"
        )
        apps_info.setStyleSheet("font-size: 11pt; padding: 20px; background-color: #e3f2fd; border-radius: 5px;")
        layout.addWidget(apps_info)
        
        # GCS-Test
        gcs_test = QLabel(
            f"🔧 <b>GCS V2.0 Status:</b><br>"
            f"✅ GCS initialisiert: {get_gcs() is not None}<br>"
            f"📂 DB-Pfad: {get_gcs().mandant_db_path if get_gcs() else 'N/A'}"
        )
        gcs_test.setStyleSheet("font-size: 10pt; padding: 15px; background-color: #f5f5f5; border-radius: 5px; border: 2px dashed #999;")
        layout.addWidget(gcs_test)
        
        layout.addStretch()
        
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
        print("\n" + "=" * 70)
        print("🚀 V2.0 HAUPTANWENDUNG GESTARTET")
        print("=" * 70)
        print(f"User: {self.user_data['name']}")
        print(f"Mandant: {self.mandant_info['name']} ({self.mandant_id})")
        print(f"GCS verfügbar: {get_gcs() is not None}")
        print("=" * 70 + "\n")
    
    def closeEvent(self, event):
        """Beim Schließen GCS zurücksetzen"""
        print("\n🔄 Hauptfenster schließt - GCS wird zurückgesetzt")
        reset_gcs()
        event.accept()


def main():
    """
    V2.0 Haupt-Entry-Point
    
    Ablauf:
    1. Login-Dialog → User-Daten
    2. Mandanten-Auswahl → Mandant-ID
    3. Hauptanwendung → Mit User-Daten + Mandant
    """
    app = QApplication(sys.argv)
    
    print("\n" + "=" * 70)
    print("🚀 PDVM V2.0 - STARTUP")
    print("=" * 70)
    
    # PHASE 1: LOGIN
    print("\n[1/3] Login-Dialog...")
    login_dialog = V2LoginDialog()
    
    if login_dialog.exec_() != QDialog.Accepted:
        print("❌ Login abgebrochen")
        return 1
    
    user_data = login_dialog.user_data  # ⭐ EINMALIG geladen!
    print(f"✅ Login erfolgreich: {user_data['name']} ({user_data['email']})")
    
    # PHASE 2: MANDANTEN-AUSWAHL
    print("\n[2/3] Mandanten-Auswahl...")
    mandanten_dialog = V2MandantenDialog(user_data)
    
    if mandanten_dialog.exec_() != QDialog.Accepted:
        print("❌ Mandanten-Auswahl abgebrochen")
        return 1
    
    selected_mandant = mandanten_dialog.selected_mandant
    mandant_info = mandanten_dialog._load_mandant_info(selected_mandant)
    
    # Mandanten-Daten aus auth.db holen (für GCS)
    mandant_data = mandanten_dialog._load_mandant_data(selected_mandant)
    
    print(f"✅ Mandant gewählt: {mandant_info['name']} ({selected_mandant})")
    
    # ⭐ GCS INITIALISIEREN (EINMALIG!)
    print("\n[2.5/3] GCS initialisieren...")
    gcs = init_gcs(
        user_data=user_data,
        mandant_guid=selected_mandant,  # ⭐ GUID!
        mandant_data=mandant_data
    )
    
    # PHASE 3: HAUPTANWENDUNG
    print("\n[3/3] Hauptanwendung starten...")
    main_window = V2MainWindow(
        user_data=user_data,           # ⭐ Weitergegeben, nicht erneut laden!
        mandant_guid=selected_mandant,  # ⭐ GUID!
        mandant_info=mandant_info
    )
    
    main_window.show()
    
    return app.exec_()


if __name__ == '__main__':
    sys.exit(main())
