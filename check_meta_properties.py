"""
Prüfe META-Eigenschaften im Startmenü
"""
import sqlite3

db_path = r"Daten\mandant_001\datenbank.db"
menu_uid = "5ca6674e-b9ce-4581-9756-64e742883f80"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("🔍 META-Eigenschaften im Startmenü:")
print("=" * 60)

query = """
SELECT field_name, wert 
FROM sys_menudaten 
WHERE uid=? AND gruppe='META' 
ORDER BY field_name
"""

cursor.execute(query, (menu_uid,))
rows = cursor.fetchall()

if rows:
    for feld, wert in rows:
        print(f"  {feld}: {wert}")
else:
    print("  ❌ Keine META-Felder gefunden!")

print("\n🔍 Alle Gruppen im Startmenü:")
print("=" * 60)

query2 = """
SELECT DISTINCT gruppe 
FROM sys_menudaten 
WHERE uid=? 
ORDER BY gruppe
"""

cursor.execute(query2, (menu_uid,))
gruppen = cursor.fetchall()

for (gruppe,) in gruppen:
    print(f"  - {gruppe}")
    
    # Felder in dieser Gruppe
    query3 = "SELECT field_name, wert FROM sys_menudaten WHERE uid=? AND gruppe=? LIMIT 5"
    cursor.execute(query3, (menu_uid, gruppe))
    felder = cursor.fetchall()
    for feld, wert in felder:
        wert_str = str(wert)[:50] + "..." if len(str(wert)) > 50 else str(wert)
        print(f"      {feld}: {wert_str}")

conn.close()
