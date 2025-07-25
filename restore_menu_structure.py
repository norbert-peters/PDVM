#!/usr/bin/env python3
"""
Reparatur der Menü-Grundstruktur - stellt die korrekte PD_grund Struktur wieder her
"""

import logging
import json
from pdvm_central_datenbank import PdvmCentralDatenbank

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def restore_menu_structure():
    """Stellt die korrekte Menü-Grundstruktur wieder her"""
    
    # Alle drei Admin-Menüs reparieren
    menu_guids = [
        "3424b00f-bb4d-4759-9689-e9e08249117b",  # Admin-Menü
        "5ca6674e-b9ce-4581-9756-64e742883f80",  # Admin-Startmenü
        "e1e77039-d1b5-46ff-b12b-cced0ae0da7c"   # Admin-Benutzermenü
    ]
    
    for menu_guid in menu_guids:
        try:
            print(f"\n🔧 Repariere Menü: {menu_guid}")
            
            # Menüdaten laden
            db = PdvmCentralDatenbank(
                db_name="PdvmManager.db",
                table_name="menudaten",
                guid=menu_guid
            )
            
            menu_data = db.lesen()
            
            if not menu_data:
                print(f"❌ Keine Daten für Menü {menu_guid} gefunden")
                continue
                
            # Prüfe verschachtelte Struktur
            if menu_guid in menu_data and isinstance(menu_data[menu_guid], dict):
                nested_data = menu_data[menu_guid]
                
                if "daten" in nested_data and isinstance(nested_data["daten"], str):
                    # JSON-String extrahieren
                    try:
                        current_structure = json.loads(nested_data["daten"])
                        print(f"✅ Aktuelle Struktur geladen: {list(current_structure.keys())}")
                        
                        # Korrekte Grundstruktur erstellen
                        correct_structure = {
                            "PD_commands": {},
                            "PD_grund": {},
                            "PD_zusatz": {
                                "PD_z_Grund": {},
                                "PD_z_Menu": {}
                            },
                            "PD_menu": {}
                        }
                        
                        # Bestehende PD_commands übernehmen falls vorhanden
                        if "PD_commands" in current_structure:
                            correct_structure["PD_commands"] = current_structure["PD_commands"]
                            print(f"📋 PD_commands übernommen: {len(current_structure['PD_commands'])} Einträge")
                        
                        # Spezielle Menü-Strukturen je nach Typ
                        if menu_guid == "5ca6674e-b9ce-4581-9756-64e742883f80":  # Startmenü
                            correct_structure["PD_grund"] = {
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
                        elif menu_guid == "3424b00f-bb4d-4759-9689-e9e08249117b":  # Admin-Menü
                            correct_structure["PD_grund"] = {
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
                            }
                        elif menu_guid == "e1e77039-d1b5-46ff-b12b-cced0ae0da7c":  # Admin-Benutzermenü
                            correct_structure["PD_grund"] = {
                                "Benutzer": {
                                    "Profile": {
                                        "Profil bearbeiten": None,
                                        "Einstellungen": None,
                                        "---": None
                                    }
                                },
                                "Testbereich": {
                                    "Enhanced Multi-Tab": {
                                        "📱 Enhanced Multi-Tab Test": "self.pdvm_enhanced_test()",
                                        "🚀 Enhanced Multi-Tab SOFORT": "self.pdvm_enhanced_frame()",
                                        "🔄 Current Frame Enhanced": "self.reload_current_frame_enhanced()",
                                        "---": None
                                    }
                                }
                            }
                        
                        # Zurück konvertieren und speichern
                        nested_data["daten"] = json.dumps(correct_structure, ensure_ascii=False, indent=2)
                        menu_data[menu_guid] = nested_data
                        
                        # In Datenbank speichern
                        db.speichern(menu_guid, menu_data)
                        
                        print(f"✅ Menü-Struktur für {menu_guid} erfolgreich repariert!")
                        print(f"📊 Neue Struktur: {list(correct_structure.keys())}")
                        
                    except json.JSONDecodeError as e:
                        print(f"❌ JSON-Fehler bei {menu_guid}: {e}")
                        
            else:
                print(f"❌ Unerwartete Datenstruktur für {menu_guid}")
                
        except Exception as e:
            print(f"❌ Fehler beim Reparieren von {menu_guid}: {e}")
    
    print("\n🎯 Menü-Reparatur abgeschlossen!")
    print("💡 Starten Sie das PDVM-System neu, um die reparierte Struktur zu verwenden.")

if __name__ == "__main__":
    restore_menu_structure()
