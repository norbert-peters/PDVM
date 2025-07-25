#!/usr/bin/env python3
"""
Direkte Prüfung und Korrektur der Menüdaten in der Datenbank
"""

import logging
import json
import sqlite3

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_and_fix_menu_database():
    """Prüft und korrigiert die Menüdaten direkt in der SQLite-Datenbank"""
    
    db_path = "PdvmManager.db"
    
    try:
        # Direkte SQLite-Verbindung
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Aktuelle Daten der beiden Menüs prüfen
        menu_guids = [
            "5ca6674e-b9ce-4581-9756-64e742883f80",  # Admin-Startmenü
            "e1e77039-d1b5-46ff-b12b-cced0ae0da7c"   # Admin-Benutzermenü
        ]
        
        for menu_guid in menu_guids:
            print(f"\n🔍 Prüfe Menü: {menu_guid}")
            
            # Aktuellen Inhalt laden
            cursor.execute("SELECT daten, bezeichnung FROM menudaten WHERE uid = ?", (menu_guid,))
            result = cursor.fetchone()
            
            if result:
                current_data, bezeichnung = result
                print(f"📋 Bezeichnung: {bezeichnung}")
                print(f"📊 Aktuelle Daten (ersten 200 Zeichen): {current_data[:200]}...")
                
                try:
                    # Versuche JSON zu parsen
                    data_dict = json.loads(current_data)
                    print(f"✅ JSON erfolgreich geladen")
                    print(f"📋 Hauptschlüssel: {list(data_dict.keys())}")
                    
                    # Prüfe verschachtelte Struktur
                    if menu_guid in data_dict:
                        nested = data_dict[menu_guid]
                        if "daten" in nested:
                            inner_data = json.loads(nested["daten"])
                            print(f"📋 Verschachtelte Struktur - Innere Schlüssel: {list(inner_data.keys())}")
                        else:
                            print("❌ Keine 'daten' in verschachtelter Struktur")
                    else:
                        print("❌ GUID nicht als Schlüssel in Hauptdaten gefunden")
                        
                except json.JSONDecodeError as e:
                    print(f"❌ JSON-Fehler: {e}")
            else:
                print(f"❌ Keine Daten für GUID {menu_guid} gefunden")
        
        conn.close()
        
        # Jetzt korrigieren mit korrektem Update
        fix_menus_correctly()
        
    except Exception as e:
        print(f"❌ Datenbankfehler: {e}")

def fix_menus_correctly():
    """Korrigiert die Menüs mit direktem SQL-Update"""
    
    db_path = "PdvmManager.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Admin-Startmenü korrigieren
        startmenu_guid = "5ca6674e-b9ce-4581-9756-64e742883f80"
        startmenu_structure = {
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
        
        # Verschachtelte Struktur für Startmenü
        nested_startmenu = {
            startmenu_guid: {
                "daten": json.dumps(startmenu_structure, ensure_ascii=False, indent=2)
            }
        }
        
        # Admin-Benutzermenü korrigieren
        usermenu_guid = "e1e77039-d1b5-46ff-b12b-cced0ae0da7c"
        usermenu_structure = {
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
        
        # Verschachtelte Struktur für Benutzermenü
        nested_usermenu = {
            usermenu_guid: {
                "daten": json.dumps(usermenu_structure, ensure_ascii=False, indent=2)
            }
        }
        
        # Direkt in Datenbank aktualisieren
        startmenu_json = json.dumps(nested_startmenu, ensure_ascii=False, indent=2)
        usermenu_json = json.dumps(nested_usermenu, ensure_ascii=False, indent=2)
        
        # UPDATE-Statements ausführen
        cursor.execute(
            "UPDATE menudaten SET daten = ? WHERE uid = ?",
            (startmenu_json, startmenu_guid)
        )
        
        cursor.execute(
            "UPDATE menudaten SET daten = ? WHERE uid = ?", 
            (usermenu_json, usermenu_guid)
        )
        
        # Änderungen committen
        conn.commit()
        
        print(f"\n✅ Admin-Startmenü ({startmenu_guid}) direkt in DB aktualisiert")
        print(f"✅ Admin-Benutzermenü ({usermenu_guid}) direkt in DB aktualisiert")
        
        # Verification - nochmal prüfen
        cursor.execute("SELECT daten FROM menudaten WHERE uid = ?", (startmenu_guid,))
        result = cursor.fetchone()
        if result:
            data = json.loads(result[0])
            if startmenu_guid in data and "daten" in data[startmenu_guid]:
                inner = json.loads(data[startmenu_guid]["daten"])
                print(f"✅ Startmenü Verifikation: {list(inner.keys())}")
        
        cursor.execute("SELECT daten FROM menudaten WHERE uid = ?", (usermenu_guid,))
        result = cursor.fetchone()
        if result:
            data = json.loads(result[0])
            if usermenu_guid in data and "daten" in data[usermenu_guid]:
                inner = json.loads(data[usermenu_guid]["daten"])
                print(f"✅ Benutzermenü Verifikation: {list(inner.keys())}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Fehler beim direkten Update: {e}")

if __name__ == "__main__":
    check_and_fix_menu_database()
    print("\n🎯 Direkte Datenbankkorrektur abgeschlossen!")
    print("🔄 Starten Sie das PDVM-System neu, um die Änderungen zu sehen")
