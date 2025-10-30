"""
Verifizierungs-Script für V2.0 Auth-Datenbank

Zeigt alle Daten aus auth.db in lesbarer Form
"""

import sqlite3
import json

def verify_auth_database():
    """Zeigt Inhalte der auth.db"""
    
    print("\n" + "=" * 70)
    print("🔍 VERIFIKATION: Daten/auth.db")
    print("=" * 70)
    
    conn = sqlite3.connect("Daten/auth.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # sys_benutzer
    print("\n📋 TABELLE: sys_benutzer")
    print("-" * 70)
    cursor.execute("SELECT * FROM sys_benutzer")
    
    for row in cursor.fetchall():
        print(f"\n👤 User: {row['benutzer']}")
        print(f"   Name: {row['name']}")
        print(f"   UID: {row['uid']}")
        print(f"   Passwort-Hash: {row['passwort'][:50]}...")
        print(f"   Erstellt: {row['created_at']}")
        
        # Daten parsen und schön anzeigen
        daten = json.loads(row['daten'])
        print(f"   Rollen: {daten['PERMISSIONS']['ROLES']}")
        print(f"   Security-Profiles: {daten['PERMISSIONS']['SEC_PROFILES']}")
        print(f"   Mandanten: {daten['MANDANTEN']['LIST']}")
        print(f"   Default-Mandant: {daten['MANDANTEN']['DEFAULT']}")
    
    # sys_mandanten
    print("\n" + "=" * 70)
    print("📋 TABELLE: sys_mandanten")
    print("-" * 70)
    cursor.execute("SELECT * FROM sys_mandanten")
    
    for row in cursor.fetchall():
        print(f"\n🏢 Mandant: {row['uid']}")
        print(f"   Name: {row['name']}")
        print(f"   Erstellt: {row['created_at']}")
        
        # Daten parsen und schön anzeigen
        daten = json.loads(row['daten'])
        print(f"   DB-Name: {daten['ROOT']['DB_NAME']}")
        print(f"   Bezeichnung: {daten['ROOT']['BEZEICHNUNG']}")
        print(f"   Status: {daten['METADATEN']['STATUS']}")
        print(f"   Country: {daten['METADATEN']['COUNTRY']}")
    
    conn.close()
    
    print("\n" + "=" * 70)
    print("✅ VERIFIKATION ABGESCHLOSSEN")
    print("=" * 70 + "\n")

if __name__ == '__main__':
    verify_auth_database()
