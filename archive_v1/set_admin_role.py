"""
Quick-Fix: User auf Admin setzen
==================================
Setzt mode='admin' für User in benutzerstamm DB
"""

import sqlite3
import json

def set_admin_mode():
    """Setzt Admin-Modus für User"""
    
    # 1. Hole User-GUID aus v2_main.py Startup-Log oder Login
    user_email = input("User Email (z.B. admin@super.de): ").strip()
    
    if not user_email:
        print("❌ Keine Email angegeben")
        return
    
    # 2. Verbinde zu benutzerstamm DB
    db_path = "Daten/mandant_001/benutzerstamm.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 3. Suche User
        cursor.execute("SELECT uid, daten FROM benutzerstamm WHERE uid LIKE ?", (f'%{user_email}%',))
        rows = cursor.fetchall()
        
        if not rows:
            # Versuche über daten JSON
            cursor.execute("SELECT uid, daten FROM benutzerstamm")
            all_rows = cursor.fetchall()
            
            for uid, daten_json in all_rows:
                try:
                    daten = json.loads(daten_json)
                    # Suche in JSON nach email
                    if 'USER' in daten and 'email' in daten['USER']:
                        if daten['USER']['email'] == user_email:
                            rows = [(uid, daten_json)]
                            break
                except:
                    continue
        
        if not rows:
            print(f"❌ User nicht gefunden: {user_email}")
            return
        
        uid, daten_json = rows[0]
        print(f"✅ User gefunden: {uid}")
        
        # 4. Parse JSON
        daten = json.loads(daten_json)
        print(f"📋 Aktuelle Daten: {list(daten.keys())}")
        
        # 5. Setze mode auf admin
        if 'USER' not in daten:
            daten['USER'] = {}
        
        old_mode = daten['USER'].get('mode', 'user')
        daten['USER']['mode'] = 'admin'
        
        print(f"🔧 Ändere mode: '{old_mode}' → 'admin'")
        
        # 6. Speichere zurück
        new_json = json.dumps(daten, ensure_ascii=False)
        cursor.execute("UPDATE benutzerstamm SET daten = ? WHERE uid = ?", (new_json, uid))
        conn.commit()
        conn.close()
        
        print("✅ User auf Admin gesetzt!")
        print("   → Starte v2_main.py neu und logge dich ein")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    set_admin_mode()
