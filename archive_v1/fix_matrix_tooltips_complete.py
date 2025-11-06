# fix_matrix_tooltips_complete.py
"""
KOMPLETTER FIX FÜR MATRIX-TOOLTIPS

Probleme:
1. Tooltips werden nicht angezeigt
2. GUID fehlt in Matrix-Logs
3. Matrix-Log muss abdatum und formatiert für familienname zeigen

Lösung:
1. Debug-Logging in pdvm_view_daten_manager.py erweitern
2. get_abdatum_matrix() Logging verbessern  
3. Tooltip-Integration in pdvm_view_widget.py prüfen
"""

import logging
logger = logging.getLogger(__name__)


# ============================================================================
# TEIL 1: ERWEITERTE DEBUG-FUNKTION FÜR MATRIX
# ============================================================================

def debug_print_matrix_row_with_abdatum(row_data: dict, row_idx: int = 0):
    """
    Erweiterte Debug-Ausgabe einer Matrix-Row mit allen 3 Ebenen
    
    Zeigt speziell:
    - uid_original (GUID)
    - familienname_original mit allen 3 Ebenen
    - Andere Felder
    """
    logger.info(f"🔍 === MATRIX ROW {row_idx} DEBUG (3-EBENEN) ===")
    
    # GUID
    guid = row_data.get('uid_original', 'UNBEKANNT')
    logger.info(f"  👤 GUID: {guid}")
    
    # Familienname mit 3 Ebenen
    if 'familienname_original' in row_data:
        fn_wert = row_data.get('familienname_original')
        fn_abdatum = row_data.get('familienname_original__abdatum')
        fn_formatiert = row_data.get('familienname_original__formatiert')
        
        logger.info(f"  📋 familienname_original:")
        logger.info(f"    ├─ 🗄️ EBENE 1 (Wert):       {fn_wert}")
        logger.info(f"    ├─ 📅 EBENE 2 (AB-Datum):   {fn_abdatum}")
        logger.info(f"    └─ 🎨 EBENE 3 (Formatiert): {fn_formatiert}")
    else:
        logger.warning(f"  ⚠️ familienname_original NICHT in row_data!")
    
    # Andere wichtige Felder
    for key in ['vorname_original', 'geburtsdatum_original']:
        if key in row_data:
            wert = row_data.get(key)
            abdatum = row_data.get(f"{key}__abdatum")
            formatiert = row_data.get(f"{key}__formatiert")
            logger.info(f"  📋 {key}: {wert} | abdatum={abdatum} | formatiert={formatiert}")
    
    # Zeige alle Keys
    all_keys = list(row_data.keys())
    logger.info(f"  🗝️ Alle Keys ({len(all_keys)}): {', '.join(all_keys[:10])}...")


# ============================================================================
# TEIL 2: ERWEITERTE get_abdatum_matrix() METHODE
# ============================================================================

def get_abdatum_matrix_debug(self, show_only=True):
    """
    Erweiterte Version von get_abdatum_matrix() mit Debug-Logging
    
    VERWENDET EBENE 3 (__formatiert Suffix) für UI-Tooltips
    """
    logger.info("🔍 === get_abdatum_matrix_debug() START ===")
    
    if not self.column_control:
        logger.error("❌ column_control ist None!")
        return None
        
    # Projektion ermitteln
    if show_only:
        columns = sorted([col for col in self.basis_columns if col.get('show', False)], 
                        key=lambda c: c.get('displayOrder', 999))
    else:
        columns = sorted(self.basis_columns, key=lambda c: c.get('expertOrder', 999))
        
    col_names = [col['name'] for col in columns]
    logger.info(f"📊 Spaltennamen ({len(col_names)}): {col_names}")
    
    abdatum_matrix = []
    
    # Über alle GUIDs iterieren
    guids = list(self.column_control.row_guids)
    logger.info(f"👤 GUIDs ({len(guids)}): {guids}")
    
    for row_idx, guid in enumerate(guids):
        row_data = self.column_control.get_row_data(guid)
        
        # DEBUG: Erste Row detailliert ausgeben
        if row_idx == 0:
            debug_print_matrix_row_with_abdatum(row_data, row_idx)
        
        abdatum_row = []
        for col_idx, col_name in enumerate(col_names):
            # EBENE 3: Formatiertes Abdatum holen (__formatiert Suffix)
            formatiert = row_data.get(f"{col_name}__formatiert")
            abdatum_row.append(formatiert)
            
            # DEBUG: Erste Row, alle Spalten ausgeben
            if row_idx == 0:
                logger.info(f"  📊 [{row_idx},{col_idx}] {col_name}__formatiert = {formatiert}")
        
        abdatum_matrix.append(abdatum_row)
    
    logger.info(f"✅ Abdatum-Matrix erstellt: {len(abdatum_matrix)} Zeilen, {len(col_names)} Spalten")
    
    # DEBUG: Zeige erste Zeile der Abdatum-Matrix
    if abdatum_matrix:
        logger.info(f"🔍 Erste Zeile Abdatum-Matrix: {abdatum_matrix[0][:5]}...")
    
    return abdatum_matrix


