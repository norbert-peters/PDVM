"""
V3 Menu Handler
===============
Einfacher, linearer Handler für V3-Menü

DESIGN-PRINZIPIEN:
- Linear: BASIS → WIDGETS → ANZEIGEN
- Keine komplexen Refresh-Logiken
- Ein Aufruf = Komplettes Menü
- Template-Integration automatisch durch LinearMenuLoader

Autor: PDVM V3.0
Datum: 02.11.2025
"""

import logging
from typing import Optional, Dict, Any
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout

from v3_menu_system import LinearMenuLoader, MenuItem
from v3_menu_widgets import V3VerticalMenu, V3HorizontalMenu
from v2_central_systemsteuerung import get_gcs

logger = logging.getLogger(__name__)


class V3MenuHandler:
    """
    V3 Menu Handler - Einfach und Linear
    
    Workflow:
    1. load_menu(menu_guid) → LinearMenuLoader → Widgets → Anzeige
    2. on_item_click(item_guid) → Command ausführen + ZUSATZ neu laden
    
    WICHTIG: Keine komplexen Refresh-Mechanismen!
    """
    
    def __init__(self, 
                 vertical_container: QWidget,
                 grund_container: QWidget,
                 zusatz_container: QWidget):
        """
        Initialisiert V3 Menu Handler
        
        Args:
            vertical_container: Container für vertikales Menü (links)
            grund_container: Container für Grundmenü (oben links)
            zusatz_container: Container für Zusatzmenü (oben rechts)
        """
        self.gcs = get_gcs()
        if not self.gcs:
            raise RuntimeError("GCS nicht initialisiert - Login erforderlich!")
        
        # Container
        self.vertical_container = vertical_container
        self.grund_container = grund_container
        self.zusatz_container = zusatz_container
        
        # Current State
        self.current_menu_guid: Optional[str] = None
        self.current_item_guid: Optional[str] = None
        
        # Current Widgets
        self.vertical_widget: Optional[V3VerticalMenu] = None
        self.grund_widget: Optional[V3HorizontalMenu] = None
        self.zusatz_widget: Optional[V3HorizontalMenu] = None
        
        # MenuItem-Cache für ZUSATZ-Lookup
        self.current_items: Dict[str, MenuItem] = {}
        
        logger.info("✅ V3MenuHandler initialisiert")
    
    def load_menu(self, menu_guid: str) -> bool:
        """
        Lädt komplettes Menü (VERTIKAL + GRUND)
        
        LINEAR:
        1. LinearMenuLoader laden
        2. Widgets erstellen
        3. In Container anzeigen
        
        Args:
            menu_guid: GUID des Menüs
            
        Returns:
            True bei Erfolg
        """
        try:
            logger.info(f"🎯 Lade V3-Menü: {menu_guid}")
            
            # 1. LinearMenuLoader laden
            loader = LinearMenuLoader(menu_guid)
            menu_structure = loader.load_menu()
            
            if not menu_structure:
                logger.error("❌ Menü-Struktur nicht geladen")
                return False
            
            # 2. Items extrahieren
            vertikal_items = menu_structure.get('VERTIKAL', [])
            grund_items = menu_structure.get('GRUND', [])
            zusatz_items = menu_structure.get('ZUSATZ', [])  # ZUSATZ auch laden!
            
            logger.info(f"📋 Menü geladen: {len(vertikal_items)} VERTIKAL, {len(grund_items)} GRUND, {len(zusatz_items)} ZUSATZ")
            
            # 3. Items in Cache speichern (für ZUSATZ-Lookup)
            # WICHTIG: ALLE Items (auch ZUSATZ) in Cache!
            self.current_items = {}
            for item in vertikal_items + grund_items + zusatz_items:
                self.current_items[item.guid] = item
            
            # 4. Clear alte Widgets
            self._clear_all_containers()
            
            # 5. VERTIKAL Widget erstellen
            if vertikal_items:
                self.vertical_widget = V3VerticalMenu(vertikal_items)
                self.vertical_widget.item_clicked.connect(self._on_item_click)
                
                layout = self.vertical_container.layout()
                if not layout:
                    layout = QVBoxLayout(self.vertical_container)
                    layout.setContentsMargins(0, 0, 0, 0)
                layout.addWidget(self.vertical_widget)
                
                logger.info("✅ Vertikalmenü angezeigt")
            
            # 6. GRUND Widget erstellen
            if grund_items:
                self.grund_widget = V3HorizontalMenu(grund_items)
                self.grund_widget.item_clicked.connect(self._on_item_click)
                
                layout = self.grund_container.layout()
                if not layout:
                    layout = QHBoxLayout(self.grund_container)
                    layout.setContentsMargins(0, 0, 0, 0)
                layout.addWidget(self.grund_widget)
                
                logger.info("✅ Grundmenü angezeigt")
            
            # 7. State speichern
            self.current_menu_guid = menu_guid
            self.current_item_guid = None
            
            # 8. V2.0: Gespeicherten Menü-Sichtbarkeits-Status anwenden
            if hasattr(self, 'main_app') and self.main_app:
                if hasattr(self.main_app, '_load_and_apply_menu_visibility'):
                    self.main_app._load_and_apply_menu_visibility(menu_guid)
            
            logger.info(f"✅ V3-Menü komplett geladen: {menu_guid}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden von V3-Menü {menu_guid}: {e}", exc_info=True)
            return False
    
    def load_startmenu(self) -> bool:
        """
        Lädt Startmenü aus User-Daten
        
        LINEAR:
        1. Startmenü-GUID aus gcs._user_data holen
        2. load_menu() aufrufen
        
        Returns:
            True bei Erfolg
        """
        try:
            logger.info("🔐 Lade V3-Startmenü")
            
            # Hole Startmenü-GUID aus User-Daten
            user_data = self.gcs._user_data
            meine_apps = user_data.get('MEINEAPPS', {})
            start_menu_guid = meine_apps.get('START')
            
            if not start_menu_guid:
                logger.error("❌ Kein Startmenü in User-Daten definiert (MEINEAPPS.START)")
                return False
            
            logger.info(f"🔍 Startmenü-GUID: {start_menu_guid}")
            
            # Lade Menü
            return self.load_menu(start_menu_guid)
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden von V3-Startmenü: {e}", exc_info=True)
            return False
    
    def load_zusatz(self, parent_item_guid: str) -> bool:
        """
        Lädt Zusatzmenü für Parent-Item
        
        LINEAR:
        1. Parent-Item finden
        2. ZUSATZ-Items aus Menü-Struktur filtern (parent_guid Match)
        3. Widget erstellen
        
        Args:
            parent_item_guid: GUID des Parent-Items
            
        Returns:
            True bei Erfolg
        """
        try:
            logger.info(f"🔄 Lade ZUSATZ für Item: {parent_item_guid}")
            
            # Parent-Item finden
            parent_item = self.current_items.get(parent_item_guid)
            if not parent_item:
                logger.warning(f"⚠️ Parent-Item {parent_item_guid} nicht gefunden")
                return False
            
            # ZUSATZ-Items filtern (alle Items mit parent_guid == parent_item_guid)
            zusatz_items = [
                item for item in self.current_items.values()
                if item.parent_guid == parent_item_guid
            ]
            
            logger.info(f"📋 ZUSATZ-Items gefunden: {len(zusatz_items)}")
            
            # Clear Container
            self._clear_container(self.zusatz_container)
            
            # Widget erstellen (nur wenn Items vorhanden)
            if zusatz_items:
                self.zusatz_widget = V3HorizontalMenu(zusatz_items)
                self.zusatz_widget.item_clicked.connect(self._on_item_click)
                
                layout = self.zusatz_container.layout()
                if not layout:
                    layout = QHBoxLayout(self.zusatz_container)
                    layout.setContentsMargins(0, 0, 0, 0)
                layout.addWidget(self.zusatz_widget)
                
                # ZUSATZ-Items auch in Cache aufnehmen
                for item in zusatz_items:
                    self.current_items[item.guid] = item
                
                logger.info("✅ Zusatzmenü angezeigt")
            else:
                logger.info("ℹ️ Kein Zusatzmenü für dieses Item")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden von ZUSATZ: {e}", exc_info=True)
            return False
    
    def _on_item_click(self, item_guid: str):
        """
        Handler für Item-Click
        
        LINEAR:
        1. ZUSATZ laden
        2. Command ausführen (falls vorhanden)
        """
        try:
            logger.info(f"🖱️ Item geklickt: {item_guid}")
            
            # State speichern
            self.current_item_guid = item_guid
            
            # 1. ZUSATZ laden
            self.load_zusatz(item_guid)
            
            # 2. Command ausführen (falls vorhanden)
            item = self.current_items.get(item_guid)
            if item and item.command:
                logger.info(f"⚡ Führe Command aus: {item.command}")
                self._execute_command(item.command, item_guid)
            else:
                logger.info("ℹ️ Kein Command für dieses Item")
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Item-Click: {e}", exc_info=True)
    
    def _execute_command(self, command: Dict[str, Any], item_guid: str):
        """
        Führt Command aus über Handler-Registry MIT ARBEITSBEREICHS-PIPELINE
        
        Args:
            command: Command-Dict mit handler und params
            item_guid: GUID des Items
        """
        try:
            handler_name = command.get('handler')
            params = command.get('params', {})
            
            if not handler_name:
                logger.warning("⚠️ Kein Handler im Command definiert")
                # Pipeline mit leerem Arbeitsbereich
                if hasattr(self, 'main_app') and self.main_app:
                    self.main_app.workspace_pipeline()
                return
            
            logger.info(f"🎯 Execute Command via Pipeline: handler={handler_name}, params={params}")
            
            # Handler-Registry holen
            from handlers import get_handler_registry
            registry = get_handler_registry()
            
            # Context für Handler erstellen
            context = {
                'item_guid': item_guid,
                'menu_guid': self.current_menu_guid,
                'menu_handler': self,
                'gcs': self.gcs,
                'main_app': getattr(self, 'main_app', None)  # Falls gesetzt
            }
            
            # Handler-Funktion vorbereiten
            handler_func = registry.get(handler_name)
            
            if not handler_func:
                logger.error(f"❌ Handler nicht gefunden: {handler_name}")
                error_msg = (
                    f"Handler '{handler_name}' nicht registriert!\n\n"
                    f"Verfügbare Handler:\n{', '.join(registry.list_available())}"
                )
                # Pipeline mit Fehlermeldung
                if hasattr(self, 'main_app') and self.main_app:
                    self.main_app.workspace_pipeline(error_message=error_msg)
                return
            
            # V3.1: Prüfe Handler-Metadaten für skip_clear
            skip_clear = False
            try:
                # Hole Handler-Modul
                handler_module_name = f"handler_{handler_name}"
                import importlib
                handler_module = importlib.import_module(f"handlers.{handler_module_name}")
                
                # Prüfe auf SKIP_CLEAR Attribut
                if hasattr(handler_module, 'SKIP_CLEAR'):
                    skip_clear = handler_module.SKIP_CLEAR
                    logger.info(f"   📋 Handler-Metadaten: skip_clear={skip_clear}")
            except Exception as e:
                logger.debug(f"   ℹ️ Keine Metadaten gefunden (verwende skip_clear=False): {e}")
            
            # PIPELINE: Arbeitsbereich löschen + Handler ausführen
            if hasattr(self, 'main_app') and self.main_app:
                # Command als Callable für Pipeline wrappen
                def execute_handler():
                    try:
                        success = handler_func(params, context, self.gcs)
                        if success:
                            logger.info(f"✅ Command erfolgreich: {handler_name}")
                        else:
                            logger.warning(f"⚠️ Command fehlgeschlagen: {handler_name}")
                        return success
                    except Exception as e:
                        logger.error(f"❌ Handler-Fehler: {e}", exc_info=True)
                        raise
                
                # V3.1: Pipeline mit skip_clear Parameter ausführen
                self.main_app.workspace_pipeline(
                    command_func=execute_handler,
                    skip_clear=skip_clear  # ← Aus Handler-Metadaten!
                )
            else:
                # Fallback ohne Pipeline (sollte nicht vorkommen)
                logger.warning("⚠️ main_app nicht verfügbar - Pipeline übersprungen")
                handler_func(params, context, self.gcs)
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Command-Ausführung: {e}", exc_info=True)
            # Pipeline mit Fehlermeldung
            if hasattr(self, 'main_app') and self.main_app:
                self.main_app.workspace_pipeline(error_message=f"Command-Fehler:\n{str(e)}")
    
    def _clear_container(self, container: QWidget):
        """
        Entfernt alle Widgets aus Container
        
        LINEAR:
        1. Layout holen
        2. Alle Widgets entfernen
        3. Layout löschen
        """
        layout = container.layout()
        if not layout:
            return
        
        # Widgets entfernen
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Layout löschen
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
    print("🧪 V3 Menu Handler Test")
    print("=" * 60)
    print("⚠️ HINWEIS: Test benötigt initialisiertes GCS + QApplication")
    print("   Führe v2_main.py aus für vollständigen Test")
    print("=" * 60)
    
    print("\n✅ Import erfolgreich")
    print("   V3MenuHandler: ✓")
    
    print("\n🎯 V3 Menu Handler Ready!")
    print("\n📋 Features:")
    print("   • load_menu() - LINEAR: Loader → Widgets → Anzeige")
    print("   • load_startmenu() - Mit User-Daten")
    print("   • load_zusatz() - Dynamisches Zusatzmenü")
    print("   • _on_item_click() - Command-Ausführung")
