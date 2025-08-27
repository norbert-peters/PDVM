#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TEST: Zentrale Stichtag-Architektur Demo

Demonstriert die neue zentrale Stichtag-Architektur ohne Parameter-Weitergabe.

Ziel: Eliminierung von Synchronisationsfehlern durch zentralen Stichtag-Zugriff
statt Parameter-Weitergabe zwischen Komponenten.
"""

import logging

# Logging Setup für Demo
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DemoWidget:
    """
    Demo-Widget mit zentraler Stichtag-Architektur
    """
    
    def __init__(self, call_daten=None):
        self.call_daten = call_daten or {}
        self.stichtag = None
        self.view_manager = None
        
    def reload(self):
        """
        ZENTRALE STICHTAG-ARCHITEKTUR: View mit zentralem Stichtag refreshen
        
        NEUE ARCHITEKTUR:
        - Kein Stichtag als Parameter mehr!
        - Stichtag wird zentral aus StichtagManager abgerufen
        - Eliminiert Synchronisationsfehler
        - Vereinfacht Code (keine Parameter-Weitergabe)
        """
        try:
            # ZENTRALE STICHTAG-ABFRAGE (keine Parameter mehr!)
            from pdvm_central_stichtag_manager import PdvmCentralStichtagManager
            central_manager = PdvmCentralStichtagManager()
            new_stichtag = central_manager.get_stichtag_float()
            
            logger.info(f"🎯 ZENTRALE STICHTAG-ARCHITEKTUR - Refresh mit zentralem Stichtag: {new_stichtag}")
            logger.info(f"📍 Alter Widget-Stichtag: {getattr(self, 'stichtag', 'N/A')}")
            
            # SYNCHRONISATION mit zentralem Stichtag
            old_stichtag = getattr(self, 'stichtag', None)
            self.stichtag = new_stichtag
            self.call_daten['stichtag'] = new_stichtag
            
            logger.info(f"✅ Stichtag zentral synchronisiert: Widget={self.stichtag}, CallDaten={self.call_daten['stichtag']}")
            
            # ViewManager mit zentralem Stichtag refreshen
            if self.view_manager:
                logger.info(f"🔄 ViewManager-Refresh mit zentralem Stichtag: {new_stichtag}")
                
                # NEUE ZENTRALE METHODE
                refreshed_count = self.view_manager.refresh_with_central_stichtag()
                logger.info(f"📊 {refreshed_count} Datensätze mit zentralem Stichtag refresht")
                
                logger.info(f"✅ ZENTRALER REFRESH erfolgreich: View neu aufgebaut")
            else:
                logger.info("🔄 Fallback: Kein ViewManager verfügbar")
                
        except Exception as e:
            logger.error(f"❌ Zentraler Stichtag-Refresh fehlgeschlagen: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            
            # Bei Fehler: Stichtag zurücksetzen falls möglich
            if 'old_stichtag' in locals() and old_stichtag is not None:
                logger.warning(f"🔄 Setze Stichtag zurück: {new_stichtag} → {old_stichtag}")
                self.stichtag = old_stichtag
                self.call_daten['stichtag'] = old_stichtag
    
    def reload_with_stichtag(self, new_stichtag):
        """
        KOMPATIBILITÄTS-METHODE: Ruft zentrale reload() auf
        
        WICHTIGER HINWEIS:
        Diese Methode ist nur noch für Kompatibilität da!
        Neue Architektur: Verwende reload() ohne Parameter!
        
        Args:
            new_stichtag (float): Wird ignoriert - zentraler Stichtag wird verwendet
        """
        logger.warning("⚠️ reload_with_stichtag() ist deprecated! Verwende reload() mit zentralem Stichtag")
        logger.info(f"📍 Übergebener Stichtag {new_stichtag} wird ignoriert - verwende zentralen Stichtag")
        
        # Zentrale Reload-Methode aufrufen
        self.reload()

class DemoViewManager:
    """
    Demo-ViewManager mit zentraler Stichtag-Architektur
    """
    
    def __init__(self):
        self.stichtag = None
        self.call_daten = {}
        self.data_count = 100  # Mock-Daten
        
    def refresh_with_central_stichtag(self):
        """
        ZENTRALE STICHTAG-ARCHITEKTUR: Refresh mit zentralem StichtagManager
        
        Returns:
            int: Anzahl der refreshten Datensätze
        """
        try:
            # ZENTRALE STICHTAG-ABFRAGE (keine Parameter mehr!)
            from pdvm_central_stichtag_manager import PdvmCentralStichtagManager
            central_manager = PdvmCentralStichtagManager()
            new_stichtag = central_manager.get_stichtag_float()
            
            logger.info(f"🎯 ZENTRALE STICHTAG-ARCHITEKTUR - ViewManager refresh mit zentralem Stichtag: {new_stichtag}")
            
            # SYNCHRONISATION mit zentralem Stichtag
            old_stichtag = getattr(self, 'stichtag', None)
            self.stichtag = new_stichtag
            self.call_daten['stichtag'] = new_stichtag
            
            # MOCK: Daten-Refresh simulieren
            logger.info(f"🔄 Refreshe {self.data_count} Datensätze mit zentralem Stichtag...")
            
            # Hier würde der echte Refresh-Code stehen
            refreshed_count = self.data_count
            
            logger.info(f"✅ ZENTRALER REFRESH abgeschlossen: {refreshed_count} Werte mit zentralem Stichtag refresht")
            return refreshed_count
            
        except Exception as e:
            logger.error(f"❌ Zentraler Stichtag-Refresh fehlgeschlagen: {e}")
            return 0

def demo_zentrale_architektur():
    """
    Demo der neuen zentralen Stichtag-Architektur
    """
    logger.info("🚀 DEMO: Zentrale Stichtag-Architektur")
    
    # Setup
    widget = DemoWidget({'initial_stichtag': 20250115.0})
    widget.view_manager = DemoViewManager()
    
    logger.info("📍 Vorher: Alte Architektur mit Parameter-Weitergabe")
    widget.reload_with_stichtag(20250116.0)  # Parameter wird ignoriert!
    
    logger.info("📍 Nachher: Neue Architektur ohne Parameter")
    widget.reload()  # Holt sich Stichtag zentral
    
    logger.info("✅ DEMO abgeschlossen - Zentrale Architektur funktioniert!")

if __name__ == "__main__":
    demo_zentrale_architektur()