# ============================================================================
# TEIL 3: PRÜFUNG DER TOOLTIP-INTEGRATION
# ============================================================================

def check_tooltip_integration(view_manager):
    """
    Prüft die Tooltip-Integration in pdvm_view_widget.py
    """
    logger.info("🔍 === TOOLTIP-INTEGRATION PRÜFEN ===")
    
    # Hole Daten vom ViewManager
    result = view_manager.get_table_data_for_display()
    
    logger.info(f"📋 Result Keys: {result.keys()}")
    logger.info(f"📊 Rows: {len(result.get('rows', []))} Zeilen")
    logger.info(f"📑 Headers: {result.get('headers', [])}")
    
    # Abdatum-Matrix prüfen
    abdatum_matrix = result.get('abdatum_matrix')
    
    if abdatum_matrix is None:
        logger.error("❌ abdatum_matrix ist None!")
        return False
    
    logger.info(f"✅ abdatum_matrix vorhanden: {len(abdatum_matrix)} Zeilen")
    
    # Erste Zeile prüfen
    if abdatum_matrix:
        first_row = abdatum_matrix[0]
        logger.info(f"🔍 Erste Zeile: {len(first_row)} Spalten")
        logger.info(f"🔍 Erste 5 Werte: {first_row[:5]}")
        
        # Prüfe auf None-Werte
        none_count = sum(1 for v in first_row if v is None)
        logger.info(f"📊 None-Werte in erster Zeile: {none_count}/{len(first_row)}")
        
        # Prüfe auf tatsächliche Werte
        has_values = any(v is not None and str(v).strip() != '' for v in first_row)
        if has_values:
            logger.info("✅ Erste Zeile hat Abdatum-Werte!")
        else:
            logger.warning("⚠️ Erste Zeile hat keine Abdatum-Werte")
        
        return has_values
    
    return False


# ============================================================================
# TEIL 4: INTEGRATION IN pdvm_view_daten_manager.py
# ============================================================================

