#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SAUBERE VERSION: pdvm_view_widget.py mit zentraler Stichtag-Architektur

Enthält die neuen Methoden:
- reload() ohne Parameter (zentrale Stichtag-Abfrage)
- reload_with_stichtag() als Kompatibilitätsmethode
- refresh_with_central_stichtag() im ViewManager

STATUS: Bereit für Integration in echtes System
"""

import logging

logger = logging.getLogger(__name__)

class PdvmViewWidget_CentralStichtagArchitecture:
    """
    Demo-Implementierung der zentralen Stichtag-Architektur für PdvmViewWidget
    
    NEUE ARCHITEKTUR:
    - reload() ohne Parameter holt Stichtag zentral
    - Eliminiert Parameter-Passing zwischen Komponenten
    - Verhindert Synchronisationsfehler
    """
    
    def __init__(self, call_daten=None):
        self.call_daten = call_daten or {}
        self.stichtag = None
        self.view_manager = None
        self.table = None  # QTableWidget in echtem System
        
    def reload(self):
        """
        🎯 ZENTRALE STICHTAG-ARCHITEKTUR: View mit zentralem Stichtag refreshen
        
        NEUE ARCHITEKTUR:
        - Kein Stichtag als Parameter mehr!
        - Stichtag wird zentral aus StichtagManager abgerufen
        - Eliminiert Synchronisationsfehler
        - Vereinfacht Code (keine Parameter-Weitergabe)
        
        Der einheitliche Refresh-Weg:
        1. Zentralen Stichtag aus PdvmCentralStichtagManager abrufen
        2. Call-Daten damit synchronisieren
        3. View komplett neu aufbauen (wie Neustart ohne DB-Reload)
        """
        try:
            # ZENTRALE STICHTAG-ABFRAGE (keine Parameter mehr!)
            from pdvm_central_stichtag_manager import PdvmCentralStichtagManager
            
            # WICHTIG: In echtem System muss PdvmCentralStichtagManager bereits initialisiert sein
            # central_manager = PdvmCentralStichtagManager(central_systemsteuerung, user_guid)
            # Für Demo verwenden wir Mock:
            logger.info("📍 DEMO: In echtem System hier PdvmCentralStichtagManager verwenden")
            
            # MOCK für Demo (in echtem System ersetzen):
            new_stichtag = 20250116.0  # central_manager.get_stichtag_float()
            
            logger.info(f"🎯 ZENTRALE STICHTAG-ARCHITEKTUR - Refresh mit zentralem Stichtag: {new_stichtag}")
            logger.info(f"📍 Alter Widget-Stichtag: {getattr(self, 'stichtag', 'N/A')}")
            
            # SYNCHRONISATION mit zentralem Stichtag
            old_stichtag = getattr(self, 'stichtag', None)
            self.stichtag = new_stichtag
            self.call_daten['stichtag'] = new_stichtag
            
            logger.info(f"✅ Stichtag zentral synchronisiert: Widget={self.stichtag}, CallDaten={self.call_daten['stichtag']}")
            
            # VIEW NEU AUFBAUEN (einheitlicher Code, ohne DB-Reload)
            logger.info("🏗️ Baue View mit zentralem Stichtag neu auf")
            
            # ViewManager mit zentralem Stichtag refreshen
            if self.view_manager:
                logger.info(f"🔄 ViewManager-Refresh mit zentralem Stichtag: {new_stichtag}")
                
                # NEUE ZENTRALE METHODE (ohne Parameter!)
                refreshed_count = self.view_manager.refresh_with_central_stichtag()
                logger.info(f"📊 {refreshed_count} Datensätze mit zentralem Stichtag refresht")
                
                # JETZT: Tabelle komplett neu laden (einheitlich wie bei load_data)
                self._reload_table_completely()
                
                logger.info(f"✅ ZENTRALER REFRESH erfolgreich: View neu aufgebaut")
            else:
                # Fallback: Kompletter Neuaufbau mit neuen Call-Daten
                logger.info("🔄 Fallback: Kompletter View-Neuaufbau")
                self.load_data()
                
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

    def _reload_table_completely(self):
        """
        EINHEITLICHES TABELLE-NEULADEN
        
        Identisch mit load_data(), aber ohne ViewManager neu zu erstellen.
        Verwendet den einheitlichen PdvmSpaltenManager-Code.
        
        WICHTIG: Prüft Stichtag-Konsistenz vor Tabellen-Aufbau
        """
        try:
            logger.info("🔄 EINHEITLICHES TABELLE-NEULADEN (wie load_data)")
            
            if not self.view_manager:
                logger.warning("⚠️ Kein ViewManager für Tabelle-Neuladen")
                return
            
            # WICHTIGE KONSISTENZ-PRÜFUNG: Stichtage synchron?
            widget_stichtag = self.stichtag
            viewmanager_stichtag = getattr(self.view_manager, 'stichtag', None)
            calldata_stichtag = self.call_daten.get('stichtag', None)
            
            if widget_stichtag != viewmanager_stichtag or widget_stichtag != calldata_stichtag:
                logger.warning(f"⚠️ STICHTAG INKONSISTENZ erkannt:")
                logger.warning(f"   Widget: {widget_stichtag}")
                logger.warning(f"   ViewManager: {viewmanager_stichtag}")
                logger.warning(f"   CallDaten: {calldata_stichtag}")
                
                # Korrigiere die Inkonsistenz
                if viewmanager_stichtag != widget_stichtag:
                    logger.info(f"🔧 Korrigiere ViewManager-Stichtag: {viewmanager_stichtag} → {widget_stichtag}")
                    self.view_manager.stichtag = widget_stichtag
                    if hasattr(self.view_manager, 'call_daten') and self.view_manager.call_daten:
                        self.view_manager.call_daten['stichtag'] = widget_stichtag
            else:
                logger.info(f"✅ Stichtag-Konsistenz OK: {widget_stichtag}")
            
            logger.info("📋 DEMO: In echtem System hier PdvmSpaltenManager + QTableWidget Code")
            
            # DEMO: Mock table reload
            logger.info("📊 DEMO Tabelle neu geladen: Mock-Daten mit zentralem Stichtag")
            logger.info("   🔄 DEMO: Erste paar Zeilen würden hier geloggt")
            logger.info("   📋 DEMO: QTableWidget würde hier neu aufgebaut")
            logger.info("✅ DEMO Tabelle komplett neu geladen")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Tabelle-Neuladen: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")

    def load_data(self):
        """Mock für load_data in echtem System"""
        logger.info("🔄 DEMO: load_data() - kompletter Neuaufbau")

# ============================================================================
# INTEGRATION PLAN FÜR ECHTES SYSTEM
# ============================================================================

def integration_plan():
    """
    Plan für Integration in echtes pdvm_view_widget.py System
    """
    
    print("""
