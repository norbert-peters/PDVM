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
- Komplexe Filter (wenn wirklich gebraucht)
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


class SimpleLinearFilterExecutionManager:
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
        
        logger.info(f"🎯 SimpleLinearFilterExecutionManager initialisiert für View: {self.view_guid}")
    
    def execute_filter_linear(self, filter_type: str, filter_config: Dict[str, Any]) -> bool:
        """
        EINFACHER FILTER-EINSTIEG - Nur grundlegende Funktionen!
        
        Args:
            filter_type: 'einfach', 'komplex' (NUR DIESE ZWEI!)
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
            if filter_type == 'einfach':
                success = self._execute_simple_filter(filter_config)
            elif filter_type == 'komplex':
                success = self._execute_complex_filter(filter_config)
            else:
                logger.error(f"❌ Unbekannter Filter-Typ: {filter_type} (Nur 'einfach' und 'komplex' unterstützt)")
                return False
            
            if success:
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
        """EINFACHE FILTER-AUSFÜHRUNG"""
        logger.info("🎯 EINFACHE FILTER-AUSFÜHRUNG")
        
        try:
            # Hole Filter-Parameter
            filter_field = filter_config.get('filter_field')
            filter_value = filter_config.get('filter_value')
            
            # Alternative Parameternamen prüfen
            if not filter_field:
                filter_field = filter_config.get('field_name')
            if not filter_value:
                filter_value = filter_config.get('search_value')
            
            if not filter_field or not filter_value:
                logger.error(f"❌ Unvollständige Filter-Konfiguration: field='{filter_field}', value='{filter_value}'")
                logger.error(f"📋 Verfügbare Config-Keys: {list(filter_config.keys())}")
                return False
            
            logger.info(f"🔍 Einfacher Filter: {filter_field} = '{filter_value}'")
            
            # MatrixManager Integration
            matrix_manager = self._get_matrix_manager()
            if matrix_manager:
                # Einfache Filter-Parameter: field_show Format
                filter_params = {f"{filter_field}_show": filter_value}
                logger.info(f"📊 Filter-Parameter für Matrix: {filter_params}")
                
                result = matrix_manager.apply_filter('einfach', filter_params)
                
                if result:
                    logger.info("✅ Einfacher Filter auf Matrix erfolgreich angewendet")
                    return True
                else:
                    logger.error("❌ Einfacher Filter auf Matrix fehlgeschlagen")
                    return False
            else:
                logger.error("❌ MatrixManager nicht verfügbar für einfachen Filter")
                return False
                
        except Exception as e:
            logger.error(f"❌ Fehler bei einfachem Filter: {e}")
            return False
    
    def _execute_complex_filter(self, filter_config: Dict[str, Any]):
        """KOMPLEXE FILTER-AUSFÜHRUNG (falls wirklich gebraucht)"""
        logger.info("🎯 KOMPLEXE FILTER-AUSFÜHRUNG")
        
        try:
            # Komplexe Filter-Logik - später implementieren falls nötig
            logger.warning("⚠️ Komplexe Filter noch nicht implementiert - verwende einfachen Fallback")
            
            # Falls es doch nur ein einfacher Filter in komplexer Verpackung ist
            if 'filter_field' in filter_config and 'filter_value' in filter_config:
                return self._execute_simple_filter(filter_config)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler bei komplexem Filter: {e}")
            return False


# Globaler Manager-Cache
_simple_linear_filter_managers = {}

def get_simple_linear_filter_manager(view_guid: str) -> Optional[SimpleLinearFilterExecutionManager]:
    """
    Hole oder erstelle EINFACHEN LinearFilterExecutionManager für View-GUID
    
    Args:
        view_guid: Eindeutige View-Identifikation
        
    Returns:
        SimpleLinearFilterExecutionManager Instance oder None
    """
    global _simple_linear_filter_managers
    
    try:
        if view_guid not in _simple_linear_filter_managers:
            _simple_linear_filter_managers[view_guid] = SimpleLinearFilterExecutionManager(view_guid)
            logger.info(f"✅ Neue EINFACHE LinearFilterExecutionManager Instanz für View: {view_guid}")
        
        return _simple_linear_filter_managers[view_guid]
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Erstellen einfacher LinearFilterExecutionManager: {e}")
        return None

def reset_all_simple_linear_filter_managers():
    """Reset aller einfachen Manager-Instanzen"""
    global _simple_linear_filter_managers
    _simple_linear_filter_managers.clear()
    logger.info("🔄 Alle EINFACHEN LinearFilterExecutionManager-Instanzen zurückgesetzt")