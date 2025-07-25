#!/usr/bin/env python3
"""
Korrekte Wiederherstellung der Admin-Startmenü und Admin-Benutzermenü Strukturen
Basierend auf der etablierten 4-Gruppen-Struktur: PD_commands, PD_grund, PD_zusatz, PD_menu
"""

import logging
import json
from pdvm_central_datenbank import PdvmCentralDatenbank

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def restore_correct_menu_structures():
    """Stellt die korrekten Menüstrukturen wieder her"""
    
    # Admin-Startmenü wiederherstellen
    restore_admin_startmenu()
    
    # Admin-Benutzermenü wiederherstellen  
    restore_admin_usermenu()

def restore_admin_startmenu():
    """Stellt das Admin-Startmenü korrekt wieder her"""
    
    startmenu_guid = "5ca6674e-b9ce-4581-9756-64e742883f80"
    
    print(f"🔧 Stelle Admin-Startmenü korrekt wieder her: {startmenu_guid}")
    
    try:
        # Korrekte Startmenü-Struktur nach etabliertem Schema
        correct_startmenu_structure = {
            "PD_commands": {
                "Basis_Hilfe": "self.show_text_klein('Admin-Startmenü Hilfe')",
                "Basis_Abmelden": "self.logout()",
                "Basis_zu den Apps": "self.open_start_menu()",
                "Basis_---": None,
                "Apps_MeineApps": "self.open_app_menu('MeineApps')",
                "Apps_Finanzen": "self.open_app_menu('Finanzen')",
                "Apps_---": None,
                "Testbereich_Enhanced Multi-Tab Test": "self.pdvm_enhanced_test()",
                "Testbereich_Enhanced Multi-Tab SOFORT": "self.pdvm_enhanced_frame()",
                "Testbereich_Current Frame Enhanced": "self.reload_current_frame_enhanced()",
                "Testbereich_Unified Dialog V3": "self.pdvm_unified_test()",
                "Testbereich_Standard Dialog": "self.pdvm_dialog('4078079f-4028-45ed-879c-3c779ecf3d0d', 0)",
                "Testbereich_---": None,
                "System_Menü umschalten": "self.toggle_menu_visibility()",
                "System_---": None,
                "Admin_Admin-Menü": "self.open_menu_editor('Admin-Menü')",
                "Admin_Admin-Startmenü": "self.open_menu_editor('Admin-Startmenü')",
                "Admin_Admin-Benutzermenü": "self.open_menu_editor('Admin-Benutzermenü')",
                "Admin_---": None
            },
            "PD_grund": {
                "Basis": {
                    "Hilfe": None,
                    "zu den Apps": None,
                    "Abmelden": None,
                    "---": None
                },
                "Apps": {
                    "MeineApps": None,
                    "Finanzen": None,
                    "---": None
                },
                "Testbereich": {
                    "Enhanced Multi-Tab Test": None,
                    "Enhanced Multi-Tab SOFORT": None,
                    "Current Frame Enhanced": None,
                    "Unified Dialog V3": None,
                    "Standard Dialog": None,
                    "---": None
                },
                "System": {
                    "Menü umschalten": None,
                    "---": None
                },
                "Admin": {
                    "Admin-Menü": None,
                    "Admin-Startmenü": None,
                    "Admin-Benutzermenü": None,
                    "---": None
                }
            },
            "PD_zusatz": {
                "PD_z_Grund": {},
                "PD_z_Menu": {}
            },
            "PD_menu": {}
        }
        
        # Als verschachtelte JSON-Struktur speichern (wie im Original)
        nested_structure = {
            startmenu_guid: {
                "daten": json.dumps(correct_startmenu_structure, ensure_ascii=False, indent=2)
            }
        }
        
        # In Datenbank speichern
        db = PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name="menudaten", 
            guid=startmenu_guid
        )
        
        db.speichern(startmenu_guid, nested_structure)
        
        print("✅ Admin-Startmenü korrekt wiederhergestellt!")
        print(f"📊 Struktur: {list(correct_startmenu_structure.keys())}")
        
    except Exception as e:
        print(f"❌ Fehler beim Wiederherstellen des Admin-Startmenüs: {e}")

def restore_admin_usermenu():
    """Stellt das Admin-Benutzermenü korrekt wieder her"""
    
    usermenu_guid = "e1e77039-d1b5-46ff-b12b-cced0ae0da7c"
    
    print(f"🔧 Stelle Admin-Benutzermenü korrekt wieder her: {usermenu_guid}")
    
    try:
        # Korrekte Benutzermenü-Struktur nach etabliertem Schema
        correct_usermenu_structure = {
            "PD_commands": {
                "Basis_Hilfe": "self.show_text_klein('Admin-Benutzermenü Hilfe')", 
                "Basis_Abmelden": "self.logout()",
                "Basis_---": None,
                "Benutzer_Profil bearbeiten": None,
                "Benutzer_Einstellungen": None,
                "Benutzer_---": None,
                "Testbereich_Enhanced Multi-Tab Test": "self.pdvm_enhanced_test()",
                "Testbereich_Enhanced Multi-Tab SOFORT": "self.pdvm_enhanced_frame()",
                "Testbereich_Current Frame Enhanced": "self.reload_current_frame_enhanced()",
                "Testbereich_---": None
            },
            "PD_grund": {
                "Basis": {
                    "Hilfe": None,
                    "Abmelden": None,
                    "---": None
                },
                "Benutzer": {
                    "Profil bearbeiten": None,
                    "Einstellungen": None,
                    "---": None
                },
                "Testbereich": {
                    "Enhanced Multi-Tab Test": None,
                    "Enhanced Multi-Tab SOFORT": None,
                    "Current Frame Enhanced": None,
                    "---": None
                }
            },
            "PD_zusatz": {
                "PD_z_Grund": {},
                "PD_z_Menu": {}
            },
            "PD_menu": {}
        }
        
        # Als verschachtelte JSON-Struktur speichern (wie im Original)
        nested_structure = {
            usermenu_guid: {
                "daten": json.dumps(correct_usermenu_structure, ensure_ascii=False, indent=2)
            }
        }
        
        # In Datenbank speichern
        db = PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name="menudaten",
            guid=usermenu_guid
        )
        
        db.speichern(usermenu_guid, nested_structure)
        
        print("✅ Admin-Benutzermenü korrekt wiederhergestellt!")
        print(f"📊 Struktur: {list(correct_usermenu_structure.keys())}")
        
    except Exception as e:
        print(f"❌ Fehler beim Wiederherstellen des Admin-Benutzermenüs: {e}")

if __name__ == "__main__":
    restore_correct_menu_structures()
    print("\n🎯 Beide Menüs korrekt nach etabliertem Schema wiederhergestellt!")
    print("💡 Enhanced Multi-Tab Funktionen bleiben als Testbereich-Einträge erhalten")
    print("🔄 Starten Sie das PDVM-System neu, um die korrekten Menüs zu verwenden")
    print("⚠️  Hinweis: Zukünftige Menü-Änderungen nur noch über das Menü-Editor-System!")
