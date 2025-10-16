#!/usr/bin/env python3
"""
EINFACHER LINEARER FILTER-EXECUTION-MANAGER V2.0 - ROLLBACK VERSION
=================================================================

KOMPLETTER ROLLBACK: Nur die grundlegenden Filter-Funktionen!

URSPRÜNGLICHES PROBLEM (gelöst):
- Nicht-lineare Filter-Pipeline verursacht inkonsistente Ergebnisse
- Filter bauen aufeinander auf statt auf kompletter Datenbasis

EINFACHE LÖSUNG:
1. Immer komplette Datenbasis als Ausgangspunkt
2. Kompletter Reset vor jeder neuen Filterung
3. Nur EIN aktiver Filter zur Zeit
4. KEINE erweiterten Filter-Funktionen

ENTFERNT (ROLLBACK):
- Extended Filter
- Hybrid Filter
- Search-String Filter 
- Complex Filter Parsing
- Alle Persistierung

NUR BEHALTEN:
- Einfache Filter (familienname, ort, etc.)
- MatrixManager Integration
- Lokaler Reset
"""

import logging
import sys
import os
from typing import Dict, Any, Optional

# Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Path setup für Imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


class LinearFilterExecutionManager:
    """
    EINFACHER Manager für BASIC Filter-Operationen
    
    ROLLBACK: Alle erweiterten Funktionen entfernt!
    
    Stellt sicher, dass:
    1. Jede Filterung mit kompletter Datenbasis startet
    2. Alle vorherigen Filter komplett gelöscht werden
    3. Nur EIN Filter aktiv ist
    4. SIMPLE Integration mit MatrixManager
    """
    
    def __init__(self, view_guid: str):
        self.view_guid = view_guid
        self.last_filter_type = None
        self.last_filter_config = None
        
        logger.info(f"🎯 LinearFilterExecutionManager initialisiert für View: {self.view_guid}")
    
    def load_filter_from_gcs(self) -> Optional[Dict[str, Any]]:
        """
        ⚠️ DEPRECATED V2 - Wird nicht mehr verwendet!
        
        V2: Matrix Manager lädt search_string direkt via _load_search_string_from_gcs()
        Diese Methode ist nur noch für Backward-Kompatibilität vorhanden.
        
        Lädt Filter-Config AUTONOM aus GCS (App-DB)
        
        Prüft beide Felder (einfach, komplex) und gibt den ersten gefundenen zurück.
        
        Returns:
            Dict mit 'type' und 'config' oder None
        """
        try:
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            
            if not gcs:
                logger.warning("⚠️ GCS nicht verfügbar - kann Filter nicht laden")
                return None
            
            # Prüfe einfacher Filter
            einfach_config, _ = gcs._app_db.get_value(self.view_guid, 'einfach')
            if einfach_config:
                logger.info(f"📊 Einfacher Filter aus GCS geladen")
                logger.info(f"   Config: {einfach_config}")
                return {
                    'type': 'einfach',
                    'config': einfach_config
                }
            
            # Prüfe komplexer Filter
            komplex_config, _ = gcs._app_db.get_value(self.view_guid, 'komplex')
            if komplex_config:
                logger.info(f"📊 Komplexer Filter aus GCS geladen")
                logger.info(f"   Config: {komplex_config}")
                return {
                    'type': 'komplex',
                    'config': komplex_config
                }
            
            logger.info(f"📋 Keine Filter-Config in GCS gefunden")
            return None
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Laden Filter aus GCS: {e}")
            return None
    
    def execute_filter_linear(self, filter_type: str, filter_config: Dict[str, Any]) -> bool:
        """
        EINFACHER FILTER-EINSTIEG - Nur grundlegende Funktionen!
        
        Args:
            filter_type: 'einfach', 'komplex', 'simple', 'parametric' (NUR DIESE!)
            filter_config: Einfache Filter-Konfiguration
        
        Returns:
            bool: True wenn erfolgreich, False wenn Fehler
        """
        logger.info(f"🎯 === EINFACHER LINEARER FILTER ===")
        logger.info(f"📌 Filter-Typ: {filter_type}")
        logger.info(f"📂 View-GUID: {self.view_guid}")
        
        try:
            # Speichere Filter-Info
            self.last_filter_type = filter_type
            self.last_filter_config = filter_config.copy()
            
            # Schritt 1: Kompletter Reset - immer komplette Datenbasis
            success_reset = self._reset_to_complete_data()
            if not success_reset:
                logger.warning("⚠️ Reset konnte nicht durchgeführt werden, versuche trotzdem Filter")
            
            # Schritt 2: EINFACHE Filter-Ausführung
            if filter_type in ['einfach', 'simple', 'parametric']:
                success = self._execute_simple_filter(filter_config)
            elif filter_type == 'komplex':
                success = self._execute_complex_filter(filter_config)
            else:
                logger.error(f"❌ Unbekannter Filter-Typ: {filter_type}")
                return False
            
            # Schritt 3: Persistierung in GCS (wenn erfolgreich)
            if success:
                self._save_filter_to_gcs(filter_type, filter_config)
                logger.info(f"✅ Einfacher linearer Filter ({filter_type}) erfolgreich")
            else:
                logger.error(f"❌ Einfacher linearer Filter ({filter_type}) fehlgeschlagen")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ FEHLER im einfachen Filter-Einstieg: {e}")
            return False
        
    def _reset_to_complete_data(self):
        """Reset auf komplette Datenbasis - OHNE Persistierung"""
        logger.info("🔄 Reset auf komplette Datenbasis...")
        
        try:
            # Hole MatrixManager
            matrix_manager = self._get_matrix_manager()
            
            if matrix_manager:
                # Versuche verschiedene Reset-Methoden
                if hasattr(matrix_manager, 'reset_to_complete_data'):
                    result = matrix_manager.reset_to_complete_data()
                    if result:
                        logger.info("✅ Reset mit reset_to_complete_data() erfolgreich")
                        return True
                
                if hasattr(matrix_manager, 'load_complete_data'):
                    result = matrix_manager.load_complete_data()
                    if result:
                        logger.info("✅ Reset mit load_complete_data() erfolgreich")
                        return True
                
                if hasattr(matrix_manager, 'reset_filter'):
                    result = matrix_manager.reset_filter()
                    if result:
                        logger.info("✅ Reset mit reset_filter() erfolgreich")
                        return True
                
                logger.warning("⚠️ Keine verfügbare Reset-Methode im MatrixManager gefunden")
                return False
            else:
                logger.warning("⚠️ MatrixManager nicht verfügbar für Reset")
                return False
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Reset: {e}")
            return False
    
    def _get_matrix_manager(self):
        """Hole MatrixManager für diese View"""
        try:
            # Import hier, um zirkuläre Imports zu vermeiden
            from pdvm_matrix_manager import get_matrix_manager
            matrix_manager = get_matrix_manager(self.view_guid)
            
            if matrix_manager:
                logger.info("✅ MatrixManager erfolgreich geholt")
            else:
                logger.warning("⚠️ MatrixManager nicht verfügbar")
                
            return matrix_manager
            
        except ImportError:
            logger.error("❌ pdvm_matrix_manager Modul nicht verfügbar")
            return None
        except Exception as e:
            logger.error(f"❌ Fehler beim Holen des MatrixManagers: {e}")
            return None
    
    def _execute_simple_filter(self, filter_config: Dict[str, Any]):
        """EINFACHE FILTER-AUSFÜHRUNG - erstellt search_string und ruft einheitlichen Filter auf"""
        logger.info("🎯 EINFACHE FILTER-AUSFÜHRUNG")
        
        try:
            # Prüfe auf bereits fertigen search_string
            search_string = filter_config.get('search_string')
            
            if not search_string:
                # Erstelle search_string aus traditionellen field/value Parametern
                filter_field = filter_config.get('filter_field') or filter_config.get('field_name')
                filter_value = filter_config.get('filter_value') or filter_config.get('search_value')
                
                if not filter_field or not filter_value:
                    logger.error(f"❌ Unvollständige Filter-Konfiguration: field='{filter_field}', value='{filter_value}'")
                    logger.error(f"📋 Verfügbare Config-Keys: {list(filter_config.keys())}")
                    return False
                
                # Erstelle search_string aus field/value
                search_string = f"{filter_field}_show:{filter_value}"
                logger.info(f"🔧 Search-String aus Parametern erstellt: '{search_string}'")
            
            logger.info(f"🔍 Führe einheitlichen Filter aus mit: '{search_string}'")
            
            # Rufe den EINHEITLICHEN Filter auf
            return self._execute_unified_filter(search_string)
                
        except Exception as e:
            logger.error(f"❌ Fehler bei einfachem Filter: {e}")
            return False
    
    def _execute_unified_filter(self, search_string: str):
        """EINHEITLICHER FILTER - akzeptiert nur search_string"""
        logger.info(f"🎯 EINHEITLICHER FILTER: '{search_string}'")
        
        try:
            # MatrixManager Integration für einheitlichen Filter
            matrix_manager = self._get_matrix_manager()
            if matrix_manager:
                # Verwende einheitlichen Filter-Aufruf - kein Filter-Typ mehr!
                result = matrix_manager.apply_filter(search_string)
                
                if result:
                    logger.info("✅ Einheitlicher Filter erfolgreich angewendet")
                    return True
                else:
                    logger.error("❌ Einheitlicher Filter fehlgeschlagen")
                    return False
            else:
                logger.error("❌ MatrixManager nicht verfügbar für einheitlichen Filter")
                return False
                
        except Exception as e:
            logger.error(f"❌ Fehler bei einheitlichem Filter: {e}")
            return False
    
    def _execute_complex_filter(self, filter_config: Dict[str, Any]):
        """KOMPLEXE FILTER-AUSFÜHRUNG - erstellt search_string und ruft einheitlichen Filter auf"""
        logger.info("🎯 KOMPLEXE FILTER-AUSFÜHRUNG")
        
        try:
            # Prüfe auf bereits fertigen search_string
            search_string = filter_config.get('search_string')
            
            if not search_string:
                # Komplexe Filter müssen ihren eigenen search_string erstellen
                logger.warning("⚠️ Komplexe Filter ohne search_string noch nicht implementiert")
                return False
            
            logger.info(f"🔍 Führe einheitlichen Filter für komplexen Filter aus: '{search_string}'")
            
            # Rufe den EINHEITLICHEN Filter auf
            return self._execute_unified_filter(search_string)
            
        except Exception as e:
            logger.error(f"❌ Fehler bei komplexem Filter: {e}")
            return False
    
    def _save_filter_to_gcs(self, filter_type: str, filter_config: Dict[str, Any]):
        """
        ⚠️ DEPRECATED V2 - Wird nicht mehr verwendet!
        
        V2: Jeder Filter-Dialog speichert selbst:
        - search_parameter_dialog.py: _save_search_string_to_gcs()
        - extended_filter_engine.py: save_field_conditions() + _build_search_string_from_conditions()
        - linear_filter_execution_manager.py: execute_global_search_filter()
        
        Diese Methode ist nur noch für Backward-Kompatibilität vorhanden.
        
        Speichert Filter persistent in GCS App-DB
        
        Args:
            filter_type: 'einfach' oder 'komplex'
            filter_config: Filter-Konfiguration
        """
        try:
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            
            if not gcs:
                logger.warning("⚠️ GCS nicht verfügbar - keine Persistierung möglich")
                return
            
            # Bestimme Feld-Name basierend auf Filter-Typ
            if filter_type in ['einfach', 'simple', 'parametric']:
                field_name = 'einfach'
            elif filter_type == 'komplex':
                field_name = 'komplex'
            else:
                logger.warning(f"⚠️ Unbekannter Filter-Typ für Persistierung: {filter_type}")
                return
            
            # Speichern in App-DB
            gcs._app_db.set_value(self.view_guid, field_name, filter_config)
            gcs._app_db.save_all_values()  # 💾 CRITICAL: Commit to database!
            
            logger.info(f"💾 Filter persistent gespeichert: {self.view_guid}/{field_name}")
            logger.info(f"   Config: {filter_config}")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern Filter in GCS: {e}")
    
    def reset_all_filters(self):
        """Reset alle Filter und kehre zur kompletten Datenbasis zurück"""
        logger.info("🔄 === RESET ALLE FILTER ===")
        
        try:
            # Reset Filter-State
            self.last_filter_type = None
            self.last_filter_config = None
            
            # Persistierung: Filter aus GCS löschen
            self._clear_filters_from_gcs()
            
            # Reset zur kompletten Datenbasis
            success = self._reset_to_complete_data()
            
            if success:
                logger.info("✅ Alle Filter erfolgreich zurückgesetzt")
                return True
            else:
                # Fallback: MatrixManager direkt mit leerem Filter aufrufen
                matrix_manager = self._get_matrix_manager()
                if matrix_manager:
                    result = matrix_manager.apply_filter(None)  # None = kein Filter
                    if result:
                        logger.info("✅ Filter-Reset über MatrixManager.apply_filter(None) erfolgreich")
                        return True
                
                logger.warning("⚠️ Filter-Reset nur teilweise erfolgreich")
                return False
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Reset aller Filter: {e}")
            return False
    
    def _clear_filters_from_gcs(self):
        """Löscht alle Filter aus GCS App-DB"""
        try:
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            
            if not gcs:
                logger.warning("⚠️ GCS nicht verfügbar - keine Persistierung möglich")
                return
            
            # Lösche beide Filter-Typen
            gcs._app_db.set_value(self.view_guid, 'einfach', None)
            gcs._app_db.set_value(self.view_guid, 'komplex', None)
            gcs._app_db.save_all_values()  # 💾 CRITICAL: Commit to database!
            
            logger.info(f"🗑️ Filter aus GCS gelöscht: {self.view_guid}/einfach, {self.view_guid}/komplex")
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Löschen Filter aus GCS: {e}")
    
    def execute_global_search_filter(self, search_string: str) -> bool:
        """
        V2: GLOBALE SUCHE - sucht in allen Feldern + persistiert search_string
        
        Args:
            search_string: Globaler Suchbegriff (z.B. 'li')
        
        Returns:
            bool: True wenn erfolgreich, False wenn Fehler
        """
        logger.info(f"🔍 === GLOBALE SUCHE V2 ===")
        logger.info(f"🔍 Suchbegriff: '{search_string}'")
        
        try:
            # Reset zur kompletten Datenbasis
            success_reset = self._reset_to_complete_data()
            if not success_reset:
                logger.warning("⚠️ Reset konnte nicht durchgeführt werden, versuche trotzdem globale Suche")
            
            # V2: Speichere Parameters + search_string
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            
            if gcs and hasattr(gcs, '_app_db') and gcs._app_db:
                # 1. Speichere Parameters für UI (unter 'gesamt')
                gcs._app_db.set_value(self.view_guid, 'gesamt', {
                    'search_text': search_string
                })
                
                # 2. Speichere search_string für Pipeline
                gcs._app_db.set_value(self.view_guid, 'search_string', search_string)
                
                # 3. CRITICAL: Speichere beide zusammen
                gcs._app_db.save_all_values()
                
                logger.info(f"💾 V2: Globale Suche + search_string persistent gespeichert")
            
            # Führe globale Suche aus
            matrix_manager = self._get_matrix_manager()
            if matrix_manager:
                # Verwende globalen Filter-Aufruf
                result = matrix_manager.apply_filter(search_string)
                
                if result:
                    logger.info("✅ Globale Suche erfolgreich angewendet")
                    return True
                else:
                    logger.error("❌ Globale Suche fehlgeschlagen")
                    return False
            else:
                logger.error("❌ MatrixManager nicht verfügbar für globale Suche")
                return False
                
        except Exception as e:
            logger.error(f"❌ Fehler bei globaler Suche: {e}")
            return False
    
    def execute_parametric_filter(self, search_string: str, filter_params: dict = None) -> bool:
        """
        V2: PARAMETRISCHER FILTER - filtert nach Feldern + persistiert search_string
        
        Args:
            search_string: Formatierter Filter-String (z.B. 'familienname_show:Müller')
            filter_params: Optional - Filter-Parameter für UI-Anzeige (dict)
        
        Returns:
            bool: True wenn erfolgreich, False wenn Fehler
        """
        logger.info(f"🔍 === PARAMETRISCHER FILTER V2 ===")
        logger.info(f"🔍 search_string: '{search_string}'")
        
        try:
            # Reset zur kompletten Datenbasis
            success_reset = self._reset_to_complete_data()
            if not success_reset:
                logger.warning("⚠️ Reset konnte nicht durchgeführt werden, versuche trotzdem Filter")
            
            # V2: Speichere search_string (Parameters wurden bereits vom Dialog gespeichert)
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            
            if gcs and hasattr(gcs, '_app_db') and gcs._app_db:
                # Speichere search_string für Pipeline
                gcs._app_db.set_value(self.view_guid, 'search_string', search_string)
                
                # Speichere
                gcs._app_db.save_all_values()
                
                logger.info(f"💾 V2: Parametrischer Filter search_string gespeichert")
            
            # Führe parametrischen Filter aus
            matrix_manager = self._get_matrix_manager()
            if matrix_manager:
                result = matrix_manager.apply_filter(search_string)
                
                if result:
                    logger.info("✅ Parametrischer Filter erfolgreich angewendet")
                    return True
                else:
                    logger.error("❌ Parametrischer Filter fehlgeschlagen")
                    return False
            else:
                logger.error("❌ MatrixManager nicht verfügbar für parametrischen Filter")
                return False
                
        except Exception as e:
            logger.error(f"❌ Fehler bei parametrischem Filter: {e}")
            return False


# Globaler Manager-Cache
_linear_filter_managers = {}

def get_linear_filter_manager(view_guid: str) -> Optional[LinearFilterExecutionManager]:
    """
    Hole oder erstelle EINFACHEN LinearFilterExecutionManager für View-GUID
    
    Args:
        view_guid: Eindeutige View-Identifikation
        
    Returns:
        LinearFilterExecutionManager Instance oder None
    """
    global _linear_filter_managers
    
    try:
        if view_guid not in _linear_filter_managers:
            _linear_filter_managers[view_guid] = LinearFilterExecutionManager(view_guid)
            logger.info(f"✅ Neue EINFACHE LinearFilterExecutionManager Instanz für View: {view_guid}")
        
        return _linear_filter_managers[view_guid]
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Erstellen LinearFilterExecutionManager: {e}")
        return None

def reset_all_linear_filter_managers():
    """Reset aller Manager-Instanzen"""
    global _linear_filter_managers
    _linear_filter_managers.clear()
    logger.info("🔄 Alle LinearFilterExecutionManager-Instanzen zurückgesetzt")