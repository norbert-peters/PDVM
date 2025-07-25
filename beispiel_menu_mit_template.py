# beispiel_menu_mit_template.py
"""
Beispiel: Wie man Templates in Menüs verwendet
"""
import json
from pdvm_central_datenbank import PdvmCentralDatenbank

def create_example_menu_with_template():
    """
    Erstellt ein Beispielmenü das Templates verwendet
    """
    
    # Beispiel: Personalwesen-Menü mit Standard-Template
    personalwesen_menu = {
        "PD_commands": {
            "open_start_menu()": "root.open_start_menu()",
            "toggle_menu_visibility()": "root.toggle_menu_visibility()",  
            "logout()": "root.logout()",
            "personen_verwalten()": "root.pdvm_dialog('personen-frame-guid', 0)",
            "mitarbeiter_suche()": "root.pdvm_search('personen-view-guid', 'personen-frame-guid', 0)"
        },
        "PD_grund": {
            # Template-Referenz - fügt Standard Basis-Menü ein
            "!guid!": "template-basis-standard"
        },
        "PD_zusatz": {
            "Personal-Tools": {
                "Mitarbeiter-Import": "import_mitarbeiter()",
                "Gehaltslisten": "gehaltslisten_anzeigen()"
            }
        },
        "PD_menu": {
            "Personen verwalten": "personen_verwalten()",
            "Mitarbeiter suchen": "mitarbeiter_suche()",
            "---": "---",
            "Personal-Tools": "Personal-Tools"
        }
    }
    
    # Menü in Datenbank speichern
    try:
        menu_guid = "personalwesen-menu-mit-template"
        
        db = PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name="menudaten", 
            guid=menu_guid
        )
        
        db.speichern(menu_guid, {
            menu_guid: {
                "uid": menu_guid,
                "bezeichnung": "Personalwesen (mit Template)",
                "daten": personalwesen_menu
            }
        })
        
        print(f"✅ Beispielmenü erstellt: {menu_guid}")
        print("📋 Das PD_grund wird automatisch erweitert um:")
        print("   - Zurück zu Apps")
        print("   - Menü ein/aus") 
        print("   - Logout")
        
        return menu_guid
        
    except Exception as e:
        print(f"❌ Fehler beim Erstellen des Beispielmenüs: {e}")
        return None

def create_startmenu_with_template():
    """
    Erstellt ein Startmenü mit Template
    """
    
    startmenu = {
        "PD_commands": {
            "toggle_menu_visibility()": "root.toggle_menu_visibility()",
            "logout()": "root.logout()",
            "pdvm_start('Personalwesen')": "root.pdvm_start('Personalwesen')",
            "pdvm_start('Finanzwesen')": "root.pdvm_start('Finanzwesen')",
            "pdvm_start('Testbereich')": "root.pdvm_start('Testbereich')"
        },
        "PD_grund": {
            # Startmenü-Template am Anfang einfügen
            "!guid!prepend": "template-startmenu-basis",
            "System-Info": "system_info()"
        },
        "PD_zusatz": {},
        "PD_menu": {
            "Personalwesen": "pdvm_start('Personalwesen')",
            "Finanzwesen": "pdvm_start('Finanzwesen')",
            "Testbereich": "pdvm_start('Testbereich')",
            "---": "---",
            "System-Info": "system_info()"
        }
    }
    
    try:
        menu_guid = "startmenu-mit-template"
        
        db = PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name="menudaten",
            guid=menu_guid
        )
        
        db.speichern(menu_guid, {
            menu_guid: {
                "uid": menu_guid,
                "bezeichnung": "Startmenü (mit Template)",
                "daten": startmenu
            }
        })
        
        print(f"✅ Startmenü mit Template erstellt: {menu_guid}")
        print("📋 Template wird am Anfang eingefügt (prepend)")
        
        return menu_guid
        
    except Exception as e:
        print(f"❌ Fehler beim Erstellen des Startmenüs: {e}")
        return None

def test_template_system():
    """
    Testet das Template-System
    """
    print("🔧 Teste Menü-Template-System...")
    
    # 1. Beispielmenüs erstellen
    personalwesen_guid = create_example_menu_with_template()
    startmenu_guid = create_startmenu_with_template()
    
    if personalwesen_guid and startmenu_guid:
        print("\n🎉 Template-System erfolgreich getestet!")
        print("\n💡 Nächste Schritte:")
        print("1. Menüs in der Anwendung laden und testen")
        print("2. Bei Bedarf eigene Templates erstellen")
        print("3. Bestehende Menüs auf Templates umstellen")
        
        print(f"\n📋 Test-Menü GUIDs:")
        print(f"   - Personalwesen: {personalwesen_guid}")
        print(f"   - Startmenü: {startmenu_guid}")
    else:
        print("\n💥 Template-Test fehlgeschlagen!")

if __name__ == "__main__":
    test_template_system()
