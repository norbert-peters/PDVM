"""Check: Welche Passwort-Hashes sind in auth.db gespeichert?"""
import sqlite3

conn = sqlite3.connect("Daten/auth.db")
cursor = conn.cursor()

cursor.execute("SELECT benutzer, passwort FROM sys_benutzer")

print("\n" + "=" * 70)
print("🔍 PASSWORT-HASHES IN auth.db")
print("=" * 70)

for row in cursor.fetchall():
    email, pw_hash = row
    print(f"\n👤 {email}")
    print(f"   Hash: {pw_hash[:60]}...")
    print(f"   Länge: {len(pw_hash)}")
    
    # Prüfe ob bcrypt-Hash
    if pw_hash.startswith('$2b$') or pw_hash.startswith('$2a$'):
        print(f"   Typ: bcrypt Hash ✅")
    else:
        print(f"   Typ: Kein bcrypt Hash! (Klartext oder anderer Hash)")

conn.close()
print("\n" + "=" * 70)
