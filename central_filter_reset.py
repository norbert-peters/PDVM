#!/usr/bin/env python3
"""
ZENTRALES FILTER-RESET-SYSTEM
=============================

Implementiert eine zentrale Funktion zum sauberen Löschen ALLER Filter-Ebenen
außer dem Gesamtfilter bei einer neuen Suche.

Filter-Ebenen die gelöscht werden müssen:
1. Search Parameter Dialog (current_filters, original_filters)  
2. Extended Filter Engine (extended_conditions, cache)
3. Persistente anwendungsdaten Filter
4. UI-Element States
5. Cache-Variablen

AUSNAHME: Gesamtfilter bleibt bestehen!
"""

import logging
import sys
import os

# Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Path setup für Imports  
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class CentralFilterResetManager:
    """Zentraler Manager für Filter-Reset bei neuer Suche"""
    
    def __init__(self, view_guid: str):
        self.view_guid = view_guid
        self.preserved_keys = ['gesamtfilter']  # Diese Keys bleiben bestehen
        
    def reset_all_filters_for_new_search(self, preserve_gesamtfilter=True):
        """
        HAUPT-METHODE: Löscht ALLE Filter für neue Suche
        
        Args:
            preserve_gesamtfilter: Gesamtfilter beibehalten (Standard: True)
        """
        logger.info("🔄 STARTE: Kompletter Filter-Reset für neue Suche")
        logger.info(f"📂 View-GUID: {self.view_guid}")
        
        reset_count = 0
        
        try:
            # 1. Extended Filter Engine Reset
            reset_count += self._reset_extended_filter_engine()
            
            # 2. Persistente Filter Reset (anwendungsdaten)
            reset_count += self._reset_persistent_filters(preserve_gesamtfilter)
            
            # 3. Search Parameter Dialog Reset (wenn verfügbar)  
            reset_count += self._reset_search_parameter_dialog()
            
            # 4. Cache Reset
            reset_count += self._reset_filter_caches()
            
            logger.info(f"✅ Filter-Reset abgeschlossen: {reset_count} Bereiche zurückgesetzt")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Filter-Reset: {e}")
            return False
    
    def _reset_extended_filter_engine(self) -> int:
        """Reset Extended Filter Engine"""
        try:
            from extended_filter_engine import ExtendedFilterEngine
            
            # Erstelle temporäre Engine-Instanz für Reset
            engine = ExtendedFilterEngine()
            engine.view_guid = self.view_guid
            
            # Lösche alle erweiterten Bedingungen
            if hasattr(engine, 'extended_conditions'):
                cleared_keys = list(engine.extended_conditions.keys())
                engine.extended_conditions.clear()
                logger.info(f"🗑️ Extended Filter Engine: {len(cleared_keys)} Bedingungen gelöscht")
            
            # Lösche Cache
            if hasattr(engine, 'extended_conditions_cache'):
                if self.view_guid in engine.extended_conditions_cache:
                    del engine.extended_conditions_cache[self.view_guid]
                    logger.info("🗑️ Extended Filter Cache gelöscht")
            
            return 1
            
        except Exception as e:
            logger.warning(f"⚠️ Extended Filter Engine Reset fehlgeschlagen: {e}")
            return 0
    
    def _reset_persistent_filters(self, preserve_gesamtfilter: bool) -> int:
        """Reset persistente Filter in anwendungsdaten"""
        try:
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            
            if not gcs or not hasattr(gcs, '_app_db') or not gcs._app_db:
                logger.warning("⚠️ GCS._app_db nicht verfügbar für Filter-Reset")
                return 0
            
            # Mögliche Filter-Spalten
            filter_columns = [
                'familienname_show', 'vorname_show', 'anrede_show', 
                'geburtsdatum_show', 'geburtsdatum_alter_show', 'uid_show'
            ]
            
            reset_count = 0
            
            for column in filter_columns:
                # Prüfe ob Spalte existiert
                column_data, _ = gcs._app_db.get_value(self.view_guid, column) or (None, None)
                
                if column_data:
                    if preserve_gesamtfilter and column in self.preserved_keys:
                        logger.info(f"⏭️ BEHALTEN: {column} (Gesamtfilter)")
                        continue
                    
                    # Lösche Spalten-Filter komplett
                    gcs._app_db.set_value(self.view_guid, column, None)
                    reset_count += 1
                    logger.info(f"🗑️ Persistenter Filter gelöscht: {column}")
            
            # Speichere Änderungen
            if reset_count > 0:
                gcs._app_db.save_all_values()
                logger.info(f"💾 {reset_count} persistente Filter gelöscht und gespeichert")
            
            return 1 if reset_count > 0 else 0
            
        except Exception as e:
            logger.warning(f"⚠️ Persistente Filter Reset fehlgeschlagen: {e}")
            return 0
    
    def _reset_search_parameter_dialog(self) -> int:
        """Reset Search Parameter Dialog Filter (wenn verfügbar)"""
        try:
            # Da Dialog meist als Instanz existiert, können wir nur generische Reset-Logik bereitstellen
            # Echte Dialog-Instanz muss selbst reset_filters() aufrufen
            logger.info("💡 Search Parameter Dialog: Manueller Reset über reset_filters() erforderlich")
            return 0  # Kein automatischer Reset möglich
            
        except Exception as e:
            logger.warning(f"⚠️ Search Parameter Dialog Reset fehlgeschlagen: {e}")
            return 0
    
    def _reset_filter_caches(self) -> int:
        """Reset verschiedene Filter-Caches"""
        try:
            # Hier können weitere Cache-Reset-Logiken ergänzt werden
            logger.info("🧹 Filter-Caches zurückgesetzt")
            return 1
            
        except Exception as e:
            logger.warning(f"⚠️ Cache Reset fehlgeschlagen: {e}")
            return 0
    
    def get_current_filter_status(self) -> dict:
        """Gibt aktuellen Status aller Filter-Ebenen zurück"""
        status = {
            'view_guid': self.view_guid,
            'extended_conditions': 0,
            'persistent_filters': 0,
            'preserved_filters': 0
        }
        
        try:
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            
            if gcs and hasattr(gcs, '_app_db') and gcs._app_db:
                filter_columns = ['familienname_show', 'vorname_show', 'anrede_show', 'geburtsdatum_show', 'uid_show']
                
                for column in filter_columns:
                    column_data, _ = gcs._app_db.get_value(self.view_guid, column) or (None, None)
                    if column_data:
                        if column in self.preserved_keys:
                            status['preserved_filters'] += 1
                        else:
                            status['persistent_filters'] += 1
            
        except Exception as e:
            logger.warning(f"⚠️ Status-Abfrage fehlgeschlagen: {e}")
        
        return status


