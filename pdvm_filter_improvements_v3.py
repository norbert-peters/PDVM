# pdvm_filter_improvements_v3.py
"""
Verbesserte Filter-Funktionen für das V3-System
Behebt das Problem mit unvollständiger Filterung leerer Werte
"""

import logging
from typing import Dict, Any, List, Union

logger = logging.getLogger(__name__)

def is_empty_value(value: Any) -> bool:
    """
    Robuste Prüfung auf leere Werte
    
    Args:
        value: Zu prüfender Wert
        
    Returns:
        bool: True wenn leer, sonst False
    """
    if value is None:
        return True
    
    if isinstance(value, str):
        # String-Prüfungen
        stripped = value.strip()
        if not stripped:
            return True
        if stripped.lower() in ["", "null", "none", "leer", "-", "n/a", "na"]:
            return True
    
    if isinstance(value, (int, float)):
        # Numerische Null-Werte
        if value == 0:
            return True
        if isinstance(value, float) and value == 0.0:
            return True
    
    return False

def apply_improved_empty_filter(records: List[Dict], field_name: str, show_empty: bool = True) -> List[Dict]:
    """
    Wendet verbesserte leere-Werte-Filterung an
    
    Args:
        records: Liste der Datensätze
        field_name: Feldname
        show_empty: True=leere Werte anzeigen, False=ausschließen
        
    Returns:
        List[Dict]: Gefilterte Datensätze
    """
    filtered_records = []
    
    for record in records:
        # Verschiedene Spalten prüfen
        original_value = record.get(f"{field_name}_original")
        show_value = record.get(f"{field_name}_show")
        
        # Robuste leere-Werte-Erkennung
        is_original_empty = is_empty_value(original_value)
        is_show_empty = is_empty_value(show_value)
        
        # Ein Wert gilt als leer, wenn BEIDE Spalten leer sind
        is_completely_empty = is_original_empty and is_show_empty
        
        if is_completely_empty:
            if show_empty:
                filtered_records.append(record)
            # Wenn show_empty=False, wird der Datensatz nicht hinzugefügt
        else:
            # Nicht-leere Werte werden immer aufgenommen
            filtered_records.append(record)
    
    return filtered_records

def apply_improved_dropdown_filter(records: List[Dict], field_name: str, selected_keys: set, show_empty: bool = True) -> List[Dict]:
    """
    Verbesserte Dropdown-Filterung mit robuster leere-Werte-Behandlung
    """
    if not selected_keys and show_empty:
        return records  # Keine Filterung
    
    filtered_records = []
    
    for record in records:
        original_value = record.get(f"{field_name}_original")
        show_value = record.get(f"{field_name}_show")
        
        # Robuste leere-Werte-Erkennung
        is_original_empty = is_empty_value(original_value)
        is_show_empty = is_empty_value(show_value)
        is_completely_empty = is_original_empty and is_show_empty
        
        if is_completely_empty:
            if show_empty:
                filtered_records.append(record)
        else:
            # Prüfe ob der Wert in den ausgewählten Keys ist
            if str(original_value) in selected_keys:
                filtered_records.append(record)
    
    return filtered_records

if __name__ == "__main__":
    # Test der verbesserten Filter-Funktionen
    test_records = [
        {"test_original": "", "test_show": ""},
        {"test_original": None, "test_show": None},
        {"test_original": 0, "test_show": ""},
        {"test_original": "value", "test_show": "Value"},
        {"test_original": "   ", "test_show": "-"},
    ]
    
    # Test mit show_empty=False (leere ausschließen)
    filtered = apply_improved_empty_filter(test_records, "test", show_empty=False)
    print(f"Mit show_empty=False: {len(filtered)} von {len(test_records)} Datensätzen")
    
    # Test mit show_empty=True (leere einschließen)  
    filtered = apply_improved_empty_filter(test_records, "test", show_empty=True)
    print(f"Mit show_empty=True: {len(filtered)} von {len(test_records)} Datensätzen")
