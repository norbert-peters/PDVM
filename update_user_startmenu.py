"""
Update User Data für Startmenü
===============================
Trägt Startmenü-GUID in User-Daten ein

Autor: PDVM V2.0
Datum: 01.11.2025
"""

import sqlite3
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_user_startmenu():
    """Aktualisiert User-Daten mit Startmenü-GUID"""
    
    # User-GUID und Startmenü-GUID
    user_guid = "4886ad26-061b-4662-a762-c8c83f36692d"
    startmenu_guid = "menu-startmenu-001"
    
    print("🔧 Update User Startmenü")
    print("=" * 60)
    print(f"User-GUID: {user_guid}")
    print(f"Startmenü-GUID: {startmenu_guid}")
    
    # Verbinde zu auth.db
    conn = sqlite3.connect('Daten/auth.db')
    cursor = conn.cursor()
    
    # Hole aktuelle User-Daten
    cursor.execute('SELECT daten FROM sys_benutzer WHERE uid = ?', (user_guid,))
    row = cursor.fetchone()
    
    if not row:
        print(f"❌ User {user_guid} nicht gefunden!")
        conn.close()
        return False
    
    # Parse JSON
    user_data = json.loads(row[0])
    
    print("\n📋 Aktuelle MEINEAPPS:")
    print(json.dumps(user_data.get('MEINEAPPS', {}), indent=2))
    
    # Update MEINEAPPS.START
    if 'MEINEAPPS' not in user_data:
        user_data['MEINEAPPS'] = {}
    
    user_data['MEINEAPPS']['START'] = startmenu_guid
    
    # Optional: Füge Startmenü auch zu LIST hinzu (für Security-Check)
    if 'LIST' not in user_data['MEINEAPPS']:
        user_data['MEINEAPPS']['LIST'] = []
    
    if startmenu_guid not in user_data['MEINEAPPS']['LIST']:
        user_data['MEINEAPPS']['LIST'].append(startmenu_guid)
    
    print("\n✅ Neue MEINEAPPS:")
    print(json.dumps(user_data['MEINEAPPS'], indent=2))
    
    # Speichere zurück
    user_data_json = json.dumps(user_data, ensure_ascii=False)
    cursor.execute(
        'UPDATE sys_benutzer SET daten = ? WHERE uid = ?',
        (user_data_json, user_guid)
    )
    conn.commit()
    conn.close()
    
    print("\n✅ User-Daten aktualisiert!")
    print("\n🎯 Nächste Schritte:")
    print("   1. python create_test_menu.py (nach v2_main.py Login)")
    print("   2. python v2_main.py")
    print("   3. Menü sollte erscheinen")
    
    return True


if __name__ == "__main__":
    update_user_startmenu()
