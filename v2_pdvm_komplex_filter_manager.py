"""
🔬 KOMPLEX-FILTER MANAGER V2
============================
ZWECK: Verwaltet komplexe Extended Filter (mehrere Bedingungen pro Feld, AND/OR)
PATTERN:
  1. Sammelt Bedingungen aus UI (4-Positionen Struktur)
  2. Baut einheitlichen search_string: "familienname_show:AND|IS|contains|Müller"
  3. Speichert Bedingungen + s_string + s_source
  4. Ruft save_all_values() auf
  5. Ruft matrix_manager.apply_filter(search_string)
"""

import logging
from typing import Optional, Dict, Any, List
from v2_central_systemsteuerung import get_gcs

logger = logging.getLogger(__name__)


class KomplexFilterManager:
    """Manager für komplexe Extended Filter"""
    
    def __init__(self, view_guid: str, matrix_manager):
        """
        Args:
            view_guid: Eindeutige View-GUID
            matrix_manager: Referenz zum MatrixManager für Filter-Ausführung
        """
        self.view_guid = view_guid
        self.matrix_manager = matrix_manager
        self.gcs = get_gcs()
        
        if not self.gcs:
            logger.error("❌ GCS nicht initialisiert!")
            raise RuntimeError("GCS nicht verfügbar")
        
        logger.info(f"🔬 KomplexFilterManager initialisiert für View: {view_guid}")
    
    def execute_komplex_filter(self, field_conditions: Dict[str, List[Dict]]) -> bool:
        """
        Führt komplexen Filter aus und persistiert alle Daten
        
        Args:
            field_conditions: Dict mit Feld → Bedingungen
                             z.B. {
                               "familienname_show": [
                                 {
                                   "position_1": "AND",
                                   "position_2": "IS",
                                   "position_3": "enthält",
                                   "position_4": "Müller"
                                 }
                               ]
                             }
            
        Returns:
            True wenn erfolgreich, False bei Fehler
        """
        try:
            logger.info(f"🔬 Komplex-Filter gestartet: {len(field_conditions)} Felder")
            
            # 1. Bedingungen unter Feld 'komplex' speichern (wie 'einfach'!)
            # Struktur: {field_key: conditions}
            komplex_data = {}
            for field_key, conditions in field_conditions.items():
                komplex_data[field_key] = {
                    'simple_search': '',  # Leer für komplexe Filter
                    'conditions': conditions
                }
                logger.info(f"💾 Feld-Bedingungen vorbereitet: {field_key} = {len(conditions)} Bedingungen")
            
            self.gcs._app_db.set_value(self.view_guid, 'komplex', komplex_data)
            logger.info(f"💾 Komplex-Parameter gespeichert: {self.view_guid}.komplex")
            
            # 2. Einheitlichen search_string bauen
            search_string = self._build_search_string(field_conditions)
            logger.info(f"🔨 search_string gebaut: '{search_string}'")
            
            # 3. s_string + s_source in VIEW-GUID Gruppe speichern (EINHEITLICH!)
            self.gcs._app_db.set_value(self.view_guid, 's_string', search_string)
            self.gcs._app_db.set_value(self.view_guid, 's_source', 'komplex')
            logger.info(f"💾 s_string + s_source in {self.view_guid} gespeichert")
            
            # 4. SOFORT in DB schreiben
            self.gcs._app_db.save_all_values()
            logger.info(f"✅ save_all_values() aufgerufen - Daten in DB")
            
            # 5. Pipeline ab FILTER durchlaufen - KORREKT!
            from v2_pdvm_pipeline import get_pipeline
            pipeline = get_pipeline(self.view_guid, self.matrix_manager)
            pipeline.run('FILTER')
            logger.info(f"✅ Pipeline ab FILTER durchlaufen")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler in Komplex-Filter: {e}", exc_info=True)
            return False
    
    def _build_search_string(self, field_conditions: Dict[str, List[Dict]]) -> str:
        """
        Baut einheitlichen search_string für Matrix Manager
        
        Format: "feld1:AND|IS|contains|wert1||feld2:OR|NOT|equals|wert2"
        
        Args:
            field_conditions: Dict mit Feld → Bedingungen
            
        Returns:
            Einheitlicher search_string
        """
        if not field_conditions:
            return ""
        
        # EINHEITLICHES FORMAT: Feld:Position1|Position2|Position3|Position4
        parts = []
        
        for field_key, conditions in field_conditions.items():
            if not conditions:
                continue
            
            for cond in conditions:
                # 4-Positionen Struktur - BEIDE Formate unterstützen!
                # Format 1: position_1, position_2, position_3, position_4
                # Format 2: logic, negation, operator, value (von Dialog)
                pos1 = cond.get('position_1') or cond.get('logic', 'AND')
                pos2 = cond.get('position_2') or cond.get('negation', 'IS')
                pos3 = cond.get('position_3') or cond.get('operator', 'enthält')
                pos4 = cond.get('position_4') or cond.get('value', '')
                
                if not pos4 or not str(pos4).strip():
                    logger.warning(f"⚠️ Skip leere Bedingung für {field_key}")
                    continue  # Skip leere Bedingungen
                
                # Format: feld:pos1|pos2|pos3|pos4
                part = f"{field_key}:{pos1}|{pos2}|{pos3}|{pos4}"
                parts.append(part)
                logger.info(f"✅ Bedingung: {part}")
        
        # Multi-Condition mit ||
        search_string = "||".join(parts)
        logger.info(f"🔨 Komplett search_string: '{search_string}'")
        
        return search_string
    
    def load_komplex_filter_ui(self) -> Dict[str, List[Dict]]:
        """
        Lädt komplexe Filter für UI-Anzeige (nur wenn s_source == 'komplex')
        
        Returns:
            Dict mit field_key → Bedingungen Mappings
        """
        try:
            # Prüfe s_source
            s_source, _ = self.gcs._app_db.get_value(self.view_guid, 's_source')
            
            if s_source != 'komplex':
                logger.info(f"ℹ️ Komplex-Filter-UI nicht laden (s_source='{s_source}')")
                return {}
            
            # Lade alle Feld-Bedingungen
            # Wir müssen wissen, welche Felder es gibt - aus column_control?
            # Hier erstmal empty, UI muss für jedes Feld einzeln laden
            
            logger.info(f"🔄 Komplex-Filter-UI bereit zum Laden")
            return {}
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden Komplex-Filter-UI: {e}")
            return {}
    
    def load_field_conditions(self, field_key: str) -> List[Dict]:
        """
        Lädt Bedingungen für ein bestimmtes Feld
        
        Args:
            field_key: Feld-Key (z.B. "familienname_show")
            
        Returns:
            Liste von Bedingungen oder []
        """
        try:
            # Hole komplette komplex-Daten
            komplex_data, _ = self.gcs._app_db.get_value(self.view_guid, 'komplex')
            
            if komplex_data and isinstance(komplex_data, dict):
                field_data = komplex_data.get(field_key, {})
                if isinstance(field_data, dict):
                    conditions = field_data.get('conditions', [])
                    return conditions if conditions else []
            
            return []
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden Feld-Bedingungen {field_key}: {e}")
            return []
    
    def clear_komplex_filter(self, field_keys: list = None) -> bool:
        """
        Löscht komplexe Filter - NUR s_string/s_source, Parameter bleiben!
        
        Args:
            field_keys: Nicht verwendet (für zukünftige Erweiterungen)
            
        Returns:
            True wenn erfolgreich
        """
        try:
            logger.info(f"🗑️ Lösche Komplex-Filter (nur s_string/s_source)")
            
            # NUR s_string und s_source löschen, Parameter bleiben!
            self.gcs._app_db.set_value(self.view_guid, 's_string', None)
            self.gcs._app_db.set_value(self.view_guid, 's_source', None)
            self.gcs._app_db.save_all_values()
            
            logger.info(f"✅ s_string/s_source gelöscht, Parameter 'komplex' bleiben erhalten")
            
            # Pipeline ab FILTER neu durchlaufen
            from v2_pdvm_pipeline import get_pipeline
            pipeline = get_pipeline(self.view_guid, self.matrix_manager)
            pipeline.run('FILTER')
            
            logger.info(f"✅ Pipeline ab FILTER neu durchlaufen")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Löschen Komplex-Filter: {e}", exc_info=True)
            return False
