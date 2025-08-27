#!/usr/bin/env python3
"""
Debug-Skript für Dialog-Persistierung
=====================================

Dieses Skript hilft dabei herauszufinden, warum Dialog-Änderungen 
nicht persistent gespeichert werden.
"""

import logging
import sys
from PyQt5.QtWidgets import QApplication

def debug_systemsteuerung_content():
    """Liest den aktuellen Inhalt der Systemsteuerung aus"""
    
    print("🔍 Debug: Systemsteuerung-Inhalt")
    print("=" * 50)
    
    try:
        from pdvm_central_datenbank import PdvmCentralDatenbank
        
        # Systemsteuerung-Instanz erstellen
        systemsteuerung_db = PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name="systemsteuerung",
            guid=None
        )
        
        # Alle Daten lesen
        all_data = systemsteuerung_db.lesen()
        print(f"📊 Gesamte Systemsteuerung-Daten:")
        
        if all_data:
            import json
            print(json.dumps(all_data, indent=2, ensure_ascii=False))
            
            # Suche nach complete_controls
            user_guid = "5f97b7da-42d4-4b03-815a-34775fbb6138"  # Deine User-GUID
            
            if user_guid in all_data:
                user_data = all_data[user_guid]
                print(f"\n🔍 User {user_guid} Daten:")
                print(json.dumps(user_data, indent=2, ensure_ascii=False))
                
                if 'complete_controls' in user_data:
                    controls_data = user_data['complete_controls']
                    print(f"\n📋 complete_controls gefunden:")
                    print(json.dumps(controls_data, indent=2, ensure_ascii=False))
                else:
                    print(f"\n❌ Keine 'complete_controls' für User {user_guid} gefunden")
            else:
                print(f"\n❌ User {user_guid} nicht in Systemsteuerung gefunden")
                print(f"📋 Verfügbare Gruppen: {list(all_data.keys())}")
        else:
            print("❌ Keine Daten in Systemsteuerung gefunden")
            
    except Exception as e:
        print(f"❌ Fehler beim Lesen der Systemsteuerung: {e}")
        import traceback
        traceback.print_exc()

def debug_provider_load():
    """Testet das Laden über den Provider"""
    
    print("\n🔍 Debug: Provider-Laden")
    print("=" * 50)
    
    try:
        from pdvm_value_view_provider import PdvmValueViewProvider
        
        # Fake App für Provider
        if not QApplication.instance():
            app = QApplication(sys.argv)
        
        # Provider erstellen
        provider = PdvmValueViewProvider(db_name="PdvmManager.db")
        
        # Test: Lade gespeicherte Config
        user_guid = "5f97b7da-42d4-4b03-815a-34775fbb6138"
        saved_config = provider._load_show_order_from_systemsteuerung(user_guid, {})
        
        if saved_config:
            print(f"✅ Gespeicherte Config gefunden:")
            import json
            print(json.dumps(saved_config, indent=2, ensure_ascii=False))
        else:
            print(f"❌ Keine gespeicherte Config für User {user_guid} gefunden")
            
    except Exception as e:
        print(f"❌ Fehler beim Provider-Test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Logging für Details
    logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')
    
    print("🎯 Dialog-Persistierung Debug")
    print("=" * 60)
    
    # 1. Systemsteuerung-Inhalt prüfen
    debug_systemsteuerung_content()
    
    # 2. Provider-Laden testen
    debug_provider_load()
    
    print("\n✅ Debug abgeschlossen")
