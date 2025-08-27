#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
SAUBERE VERSION: pdvm_view_daten_manager.py mit zentraler Stichtag-Architektur

Enthält die neuen Methoden:
- refresh_with_central_stichtag() ohne Parameter (zentrale Stichtag-Abfrage)
- refresh_with_stichtag() als Kompatibilitätsmethode

STATUS: Bereit für Integration in echtes System
"""

import logging

logger = logging.getLogger(__name__)

class PdvmViewDatenManager_CentralStichtagArchitecture:
    """
    Demo-Implementierung der zentralen Stichtag-Architektur für PdvmViewDatenManager
    
    NEUE ARCHITEKTUR:
    - refresh_with_central_stichtag() ohne Parameter holt Stichtag zentral
    - Eliminiert Parameter-Passing zwischen Komponenten
    - Verhindert Synchronisationsfehler
    """
    
    def __init__(self):
        self.stichtag = None
        self.call_daten = {}
        self.column_control = None
        self.datenbank = None
        
    def refresh_with_central_stichtag(self):
        """
        🎯 ZENTRALE STICHTAG-ARCHITEKTUR: Refresh mit zentralem StichtagManager
        
        NEUE ARCHITEKTUR:
        - Kein Stichtag als Parameter mehr!
        - Stichtag wird zentral aus PdvmCentralStichtagManager abgerufen
        - Eliminiert Synchronisationsfehler zwischen Komponenten
        - Vereinfacht Code (keine Parameter-Weitergabe)
        
        Returns:
            int: Anzahl der refreshten Datensätze
        """
        try:
            # ZENTRALE STICHTAG-ABFRAGE (keine Parameter mehr!)
            from pdvm_central_stichtag_manager import PdvmCentralStichtagManager
            
            # WICHTIG: In echtem System muss PdvmCentralStichtagManager bereits initialisiert sein
            # central_manager = PdvmCentralStichtagManager.get_instance()  # Singleton
            # Für Demo verwenden wir Mock:
            logger.info("📍 DEMO: In echtem System hier globalen PdvmCentralStichtagManager verwenden")
            
            # MOCK für Demo (in echtem System ersetzen):
            new_stichtag = 20250116.0  # central_manager.get_stichtag_float()
            
            logger.info(f"🎯 ZENTRALE STICHTAG-ARCHITEKTUR - ViewManager refresh mit zentralem Stichtag: {new_stichtag}")
            logger.info(f"📍 Alter ViewManager-Stichtag: {getattr(self, 'stichtag', 'N/A')}")
            
            if not self.column_control or not getattr(self.column_control, 'row_guids', None):
                logger.warning("⚠️ Keine Daten zum Refreshen vorhanden")
                return 0
                
            # SYNCHRONISATION mit zentralem Stichtag
            old_stichtag = getattr(self, 'stichtag', None)
            self.stichtag = new_stichtag
            
            # SYNCHRONISATION: Auch call_daten mit zentralem Stichtag aktualisieren
            if hasattr(self, 'call_daten') and self.call_daten:
                logger.info(f"🔄 Synchronisiere call_daten mit zentralem Stichtag: {self.call_daten.get('stichtag')} → {new_stichtag}")
                self.call_daten['stichtag'] = new_stichtag
            
            # DEMO: Mock refresh process
            logger.info("📋 DEMO: In echtem System hier get_value Aufrufe mit zentralem Stichtag")
            
            # MOCK für Demo (in echtem System würde hier der echte Code stehen):
            mock_row_guids = ['54073c2c-demo', 'another-guid']
            mock_spalten = ['Familienname', 'Vorname', 'Geburtsdatum']
            
            refreshed_count = 0
            for row_guid in mock_row_guids:
                for spaltenname in mock_spalten:
                    try:
                        # HIER: get_value mit zentralem Stichtag (echter Code)
                        # new_value = self.datenbank.get_value(row_guid, spaltenname, new_stichtag)
                        
                        # DEMO Mock:
                        if row_guid == '54073c2c-demo' and spaltenname == 'Familienname':
                            new_value = "Mustermann"  # Mock: Juli 2025 hat Familienname
                            old_value = ""  # Mock: Juni 2025 war leer
                            
                            guid_short = str(row_guid)[:12]
                            logger.info(f"   🔄 DEMO: {guid_short}.../{spaltenname}: '{old_value}' → '{new_value}'")
                        
                        refreshed_count += 1
                    except Exception as e:
                        logger.warning(f"⚠️ DEMO: Refresh-Fehler für {row_guid[:12]}.../{spaltenname}: {e}")
            
            logger.info(f"✅ ZENTRALER REFRESH abgeschlossen: {refreshed_count} Werte mit zentralem Stichtag refresht")
            return refreshed_count
            
        except Exception as e:
            logger.error(f"❌ Zentraler Stichtag-Refresh fehlgeschlagen: {e}")
            import traceback
            logger.error(f"❌ Traceback: {traceback.format_exc()}")
            
            # Bei Fehler: Stichtag zurücksetzen falls möglich
            if 'old_stichtag' in locals() and old_stichtag is not None:
                logger.warning(f"🔄 Setze Stichtag zurück: {new_stichtag} → {old_stichtag}")
                self.stichtag = old_stichtag
                if hasattr(self, 'call_daten') and self.call_daten:
                    self.call_daten['stichtag'] = old_stichtag
            
            return 0
    
    def refresh_with_stichtag(self, new_stichtag):
        """
        KOMPATIBILITÄTS-METHODE: Ruft zentrale refresh_with_central_stichtag() auf
        
        WICHTIGER HINWEIS:
        Diese Methode ist nur noch für Kompatibilität da!
        Neue Architektur: Verwende refresh_with_central_stichtag() ohne Parameter!
        
        Args:
            new_stichtag (float): Wird ignoriert - zentraler Stichtag wird verwendet
            
        Returns:
            int: Anzahl der refreshten Datensätze
        """
        logger.warning("⚠️ refresh_with_stichtag() ist deprecated! Verwende refresh_with_central_stichtag() mit zentralem Stichtag")
        logger.info(f"📍 Übergebener Stichtag {new_stichtag} wird ignoriert - verwende zentralen Stichtag")
        
        # Zentrale Refresh-Methode aufrufen
        return self.refresh_with_central_stichtag()

# ============================================================================
# INTEGRATION PLAN FÜR ECHTEN VIEWMANAGER
# ============================================================================

def viewmanager_integration_code():
    """
    Code-Beispiel für echte Integration in pdvm_view_daten_manager.py
    """
    
    return '''
# In echtem pdvm_view_daten_manager.py:

def refresh_with_central_stichtag(self):
    """
    ZENTRALE STICHTAG-ARCHITEKTUR: Refresh mit zentralem StichtagManager
    """
    try:
        # ZENTRALE STICHTAG-ABFRAGE
        from pdvm_central_stichtag_manager import PdvmCentralStichtagManager
        
        # WICHTIG: Globale Instanz verwenden (bereits initialisiert)
        central_manager = get_global_stichtag_manager()  # Oder Singleton Pattern
        new_stichtag = central_manager.get_stichtag_float()
        
        if not self.column_control or not self.column_control.row_guids:
            return 0
            
        # SYNCHRONISATION mit zentralem Stichtag
        old_stichtag = self.stichtag
        self.stichtag = new_stichtag
        
        if hasattr(self, 'call_daten') and self.call_daten:
            self.call_daten['stichtag'] = new_stichtag
        
        # REFRESH: Alle get_value Aufrufe mit zentralem Stichtag erneuern
        refreshed_count = 0
        for row_guid in self.column_control.row_guids:
            for spaltenname in self.column_control.spalten_dict.keys():
                try:
                    # get_value mit zentralem Stichtag
                    new_value = self.datenbank.get_value(row_guid, spaltenname, new_stichtag)
                    
                    # Wert im column_control aktualisieren
                    if row_guid in self.column_control.werte_dict:
                        if spaltenname in self.column_control.werte_dict[row_guid]:
                            old_value = self.column_control.werte_dict[row_guid][spaltenname]
                            self.column_control.werte_dict[row_guid][spaltenname] = new_value
                            
                            # Logging nur bei Änderungen (für GUID 54073c2c Debugging)
                            if old_value != new_value:
                                guid_short = str(row_guid)[:12]
                                logger.info(f"   🔄 {guid_short}.../{spaltenname}: '{old_value}' → '{new_value}'")
                                
                            refreshed_count += 1
                except Exception as e:
                    logger.warning(f"⚠️ Refresh-Fehler für {row_guid[:12]}.../{spaltenname}: {e}")
        
        logger.info(f"✅ ZENTRALER REFRESH: {refreshed_count} Werte refresht")
        return refreshed_count
        
    except Exception as e:
        logger.error(f"❌ Zentraler Stichtag-Refresh fehlgeschlagen: {e}")
        return 0

def refresh_with_stichtag(self, new_stichtag):
    """KOMPATIBILITÄTS-METHODE - deprecated!"""
    logger.warning("⚠️ refresh_with_stichtag() deprecated! Verwende refresh_with_central_stichtag()")
    return self.refresh_with_central_stichtag()
    '''

if __name__ == "__main__":
    # Demo der neuen ViewManager Architektur
    logging.basicConfig(level=logging.INFO)
    
    print("🚀 DEMO: Zentrale Stichtag-Architektur für PdvmViewDatenManager")
    print("=" * 70)
    
    view_manager = PdvmViewDatenManager_CentralStichtagArchitecture()
    
    # Mock column_control für Demo
    class MockColumnControl:
        def __init__(self):
            self.row_guids = ['54073c2c-demo', 'another-guid']
    
    view_manager.column_control = MockColumnControl()
    
    print("\n📍 DEMO: Alte Methode (deprecated)")
    result = view_manager.refresh_with_stichtag(20250115.0)  # Parameter wird ignoriert!
    print(f"Refreshed: {result} Datensätze")
    
    print("\n📍 DEMO: Neue Methode (zentral)")
    result = view_manager.refresh_with_central_stichtag()  # Kein Parameter!
    print(f"Refreshed: {result} Datensätze")
    
    print("\n" + "=" * 70)
    print("📋 INTEGRATION CODE für echten ViewManager:")
    print(viewmanager_integration_code())
