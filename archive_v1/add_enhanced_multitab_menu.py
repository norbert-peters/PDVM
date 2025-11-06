#!/usr/bin/env python3
"""
Fügt Enhanced Multi-Tab-Menüeintrag hinzu
"""

import logging
from pdvm_central_datenbank import PdvmCentralDatenbank
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_enhanced_multitab_menu():
    """Fügt Enhanced Multi-Tab-Menüeintrag zu den Menüs hinzu"""
    
    # Menü-IDs
    menu_ids = [
        "5ca6674e-b9ce-4581-9756-64e742883f80",  # Admin-Startmenü
        "e1e77039-d1b5-46ff-b12b-cced0ae0da7c"   # Admin-Benutzermenü
    ]
    
    for menu_id in menu_ids:
        try:
            # Menü-Datenbank öffnen
            menu_db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name="menudaten",
                guid=menu_id
            )
            
            # Aktuelle Daten laden
            raw_data = menu_db.lesen()
            if not raw_data:
                print(f"❌ Menü {menu_id} nicht gefunden")
                continue
                
            # Daten extrahieren
            data = raw_data.get(menu_id, {})
            daten_str = data.get("daten", "{}")
            
            # JSON-Daten parsen
            menu_data = json.loads(daten_str)
            commands = menu_data.get("PD_commands", {})
            
            # Enhanced Multi-Tab-Einträge hinzufügen
            new_entries = {
                "Testbereich_📱 Enhanced Multi-Tab Test": "self.pdvm_enhanced_test()",
                "Testbereich_🚀 Enhanced Multi-Tab SOFORT": "self.pdvm_enhanced_frame()",
                "Testbereich_🔄 Current Frame Enhanced": "self.reload_current_frame_enhanced()"
            }
            
            # Einträge hinzufügen/aktualisieren
            added = []
            for key, command in new_entries.items():
                if key not in commands:
                    commands[key] = command
                    added.append(key)
                else:
                    print(f"✅ {key} bereits vorhanden - wird aktualisiert")
                    commands[key] = command
                    added.append(key)
            
            # Daten zurückspeichern
            menu_data["PD_commands"] = commands
            data["daten"] = json.dumps(menu_data, indent=2, ensure_ascii=False)
            
            # In Datenbank speichern
            updated_data = {menu_id: data}
            menu_db.speichern(menu_id, updated_data)
            
            print(f"✅ Enhanced Multi-Tab-Einträge für Menü {menu_id} hinzugefügt:")
            for entry in added:
                print(f"   • {entry}")
            
        except Exception as e:
            print(f"❌ Fehler bei Menü {menu_id}: {e}")

if __name__ == "__main__":
    print("🔧 Füge Enhanced Multi-Tab-Menüeinträge hinzu...")
    add_enhanced_multitab_menu()
    print("\n🎯 Neue Menüeinträge verfügbar:")
    print("   📱 Enhanced Multi-Tab Test - Vollständiger Test")
    print("   🚀 Enhanced Multi-Tab SOFORT - Sofortige Aktivierung")
    print("   🔄 Current Frame Enhanced - Aktuelles Frame mit Enhanced laden")
    print("\n💡 Starten Sie das PDVM-System neu, um die Menüeinträge zu sehen!")
