#!/usr/bin/env python
# check_view_structure.py
"""
Prüft die Struktur der View-Konfiguration
"""

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_view_structure():
    """Prüft die Struktur der View-Daten"""
    try:
        from pdvm_central_datenbank import PdvmCentralDatenbank
        
        view_guid = "0d10a0d0-b1a5-4544-b284-e8a09ca979b5"
        
        # View-Daten laden
        view_db = PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name="viewdaten",
            guid=view_guid
        )
        
        view_config = view_db.lesen()
        logger.info(f"🔍 View-Konfiguration für {view_guid}:")
        
        if isinstance(view_config, dict):
            for key, value in view_config.items():
                logger.info(f"   {key}: {type(value).__name__} = {value}")
                
                # Wenn value ein dict ist, gehe eine Ebene tiefer
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        logger.info(f"      {sub_key}: {type(sub_value).__name__}")
                        if sub_key == "fields" and isinstance(sub_value, list):
                            logger.info(f"         Anzahl Felder: {len(sub_value)}")
                            if sub_value:
                                logger.info(f"         Erstes Feld: {sub_value[0]}")
        else:
            logger.info(f"   Typ: {type(view_config).__name__}")
            logger.info(f"   Inhalt: {view_config}")
        
        # Schaue nach, was in der Datenbank für diese View wirklich steht
        logger.info(f"\n🔍 Alle Daten für View {view_guid}:")
        all_data = view_db.data
        if all_data:
            for group_key, group_value in all_data.items():
                logger.info(f"   Gruppe '{group_key}': {type(group_value).__name__}")
                if isinstance(group_value, str):
                    try:
                        import json
                        parsed = json.loads(group_value)
                        logger.info(f"      JSON-Inhalt: {type(parsed).__name__} mit {len(parsed) if hasattr(parsed, '__len__') else 'N/A'} Einträgen")
                        if isinstance(parsed, dict):
                            for sub_key in parsed.keys():
                                logger.info(f"         Key: {sub_key}")
                    except:
                        logger.info(f"      String-Inhalt (erste 100 Zeichen): {group_value[:100]}")
        
        return view_config
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Prüfen der View-Struktur: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    check_view_structure()
