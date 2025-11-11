"""
PDVM Systemstart - ULTRA MINIMALISTISCH & LINEAR

PRINZIPIEN:
1. NUR UI-Layout erstellen
2. Container bereitstellen (sichtbar!)
3. Autonome Module aufrufen
4. KEINE Business-Logik

ARCHITEKTUR:
    __init__:
        [1] GCS holen
        [2] Window-Titel setzen
        [3] UI-Layout erstellen (Container)
        [4] Container in GCS registrieren
        [5] Autonome Module rendern
"""

import logging
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel
from pdvm_central_systemsteuerung import get_gcs

logger = logging.getLogger(__name__)


class V2MainAppComplete(QMainWindow):
    """
    PDVM Hauptanwendung - Ultra minimalistisch
    
    Verantwortung:
    - UI-Layout mit Containern erstellen
    - Container SICHTBAR bereitstellen
    - Autonome Module aufrufen
    
    KEINE Verantwortung:
    - Menu-Rendering (→ PdvmMenuSystemAutonomous)
    - Stichtag-Bar (→ PdvmStichtagBar)
    - Welcome-Screen (→ PdvmWelcomeScreen)
    - Command-Execution (→ Menu-Handler)
    """
    
    def __init__(self):
        super().__init__()
        
        logger.info("🔹 PDVM Systemstart - ULTRA LINEAR")
        
        # ========================================
        # [1] GCS HOLEN
        # ========================================
        self.gcs = get_gcs()
        if not self.gcs:
            raise RuntimeError("❌ GCS muss vor MainApp initialisiert sein!")
        logger.info("✅ GCS verfügbar")
        
        # ========================================
        # [2] WINDOW-TITEL
        # ========================================
        try:
            # Mandant aus GCS
            mandant_data = self.gcs._mandant_data
            mandant_name = mandant_data.get('ROOT', {}).get('BEZEICHNUNG', 'Unbekannt')
            
            # User aus GCS
            user_data = self.gcs._user_data
            user_info = user_data.get('USER', {})
            user_name = f"{user_info.get('ANREDE', '')} {user_info.get('VORNAME', '')} {user_info.get('NAME', '')}".strip() or 'Unbekannt'
            
            # Version aus GCS
            version = self.gcs.version if hasattr(self.gcs, 'version') else '0.0'
            
            # Titel setzen
            self.setWindowTitle(f"PDVM-SYSTEM v{version} - {mandant_name} - {user_name}")
            self.resize(1200, 700)
            
            logger.info(f"✅ Window-Titel: {mandant_name} / {user_name}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Setzen des Window-Titels: {e}")
            self.setWindowTitle("PDVM-SYSTEM")
            self.resize(1200, 700)
        
        # ========================================
        # [3] UI-LAYOUT ERSTELLEN
        # ========================================
        logger.info("🔧 Erstelle UI-Layout...")
        
        # Central Widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Haupt-Layout: Vertikal
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # ===== EBENE 1: HORIZONTALES MENÜ OBEN (GRUND) =====
        self.grund_menu_container = QFrame()
        self.grund_menu_container.setFixedHeight(40)
        self.grund_menu_container.setStyleSheet("background-color: transparent;")
        main_layout.addWidget(self.grund_menu_container)
        logger.info("✅ GRUND-Menu-Container erstellt (oben)")
        
        # ===== EBENE 2: ARBEITSBEREICH (VERTIKAL + CONTENT) =====
        work_area = QWidget()
        work_area_layout = QHBoxLayout(work_area)
        work_area_layout.setContentsMargins(0, 0, 0, 0)
        work_area_layout.setSpacing(0)
        
        # VERTIKAL-Menü Container (links)
        self.vertical_menu_container = QFrame()
        self.vertical_menu_container.setFixedWidth(200)
        self.vertical_menu_container.setStyleSheet("""
            QFrame {
                background-color: #ecf0f1;
                border-right: 1px solid #bdc3c7;
            }
        """)
        work_area_layout.addWidget(self.vertical_menu_container)
        logger.info("✅ Vertikal-Menu-Container erstellt (links)")
        
        # Rechte Seite: Vertikal (Stichtag + Workspace)
        right_side = QWidget()
        right_side_layout = QVBoxLayout(right_side)
        right_side_layout.setContentsMargins(0, 0, 0, 0)
        right_side_layout.setSpacing(0)
        work_area_layout.addWidget(right_side)
        
        # Stichtag-Bar Container
        self.stichtag_container = QFrame()
        self.stichtag_container.setFixedHeight(50)
        right_side_layout.addWidget(self.stichtag_container)
        logger.info("✅ Stichtag-Container erstellt")
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #bdc3c7;")
        separator.setFixedHeight(2)
        right_side_layout.addWidget(separator)
        
        # Workspace Container (dynamischer Bereich)
        self.workspace_container = QFrame()
        self.workspace_container.setStyleSheet("background-color: white;")
        right_side_layout.addWidget(self.workspace_container)
        logger.info("✅ Workspace-Container erstellt")
        
        main_layout.addWidget(work_area)
        logger.info("✅ UI-Layout vollständig erstellt")
        
        # ========================================
        # [4] CONTAINER IN GCS REGISTRIEREN
        # ========================================
        logger.info("📦 Registriere Container in GCS...")
        self.gcs.register_menu_containers(
            vertical=self.vertical_menu_container,
            grund=self.grund_menu_container,
            zusatz=None  # ZUSATZ später hinzufügen
        )
        logger.info("✅ Container in GCS registriert")
        
        # ========================================
        # [5] AUTONOME MODULE RENDERN
        # ========================================
        logger.info("🎨 Starte autonome Module...")
        
        # 5.1 Stichtag-Bar rendern
        try:
            from pdvm_stichtag_bar import PdvmStichtagBar
            PdvmStichtagBar.render(self.stichtag_container)
            logger.info("✅ Stichtag-Bar gerendert")
        except Exception as e:
            logger.error(f"❌ Fehler beim Rendern der Stichtag-Bar: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        # 5.2 Welcome-Screen rendern
        try:
            from pdvm_welcome_screen import PdvmWelcomeScreen
            PdvmWelcomeScreen.render(self.workspace_container)
            logger.info("✅ Welcome-Screen gerendert")
        except Exception as e:
            logger.error(f"❌ Fehler beim Rendern des Welcome-Screens: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        # 5.3 Menü-System laden
        try:
            from pdvm_menu_handler import get_menu_handler
            self.menu_handler = get_menu_handler(self)
            logger.info("✅ Menu-Handler initialisiert")
            
            # Startmenü-GUID aus Menu-DB holen
            try:
                menu_db = self.gcs._menu_system_db
                # Hole Startmenü-GUID aus sys_menudaten
                startmenu_guid_data, _ = menu_db.get_value(self.gcs.user_guid, 'startmenu')
                startmenu_guid = startmenu_guid_data if startmenu_guid_data else '5ca6674e-b9ce-4581-9756-64e742883f80'  # Fallback
                logger.info(f"📋 Startmenü-GUID: {startmenu_guid}")
            except Exception as e:
                logger.warning(f"⚠️ Konnte Startmenü-GUID nicht laden: {e}")
                # Standard-GUID verwenden
                startmenu_guid = '5ca6674e-b9ce-4581-9756-64e742883f80'
                logger.info(f"📋 Verwende Standard-Startmenü-GUID: {startmenu_guid}")
            
            from pdvm_menu_system_autonomous import PdvmMenuSystemAutonomous
            PdvmMenuSystemAutonomous.load_startmenu(startmenu_guid, self.menu_handler)
            logger.info("✅ Menü-System geladen")
            
            # Stelle Menü-Sichtbarkeit wieder her (Startmenü ist immer sichtbar)
            self.restore_menu_visibility()
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden des Menü-Systems: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        logger.info("🚀 PDVM Systemstart ABGESCHLOSSEN")
    
    def toggle_menu_visibility(self):
        """
        Schaltet NUR das vertikale Menü ein/aus.
        
        Sichtbarkeit wird persistent in GCS._db gespeichert:
        - Gruppe: user_guid
        - Feld: 'menu_{menu_guid}'
        - Wert: True (sichtbar) / False (versteckt)
        
        WICHTIG: Startmenü darf NICHT ausgeblendet werden!
        """
        if not hasattr(self, 'vertical_menu_container'):
            logger.warning("⚠️ vertical_menu_container nicht gefunden")
            return
        
        try:
            # Hole aktuelle Menu-GUID
            current_menu_guid = self.gcs._menu_system_db.guid
            logger.info(f"🔍 Aktuelle Menu-GUID: {current_menu_guid}")
            
            # Hole Startmenü-GUID
            menu_db = self.gcs._menu_system_db
            startmenu_guid_data, _ = menu_db.get_value(self.gcs.user_guid, 'startmenu')
            startmenu_guid = startmenu_guid_data if startmenu_guid_data else '5ca6674e-b9ce-4581-9756-64e742883f80'
            
            # KRITISCH: Startmenü darf nicht ausgeblendet werden!
            if current_menu_guid == startmenu_guid:
                logger.warning("⚠️ Startmenü kann nicht ausgeblendet werden!")
                return
            
            # Toggle Sichtbarkeit
            current_visible = self.vertical_menu_container.isVisible()
            new_visible = not current_visible
            self.vertical_menu_container.setVisible(new_visible)
            
            # Persistiere in GCS._db (Systemsteuerung)
            field_name = f'menu_{current_menu_guid}'
            self.gcs._db.set_value(self.gcs.user_guid, field_name, new_visible)
            self.gcs._db.save_all_values()
            
            status = "sichtbar" if new_visible else "versteckt"
            logger.info(f"✅ Vertikal-Menü: {status}")
            logger.info(f"💾 Gespeichert: Gruppe={self.gcs.user_guid}, Feld={field_name}, Wert={new_visible}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Toggle der Menü-Sichtbarkeit: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def restore_menu_visibility(self):
        """
        Stellt gespeicherte Menü-Sichtbarkeit wieder her.
        
        Wird nach jedem Menü-Wechsel aufgerufen.
        Lädt Sichtbarkeit aus GCS._db: Gruppe=user_guid, Feld='menu_{menu_guid}'
        
        WICHTIG: Startmenü ist IMMER sichtbar!
        """
        if not hasattr(self, 'vertical_menu_container'):
            logger.warning("⚠️ vertical_menu_container nicht gefunden")
            return
        
        try:
            # Hole aktuelle Menu-GUID
            current_menu_guid = self.gcs._menu_system_db.guid
            logger.info(f"🔍 Stelle Sichtbarkeit wieder her für Menu-GUID: {current_menu_guid}")
            
            # Hole Startmenü-GUID
            menu_db = self.gcs._menu_system_db
            startmenu_guid_data, _ = menu_db.get_value(self.gcs.user_guid, 'startmenu')
            startmenu_guid = startmenu_guid_data if startmenu_guid_data else '5ca6674e-b9ce-4581-9756-64e742883f80'
            
            # KRITISCH: Startmenü ist IMMER sichtbar!
            if current_menu_guid == startmenu_guid:
                self.vertical_menu_container.setVisible(True)
                logger.info("✅ Startmenü → Vertikal-Menü IMMER sichtbar")
                return
            
            # Lade gespeicherte Sichtbarkeit aus GCS._db
            field_name = f'menu_{current_menu_guid}'
            visibility_data, _ = self.gcs._db.get_value(self.gcs.user_guid, field_name)
            
            # Default: sichtbar (falls noch nicht gespeichert)
            if visibility_data is None:
                visibility = True
                logger.info(f"ℹ️ Keine gespeicherte Sichtbarkeit → Default: sichtbar")
            else:
                visibility = bool(visibility_data)
                logger.info(f"📖 Geladene Sichtbarkeit: {visibility}")
            
            # Setze Sichtbarkeit
            self.vertical_menu_container.setVisible(visibility)
            status = "sichtbar" if visibility else "versteckt"
            logger.info(f"✅ Vertikal-Menü wiederhergestellt: {status}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Wiederherstellen der Menü-Sichtbarkeit: {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Fallback: sichtbar
            self.vertical_menu_container.setVisible(True)
    
    def logout(self):
        """
        Meldet Benutzer ab und startet Anwendung neu
        
        Startet Python-Prozess neu mit gleichen Argumenten,
        dann schließt aktuelle Anwendung.
        """
        logger.info("🔵 Logout: Starte Anwendung neu...")
        
        import sys
        import os
        from PyQt5.QtCore import QProcess
        
        # Python-Executable und Skript-Pfad
        python_exe = sys.executable
        script_path = sys.argv[0]
        
        # Vollständiger Pfad zum Skript
        if not os.path.isabs(script_path):
            script_path = os.path.abspath(script_path)
        
        logger.info(f"   Python: {python_exe}")
        logger.info(f"   Skript: {script_path}")
        
        # Neuen Prozess starten (unabhängig)
        QProcess.startDetached(python_exe, [script_path])
        
        logger.info("✅ Neustart gestartet - Schließe aktuelle Anwendung...")
        
        # Kurzer Delay damit neuer Prozess startet
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(500, self.close)  # Nach 500ms schließen


def main():
    """
    Haupteinstiegspunkt - nur für Standalone-Tests
    """
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # GCS muss VOR MainApp initialisiert sein!
    from pdvm_central_systemsteuerung import PdvmCentralSystemsteuerung, register_gcs
    
    # Demo-Daten
    user_guid = "demo-user-guid"
    user_data = {
        'USER': {
            'ANREDE': 'Herr',
            'VORNAME': 'Max',
            'NAME': 'Mustermann'
        }
    }
    mandant_guid = "demo-mandant-guid"
    mandant_data = {
        'ROOT': {
            'BEZEICHNUNG': 'Demo-Mandant'
        },
        'METADATEN': {
            'MANDANT_ID': 'mandant_001'
        }
    }
    
    try:
        # GCS initialisieren
        gcs = PdvmCentralSystemsteuerung(user_guid, user_data, mandant_guid, mandant_data)
        register_gcs(gcs)
        
        # Hauptanwendung starten
        main_window = V2MainAppComplete()
        main_window.show()
        
        logger.info("🚀 Standalone-Test gestartet")
        return app.exec_()
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Starten: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
