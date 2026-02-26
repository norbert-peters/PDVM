"""
📋 EINFACH-FILTER MANAGER
=========================
ZWECK: Verwaltet einfache parametrische Filter (feldbasiert, ein Wert pro Feld)
PATTERN:
  1. Sammelt Parameter aus UI (z.B. {"familienname_show": "Müller"})
  2. Baut einheitlichen search_string: "familienname_show:contains:Müller"
  3. Speichert Parameter + s_string + s_source
  4. Ruft save_all_values() auf
  5. Ruft matrix_manager.apply_filter(search_string)
"""

import logging
from typing import Optional, Dict, Any
from pdvm_central_systemsteuerung import get_gcs

logger = logging.getLogger(__name__)


class EinfachFilterManager:
    """Manager für einfache parametrische Filter"""
    
    def __init__(self, view_guid: str, matrix_manager, controller=None):
        """
        Args:
            view_guid: Eindeutige View-GUID
            matrix_manager: Referenz zum MatrixManager für Filter-Ausführung
            controller: Referenz zum View-Controller für UI-Refresh (optional)
        """
        self.view_guid = view_guid
        self.matrix_manager = matrix_manager
        self.controller = controller
        self.gcs = get_gcs()
        
        if not self.gcs:
            logger.error("❌ GCS nicht initialisiert!")
            raise RuntimeError("GCS nicht verfügbar")
        
        logger.info(f"📋 EinfachFilterManager initialisiert für View: {view_guid}")
    
    def execute_einfach_filter(self, filter_params: Dict[str, str]) -> bool:
        """
        Führt einfachen Filter aus - ULTRA EINFACH!
        
        1. Parameter unter 'einfach' in app_db speichern
        2. s_string und s_source setzen
        3. save_all_values()
        4. pipeline.run('FILTER') → Pipeline läuft durch!
        
        Args:
            filter_params: Dict mit Feld → Wert Paaren
                          z.B. {"familienname_show": "Müller", "vorname_show": "Max"}
            
        Returns:
            True wenn erfolgreich, False bei Fehler
        """
        try:
            logger.info(f"📋 Einfach-Filter: {filter_params}")
            
            # 1. Parameter unter 'einfach' speichern
            self.gcs._app_db.set_value(self.view_guid, 'einfach', filter_params)
            logger.info(f"💾 Parameter unter 'einfach' gespeichert")
            
            # 2. Einheitlichen search_string bauen
            search_string = self._build_search_string(filter_params)
            logger.info(f"🔨 search_string: '{search_string}'")
            
            # 3. s_string + s_source setzen
            self.gcs._app_db.set_value(self.view_guid, 's_string', search_string)
            self.gcs._app_db.set_value(self.view_guid, 's_source', 'einfach')
            
            # 4. In DB schreiben
            self.gcs._app_db.save_all_values()
            logger.info(f"✅ save_all_values() aufgerufen")
            
            # 5. Pipeline durchlaufen - EINFACH!
            from pdvm_pipeline import get_pipeline
            pipeline = get_pipeline(self.view_guid, self.matrix_manager)
            pipeline.run('FILTER')
            
            # 6. UI aktualisieren (wenn Controller verfügbar)
            if self.controller:
                logger.info("🎨 UI-Refresh nach Filter...")
                self.controller.refresh_ui_from_pipeline()
            else:
                logger.warning("⚠️ Controller nicht verfügbar - kein UI-Refresh")
            
            logger.info(f"✅ Einfach-Filter abgeschlossen")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler in Einfach-Filter: {e}", exc_info=True)
            return False
    
    def _build_search_string(self, filter_params: Dict[str, str]) -> str:
        """
        Baut einheitlichen search_string für Matrix Manager
        
        Format: "feld1:contains:wert1||feld2:contains:wert2"
        
        Args:
            filter_params: Dict mit Feld → Wert Paaren
            
        Returns:
            Einheitlicher search_string
        """
        if not filter_params:
            return ""
        
        # EINHEITLICHES FORMAT: Feld:Operator:Wert
        # Standard-Operator für einfache Filter: contains
        parts = []
        for field_key, value in filter_params.items():
            if value and value.strip():
                part = f"{field_key}:contains:{value.strip()}"
                parts.append(part)
        
        # Multi-Field mit ||
        search_string = "||".join(parts)
        
        return search_string
    
    def load_einfach_filter_ui(self) -> Dict[str, Any]:
        """
        Lädt einfache Filter für UI-Anzeige (nur wenn s_source == 'einfach')
        
        Returns:
            Dict mit field_key → Parameter Mappings
        """
        try:
            # Prüfe s_source
            s_source, _ = self.gcs._app_db.get_value(self.view_guid, 's_source')
            
            if s_source != 'einfach':
                logger.info(f"ℹ️ Einfach-Filter-UI nicht laden (s_source='{s_source}')")
                return {}
            
            # Lade alle Feld-Parameter
            # Wir müssen wissen, welche Felder es gibt - aus column_control?
            # Hier erstmal empty, UI muss für jedes Feld einzeln laden
            
            logger.info(f"🔄 Einfach-Filter-UI bereit zum Laden")
            return {}
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden Einfach-Filter-UI: {e}")
            return {}
    
    def load_field_filter(self, field_key: str) -> Optional[str]:
        """
        Lädt Filter für ein bestimmtes Feld
        
        Args:
            field_key: Feld-Key (z.B. "familienname_show")
            
        Returns:
            Filter-Wert oder None
        """
        try:
            # Hole einfach-Daten
            einfach_data, _ = self.gcs._app_db.get_value(self.view_guid, 'einfach')
            
            if einfach_data and isinstance(einfach_data, dict):
                value = einfach_data.get(field_key, '')
                return value if value else None
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden Feld-Filter {field_key}: {e}")
            return None
    
    def clear_einfach_filter(self, field_keys: list = None) -> bool:
        """
        Löscht einfache Filter - NUR s_string/s_source, Parameter bleiben!
        
        Args:
            field_keys: Nicht verwendet (für zukünftige Erweiterungen)
            
        Returns:
            True wenn erfolgreich
        """
        try:
            logger.info(f"🗑️ Lösche Einfach-Filter (nur s_string/s_source)")
            
            # NUR s_string und s_source löschen, Parameter bleiben!
            self.gcs._app_db.set_value(self.view_guid, 's_string', None)
            self.gcs._app_db.set_value(self.view_guid, 's_source', None)
            self.gcs._app_db.save_all_values()
            
            logger.info(f"✅ s_string/s_source gelöscht, Parameter 'einfach' bleiben erhalten")
            
            # Pipeline ab FILTER neu durchlaufen
            from pdvm_pipeline import get_pipeline
            pipeline = get_pipeline(self.view_guid, self.matrix_manager)
            pipeline.run('FILTER')
            
            logger.info(f"✅ Pipeline ab FILTER neu durchlaufen")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Löschen Einfach-Filter: {e}", exc_info=True)
            return False
