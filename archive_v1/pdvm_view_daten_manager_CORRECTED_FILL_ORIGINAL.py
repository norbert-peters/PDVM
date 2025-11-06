# pdvm_view_daten_manager_CORRECTED_FILL_ORIGINAL.py
"""
KORREKTE _fill_original_columns() Methode

Ersetze die bestehende Methode in pdvm_view_daten_manager.py
"""

def _fill_original_columns(self, row_record: dict, temp_instance, temp_dt):
    """
    SCHRITT 3a: _original Spalten befüllen mit 3-EBENEN-STRUKTUR
    
    KORREKTE LOGIK aus pdvm_view_dialog.py:
    1. Sortiere Controls: Basis-Felder vor Zusatzfeldern
    2. Basis-Felder: get_value() → (wert, abdatum)
    3. Zusatzfelder (date_alter etc.): Berechnung aus Basis-Feld
    4. Für jeden control_key: 3 Ebenen befüllen
    """
    try:
        # === Sortiere Controls: Basis-Felder VOR Zusatzfeldern ===
        def sort_key(col):
            col_type = col.get('type', '')
            if col_type in ['date_alter', 'date_jahr', 'date_monat', 'date_tag']:
                return 1  # Zusatzfelder später
            else:
                return 0  # Basis-Felder zuerst
        
        # Nur _original Controls (ohne uid_original)
        original_cols = [col for col in self.basis_columns 
                       if col['name'].endswith('_original') and col['name'] != 'uid_original']
        sorted_cols = sorted(original_cols, key=sort_key)
        
        logger.debug(f"🔄 Verarbeite {len(sorted_cols)} _original Felder (sortiert)")
        
        for col in sorted_cols:
            col_name = col['name']
            col_type = col.get('type', '')
            gruppe = col.get('gruppe', 'PERSDATEN')
            feld = col.get('feld')
            
            if gruppe:
                gruppe = str(gruppe).upper()
            if feld:
                feld = str(feld).upper()
            
            # === SPEZIALFALL: Date-Zusatzfelder (alter, jahr, monat, tag) ===
            if col_type in ['date_alter', 'date_jahr', 'date_monat', 'date_tag']:
                # Basis-Feld finden
                zusatz_suffix = col_type.replace('date_', '')
                base_field = col_name.replace('_original', '').replace(f'_{zusatz_suffix}', '')
                base_original = f"{base_field}_original"
                base_wert = row_record.get(base_original)
                
                logger.debug(f"  📅 Zusatzfeld {col_name}: Basis={base_original}, Wert={base_wert}")
                
                if base_wert and base_wert != 1001.0:
                    try:
                        temp_dt.PdvmDateTime = float(base_wert)
                        
                        if col_type == 'date_alter':
                            calculated_value = str(temp_dt.calc_alter(gcs.stichtag))
                        elif col_type == 'date_jahr':
                            calculated_value = str(temp_dt.Year)
                        elif col_type == 'date_monat':
                            calculated_value = str(temp_dt.Month)
                        elif col_type == 'date_tag':
                            calculated_value = str(temp_dt.Day)
                        else:
                            calculated_value = ""
                        
                        row_record[col_name] = calculated_value
                        logger.debug(f"  ✅ {col_name} = {calculated_value}")
                    except Exception as e:
                        row_record[col_name] = ""
                        logger.debug(f"  ⚠️ Berechnung fehlgeschlagen für {col_name}: {e}")
                else:
                    row_record[col_name] = ""
                
                # Date-Zusatzfelder haben kein eigenes Abdatum
                row_record[f"{col_name}__abdatum"] = None
                row_record[f"{col_name}__formatiert"] = None
                continue
            
            # === NORMALFALL: Basis-Felder aus DB ===
            if feld and gruppe:
                try:
                    # KRITISCH: get_value() gibt Tupel zurück (wert, abdatum)
                    result = temp_instance.get_value(gruppe, feld, gcs.st_inst.PdvmDateTime)
                    
                    # Tupel auspacken
                    if isinstance(result, tuple) and len(result) >= 2:
                        wert, abdatum = result[0], result[1]
                    else:
                        wert, abdatum = result, None
                    
                    logger.debug(f"  🔍 {col_name}: wert={wert}, abdatum={abdatum}")
                    
                    # === 3-EBENEN BEFÜLLEN ===
                    
                    # EBENE 1: Wert
                    row_record[col_name] = wert
                    
                    # EBENE 2: AB-Datum (roh)
                    row_record[f"{col_name}__abdatum"] = abdatum
                    
                    # EBENE 3: Formatiertes AB-Datum
                    if abdatum:
                        temp_dt.PdvmDateTime = float(abdatum)
                        formatiert = temp_dt.FormTimeStamp
                        row_record[f"{col_name}__formatiert"] = formatiert
                        logger.debug(f"  🎨 {col_name}__formatiert = {formatiert}")
                    else:
                        row_record[f"{col_name}__formatiert"] = None
                    
                except Exception as e:
                    logger.debug(f"  ⚠️ get_value Fehler für {col_name}: {e}")
                    # Fehlerfall: Alle 3 Ebenen leer
                    row_record[col_name] = ""
                    row_record[f"{col_name}__abdatum"] = None
                    row_record[f"{col_name}__formatiert"] = None
            else:
                # Kein Feld/Gruppe: Alle 3 Ebenen leer
                row_record[col_name] = ""
                row_record[f"{col_name}__abdatum"] = None
                row_record[f"{col_name}__formatiert"] = None
                
    except Exception as e:
        logger.error(f"❌ Fehler beim Befüllen der _original Spalten: {e}")
        import traceback
        traceback.print_exc()
