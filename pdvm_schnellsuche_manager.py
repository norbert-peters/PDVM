"""
🔍 SCHNELLSUCHE MANAGER
======================
ZWECK: Verwaltet Schnellsuche (globale Suche über alle sichtbaren Spalten)
PATTERN: 
  1. Sammelt Parameter aus UI
  2. Baut einheitlichen search_string: "GLOBAL:contains:lau"
  3. Speichert Parameter + s_string + s_source
  4. Ruft save_all_values() auf
  5. Ruft matrix_manager.apply_filter(search_string)
"""

import logging
from typing import Optional, Dict, Any
from pdvm_central_systemsteuerung import get_gcs

logger = logging.getLogger(__name__)


class SchnellsucheManager:
    """Manager für Schnellsuche - setzt DB und ruft Pipeline auf"""
    
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
        
        logger.info(f"🔍 SchnellsucheManager initialisiert für View: {view_guid[:20]}...")
    
    def execute_schnellsuche(self, search_text: str) -> bool:
        """
        Führt Schnellsuche aus - ULTRA EINFACH!
        
        1. Parameter in app_db speichern
        2. save_all_values()
        3. pipeline.run('FILTER') → Pipeline läuft durch!
        
        Args:
            search_text: Suchtext aus UI (z.B. "lau")
            
        Returns:
            True wenn erfolgreich, False bei Fehler
        """
        try:
            logger.info(f"🔍 Schnellsuche: '{search_text}'")
            
            # 1. Parameter in app_db speichern
            params = {'search_text': search_text}
            self.gcs._app_db.set_value(self.view_guid, 'schnell', params)
            self.gcs._app_db.set_value(self.view_guid, 's_string', search_text.strip())
            self.gcs._app_db.set_value(self.view_guid, 's_source', 'schnell')
            
            # 2. In DB schreiben
            self.gcs._app_db.save_all_values()
            
            # 3. Pipeline durchlaufen - EINFACH!
            self.pipeline.run('FILTER')
            
            logger.info(f"✅ Schnellsuche abgeschlossen")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler in Schnellsuche: {e}", exc_info=True)
            return False
    
    def _build_search_string(self, search_text: str) -> str:
        """
        Baut einheitlichen search_string für Matrix Manager
        
        Format: "GLOBAL:contains:suchtext"
        
        GLOBAL signalisiert Matrix Manager: Suche in ALLEN sichtbaren Spalten
        
        Args:
            search_text: Suchtext aus UI
            
        Returns:
            Einheitlicher search_string
        """
        if not search_text or not search_text.strip():
            return ""
        
        # EINHEITLICHES FORMAT: Feld:Operator:Wert
        # GLOBAL = spezielle Markierung für "alle Spalten durchsuchen"
        search_string = f"GLOBAL:contains:{search_text.strip()}"
        
        return search_string
    
    def load_schnellsuche_ui(self) -> Optional[str]:
        """
        Lädt Schnellsuche für UI-Anzeige (nur wenn s_source == 'schnell')
        
        Returns:
            Suchtext oder None wenn andere Filter aktiv
        """
        try:
            # Prüfe s_source
            s_source, _ = self.gcs._app_db.get_value(self.view_guid, 's_source')
            
            if s_source != 'schnell':
                logger.info(f"ℹ️ Schnellsuche-UI nicht laden (s_source='{s_source}')")
                return None
            
            # Lade Parameter
            params, _ = self.gcs._app_db.get_value(self.view_guid, 'schnell')
            
            if params and isinstance(params, dict):
                search_text = params.get('search_text', '')
                logger.info(f"🔄 Schnellsuche-UI geladen: '{search_text}'")
                return search_text
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden Schnellsuche-UI: {e}")
            return None
    
    def clear_schnellsuche(self) -> bool:
        """
        Löscht Schnellsuche komplett
        
        Löscht Schnellsuche - NUR s_string/s_source, Parameter bleiben!
        
        Returns:
            True wenn erfolgreich
        """
        try:
            logger.info(f"🗑️ Lösche Schnellsuche (nur s_string/s_source)")
            
            # NUR s_string und s_source löschen, Parameter bleiben!
            self.gcs._app_db.set_value(self.view_guid, 's_string', None)
            self.gcs._app_db.set_value(self.view_guid, 's_source', None)
            self.gcs._app_db.save_all_values()
            
            logger.info(f"✅ s_string/s_source gelöscht, Parameter 'schnell' bleiben erhalten")
            
            # Pipeline ab FILTER neu durchlaufen
            from pdvm_pipeline import get_pipeline
            pipeline = get_pipeline(self.view_guid, self.matrix_manager)
            pipeline.run('FILTER')
            
            logger.info(f"✅ Pipeline ab FILTER neu durchlaufen")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Löschen Schnellsuche: {e}", exc_info=True)
            return False