🎯 INTEGRATION PLAN: Zentrale Stichtag-Architektur in echtes System

SCHRITT 1: Widget-Code reparieren ✅ ERLEDIGT
  ├─ Neue reload() Methode ohne Parameter hinzufügen
  ├─ reload_with_stichtag() als Kompatibilitätsmethode
  └─ _reload_table_completely() mit Konsistenz-Prüfung

SCHRITT 2: Globale PdvmCentralStichtagManager Instanz ⏳ ZU TUN
  ├─ In PDVM-Systemstart.py nach Login initialisieren:
  │   central_stichtag_manager = PdvmCentralStichtagManager(
  │       central_systemsteuerung, user_guid, initial_stichtag
  │   )
  ├─ Als globale Variable oder App-Attribut speichern
  └─ In reload() echten Manager statt Mock verwenden

SCHRITT 3: Alle reload_with_stichtag() Aufrufe ersetzen ⏳ ZU TUN
  ├─ Suche nach: reload_with_stichtag(
  ├─ Ersetze durch: reload()
  └─ Test: Funktionalität bleibt gleich, aber ohne Parameter

SCHRITT 4: ViewManager Integration ✅ ERLEDIGT
  ├─ refresh_with_central_stichtag() bereits implementiert
  └─ In reload() verwenden statt refresh_with_stichtag()

VORTEILE der neuen Architektur:
  ✅ Keine Parameter-Weitergabe mehr
  ✅ Eliminiert Synchronisationsfehler  
  ✅ Einfacherer, sauberer Code
  ✅ Zentrale Stichtag-Kontrolle
  ✅ Weniger Fehlerquellen
    """)

if __name__ == "__main__":
    # Demo der neuen Architektur
    logger.basicConfig(level=logging.INFO)
    
    print("🚀 DEMO: Zentrale Stichtag-Architektur für PdvmViewWidget")
    print("=" * 60)
    
    widget = PdvmViewWidget_CentralStichtagArchitecture({'test': True})
    
    # Mock ViewManager für Demo
    class MockViewManager:
        def __init__(self):
            self.stichtag = None
            self.call_daten = {}
        def refresh_with_central_stichtag(self):
            logger.info("📊 DEMO: ViewManager refresh_with_central_stichtag() aufgerufen")
            return 42  # Mock count
    
    widget.view_manager = MockViewManager()
    
    print("\n📍 DEMO: Alte Methode (deprecated)")
    widget.reload_with_stichtag(20250115.0)  # Parameter wird ignoriert!
    
    print("\n📍 DEMO: Neue Methode (zentral)")
    widget.reload()  # Kein Parameter!
    
    print("\n" + "=" * 60)
    integration_plan()
