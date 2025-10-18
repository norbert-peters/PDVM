"""
🔧 TEMPORÄRER FIX für unified_linear_filter.py Column-Mapping
"""

def fix_single_column_search_method():
    """Erstellt die korrigierte _apply_single_column_search Methode"""
    
    method_code = '''    def _apply_single_column_search(self, filter_config: FilterConfig) -> bool:
        """Einzelsuche: Sucht in einer bestimmten Spalte - MIT CONTROL-KEY MAPPING"""
        try:
            if not filter_config.field_name:
                logger.error("❌ Einzelsuche: Kein field_name angegeben")
                return False

            search_text = filter_config.search_text.strip()
            if not search_text:
                return True

            # SPALTEN-INDEX ÜBER CONTROL-KEY MAPPING FINDEN
            target_col = None
            control_key = filter_config.field_name
            logger.info(f"🔧 Suche Control-Key: '{control_key}'")
            
            # PRIORITÄT 1: Control-Key Mapping verwenden
            if control_key in self.column_mapping:
                target_col = self.column_mapping[control_key]
                logger.info(f"✅ Control-Key '{control_key}' → Column-Index {target_col}")
            else:
                # FALLBACK: Header-Text Suche (für Rückwärtskompatibilität)
                logger.info(f"⚠️ Control-Key '{control_key}' nicht im Mapping, verwende Header-Text Fallback")
                available_headers = []
                for col in range(self.table.columnCount()):
                    header_item = self.table.horizontalHeaderItem(col)
                    if header_item:
                        header_text = header_item.text()
                        available_headers.append(header_text)
                        logger.info(f"   📋 Spalte {col}: '{header_text}'")
                        if header_text == control_key:
                            target_col = col
                            logger.info(f"   ✅ Header-Match gefunden bei Index {col}")

            if target_col is None:
                logger.error(f"❌ Control-Key/Spalte '{control_key}' nicht gefunden")
                logger.error(f"❌ Column-Mapping Keys: {list(self.column_mapping.keys())}")
                return False
            
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
            
            logger.info(f"✅ Einzelsuche in '{control_key}': {hidden_count} Zeilen ausgeblendet")
            return True
            
        except Exception as e:
            logger.error(f"❌ Fehler bei Einzelsuche: {e}")
            return False'''
    
    return method_code

if __name__ == "__main__":
    print("🔧 Fix-Code für unified_linear_filter.py:")
    print(fix_single_column_search_method())