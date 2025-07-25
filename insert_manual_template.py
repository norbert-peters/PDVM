# insert_manual_template.py
"""
Fügt das manuell erstellte Template in die menudaten-Tabelle ein
"""
import json
import logging
from pdvm_central_datenbank import PdvmCentralDatenbank

# Logger-Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def insert_user_template():
    """Fügt das Benutzer-Template in die Datenbank ein"""
    
    # Template-GUID und -Daten
    template_guid = "1a653694-3132-48d9-bc3e-a512962ae8e6"
    
    # Template-Struktur (vom Benutzer bereitgestellt)
    template_data = {
        "PD_commands": {
            "Basis_Hilfe": "self.show_text_klein('Admin-Benutzermenü Hilfe')",
            "Basis_Abmelden": "self.logout()",
            "Basis_zu den Apps": "self.open_start_menu()",
            "Basis_Menü ein/aus": "self.toggle_menu_visibility()",
            "Basis_---": None
        },
        "PD_grund": {
            "Basis": {
                "Hilfe": None,
                "---(1)": None,
                "Menü ein/aus": None,
                "---(2)": None,
                "zu den Apps": None,
                "---(3)": None,
                "Abmelden": None,
                "---": None
            }
        },
        "PD_zusatz": {
            "PD_z_Grund": {},
            "PD_z_Menu": {}
        },
        "PD_menu": {}
    }
    
    try:
        print(f"📋 Füge Template mit GUID {template_guid} in Datenbank ein...")
        
        # Datenbank-Verbindung
        db = PdvmCentralDatenbank(
            db_name="PdvmManager.db",
            table_name="menudaten",
            guid=template_guid
        )
        
        # Template speichern (als JSON-String in 'daten' Spalte)
        success = db.speichern(template_guid, template_data)
        
        if success:
            print("✅ Template erfolgreich in Datenbank eingefügt!")
            
            # Verifikation: Template wieder laden
            print("🔍 Verifikation: Template laden...")
            loaded_data = db.lesen()
            
            if loaded_data and isinstance(loaded_data, dict):
                print("✅ Template-Verifikation erfolgreich!")
                print(f"📊 Template enthält {len(loaded_data)} Hauptgruppen:")
                
                for group_name, group_data in loaded_data.items():
                    if isinstance(group_data, dict):
                        print(f"   - {group_name}: {len(group_data)} Einträge")
                    else:
                        print(f"   - {group_name}: {type(group_data).__name__}")
                        
                return True
            else:
                print("❌ Template-Verifikation fehlgeschlagen")
                return False
                
        else:
            print("❌ Fehler beim Speichern des Templates")
            return False
            
    except Exception as e:
        print(f"❌ Fehler beim Template-Einfügen: {e}")
        return False

def test_template_after_insertion():
    """Testet das Template-System nach dem Einfügen"""
    print("\n🧪 Teste Template-System nach Einfügen...")
    
    try:
        from pdvm_menu_template_handler import PdvmMenuTemplateHandler
        
        template_handler = PdvmMenuTemplateHandler()
        template_guid = "1a653694-3132-48d9-bc3e-a512962ae8e6"
        
        # Template laden
        template_data = template_handler._load_template(template_guid)
        
        if template_data:
            print("✅ Template erfolgreich geladen!")
            
            # Test-Merging
            test_menu = {
                "PD_commands": {
                    "Benutzer_Profil bearbeiten": None,
                    "Testbereich_Enhanced Multi-Tab Test": "self.pdvm_enhanced_test()"
                },
                "PD_grund": {
                    "!guid!": template_guid
                },
                "PD_zusatz": {"PD_z_Grund": {}, "PD_z_Menu": {}},
                "PD_menu": {}
            }
            
            processed_menu = template_handler.process_menu_templates(test_menu)
            
            # Ergebnisse prüfen
            grund = processed_menu.get("PD_grund", {})
            if "!guid!" not in grund and "Basis" in grund:
                print("✅ Template-Merging erfolgreich!")
                print(f"📊 PD_grund enthält jetzt: {list(grund.keys())}")
                
                commands = processed_menu.get("PD_commands", {})
                print(f"📊 PD_commands enthält {len(commands)} Kommandos:")
                for cmd in list(commands.keys())[:5]:  # Erste 5 anzeigen
                    print(f"   - {cmd}")
                if len(commands) > 5:
                    print(f"   ... und {len(commands) - 5} weitere")
                
                return True
            else:
                print("❌ Template-Merging fehlgeschlagen - !guid! noch vorhanden")
                return False
        else:
            print("❌ Template konnte nicht geladen werden")
            return False
            
    except Exception as e:
        print(f"❌ Fehler beim Template-Test: {e}")
        return False

def main():
    """Hauptfunktion"""
    print("🔧 Template-Datenbank Einfügen")
    print("=" * 50)
    
    # 1. Template einfügen
    insertion_success = insert_user_template()
    
    if insertion_success:
        # 2. Template testen
        test_success = test_template_after_insertion()
        
        if test_success:
            print("\n🎉 Template erfolgreich eingefügt und getestet!")
            print("💡 Sie können jetzt das Template in Ihren Menüs verwenden")
            print("📋 Verwenden Sie: \"!guid!\": \"1a653694-3132-48d9-bc3e-a512962ae8e6\"")
        else:
            print("\n💥 Template eingefügt, aber Test fehlgeschlagen")
    else:
        print("\n❌ Template-Einfügen fehlgeschlagen")

if __name__ == "__main__":
    main()
