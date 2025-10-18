"""
🗑️ FILTER RESET MANAGER
=======================
ZWECK: Zentrale, einfache Methode zum Löschen aller Filter-Typen
PATTERN: 
  1. Parameter des spezifischen Filters löschen (schnell/einfach/komplex)
  2. s_string + s_source für die View löschen
  3. save_all_values() aufrufen
  4. Matrix Manager Filter entfernen: apply_filter(None)
  
VERWENDUNG:
    manager = FilterResetManager(view_guid, matrix_manager)
    manager.reset_filter('schnell')  # Löscht Schnellsuche
    manager.reset_filter('einfach')  # Löscht Einfach-Filter
    manager.reset_filter('komplex')  # Löscht Komplex-Filter
    manager.reset_all_filters()      # Löscht ALLE Filter
"""

import logging
from typing import Optional, Literal
from pdvm_central_systemsteuerung import get_gcs

logger = logging.getLogger(__name__)

FilterType = Literal['schnell', 'einfach', 'komplex']


class FilterResetManager:
    """Zentraler Manager zum Löschen aller Filter-Typen"""
    
    def __init__(self, view_guid: str, matrix_manager):
        """
        Args:
            view_guid: Eindeutige View-GUID
            matrix_manager: Matrix Manager (für Pipeline)
        """
        self.view_guid = view_guid
        self.matrix_manager = matrix_manager
        self.gcs = get_gcs()
        
        if not self.gcs:
            logger.error("❌ GCS nicht initialisiert!")
            raise RuntimeError("GCS nicht verfügbar")
        
        # Pipeline holen
        from pdvm_pipeline import get_pipeline
        self.pipeline = get_pipeline(view_guid, matrix_manager)
        
        logger.info(f"🗑️ FilterResetManager initialisiert für View: {view_guid[:20]}...")
    
    def reset_all_filters(self) -> bool:
        """
        Löscht ALLE AKTIVEN Filter - Parameter bleiben erhalten!
        
        WICHTIG: Nur s_string, s_source und schnell werden gelöscht.
        Die Parameter von 'einfach' und 'komplex' bleiben erhalten!
        
        1. 'schnell', 's_string', 's_source' auf None
        2. save_all_values()
        3. pipeline.run('FILTER') → Pipeline läuft durch!
        
        Returns:
            True wenn erfolgreich, False bei Fehler
        """
        try:
            logger.info(f"🗑️ ALLE AKTIVEN Filter löschen (Parameter bleiben)")
            
            # NUR aktive Filter löschen, Parameter bleiben!
            self.gcs._app_db.set_value(self.view_guid, 'schnell', None)
            self.gcs._app_db.set_value(self.view_guid, 's_string', None)
            self.gcs._app_db.set_value(self.view_guid, 's_source', None)
            # 'einfach' und 'komplex' Parameter BLEIBEN erhalten!
            
            # 2. In DB schreiben
            self.gcs._app_db.save_all_values()
            logger.info(f"✅ s_string/s_source/schnell gelöscht, einfach/komplex bleiben")
            
            # 3. Pipeline durchlaufen - EINFACH!
            self.pipeline.run('FILTER')
            
            logger.info(f"✅ Alle aktiven Filter gelöscht, Parameter erhalten")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Filter-Reset: {e}", exc_info=True)
            return False
    
    def get_active_filter_type(self) -> Optional[FilterType]:
        """
        Ermittelt welcher Filter-Typ aktuell aktiv ist
        
        Returns:
            'schnell' | 'einfach' | 'komplex' | None
        """
        try:
            s_source, _ = self.gcs._app_db.get_value(self.view_guid, 's_source')
            
            if s_source in ['schnell', 'einfach', 'komplex']:
                return s_source
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Ermitteln aktiver Filter: {e}")
            return None


def get_filter_reset_manager(view_guid: str, matrix_manager) -> FilterResetManager:
    """
    Factory-Funktion für FilterResetManager
    
    Args:
        view_guid: Eindeutige View-GUID
        matrix_manager: Referenz zum MatrixManager
        
    Returns:
        FilterResetManager-Instanz
    """
    return FilterResetManager(view_guid, matrix_manager)
