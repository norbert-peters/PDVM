"""
V2 Menu Handler (Orchestrator)
===============================
Koordiniert alle Menü-Komponenten

Features:
- Load Menu (VERTIKAL + GRUND)
- Refresh Zusatzmenü bei Item-Click
- Command-Ausführung
- Startmenü mit Security-Check

Autor: PDVM V2.0
Datum: 01.11.2025
"""

import logging
from typing import Optional, Dict, Any, List
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QFrame

from v2_menu_schema import MenuItem, MenuContainer
from v2_menu_storage import get_menu_storage
from v2_menu_builder import V2MenuBuilder, V2VerticalMenuWidget, V2HorizontalMenuWidget
from v2_command_handler import get_command_handler
from v2_central_systemsteuerung import get_gcs

logger = logging.getLogger(__name__)


class V2MenuHandler:
    """
    Menu Handler - Orchestrator für komplettes Menüsystem
    
    Workflow:
    1. load_menu(menu_guid) → Lädt VERTIKAL + GRUND
    2. on_item_click(item_guid) → Führt Command aus + Refresht ZUSATZ
    3. refresh_zusatz(item_guid) → Aktualisiert Zusatzmenü
    
    Refresh-Zeitpunkte:
    - VERTIKAL + GRUND: Bei jedem Menü-Wechsel (load_menu)
    - ZUSATZ: Bei jedem Menüpunkt-Klick
    """
    
    def __init__(self, 
                 vertical_container: QWidget,
                 grund_container: QWidget,
                 zusatz_container: QWidget):
        """
        Initialisiert Menu Handler
        
        Args:
            vertical_container: Container für vertikales Menü (links)
            grund_container: Container für Grundmenü (oben links)
            zusatz_container: Container für Zusatzmenü (oben rechts)
        """
        self.gcs = get_gcs()
        if not self.gcs:
            raise RuntimeError("GCS nicht initialisiert")
        
        self.storage = get_menu_storage()
        if not self.storage:
            raise RuntimeError("Menu Storage nicht initialisiert")
        
        self.builder = V2MenuBuilder()
        self.command_handler = get_command_handler()
        if not self.command_handler:
            raise RuntimeError("Command Handler nicht initialisiert")
        
        # Container für Widgets
        self.vertical_container = vertical_container
        self.grund_container = grund_container
        self.zusatz_container = zusatz_container
        
        # Current State
        self.current_menu_guid: Optional[str] = None
        self.current_item_guid: Optional[str] = None
        
        # Widgets (werden bei load_menu erstellt)
        self.vertical_widget: Optional[V2VerticalMenuWidget] = None
        self.grund_widget: Optional[V2HorizontalMenuWidget] = None
        self.zusatz_widget: Optional[V2HorizontalMenuWidget] = None
        
        logger.info("✅ V2MenuHandler initialisiert")
    
    def load_menu(self, menu_guid: str) -> bool:
        """
        Lädt komplettes Menü (VERTIKAL + GRUND)
        
        Refresh-Zeitpunkt: Bei jedem Menü-Wechsel
        
        Args:
            menu_guid: GUID des zu ladenden Menüs
            
        Returns:
            True bei Erfolg
        """
        try:
            logger.info(f"🎯 Lade Menü: {menu_guid}")
            
            # Clear alte Widgets
            self._clear_all_containers()
            
            # 1. Lade VERTIKAL
            self.vertical_widget = self.builder.build_vertical(
                menu_guid,
                on_item_click=self._on_item_click
            )
            
            if self.vertical_widget:
                # Füge zu Container hinzu
                layout = self.vertical_container.layout()
                if not layout:
                    layout = QVBoxLayout(self.vertical_container)
                    layout.setContentsMargins(0, 0, 0, 0)
                layout.addWidget(self.vertical_widget)
                
                # WICHTIG: Erzwinge sofortige Aktualisierung
                self.vertical_container.updateGeometry()
                self.vertical_container.update()
                
                logger.info("✅ Vertikalmenü geladen")
            else:
                logger.warning("⚠️ Kein Vertikalmenü verfügbar")
            
            # 2. Lade GRUND
            self.grund_widget = self.builder.build_grund(
                menu_guid,
                on_item_click=self._on_item_click
            )
            
            if self.grund_widget:
                # Füge zu Container hinzu
                layout = self.grund_container.layout()
                if not layout:
                    layout = QHBoxLayout(self.grund_container)
                    layout.setContentsMargins(0, 0, 0, 0)
                layout.addWidget(self.grund_widget)
                
                # WICHTIG: Erzwinge sofortige Aktualisierung
                self.grund_container.updateGeometry()
                self.grund_container.update()
                
                logger.info("✅ Grundmenü geladen")
            else:
                logger.warning("⚠️ Kein Grundmenü verfügbar")
            
            # Speichere State
            self.current_menu_guid = menu_guid
            self.current_item_guid = None  # Reset bei Menü-Wechsel
            
            logger.info(f"✅ Menü komplett geladen: {menu_guid}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden von Menü {menu_guid}: {e}")
            return False
    
    def load_startmenu(self) -> bool:
        """
        Lädt Startmenü mit Security-Check
        
        SPEZIALFALL: Nur Menüs anzeigen deren GUID in gcs._u_db
        unter MEINEAPPS.LIST existiert (persönliche App-Zulassung)
        
        Returns:
            True bei Erfolg
        """
        try:
            logger.info("🔐 Lade Startmenü mit Security-Check")
            
            # Hole User-Apps aus gcs._u_db (User-Daten)
            user_data = self.gcs._user_data
            meine_apps = user_data.get('MEINEAPPS', {})
            start_menu_guid = meine_apps.get('START')
            
            if not start_menu_guid:
                logger.error("❌ Kein Startmenü in User-Daten definiert")
                return False
            
            logger.info(f"🔍 Startmenü-GUID: {start_menu_guid}")
            
            # Prüfe ob Menü existiert
            if not self.storage.menu_exists(start_menu_guid):
                logger.error(f"❌ Startmenü {start_menu_guid} existiert nicht")
                return False
            
            # Lade Menü (normale load_menu, aber nur erlaubte Apps)
            # WICHTIG: Container muss bereits gefilterte Items enthalten
            # oder wir filtern hier vor dem Anzeigen
            
            success = self.load_menu(start_menu_guid)
            
            if success:
                # Zusätzlicher Security-Filter für Startmenü
                self._apply_startmenu_security()
                logger.info("✅ Startmenü geladen und gefiltert")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden von Startmenü: {e}")
            return False
    
    def _apply_startmenu_security(self):
        """
        Wendet Security-Filter auf Startmenü an
        
        Versteckt Buttons deren Command nicht erlaubt ist
        """
        try:
            # Hole erlaubte App-GUIDs
            user_data = self.gcs._user_data
            meine_apps = user_data.get('MEINEAPPS', {})
            erlaubte_apps = meine_apps.get('LIST', [])
            
            logger.info(f"🔍 Erlaubte Apps: {erlaubte_apps}")
            
            # Filter Vertikal-Buttons
            if self.vertical_widget:
                for button in self.vertical_widget.buttons:
                    # Prüfe ob Item einen Command hat
                    if button.item.COMMAND_GUID:
                        # Hole Container für Command-Lookup
                        container = self.storage.get_menu(self.current_menu_guid)
                        if container:
                            command = container.get_command_by_guid(button.item.COMMAND_GUID)
                            if command:
                                # Prüfe Security
                                # Für Startmenü: Zusätzlich prüfen ob in erlaubte_apps
                                if not self._is_app_allowed(command, erlaubte_apps):
                                    button.hide()
                                    logger.info(f"   🔒 Button versteckt: {button.item.LABEL}")
            
            logger.info("✅ Startmenü-Security angewendet")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Startmenü-Security: {e}")
    
    def _is_app_allowed(self, command: Any, erlaubte_apps: List[str]) -> bool:
        """
        Prüft ob Command/App erlaubt ist
        
        Für Startmenü: Command.GUID oder zugehörige App-GUID
        muss in erlaubte_apps sein
        """
        # TODO: Logic für App-Zulassung
        # Für jetzt: Standard-Security-Check
        user_data = self.gcs._user_data
        permissions = user_data.get('PERMISSIONS', {})
        user_sec_profiles = permissions.get('SEC_PROFILES', [])
        
        return command.is_allowed_for_user(user_sec_profiles)
    
    def refresh_vertical(self) -> bool:
        """
        Aktualisiert nur Vertikalmenü
        
        Returns:
            True bei Erfolg
        """
        if not self.current_menu_guid:
            logger.warning("⚠️ Kein Menü geladen")
            return False
        
        try:
            # Clear Container
            self._clear_container(self.vertical_container)
            
            # Rebuild
            self.vertical_widget = self.builder.build_vertical(
                self.current_menu_guid,
                on_item_click=self._on_item_click
            )
            
            if self.vertical_widget:
                layout = self.vertical_container.layout()
                if not layout:
                    layout = QVBoxLayout(self.vertical_container)
                    layout.setContentsMargins(0, 0, 0, 0)
                layout.addWidget(self.vertical_widget)
                logger.info("✅ Vertikalmenü aktualisiert")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktualisieren Vertikalmenü: {e}")
            return False
    
    def refresh_grund(self) -> bool:
        """
        Aktualisiert nur Grundmenü
        
        Returns:
            True bei Erfolg
        """
        if not self.current_menu_guid:
            logger.warning("⚠️ Kein Menü geladen")
            return False
        
        try:
            # Clear Container
            self._clear_container(self.grund_container)
            
            # Rebuild
            self.grund_widget = self.builder.build_grund(
                self.current_menu_guid,
                on_item_click=self._on_item_click
            )
            
            if self.grund_widget:
                layout = self.grund_container.layout()
                if not layout:
                    layout = QHBoxLayout(self.grund_container)
                    layout.setContentsMargins(0, 0, 0, 0)
                layout.addWidget(self.grund_widget)
                logger.info("✅ Grundmenü aktualisiert")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktualisieren Grundmenü: {e}")
            return False
    
    def refresh_zusatz(self, item_guid: str) -> bool:
        """
        Aktualisiert Zusatzmenü für Item
        
        Refresh-Zeitpunkt: Bei jedem Menüpunkt-Klick
        Mit Vererbung!
        
        Args:
            item_guid: GUID des Parent-Items
            
        Returns:
            True bei Erfolg
        """
        if not self.current_menu_guid:
            logger.warning("⚠️ Kein Menü geladen")
            return False
        
        try:
            logger.info(f"🔄 Refresh Zusatzmenü für Item: {item_guid}")
            
            # Clear Container
            self._clear_container(self.zusatz_container)
            
            # Build Zusatz (mit Vererbung!)
            self.zusatz_widget = self.builder.build_zusatz(
                self.current_menu_guid,
                item_guid,
                on_item_click=self._on_item_click
            )
            
            if self.zusatz_widget:
                layout = self.zusatz_container.layout()
                if not layout:
                    layout = QHBoxLayout(self.zusatz_container)
                    layout.setContentsMargins(0, 0, 0, 0)
                layout.addWidget(self.zusatz_widget)
                logger.info("✅ Zusatzmenü aktualisiert")
                return True
            else:
                logger.info("ℹ️ Kein Zusatzmenü für dieses Item")
                return True  # Kein Zusatzmenü ist OK
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Aktualisieren Zusatzmenü: {e}")
            return False
    
    def _on_item_click(self, item_guid: str):
        """
        Handler für Item-Click
        
        Workflow:
        1. Speichere current_item_guid
        2. Refresh Zusatzmenü
        3. Führe Command aus (falls vorhanden)
        """
        try:
            logger.info(f"🖱️ Item geklickt: {item_guid}")
            
            # Speichere State
            self.current_item_guid = item_guid
            
            # 1. Refresh Zusatzmenü
            self.refresh_zusatz(item_guid)
            
            # 2. Hole Item aus Container
            container = self.storage.get_menu(self.current_menu_guid)
            if not container:
                logger.error("❌ Container nicht gefunden")
                return
            
            item = container.get_item_by_guid(item_guid)
            if not item:
                logger.error(f"❌ Item {item_guid} nicht gefunden")
                return
            
            # 3. Führe Command aus (falls vorhanden)
            if item.COMMAND_GUID:
                logger.info(f"⚡ Führe Command aus: {item.COMMAND_GUID}")
                
                # Erweiterter Context für Command-Handler
                context = {
                    'menu_guid': self.current_menu_guid,
                    'item_guid': item_guid,
                    'item': item,
                    'menu_handler': self,
                    'vertical_container': self.vertical_container,
                    'grund_container': self.grund_container,
                    'zusatz_container': self.zusatz_container
                }
                
                # Versuche main_app zu finden (über parent-chain)
                main_app = self._find_main_app()
                if main_app:
                    context['main_app'] = main_app
                    context['content_frame'] = getattr(main_app, 'content_frame', None)
                else:
                    logger.warning("⚠️ main_app nicht gefunden - Handler haben eingeschränkten Zugriff")
                
                self.command_handler.execute(
                    self.current_menu_guid,
                    item.COMMAND_GUID,
                    context
                )
            else:
                logger.info("ℹ️ Kein Command für dieses Item")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Item-Click: {e}")
    
    def _find_main_app(self):
        """
        Findet main_app über Widget-Parent-Chain
        
        Returns:
            V2MainAppComplete oder None
        """
        try:
            # Starte bei vertical_container und gehe Parent-Chain hoch
            current = self.vertical_container
            depth = 0
            max_depth = 10
            
            while current and depth < max_depth:
                # Prüfe ob current die Hauptanwendung ist
                class_name = current.__class__.__name__
                if 'MainApp' in class_name or 'V2MainAppComplete' in class_name:
                    logger.info(f"✅ main_app gefunden: {class_name}")
                    return current
                
                # Prüfe ob current menu_handler hat (Indikator für MainApp)
                if hasattr(current, 'menu_handler') and hasattr(current, 'content_frame'):
                    logger.info(f"✅ main_app gefunden via Attribute: {class_name}")
                    return current
                
                # Gehe einen Level höher
                current = current.parent()
                depth += 1
            
            logger.warning("⚠️ main_app nicht in Parent-Chain gefunden")
            return None
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Suchen von main_app: {e}")
            return None
    
    def _clear_container(self, container: QWidget):
        """
        Entfernt alle Widgets UND Layout aus Container
        
        LINEAR und EINFACH:
        1. Widgets aus Layout entfernen
        2. Layout mit SIP löschen (echtes Delete in Qt)
        """
        layout = container.layout()
        if not layout:
            return  # Nichts zu tun
        
        # Schritt 1: Alle Widgets entfernen
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Schritt 2: Layout mit SIP löschen (ECHTES Delete in Qt)
        try:
            from sip import delete  # type: ignore
            delete(layout)
        except ImportError:
            # PyQt5.sip in neueren Versionen
            from PyQt5 import sip  # type: ignore
            sip.delete(layout)
    
    def _clear_all_containers(self):
        """Entfernt Widgets aus allen Containern"""
        self._clear_container(self.vertical_container)
        self._clear_container(self.grund_container)
        self._clear_container(self.zusatz_container)
        
        self.vertical_widget = None
        self.grund_widget = None
        self.zusatz_widget = None


if __name__ == "__main__":
    # ===== TEST =====
    print("🧪 V2 Menu Handler Test")
    print("=" * 60)
    print("⚠️ HINWEIS: Test benötigt initialisiertes GCS + QApplication")
    print("   Führe v2_main.py aus für vollständigen Test")
    print("=" * 60)
    
    # Teste nur Import
    print("\n✅ Import erfolgreich")
    print("   V2MenuHandler: ✓")
    
    print("\n🎯 Menu Handler Module Ready!")
    print("\n📋 Features:")
    print("   • load_menu() - Lädt VERTIKAL + GRUND")
    print("   • load_startmenu() - Mit Security-Check")
    print("   • refresh_zusatz() - Mit Vererbung")
    print("   • _on_item_click() - Command-Ausführung + Zusatz-Refresh")
