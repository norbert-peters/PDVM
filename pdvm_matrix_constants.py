"""
Konstanten für 3-Ebenen Array-Struktur in Matrix-System

Jede Spalte enthält ein Array mit 3 Elementen:
  [0] = WERT: Der eigentliche Wert (String, int, float, etc.)
  [1] = ABDATUM: AB-Datum (float, z.B. 2025043.0)
  [2] = FORMATIERT: Formatiertes AB-Datum (String, z.B. "12.02.2025 - 00:00:00")

Beispiel:
    row_data['familienname_original'] = ['Mustermann', 2025043.0, '12.02.2025 - 00:00:00']
    
    wert = row_data['familienname_original'][WERT]
    abdatum = row_data['familienname_original'][ABDATUM]
    formatiert = row_data['familienname_original'][FORMATIERT]
"""

# ============================================================================
# Array-Indices für Spalten-Werte (3-Ebenen-Struktur)
# ============================================================================

WERT = 0        # Index 0: Der eigentliche Wert
ABDATUM = 1     # Index 1: AB-Datum (roh, float)
FORMATIERT = 2  # Index 2: Formatiertes AB-Datum (String)

# Anzahl Ebenen im Array
EBENEN_COUNT = 3


# ============================================================================
# Helper-Funktionen
# ============================================================================

def create_cell(wert, abdatum=None, formatiert=None):
    """
    Erstellt eine Zelle mit 3 Ebenen
    
    Args:
        wert: Der eigentliche Wert (String, int, float, etc.)
        abdatum: AB-Datum (roh, float, optional)
        formatiert: Formatiertes AB-Datum (String, optional)
    
    Returns:
        Array mit 3 Elementen [wert, abdatum, formatiert]
    
    Example:
        >>> cell = create_cell('Mustermann', 2025043.0, '12.02.2025 - 00:00:00')
        >>> cell
        ['Mustermann', 2025043.0, '12.02.2025 - 00:00:00']
    """
    return [wert, abdatum, formatiert]


def get_wert(cell):
    """
    Holt EBENE 1 (Wert) aus Zelle
    
    Args:
        cell: Array [wert, abdatum, formatiert] oder Legacy-Wert
    
    Returns:
        Wert (EBENE 1)
    
    Example:
        >>> cell = ['Mustermann', 2025043.0, '12.02.2025']
        >>> get_wert(cell)
        'Mustermann'
    """
    if isinstance(cell, list) and len(cell) >= 1:
        return cell[WERT]
    return cell  # Fallback für Legacy (direkte Werte)


def get_abdatum(cell):
    """
    Holt EBENE 2 (AB-Datum) aus Zelle
    
    Args:
        cell: Array [wert, abdatum, formatiert] oder Legacy-Wert
    
    Returns:
        AB-Datum (EBENE 2, float) oder None
    
    Example:
        >>> cell = ['Mustermann', 2025043.0, '12.02.2025']
        >>> get_abdatum(cell)
        2025043.0
    """
    if isinstance(cell, list) and len(cell) >= 2:
        return cell[ABDATUM]
    return None


def get_formatiert(cell):
    """
    Holt EBENE 3 (Formatiertes AB-Datum) aus Zelle
    
    Args:
        cell: Array [wert, abdatum, formatiert] oder Legacy-Wert
    
    Returns:
        Formatiertes AB-Datum (EBENE 3, String) oder None
    
    Example:
        >>> cell = ['Mustermann', 2025043.0, '12.02.2025 - 00:00:00']
        >>> get_formatiert(cell)
        '12.02.2025 - 00:00:00'
    """
    if isinstance(cell, list) and len(cell) >= 3:
        return cell[FORMATIERT]
    return None


def ensure_array_format(cell_value):
    """
    Konvertiert alte Key-Struktur zu Array (Legacy-Support)
    
    Args:
        cell_value: Entweder Array [wert, abdatum, formatiert] oder direkter Wert
    
    Returns:
        Array mit 3 Elementen
    
    Example:
        >>> ensure_array_format('Mustermann')
        ['Mustermann', None, None]
        
        >>> ensure_array_format(['Mustermann', 2025043.0, '12.02.2025'])
        ['Mustermann', 2025043.0, '12.02.2025']
    """
    if isinstance(cell_value, list) and len(cell_value) >= EBENEN_COUNT:
        return cell_value  # Bereits korrektes Array
    elif isinstance(cell_value, list):
        # Array zu kurz - auffüllen
        return cell_value + [None] * (EBENEN_COUNT - len(cell_value))
    else:
        # Legacy: Direkter Wert → Array
        return [cell_value, None, None]


def is_empty_cell(cell):
    """
    Prüft ob Zelle leer ist (alle Ebenen None oder leer)
    
    Args:
        cell: Array [wert, abdatum, formatiert]
    
    Returns:
        True wenn alle Ebenen leer/None
    
    Example:
        >>> is_empty_cell([None, None, None])
        True
        >>> is_empty_cell(['', None, None])
        True
        >>> is_empty_cell(['Mustermann', None, None])
        False
    """
    if not isinstance(cell, list):
        return cell is None or cell == ''
    
    wert = get_wert(cell)
    return wert is None or wert == ''
