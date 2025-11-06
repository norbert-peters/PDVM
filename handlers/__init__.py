"""
Handler-Registry für PDVM V2.0 Command System
==============================================

Dieses Modul verwaltet alle Command-Handler.

Handler-Konvention:
- Dateiname: handler_<name>.py
- Funktion: execute(params: dict, context: dict, gcs) -> bool
- Auto-Import über get_handler_registry()

Autor: PDVM V2.0
Datum: 01.11.2025
"""

import logging
import importlib
import os
from pathlib import Path
from typing import Dict, Callable, Optional

logger = logging.getLogger(__name__)


class HandlerRegistry:
    """
    Registry für dynamisches Laden von Handlern
    
    Convention-over-Configuration:
    - handler_open_view.py → 'open_view'
    - handler_show_dialog.py → 'show_dialog'
    """
    
    def __init__(self):
        """Initialisiert Registry"""
        self._handlers: Dict[str, Callable] = {}
        self._handler_dir = Path(__file__).parent
        logger.info("✅ HandlerRegistry initialisiert")
    
    def register(self, handler_name: str, handler_func: Callable):
        """
        Registriert Handler manuell
        
        Args:
            handler_name: Name des Handlers (z.B. 'open_view')
            handler_func: Funktion mit Signatur (params, context, gcs) -> bool
        """
        self._handlers[handler_name] = handler_func
        logger.info(f"✅ Handler registriert: {handler_name}")
    
    def get(self, handler_name: str) -> Optional[Callable]:
        """
        Holt Handler (lädt automatisch bei Bedarf)
        
        Args:
            handler_name: Name des Handlers
            
        Returns:
            Handler-Funktion oder None
        """
        # Bereits geladen?
        if handler_name in self._handlers:
            return self._handlers[handler_name]
        
        # Versuche zu laden
        if self._load_handler(handler_name):
            return self._handlers.get(handler_name)
        
        return None
    
    def _load_handler(self, handler_name: str) -> bool:
        """
        Lädt Handler dynamisch aus Datei
        
        Args:
            handler_name: Name des Handlers (z.B. 'open_view')
            
        Returns:
            True wenn erfolgreich geladen
        """
        try:
            # Dateiname ableiten: open_view → handler_open_view.py
            module_name = f"handler_{handler_name}"
            file_path = self._handler_dir / f"{module_name}.py"
            
            if not file_path.exists():
                logger.warning(f"⚠️ Handler-Datei nicht gefunden: {file_path}")
                return False
            
            # Dynamischer Import
            module = importlib.import_module(f"handlers.{module_name}")
            
            # Hole execute-Funktion
            if not hasattr(module, 'execute'):
                logger.error(f"❌ Handler {module_name} hat keine execute() Funktion")
                return False
            
            # Registriere
            self._handlers[handler_name] = module.execute
            logger.info(f"✅ Handler dynamisch geladen: {handler_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden von Handler {handler_name}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def load_all(self):
        """Lädt alle Handler aus dem handlers/ Verzeichnis"""
        logger.info("🔄 Lade alle Handler...")
        
        count = 0
        for file_path in self._handler_dir.glob("handler_*.py"):
            # handler_open_view.py → open_view
            handler_name = file_path.stem.replace("handler_", "")
            
            if self._load_handler(handler_name):
                count += 1
        
        logger.info(f"✅ {count} Handler geladen")
    
    def list_available(self) -> list:
        """
        Listet alle verfügbaren Handler
        
        Returns:
            Liste von Handler-Namen
        """
        # Bereits geladene
        loaded = set(self._handlers.keys())
        
        # Verfügbare Dateien
        available = set()
        for file_path in self._handler_dir.glob("handler_*.py"):
            handler_name = file_path.stem.replace("handler_", "")
            available.add(handler_name)
        
        return sorted(loaded | available)


# Singleton-Instanz
_registry: Optional[HandlerRegistry] = None


def get_handler_registry() -> HandlerRegistry:
    """
    Holt Singleton-Instanz der Handler-Registry
    
    Returns:
        HandlerRegistry-Instanz
    """
    global _registry
    if _registry is None:
        _registry = HandlerRegistry()
    return _registry


def register_handler(handler_name: str, handler_func: Callable):
    """
    Shortcut: Registriert Handler
    
    Args:
        handler_name: Name des Handlers
        handler_func: Handler-Funktion
    """
    registry = get_handler_registry()
    registry.register(handler_name, handler_func)


def get_handler(handler_name: str) -> Optional[Callable]:
    """
    Shortcut: Holt Handler
    
    Args:
        handler_name: Name des Handlers
        
    Returns:
        Handler-Funktion oder None
    """
    registry = get_handler_registry()
    return registry.get(handler_name)
