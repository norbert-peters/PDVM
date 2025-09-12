#!/usr/bin/env python3
"""
Setup-Script für die App-GUIDs in der GCS-Datenbank.
Erstellt die notwendigen Einträge für alle Anwendungen.
"""

def setup_application_guids():
    """
    Erstellt die App-GUIDs für alle Anwendungen in der GCS-Datenbank.
    """
    # App-GUIDs (diese sollten aus dem echten System kommen)
    app_guids = {
        "Testbereich": "testbereich-guid-12345",
        "Personalwesen": "personalwesen-guid-67890", 
        "Finanzwesen": "finanzwesen-guid-abcdef",
        "Administration": "administration-guid-fedcba",
        "Benutzerdaten": "benutzerdaten-guid-098765"
    }
    
    try:
        from pdvm_central_datenbank import PdvmCentralDatenbank
        
        # Erstelle Datenbank-Instanz
        db = PdvmCentralDatenbank()
        
        # Setze User-GUID (sollte aus dem echten System kommen)
        user_guid = "4886ad26-061b-4662-a762-c8c83f36692d"
        db.set_guid(user_guid)
        
        print("📋 Erstelle App-GUIDs in der GCS-Datenbank:")
        
        for app_name, app_guid in app_guids.items():
            try:
                db.set_value(gruppe="Application", feld=app_name, wert=app_guid)
                print(f"   ✅ {app_name}: {app_guid}")
            except Exception as e:
                print(f"   ❌ {app_name}: Fehler - {e}")
        
        print("\n🎉 App-GUIDs erfolgreich erstellt!")
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Setup der App-GUIDs: {e}")
        return False

def test_app_guids():
    """
    Testet ob die App-GUIDs korrekt geladen werden können.
    """
    try:
        from pdvm_central_datenbank import PdvmCentralDatenbank
        
        db = PdvmCentralDatenbank()
        user_guid = "4886ad26-061b-4662-a762-c8c83f36692d"
        db.set_guid(user_guid)
        
        apps = ['Testbereich', 'Personalwesen', 'Finanzwesen', 'Administration', 'Benutzerdaten']
        print("\n🔍 Teste App-GUIDs:")
        
        for app in apps:
            try:
                app_guid = db.get_value(gruppe="Application", feld=app)
                if app_guid:
                    print(f"   ✅ {app}: {app_guid}")
                else:
                    print(f"   ❌ {app}: Nicht gefunden")
            except Exception as e:
                print(f"   💥 {app}: Fehler - {e}")
                
    except Exception as e:
        print(f"❌ Fehler beim Testen der App-GUIDs: {e}")

if __name__ == "__main__":
    print("🚀 === APP-GUID SETUP ===")
    
    # Setup durchführen
    if setup_application_guids():
        # Test durchführen
        test_app_guids()
    else:
        print("❌ Setup fehlgeschlagen!")
