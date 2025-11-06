#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HILFSTOOL: Verfügbare Views in der Datenbank finden

Zeigt alle verfügbaren View-GUIDs in der viewdaten Tabelle an.
"""

import logging
import sys
import os

# Logging konfigurieren
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def find_available_views():
    """Findet verfügbare Views in der Datenbank"""
    try:
        logger.info("🔍 Suche verfügbare Views in der Datenbank...")
        
        from pdvm_central_datenbank import PdvmCentralDatenbank
        
        # ViewDaten-Tabelle ohne spezifische GUID öffnen
        view_db = PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name="viewdaten",
            guid=None
        )
        
        # Alle ViewDaten laden
        all_views = view_db.lesen_alle_ohne_system(limit=50)
        
        logger.info(f"📋 {len(all_views)} Views gefunden:")
        logger.info("=" * 60)
        
        for i, view_info in enumerate(all_views):
            view_guid = view_info["uid"]
            view_data = view_info["daten_dict"]
            
            print(f"{i+1:2d}. GUID: {view_guid}")
            
            # Versuche wichtige Informationen zu extrahieren
            if "ROOT" in view_data:
                root_data = view_data["ROOT"]
                view_table = root_data.get("VIEW_TABLE", "N/A")
                print(f"    Tabelle: {view_table}")
                
            if "METADATEN" in view_data:
                meta_keys = list(view_data["METADATEN"].keys())
                print(f"    Metadaten: {meta_keys[:3]}..." if len(meta_keys) > 3 else f"    Metadaten: {meta_keys}")
            
            print()
            
        # Nimm die erste verfügbare View für den Test
        if all_views:
            first_view = all_views[0]
            print("🎯 Empfehlung für Test:")
            print(f"   Verwende GUID: {first_view['uid']}")
            return first_view['uid']
        else:
            print("❌ Keine Views gefunden!")
            return None
            
    except Exception as e:
        logger.error(f"❌ Fehler beim Suchen der Views: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    guid = find_available_views()
    if guid:
        print(f"\n✅ Test mit dieser GUID: {guid}")
    else:
        print("\n❌ Keine Views verfügbar für Test")
