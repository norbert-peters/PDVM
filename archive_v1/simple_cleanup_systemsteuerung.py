#!/usr/bin/env python3
"""
EINFACHE BEREINIGUNG: Lösche alle view_guid Daten aus systemsteuerung
======================================================================

Da die aktuelle Struktur stark inkonsistent ist, ist es am einfachsten
alle view-spezifischen Daten zu löschen und neu zu beginnen.

Nur User-Settings werden beibehalten.
"""

import sqlite3
import json

def simple_cleanup():
    """
    Löscht alle view_guid Daten, behält nur User-Settings
    """
    print("🧹 EINFACHE BEREINIGUNG - NUR USER SETTINGS BEHALTEN")
    print("=" * 60)
    
    conn = sqlite3.connect('PdvmManager.db')
    cursor = conn.cursor()
    
    # Backup erstellen
    import datetime
    backup_suffix = datetime.datetime.now().strftime("%Y%m%d_%H%M%S") 
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS systemsteuerung_backup_{backup_suffix} AS 
        SELECT * FROM systemsteuerung WHERE historisch = 0
    ''')
    print(f"✅ Backup erstellt: systemsteuerung_backup_{backup_suffix}")
    
    # Aktuelle Daten lesen
    cursor.execute('SELECT uid, daten FROM systemsteuerung WHERE historisch = 0')
    rows = cursor.fetchall()
    
    # Nur User-Settings extrahieren  
    user_settings = {}
    
    for uid, daten_json in rows:
        if not daten_json or daten_json == '{}':
            continue
            
        try:
            daten = json.loads(daten_json)
        except:
            continue
        
        # Nur User-GUID Keys (nicht View-GUIDs) behalten
        clean_data = {}
        for key, value in daten.items():
            if len(key) == 36 and '-' in key:  # GUID Format
                # Ist es eine User-GUID? (nicht 0d10a0d0, 3E8F, 4886 für Views)
                if not (key.startswith('0d10a0d0') or key.startswith('3E8F') or key.startswith('4886')):
                    clean_data[key] = value
                    print(f"   ✅ User Settings behalten: {key}")
                else:
                    print(f"   ❌ View Daten gelöscht: {key}")
            else:
                print(f"   ⚪ Ignoriert: {key}")
        
        if clean_data:
            user_settings[uid] = clean_data
    
    # Alte Daten als historisch markieren
    cursor.execute('UPDATE systemsteuerung SET historisch = 1 WHERE historisch = 0')
    print("✅ Alte Daten als historisch markiert")
    
    # Nur User Settings neu einfügen
    import time
    current_time = str(time.time())
    
    for uid, settings in user_settings.items():
        cursor.execute('''
            INSERT INTO systemsteuerung (uid, daten, historisch, last_modified, stichtag)
            VALUES (?, ?, 0, ?, '9999365.00000')
        ''', (uid, json.dumps(settings, ensure_ascii=False), current_time))
        print(f"✅ User {uid}: Settings wiederhergestellt")
    
    conn.commit()
    conn.close()
    
    print(f"\n🎉 EINFACHE BEREINIGUNG ABGESCHLOSSEN!")
    print(f"   - Alle View-Daten gelöscht")
    print(f"   - {len(user_settings)} User Settings beibehalten")
    print(f"   - Views werden beim nächsten Start neu initialisiert")

def preview_simple_cleanup():
    """
    Zeigt Vorschau was gelöscht/behalten wird
    """
    print("🔍 VORSCHAU EINFACHE BEREINIGUNG")
    print("=" * 60)
    
    conn = sqlite3.connect('PdvmManager.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT uid, daten FROM systemsteuerung WHERE historisch = 0')
    rows = cursor.fetchall()
    
    will_keep = []
    will_delete = []
    
    for uid, daten_json in rows:
        if not daten_json or daten_json == '{}':
            continue
            
        try:
            daten = json.loads(daten_json)
        except:
            continue
        
        for key, value in daten.items():
            if len(key) == 36 and '-' in key:  # GUID Format
                if not (key.startswith('0d10a0d0') or key.startswith('3E8F') or key.startswith('4886')):
                    will_keep.append(f"{uid}: {key} (User Settings)")
                else:
                    will_delete.append(f"{uid}: {key} (View Data)")
            else:
                will_delete.append(f"{uid}: {key} (Unbekannt)")
    
    print("✅ WIRD BEHALTEN:")
    for item in will_keep:
        print(f"   {item}")
    
    print("\n❌ WIRD GELÖSCHT:")  
    for item in will_delete:
        print(f"   {item}")
    
    conn.close()

if __name__ == "__main__":
    preview_simple_cleanup()
    
    print("\n" + "="*60)
    print("🎯 ZUM BEREINIGEN:")
    print("   simple_cleanup()  # Führt die Bereinigung durch") 
    print("="*60)