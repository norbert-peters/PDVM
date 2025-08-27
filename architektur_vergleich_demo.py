#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
KONZEPT: Zentrale Stichtag-Architektur Implementation

Diese Datei zeigt das Konzept für die zentrale Stichtag-Architektur.

PROBLEM:
- Parameter-Weitergabe führt zu Synchronisationsfehlern
- reload_with_stichtag(new_stichtag) ist fehleranfällig
- Inkonsistenzen zwischen Widget, ViewManager und CallDaten

LÖSUNG:
- Zentrale Stichtag-Instanz (PdvmCentralStichtagManager)
- Keine Parameter-Weitergabe mehr
- reload() ohne Parameter holt sich Strichtag zentral

ARCHITECTURE:
1. Zentrale Stichtag-Verwaltung durch PdvmCentralStichtagManager
2. Widget.reload() ohne Parameter
3. ViewManager.refresh_with_central_stichtag() ohne Parameter
4. Alle Komponenten greifen auf dieselbe zentrale Instanz zu

VORTEILE:
- Keine Synchronisationsfehler mehr
- Einfacherer Code (keine Parameter)
- Konsistente Stichtag-Verwaltung
- Weniger Fehlerquellen
"""

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# ZENTRALE STICHTAG-VERWALTUNG (Singleton Pattern)
# ============================================================================

class GlobalStichtagManager:
    """
    Globale Stichtag-Instanz für Demo-Zwecke
    
    In der echten Anwendung wird das durch PdvmCentralStichtagManager ersetzt,
    der einmal initialisiert und dann global verfügbar ist.
    """
    _instance = None
    _stichtag = 20250116.0
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def get_stichtag_float(self):
        logger.debug(f"🎯 Zentral abgerufener Stichtag: {self._stichtag}")
        return self._stichtag
    
    def set_stichtag(self, new_stichtag):
        logger.info(f"🗓️ Zentral gesetzter Stichtag: {self._stichtag} → {new_stichtag}")
        self._stichtag = new_stichtag

# ============================================================================
# NEUE ZENTRALE ARCHITEKTUR
# ============================================================================

class ModernWidget:
    """
    Widget mit zentraler Stichtag-Architektur (NACH dem Refactoring)
    """
    
    def __init__(self, call_daten=None):
        self.call_daten = call_daten or {}
        self.stichtag = None
        self.view_manager = None
        
    def reload(self):
        """
        🎯 ZENTRALE STICHTAG-ARCHITEKTUR: reload() OHNE Parameter
        
        Vorteile:
        - Kein Parameter-Passing mehr
        - Stichtag wird zentral abgerufen
        - Keine Synchronisationsfehler
        - Einfacher Code
        """
        try:
            # ZENTRALE STICHTAG-ABFRAGE
            stichtag_manager = GlobalStichtagManager.get_instance()
            new_stichtag = stichtag_manager.get_stichtag_float()
            
            logger.info(f"✨ MODERNE ARCHITEKTUR: reload() mit zentralem Stichtag {new_stichtag}")
            
            # Synchronisation (nur intern, kein Parameter-Passing)
            self.stichtag = new_stichtag
            self.call_daten['stichtag'] = new_stichtag
            
            # ViewManager refresh (auch OHNE Parameter!)
            if self.view_manager:
                refreshed_count = self.view_manager.refresh_with_central_stichtag()
                logger.info(f"📊 {refreshed_count} Datensätze refresht")
                
            logger.info("✅ MODERNE ARCHITEKTUR: reload() erfolgreich")
            
        except Exception as e:
            logger.error(f"❌ Moderner reload() fehlgeschlagen: {e}")

class ModernViewManager:
    """
    ViewManager mit zentraler Stichtag-Architektur (NACH dem Refactoring)
    """
    
    def __init__(self):
        self.stichtag = None
        self.call_daten = {}
        self.data_count = 50
        
    def refresh_with_central_stichtag(self):
        """
        🎯 ZENTRALE STRICHTAG-ARCHITEKTUR: refresh_with_central_stichtag() OHNE Parameter
        
        Returns:
            int: Anzahl refreshter Datensätze
        """
        try:
            # ZENTRALE STICHTAG-ABFRAGE
            stichtag_manager = GlobalStichtagManager.get_instance()
            new_stichtag = stichtag_manager.get_stichtag_float()
            
            logger.info(f"✨ MODERNE ARCHITEKTUR: ViewManager refresh mit zentralem Stichtag {new_stichtag}")
            
            # Synchronisation (nur intern)
            self.stichtag = new_stichtag
            self.call_daten['stichtag'] = new_stichtag
            
            # Data refresh simulation
            refreshed_count = self.data_count
            logger.info(f"🔄 ViewManager: {refreshed_count} Datensätze mit zentralem Stichtag refresht")
            
            return refreshed_count
            
        except Exception as e:
            logger.error(f"❌ Moderner ViewManager refresh fehlgeschlagen: {e}")
            return 0

# ============================================================================
# ALTE ARCHITEKTUR (vor dem Refactoring)
# ============================================================================

class LegacyWidget:
    """
    Widget mit alter Parameter-Passing-Architektur (VOR dem Refactoring)
    """
    
    def __init__(self, call_daten=None):
        self.call_daten = call_daten or {}
        self.stichtag = None
        self.view_manager = None
        
    def reload_with_stichtag(self, new_stichtag):
        """
        ❌ ALTE ARCHITEKTUR: reload_with_stichtag(parameter) - FEHLERANFÄLLIG
        
        Probleme:
        - Parameter-Passing zwischen Komponenten
        - Synchronisationsfehler möglich
        - Komplexerer Code
        - Fehlerquelle: Welcher Stichtag ist aktuell?
        """
        try:
            logger.info(f"⚠️ ALTE ARCHITEKTUR: reload_with_stichtag({new_stichtag})")
            
            # Problematische Synchronisation mit Parametern
            old_stichtag = self.stichtag
            self.stichtag = new_stichtag  # Widget-Stichtag
            self.call_daten['stichtag'] = new_stichtag  # CallDaten-Stichtag
            
            # Parameter-Passing an ViewManager (fehleranfällig!)
            if self.view_manager:
                refreshed_count = self.view_manager.refresh_with_stichtag(new_stichtag)  # Parameter!
                logger.info(f"📊 {refreshed_count} Datensätze refresht")
                
            logger.info("✅ ALTE ARCHITEKTUR: reload_with_stichtag() erfolgreich")
            
        except Exception as e:
            logger.error(f"❌ Alter reload_with_stichtag() fehlgeschlagen: {e}")

class LegacyViewManager:
    """
    ViewManager mit alter Parameter-Passing-Architektur (VOR dem Refactoring)
    """
    
    def __init__(self):
        self.stichtag = None
        self.call_daten = {}
        self.data_count = 50
        
    def refresh_with_stichtag(self, new_stichtag):
        """
        ❌ ALTE ARCHITEKTUR: refresh_with_stichtag(parameter) - PARAMETER-PASSING
        
        Probleme:
        - Stichtag als Parameter (Synchronisationsfehler möglich)
        - Komplexere Aufruf-Kette
        - Fehlerquelle: Stimmen alle Stichtag-Parameter überein?
        """
        try:
            logger.info(f"⚠️ ALTE ARCHITEKTUR: ViewManager refresh_with_stichtag({new_stichtag})")
            
            # Problematische Parameter-Synchronisation
            if self.stichtag != new_stichtag:
                logger.warning(f"⚠️ SYNCHRONISATION: ViewManager-Stichtag {self.stichtag} ≠ Parameter {new_stichtag}")
            
            self.stichtag = new_stichtag
            self.call_daten['stichtag'] = new_stichtag
            
            # Data refresh simulation
            refreshed_count = self.data_count
            logger.info(f"🔄 ViewManager: {refreshed_count} Datensätze refresht")
            
            return refreshed_count
            
        except Exception as e:
            logger.error(f"❌ Alter ViewManager refresh fehlgeschlagen: {e}")
            return 0

# ============================================================================
# DEMO & VERGLEICH
# ============================================================================

def demo_architecture_comparison():
    """
    Vergleich zwischen alter und neuer Architektur
    """
    logger.info("🔄 ARCHITEKTUR-VERGLEICH: Alt vs. Neu")
    logger.info("=" * 60)
    
    # Setup globaler Stichtag
    stichtag_manager = GlobalStichtagManager.get_instance()
    stichtag_manager.set_stichtag(20250116.0)
    
    print()
    logger.info("❌ ALTE ARCHITEKTUR - Parameter-Passing:")
    logger.info("-" * 40)
    
    legacy_widget = LegacyWidget({'test': True})
    legacy_widget.view_manager = LegacyViewManager()
    legacy_widget.view_manager.stichtag = 20250115.0  # Inkonsistenz möglich!
    
    # Alter Aufruf mit Parameter
    legacy_widget.reload_with_stichtag(20250117.0)
    
    print()
    logger.info("✨ NEUE ARCHITEKTUR - Zentrale Verwaltung:")
    logger.info("-" * 40)
    
    modern_widget = ModernWidget({'test': True})
    modern_widget.view_manager = ModernViewManager()
    
    # Neuer Aufruf OHNE Parameter
    modern_widget.reload()
    
    print()
    logger.info("🎯 FAZIT:")
    logger.info("- Alte Architektur: Parameter-Passing, Synchronisationsfehler möglich")
    logger.info("- Neue Architektur: Zentral, konsistent, einfacher")
    logger.info("- Refactoring eliminiert Fehlerquellen!")

if __name__ == "__main__":
    demo_architecture_comparison()
