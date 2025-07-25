#!/usr/bin/env python3
"""
Fix für Startmenü-Struktur - repariert PD_grund Fehler
"""

import logging
from pdvm_central_datenbank import PdvmCentralDatenbank

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_startmenu_structure():
    """Repariert die Startmenü-Struktur"""
    
    startmenu_guid = "5ca6674e-b9ce-4581-9756-64e742883f80"
    
    # Menüdaten laden
    db = PdvmCentralDatenbank(
        db_name="PdvmManager.db",
        table_name="menudaten",
        guid=startmenu_guid
    )
    
    menu_data = db.lesen()
    print(f"🔍 Aktuelle Startmenü-Daten: {type(menu_data)}")
    print(f"📊 Schlüssel: {menu_data.keys() if isinstance(menu_data, dict) else 'Kein Dict'}")
    
    if isinstance(menu_data, dict) and startmenu_guid in menu_data:
        # Verschachtelte Struktur - extrahiere echte Daten
        nested_data = menu_data[startmenu_guid]
        print(f"🔍 Verschachtelte Daten gefunden: {type(nested_data)}")
        
        if isinstance(nested_data, dict) and "daten" in nested_data:
            # JSON-String in den Daten
            import json
            try:
                actual_data = json.loads(nested_data["daten"])
                print(f"✅ JSON-Daten erfolgreich geladen: {type(actual_data)}")
                print(f"📊 Schlüssel in actual_data: {actual_data.keys() if isinstance(actual_data, dict) else 'Kein Dict'}")
                
                # Prüfe ob PD_grund fehlt
                if "PD_commands" in actual_data and "PD_grund" not in actual_data:
                    print("❌ PD_grund fehlt! Füge hinzu...")
                    
                    # Standard PD_grund Struktur hinzufügen
                    actual_data["PD_grund"] = {
                        "Startmenü": {
                            "App Auswahl": {
                                "MeineApps": "self.open_app_menu('MeineApps')",
                                "Finanzen": "self.open_app_menu('Finanzen')",
                                "---": None
                            },
                            "System": {
                                "Start-Menü": "self.open_start_menu()",
                                "Abmelden": "self.logout()",
                                "---": None
                            }
                        },
                        "Testbereich": {
                            "Dialog Tests": {
                                "📱 Enhanced Multi-Tab Test": "self.pdvm_enhanced_test()",
                                "🚀 Enhanced Multi-Tab SOFORT": "self.pdvm_enhanced_frame()",
                                "🔄 Current Frame Enhanced": "self.reload_current_frame_enhanced()",
                                "🎨 Unified Dialog V3": "self.pdvm_unified_test()",
                                "📊 Standard Dialog": "self.pdvm_dialog('4078079f-4028-45ed-879c-3c779ecf3d0d', 0)",
                                "---": None
                            },
                            "System Tests": {
                                "🔧 Menü umschalten": "self.toggle_menu_visibility()",
                                "---": None
                            }
                        },
                        "Admin": {
                            "Menü Editor": {
                                "Admin-Menü": "self.open_menu_editor('Admin-Menü')",
                                "Admin-Startmenü": "self.open_menu_editor('Admin-Startmenü')",
                                "Admin-Benutzermenü": "self.open_menu_editor('Admin-Benutzermenü')",
                                "---": None
                            }
                        }
                    }
                    
                    # Zurück konvertieren und speichern
                    nested_data["daten"] = json.dumps(actual_data, ensure_ascii=False, indent=2)
                    menu_data[startmenu_guid] = nested_data
                    
                    # Speichern
                    db.speichern(startmenu_guid, menu_data)
                    print("✅ PD_grund Struktur erfolgreich hinzugefügt!")
                    
                else:
                    print("✅ PD_grund bereits vorhanden oder PD_commands fehlt")
                    
            except json.JSONDecodeError as e:
                print(f"❌ JSON-Fehler: {e}")
        else:
            print(f"❌ Keine 'daten' in verschachtelter Struktur gefunden")
    else:
        print(f"❌ Erwartete verschachtelte Struktur nicht gefunden")

if __name__ == "__main__":
    fix_startmenu_structure()
