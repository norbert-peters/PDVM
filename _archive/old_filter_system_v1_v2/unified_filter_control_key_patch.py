"""
🔧 UNIFIED LINEAR FILTER - CONTROL-KEY PATCH
==============================================

Dieser Patch ersetzt die problematische _apply_single_column_search Methode
mit einer vereinfachten Control-Key basierten Suche.
"""

import logging
from control_key_filter_simple import find_column_by_control_key

logger = logging.getLogger(__name__)

def patched_apply_single_column_search(self, filter_config):
    """
    PATCH: Vereinfachte Einzelsuche mit Control-Key Unterstützung
    
    Ersetzt die problematische Methode in UnifiedLinearFilter
    """
    try:
        if not filter_config.field_name:
            logger.error("❌ Einzelsuche: Kein field_name angegeben")
            return False

        search_text = filter_config.search_text.strip()
        if not search_text:
            return True

        # VEREINFACHTE CONTROL-KEY SUCHE
        control_key = filter_config.field_name
        logger.info(f"🎯 PATCH: Suche Control-Key: '{control_key}'")
        
        # Spalten-Index über Control-Key finden
        target_col = find_column_by_control_key(self.table, control_key)
        if target_col is None:
            return False
        
        logger.info(f"✅ PATCH: Control-Key '{control_key}' → Spalte {target_col}")
        
        if not filter_config.case_sensitive:
            search_text = search_text.lower()
        
        hidden_count = 0
        
        for row in range(self.table.rowCount()):
            item = self.table.item(row, target_col)
            row_matches = False
            
            if item:
                cell_text = item.text()
                if not filter_config.case_sensitive:
                    cell_text = cell_text.lower()
                
                if filter_config.whole_word:
                    row_matches = (search_text == cell_text)
                else:
                    row_matches = (search_text in cell_text)
            
            if not row_matches:
                self.table.setRowHidden(row, True)
                hidden_count += 1
        
        logger.info(f"✅ PATCH: Control-Key Filter '{control_key}': {hidden_count} Zeilen ausgeblendet")
        return True
        
    except Exception as e:
        logger.error(f"❌ PATCH Fehler bei Einzelsuche '{filter_config.field_name}': {e}")
        return False


def apply_unified_filter_patch():
    """
    Wendet den Control-Key Patch auf UnifiedLinearFilter an
    """
    try:
        from unified_linear_filter import UnifiedLinearFilter
        
        # Monkey-Patch: Ersetze die problematische Methode
        UnifiedLinearFilter._apply_single_column_search = patched_apply_single_column_search
        
        logger.info("✅ UNIFIED LINEAR FILTER CONTROL-KEY PATCH angewendet")
        return True
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Anwenden des Patches: {e}")
        return False


if __name__ == "__main__":
    print("🔧 Unified Linear Filter Control-Key Patch")
    result = apply_unified_filter_patch()
    print(f"Patch angewendet: {result}")