INTEGRATION_CODE = """
# In pdvm_view_daten_manager.py

# 1. Füge die debug_print_matrix_row_with_abdatum Funktion hinzu:

def _debug_print_matrix_row(self, row_data: dict, row_idx: int = 0):
    '''
    Erweiterte Debug-Ausgabe einer Matrix-Row mit allen 3 Ebenen
    '''
    logger.info(f"🔍 === MATRIX ROW {row_idx} DEBUG (3-EBENEN) ===")
    
    # GUID
    guid = row_data.get('uid_original', 'UNBEKANNT')
    logger.info(f"  👤 GUID: {guid}")
    
    # Familienname mit 3 Ebenen
    if 'familienname_original' in row_data:
        fn_wert = row_data.get('familienname_original')
        fn_abdatum = row_data.get('familienname_original__abdatum')
        fn_formatiert = row_data.get('familienname_original__formatiert')
        
        logger.info(f"  📋 familienname_original:")
        logger.info(f"    ├─ 🗄️ EBENE 1 (Wert):       {fn_wert}")
        logger.info(f"    ├─ 📅 EBENE 2 (AB-Datum):   {fn_abdatum}")
        logger.info(f"    └─ 🎨 EBENE 3 (Formatiert): {fn_formatiert}")
    else:
        logger.warning(f"  ⚠️ familienname_original NICHT in row_data!")
    
    # Alle Keys zeigen
    all_keys = list(row_data.keys())
    logger.info(f"  🗝️ Alle Keys ({len(all_keys)}): {', '.join(all_keys[:15])}...")


# 2. Erweitere get_abdatum_matrix() mit Debug-Logging:

def get_abdatum_matrix(self, show_only=True):
    '''
    Gibt die Abdatum-Matrix für die aktuelle Projektion zurück
    
    VERWENDET EBENE 3 (__formatiert Suffix) für UI-Tooltips
    '''
    logger.info("🔍 === get_abdatum_matrix() START ===")
    
    if not self.column_control:
        logger.error("❌ column_control ist None!")
        return None
        
    # Projektion ermitteln
    if show_only:
        columns = sorted([col for col in self.basis_columns if col.get('show', False)], 
                        key=lambda c: c.get('displayOrder', 999))
    else:
        columns = sorted(self.basis_columns, key=lambda c: c.get('expertOrder', 999))
        
    col_names = [col['name'] for col in columns]
    logger.info(f"📊 Spaltennamen ({len(col_names)}): {col_names[:5]}...")
    
    abdatum_matrix = []
    
    # Über alle GUIDs iterieren
    guids = list(self.column_control.row_guids)
    logger.info(f"👤 GUIDs ({len(guids)}): {guids[:3]}...")
    
    for row_idx, guid in enumerate(guids):
        row_data = self.column_control.get_row_data(guid)
        
        # DEBUG: Erste Row detailliert ausgeben
        if row_idx == 0:
            self._debug_print_matrix_row(row_data, row_idx)
        
        abdatum_row = []
        for col_idx, col_name in enumerate(col_names):
            # EBENE 3: Formatiertes Abdatum holen (__formatiert Suffix)
            formatiert = row_data.get(f"{col_name}__formatiert")
            abdatum_row.append(formatiert)
            
            # DEBUG: Log für familienname
            if row_idx == 0 and col_name == 'familienname_original':
                logger.info(f"  🔍 familienname_original__formatiert = '{formatiert}'")
        
        abdatum_matrix.append(abdatum_row)
    
    logger.info(f"✅ Abdatum-Matrix erstellt: {len(abdatum_matrix)} Zeilen, {len(col_names)} Spalten")
    
    # DEBUG: Zeige erste Zeile
    if abdatum_matrix and abdatum_matrix[0]:
        logger.info(f"🔍 Erste Zeile Abdatum-Matrix (erste 5): {abdatum_matrix[0][:5]}")
    
    return abdatum_matrix


# 3. Rufe Debug-Funktion in _load_records_data() auf:

def _load_records_data(self, limit=100):
    '''...'''
    # ... bestehender Code ...
    
    # Nach der Schleife: Erste Row debuggen
    if self.column_control.row_guids:
        first_guid = list(self.column_control.row_guids)[0]
        first_row = self.column_control.get_row_data(first_guid)
        self._debug_print_matrix_row(first_row, 0)
    
    # ... Rest des Codes ...
"""

print(INTEGRATION_CODE)


# ============================================================================
# MAIN: TEST-SUITE
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    logger.info("=" * 80)
    logger.info("MATRIX-TOOLTIPS FIX - INTEGRATION GUIDE")
    logger.info("=" * 80)
    
    logger.info("""
    
SCHRITTE ZUR INTEGRATION:

1. Öffne pdvm_view_daten_manager.py

2. Füge die _debug_print_matrix_row() Methode hinzu (siehe INTEGRATION_CODE oben)

3. Erweitere get_abdatum_matrix() mit Debug-Logging (siehe INTEGRATION_CODE oben)

4. Rufe _debug_print_matrix_row() in _load_records_data() auf (siehe INTEGRATION_CODE oben)

5. Starte die Anwendung und öffne eine View

6. Prüfe die Logs:
   - "=== MATRIX ROW 0 DEBUG (3-EBENEN) ===" muss erscheinen
   - "GUID:" muss einen Wert zeigen (nicht "UNBEKANNT")
   - "familienname_original:" muss alle 3 Ebenen zeigen
   - "get_abdatum_matrix() START" muss erscheinen
   - "Abdatum-Matrix erstellt:" muss Zeilen/Spalten zeigen

7. Hover über Tabellen-Zelle:
   - Tooltip mit "abdatum: ..." muss erscheinen
   
WENN TOOLTIPS NICHT ERSCHEINEN:

A. Prüfe ob abdatum_matrix in get_table_data_for_display() zurückgegeben wird
B. Prüfe ob abdatum_matrix in pdvm_view_widget.py._load_table_data() ankommt
C. Prüfe ob item.setToolTip() aufgerufen wird
D. Prüfe ob ab_value nicht None ist

    """)
    
    logger.info("=" * 80)
    logger.info("INTEGRATION CODE siehe oben")
    logger.info("=" * 80)
