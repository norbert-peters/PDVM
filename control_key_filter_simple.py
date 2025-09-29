"""
🔧 VEREINFACHTE LÖSUNG: Control-Key basierte Filter-Suche
=========================================================

PROBLEM: SearchParameterDialog sendet Control-Keys wie 'vorname_show', 
aber Header zeigt Display-Namen wie 'Vorname' oder 'Vorname\nvorname_show' (Expert-Mode)

LÖSUNG: Erweiterte Header-Analyse, die sowohl Display-Namen als auch Control-Keys erkennt
"""

import logging
logger = logging.getLogger(__name__)

def find_column_by_control_key(table_widget, control_key: str) -> int:
    """
    Findet Spalten-Index basierend auf Control-Key
    
    Sucht in:
    1. Header-Text direkt (falls Control-Key als Header verwendet wird)
    2. Multi-Line Header (zweite Zeile enthält Control-Key im Expert-Mode)
    3. ToolTip (enthält Control-Key: ...)
    
    Args:
        table_widget: QTableWidget
        control_key: Control-Key wie 'vorname_show'
        
    Returns:
        int: Spalten-Index oder None wenn nicht gefunden
    """
    logger.info(f"🔍 Suche Control-Key: '{control_key}'")
    
    for col in range(table_widget.columnCount()):
        header_item = table_widget.horizontalHeaderItem(col)
        if not header_item:
            continue
            
        header_text = header_item.text()
        tooltip_text = header_item.toolTip() if header_item.toolTip() else ""
        
        logger.info(f"   📋 Spalte {col}: Header='{header_text}', ToolTip='{tooltip_text[:50]}...'")
        
        # 1. DIREKTE SUCHE: Control-Key ist der Header-Text
        if header_text == control_key:
            logger.info(f"   ✅ DIREKT: Control-Key '{control_key}' gefunden bei Index {col}")
            return col
            
        # 2. MULTI-LINE SUCHE: Header hat mehrere Zeilen (Expert-Mode)
        if '\n' in header_text:
            lines = header_text.split('\n')
            for line in lines:
                if line.strip() == control_key:
                    logger.info(f"   ✅ MULTI-LINE: Control-Key '{control_key}' in Zeile '{line}' bei Index {col}")
                    return col
                    
        # 3. TOOLTIP SUCHE: "Control-Key: vorname_show"
        if f"Control-Key: {control_key}" in tooltip_text:
            logger.info(f"   ✅ TOOLTIP: Control-Key '{control_key}' in ToolTip bei Index {col}")
            return col
    
    logger.error(f"❌ Control-Key '{control_key}' nicht gefunden")
    return None


def enhanced_single_column_search(table_widget, control_key: str, search_text: str, case_sensitive: bool = False, whole_word: bool = False) -> bool:
    """
    VEREINFACHTE Einzelsuche mit Control-Key Unterstützung
    
    Args:
        table_widget: QTableWidget
        control_key: Control-Key der Spalte
        search_text: Suchtext
        case_sensitive: Groß-/Kleinschreibung beachten
        whole_word: Ganzes Wort suchen
        
    Returns:
        bool: True wenn erfolgreich
    """
    try:
        if not search_text.strip():
            return True
            
        # Spalten-Index über Control-Key finden
        target_col = find_column_by_control_key(table_widget, control_key)
        if target_col is None:
            return False
            
        search_value = search_text.strip()
        if not case_sensitive:
            search_value = search_value.lower()
        
        hidden_count = 0
        
        for row in range(table_widget.rowCount()):
            item = table_widget.item(row, target_col)
            row_matches = False
            
            if item:
                cell_text = item.text()
                if not case_sensitive:
                    cell_text = cell_text.lower()
                
                if whole_word:
                    row_matches = (search_value == cell_text)
                else:
                    row_matches = (search_value in cell_text)
            
            if not row_matches:
                table_widget.setRowHidden(row, True)
                hidden_count += 1
        
        logger.info(f"✅ Control-Key Filter '{control_key}': {hidden_count} Zeilen ausgeblendet")
        return True
        
    except Exception as e:
        logger.error(f"❌ Fehler bei Control-Key Filter '{control_key}': {e}")
        return False


if __name__ == "__main__":
    print("🔧 Vereinfachte Control-Key basierte Filter-Lösung")
    print("   - Keine Column-Mappings")
    print("   - Direkte Control-Key Suche in Header/ToolTip")
    print("   - Unterstützt Expert-Mode Multi-Line Header")