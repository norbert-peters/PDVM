file_path = 'pdvm_view_matrix_manager.py'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Finde den Beginn
start_idx = None
end_idx = None

for i, line in enumerate(lines):
    if 'def _load_search_string_from_gcs' in line:
        start_idx = i
        print(f'Gefunden: _load_search_string_from_gcs in Zeile {i+1}')
    elif start_idx is not None and 'def _load_sort_config_from_gcs' in line:
        end_idx = i
        print(f'Gefunden: _load_sort_config_from_gcs in Zeile {i+1}')
        break

if start_idx and end_idx:
    # Neue Methode
    new_method = '''    def _load_search_string_from_gcs(self) -> Optional[str]:
        """Lädt search_string DIREKT aus GCS - EINFACH!"""
        try:
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            
            if not gcs:
                logger.warning("GCS nicht verfügbar - kein Filter")
                return None
            
            search_string, _ = gcs._app_db.get_value(self.view_guid, 'search_string')
            
            if search_string:
                logger.info(f"  Search-String aus GCS geladen: '{search_string}'")
                return search_string
            else:
                logger.info(f"  Kein search_string in GCS - kein Filter")
                return None
                
        except Exception as e:
            logger.error(f"Fehler beim Laden search_string aus GCS: {e}")
            return None
    
'''
    
    # Ersetze
    new_lines = lines[:start_idx] + [new_method] + lines[end_idx:]
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f'Datei bereinigt! Zeilen {start_idx+1} bis {end_idx} ersetzt')
else:
    print('Methoden nicht gefunden!')
