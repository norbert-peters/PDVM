#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug-Skript: Analysiere wo die App-GUIDs in den Benutzerdaten stehen
"""

from pdvm_central_systemsteuerung_final import get_gcs

def debug_app_guids():
    """Analysiere die GCS-Struktur und App-GUID-Speicherung"""
    print("🔍 Debug: App-GUID-Analyse")
    print("=" * 50)
    
    # GCS-Instanz laden
    gcs = get_gcs()
    
    print(f"👤 Aktueller Benutzer: {gcs._user_guid}")
    print(f"📋 Benutzerdaten-Keys: {list(gcs._user_data.keys()) if gcs._user_data else 'Keine'}")
    
    # Prüfe DB-Instanz
    if hasattr(gcs._db, 'data'):
        print(f"💾 DB-Daten verfügbar: {len(gcs._db.data)} Gruppen")
        print(f"📦 Verfügbare Gruppen: {list(gcs._db.data.keys())[:10] if gcs._db.data else 'Keine'}")
        
        # Prüfe ob User-GUID als Gruppe existiert
        if gcs._user_guid in gcs._db.data:
            user_group = gcs._db.data[gcs._user_guid]
            print(f"✅ User-Gruppe gefunden: {type(user_group)}")
            if isinstance(user_group, dict):
                print(f"📝 Felder in User-Gruppe: {list(user_group.keys())}")
                
                # Prüfe spezifisch nach MeineApps
                if 'MeineApps' in user_group:
                    meine_apps = user_group['MeineApps']
                    print(f"📱 MeineApps gefunden: {type(meine_apps)}")
                    if isinstance(meine_apps, str):
                        print(f"📱 MeineApps (ersten 200 Zeichen): {meine_apps[:200]}...")
                    else:
                        print(f"📱 MeineApps Inhalt: {meine_apps}")
                else:
                    print("❌ MeineApps nicht in User-Gruppe gefunden")
            else:
                print(f"⚠️ User-Gruppe ist kein Dictionary: {user_group}")
        else:
            print(f"❌ User-GUID {gcs._user_guid} nicht als Gruppe gefunden")
    else:
        print("❌ DB-Instanz hat keine data-Attribute")
    
    print("\n" + "=" * 50)
    print("🧪 Teste get_value-Zugriff:")
    
    # Teste verschiedene Zugriffsmuster
    test_felder = ['MeineApps', 'startmenu', 'apps', 'Applications', 'meineapps']
    
    for feld in test_felder:
        try:
            wert = gcs._db.get_value(gruppe=gcs._user_guid, feld=feld)
            if wert:
                print(f"✅ {feld}: {type(wert)} - {str(wert)[:100]}...")
            else:
                print(f"❌ {feld}: Nicht gefunden")
        except Exception as e:
            print(f"💥 {feld}: Fehler - {e}")
    
    print("\n" + "=" * 50)
    print("🔍 Suche nach App-Namen in allen Feldern:")
    
    # Suche nach bekannten App-Namen in der User-Gruppe
    app_namen = ['Testbereich', 'Personalwesen', 'Finanzwesen', 'Administration', 'Benutzerdaten']
    
    if gcs._user_guid in gcs._db.data and isinstance(gcs._db.data[gcs._user_guid], dict):
        user_data = gcs._db.data[gcs._user_guid]
        for feld_name, feld_wert in user_data.items():
            feld_str = str(feld_wert).lower()
            for app_name in app_namen:
                if app_name.lower() in feld_str:
                    print(f"🎯 '{app_name}' gefunden in Feld '{feld_name}': {str(feld_wert)[:200]}...")
                    break

if __name__ == "__main__":
    debug_app_guids()