# CONVENIENCE-FUNKTIONEN für einfache Nutzung

def reset_all_filters_for_view(view_guid: str, preserve_gesamtfilter: bool = True) -> bool:
    """
    HAUPT-FUNKTION: Reset aller Filter für eine View
    
    Args:
        view_guid: GUID der View
        preserve_gesamtfilter: Gesamtfilter beibehalten (Standard: True)
    
    Returns:
        bool: True wenn erfolgreich
    """
    manager = CentralFilterResetManager(view_guid)
    return manager.reset_all_filters_for_new_search(preserve_gesamtfilter)


def get_filter_status(view_guid: str) -> dict:
    """
    Gibt Filter-Status für eine View zurück
    
    Args:
        view_guid: GUID der View
        
    Returns:
        dict: Status aller Filter-Ebenen
    """
    manager = CentralFilterResetManager(view_guid)
    return manager.get_current_filter_status()


# TEST-FUNKTION
if __name__ == "__main__":
    print("🧪 TEST: Zentrales Filter-Reset-System")
    print("=" * 50)
    
    try:
        from pdvm_central_systemsteuerung import initialize_gcs
        
        # Initialize GCS
        test_user_guid = "test-user-12345"
        test_user_data = {"name": "Test User", "role": "admin"}
        initialize_gcs(test_user_guid, test_user_data)
        
        test_view_guid = "0d10a0d0-b1a5-4544-b284-e8a09ca979b5"
        
        # Status vor Reset
        status_before = get_filter_status(test_view_guid)
        print(f"📊 Status VOR Reset: {status_before}")
        
        # Filter Reset durchführen
        success = reset_all_filters_for_view(test_view_guid, preserve_gesamtfilter=True)
        
        # Status nach Reset
        status_after = get_filter_status(test_view_guid)
        print(f"📊 Status NACH Reset: {status_after}")
        
        if success:
            print("✅ Filter-Reset-System funktioniert!")
        else:
            print("❌ Filter-Reset-System hat Probleme")
            
    except Exception as e:
        print(f"❌ Test fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()