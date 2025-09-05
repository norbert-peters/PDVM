#!/usr/bin/env python3
"""
PdvmViewManagerRegistry - Singleton Registry für persistente DatenManager
Implementiert die neue Architektur: DatenManager (persistent) -> Widget (disposable)

NEUE ARCHITEKTUR:
DatenManager (singleton/persistent)
├── Widget erstellen/refreshen  
├── Controls verwalten (vollständig)  
└── Daten aktualisieren  

Damit sind die Column Controls immer da, auch nach Widget-Neustart!
"""

import logging
import traceback
from typing import Dict, Any, Optional, TYPE_CHECKING

# Verhindert zirkuläre Imports zur Laufzeit
if TYPE_CHECKING:
    from pdvm_view_daten_manager import PdvmViewDatenManager
    from pdvm_view_widget_new_architecture import PdvmViewWidget

logger = logging.getLogger(__name__)


class PdvmViewManagerRegistry:
    """
    Singleton-Registry für persistente DatenManager Instanzen.
    Jeder DatenManager lebt für eine view_guid und bleibt über Widget-Refreshs hinweg erhalten.
    """
    
    _instance: Optional['PdvmViewManagerRegistry'] = None
    _managers: Dict[str, 'PdvmViewDatenManager'] = {}
    
    def __new__(cls) -> 'PdvmViewManagerRegistry':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def get_manager(cls, call_daten: dict) -> 'PdvmViewDatenManager':
        """
        Holt oder erstellt einen persistenten DatenManager für eine view_guid.
        
        Returns:
            PdvmViewDatenManager: Persistente Instanz (überlebt Widget-Refreshs)
        """
        registry = cls()
        view_guid = call_daten.get('view_guid', 'default')
        
        if view_guid not in registry._managers:
            logger.info(f"🆕 Erstelle neuen persistenten DatenManager für view_guid: {view_guid}")
            from pdvm_view_daten_manager import PdvmViewDatenManager
            registry._managers[view_guid] = PdvmViewDatenManager(call_daten)
        else:
            logger.info(f"♻️ Verwende bestehenden persistenten DatenManager für view_guid: {view_guid}")
            # Update call_daten für bestehenden Manager (falls sich Parameter geändert haben)
            registry._managers[view_guid].update_call_daten(call_daten)
            
        return registry._managers[view_guid]
    
    @classmethod
    def refresh_manager(cls, view_guid: str):
        """
        Führt einen Refresh für einen bestehenden DatenManager durch.
        Der DatenManager bleibt erhalten, nur die Daten/Projektion wird aktualisiert.
        """
        registry = cls()
        if view_guid in registry._managers:
            manager = registry._managers[view_guid]
            logger.info(f"🔄 Refreshe persistenten DatenManager für view_guid: {view_guid}")
            manager.refresh_controls_and_projection()
        else:
            logger.warning(f"⚠️ Kein DatenManager für Refresh gefunden: {view_guid}")
    
    @classmethod 
    def create_widget_for_manager(cls, call_daten: dict, parent=None, reload_callback=None) -> 'PdvmViewWidget':
        """
        NEUE ARCHITEKTUR: Erstellt ein Widget das von einem persistenten DatenManager kontrolliert wird.
        
        Der DatenManager:
        - Ist persistent (überlebt Widget-Refreshs)  
        - Verwaltet alle Column Controls vollständig
        - Erstellt/kontrolliert das Widget
        
        Das Widget:
        - Ist disposable (kann jederzeit neu erstellt werden)
        - Holt alle Daten vom persistenten DatenManager
        - Verliert nie Settings, weil der DatenManager persistent ist
        """
        try:
            # 1. Persistenten DatenManager holen/erstellen
            manager = cls.get_manager(call_daten)
            
            # 2. Widget vom DatenManager erstellen lassen
            widget = manager.create_controlled_widget(parent=parent, reload_callback=reload_callback)
            
            logger.info(f"✅ Widget erfolgreich von persistentem DatenManager erstellt")
            return widget
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen des DatenManager-kontrollierten Widgets: {e}")
            traceback.print_exc()
            raise
    
    @classmethod
    def refresh_widget_for_manager(cls, view_guid: str) -> Optional['PdvmViewWidget']:
        """
        Führt einen Widget-Refresh über den persistenten DatenManager durch.
        Der DatenManager bleibt erhalten und erstellt das Widget neu.
        """
        registry = cls()
        if view_guid in registry._managers:
            manager = registry._managers[view_guid]
            logger.info(f"🔄 Refreshe Widget über persistenten DatenManager: {view_guid}")
            return manager.refresh_controlled_widget()
        else:
            logger.error(f"❌ Kein persistenter DatenManager für Widget-Refresh gefunden: {view_guid}")
            return None
    
    @classmethod
    def clear_manager(cls, view_guid: str):
        """Entfernt einen DatenManager aus der Registry (für Cleanup)."""
        registry = cls()
        if view_guid in registry._managers:
            del registry._managers[view_guid]
            logger.info(f"🗑️ DatenManager entfernt: {view_guid}")
    
    @classmethod
    def get_all_managers(cls) -> Dict[str, 'PdvmViewDatenManager']:
        """Gibt alle aktiven DatenManager zurück (für Debugging)."""
        registry = cls()
        return registry._managers.copy()
