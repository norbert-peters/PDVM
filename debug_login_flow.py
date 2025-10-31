"""
🔍 DEBUG: Simuliert exakt den Login-Dialog Flow
"""

import sqlite3
import json

try:
    import bcrypt
    BCRYPT_AVAILABLE = True
    print("✅ bcrypt ist verfügbar")
except ImportError:
    BCRYPT_AVAILABLE = False
    print("❌ bcrypt NICHT verfügbar")

def verify_password(password: str, hashed: str) -> bool:
    """
    EXAKT GLEICHE FUNKTION wie in v2_login_dialog.py
    """
    try:
        if BCRYPT_AVAILABLE:
            result = bcrypt.checkpw(
                password.encode('utf-8'), 
                hashed.encode('utf-8')
            )
            print(f"   bcrypt.checkpw() Result: {result}")
            return result
        else:
            # Fallback: Einfacher String-Vergleich (nur für Demo!)
            result = password == hashed
            print(f"   String-Vergleich Result: {result}")
            return result
    except Exception as e:
        print(f"❌ Fehler bei Passwort-Verifikation: {e}")
        return False

# EXAKT GLEICHER ABLAUF wie on_login_clicked()
auth_db_path = r"c:\Users\norbe\OneDrive\Dokumente\MyApplication\Daten\auth.db"

email = "admin@super.de"
password = "admin"

print(f"\n🔍 SIMULIERE LOGIN-DIALOG FLOW:")
print(f"   Email: {email}")
print(f"   Passwort: {password}")
print(f"   DB: {auth_db_path}")

# User-Datenbank öffnen (EINMALIG!)
try:
    conn = sqlite3.connect(auth_db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT * FROM sys_benutzer WHERE benutzer = ?",
        (email,)
    )
    
    user_row = cursor.fetchone()
    conn.close()
    
    if not user_row:
        print(f"❌ Benutzer '{email}' nicht gefunden!")
    else:
        print(f"✅ Benutzer gefunden: {user_row['name']}")
        
        # Hash anzeigen
        stored_hash = user_row['passwort']
        print(f"   Gespeicherter Hash: {stored_hash}")
        print(f"   Hash-Länge: {len(stored_hash)}")
        
        # Passwort-Eingaben debuggen
        print(f"\n🔍 PASSWORT DEBUGGING:")
        print(f"   Eingegebenes Passwort: '{password}'")
        print(f"   Passwort-Länge: {len(password)}")
        print(f"   Passwort repr(): {repr(password)}")
        print(f"   Passwort .encode('utf-8'): {password.encode('utf-8')}")
        
        # Passwort prüfen
        print(f"\n🔍 VERIFIZIERUNG:")
        result = verify_password(password, stored_hash)
        
        if result:
            print(f"\n✅ LOGIN ERFOLGREICH!")
            user_data = {
                'uid': user_row['uid'],
                'email': email,
                'name': user_row['name'],
                'daten': json.loads(user_row['daten'])
            }
            print(f"   Name: {user_data['name']}")
            print(f"   Rollen: {user_data['daten']['PERMISSIONS']['ROLES']}")
        else:
            print(f"\n❌ FALSCHES PASSWORT!")
            
except sqlite3.Error as e:
    print(f"❌ Datenbank-Fehler: {e}")
except Exception as e:
    print(f"❌ Fehler: {e}")
    import traceback
    traceback.print_exc()
