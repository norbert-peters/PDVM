#!/usr/bin/env python3
"""
Spezielle Reparatur für das erste Admin-Menü mit direkter Datenstruktur
"""

import logging
import json
from pdvm_central_datenbank import PdvmCentralDatenbank

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_admin_menu_structure():
    """Repariert das erste Admin-Menü mit direkter Struktur"""
    
    admin_menu_guid = "3424b00f-bb4d-4759-9689-e9e08249117b"
    
    try:
        print(f"🔧 Repariere Admin-Menü: {admin_menu_guid}")
        
        # Menüdaten laden
        db = PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name="menudaten",
            guid=admin_menu_guid
        )
        
        menu_data = db.lesen()
        print(f"📊 Geladene Daten-Struktur: {type(menu_data)}")
        print(f"📋 Schlüssel: {list(menu_data.keys()) if isinstance(menu_data, dict) else 'Kein Dict'}")
        
        # Prüfe direkte Struktur (ohne GUID-Verschachtelung)
        if isinstance(menu_data, dict) and "PD_commands" in menu_data:
            print("✅ Direkte Struktur gefunden - repariere...")
            
            # Bestehende PD_commands speichern
            existing_commands = menu_data.get("PD_commands", {})
            print(f"📋 Bestehende Commands: {len(existing_commands)} Einträge")
            
            # Korrekte Grundstruktur erstellen
            correct_structure = {
                "PD_commands": existing_commands,
                "PD_grund": {
                    "Basis": {
                        "Hilfe": "self.show_text_klein('Admin-Menü Hilfe')",
                        "Abmelden": "self.logout()",
                        "---": None
                    },
                    "Testbereich": {
                        "Enhanced Multi-Tab": {
                            "📱 Enhanced Multi-Tab Test": "self.pdvm_enhanced_test()",
                            "🚀 Enhanced Multi-Tab SOFORT": "self.pdvm_enhanced_frame()",
                            "🔄 Current Frame Enhanced": "self.reload_current_frame_enhanced()",
                            "---": None
                        }
                    },
                    "Einstellungen": {
                        "Layout": {
                            "Layout hinzufügen": None,
                            "---": None
                        }
                    }
                },
                "PD_zusatz": {
                    "PD_z_Grund": {},
                    "PD_z_Menu": {}
                },
                "PD_menu": {}
            }
            
            # Direkt speichern (ohne GUID-Verschachtelung)
            db.speichern(admin_menu_guid, correct_structure)
            
            print("✅ Admin-Menü-Struktur erfolgreich repariert!")
            print(f"📊 Neue Struktur: {list(correct_structure.keys())}")
            
        else:
            print("❌ Erwartete direkte Struktur nicht gefunden")
            print(f"🔍 Tatsächliche Struktur: {menu_data}")
            
    except Exception as e:
        print(f"❌ Fehler beim Reparieren des Admin-Menüs: {e}")
    
    print("\n🎯 Admin-Menü-Reparatur abgeschlossen!")

if __name__ == "__main__":
    fix_admin_menu_structure()
