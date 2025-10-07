"""
Matrix Debug Helper - Direkte Debug-Ausgabe für View-Dialoge
🎯 Zweck: Einfache Methoden für Matrix-Debug in bestehenden View-Sortierungen
"""

import logging
from clean_matrix_manager import get_clean_matrix_manager

logger = logging.getLogger(__name__)

def debug_matrix_after_sort(view_guid, action_description="Sortierung"):
    """
    🎯 HAUPT-DEBUG-METHODE: Nach Sortierung aufrufen
    Zeigt nur die SORTED_MATRIX (das ist das was der User sehen will)
    """
    try:
        matrix_manager = get_clean_matrix_manager(view_guid)
        
        logger.info(f"🔍 === SORT DEBUG: {action_description} ===")
        logger.info(f"🔍 SORTED_MATRIX Inhalt:")
        
        if matrix_manager.sorted_matrix:
            _debug_matrix_simple("SORTED", matrix_manager.sorted_matrix, matrix_manager.columns)
        else:
            logger.info(f"   📝 SORTED_MATRIX ist leer")
        
        logger.info(f"🔍 === ENDE SORT DEBUG ===")
        
    except Exception as e:
        logger.error(f"❌ Matrix Debug Fehler: {e}")

def debug_all_matrices(view_guid, action_description="Unbekannte Aktion"):
    """
    🎯 VOLLSTÄNDIGER DEBUG: Zeigt alle 3 Matrizen
    Für komplexe Diagnose
    """
    try:
        matrix_manager = get_clean_matrix_manager(view_guid)
        
        logger.info(f"🎯 === VOLLSTÄNDIGER MATRIX DEBUG: {action_description} ===")
        
        # BASIS_MATRIX
        logger.info(f"🔍 BASIS_MATRIX:")
        if matrix_manager.basis_matrix:
            _debug_matrix_simple("BASIS", matrix_manager.basis_matrix, matrix_manager.columns)
        else:
            logger.info(f"   📝 BASIS_MATRIX ist leer")
        
        # FILTERED_MATRIX
        logger.info(f"🔍 FILTERED_MATRIX:")
        if matrix_manager.filtered_matrix:
            _debug_matrix_simple("FILTERED", matrix_manager.filtered_matrix, matrix_manager.columns)
        else:
            logger.info(f"   📝 FILTERED_MATRIX ist leer")
        
        # SORTED_MATRIX
        logger.info(f"🔍 SORTED_MATRIX:")
        if matrix_manager.sorted_matrix:
            _debug_matrix_simple("SORTED", matrix_manager.sorted_matrix, matrix_manager.columns)
        else:
            logger.info(f"   📝 SORTED_MATRIX ist leer")
        
        logger.info(f"🎯 === ENDE VOLLSTÄNDIGER DEBUG ===")
        
    except Exception as e:
        logger.error(f"❌ Vollständiger Matrix Debug Fehler: {e}")

def _debug_matrix_simple(matrix_name, matrix_data, columns):
    """
    Einfache Matrix-Debug-Ausgabe
    """
    debug_columns = ['uid_original', 'vorname_original', 'vorname_show', 'geburtsdatum_original', 'geburtsdatum_show']
    
    if not matrix_data:
        logger.info(f"   📝 {matrix_name}_MATRIX ist leer")
        return
    
    # Verfügbare Debug-Spalten finden
    available_columns = [col for col in debug_columns if col in columns]
    if not available_columns:
        logger.info(f"   📝 {matrix_name}_MATRIX: Debug-Spalten nicht verfügbar")
        logger.info(f"   📝 Verfügbare Spalten: {list(columns)[:5]}...")  # Erste 5 zeigen
        return
    
    logger.info(f"   📋 {len(matrix_data)} Zeilen - Debug-Spalten: {' | '.join(available_columns)}")
    
    # Erste 3 Zeilen als Beispiel
    for i, row in enumerate(matrix_data[:3]):
        debug_values = []
        for col in available_columns:
            value = row.get(col, 'N/A')
            # Kürze lange Werte
            if isinstance(value, str) and len(value) > 20:
                value = value[:17] + "..."
            debug_values.append(str(value))
        
        logger.info(f"   📄 Zeile {i+1}: {' | '.join(debug_values)}")
    
    if len(matrix_data) > 3:
        logger.info(f"   📝 ... und {len(matrix_data) - 3} weitere Zeilen")

def notify_sort_operation(view_guid, column_name, sort_order):
    """
    🎯 SORTIER-BENACHRICHTIGUNG: 
    Kann in bestehende Sortier-Methoden eingefügt werden
    """
    logger.info(f"📊 SORTIERUNG: Spalte '{column_name}' ({sort_order}) in View {view_guid}")
    # Nach der Sortierung den Debug anzeigen
    debug_matrix_after_sort(view_guid, f"Spalte '{column_name}' ({sort_order})")