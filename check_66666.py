import sqlite3
conn = sqlite3.connect('Daten/pdvm_system.db')
cursor = conn.cursor()

# Prüfe Tabelle
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sys_tabellen_dictionary'")
table = cursor.fetchone()

if table:
    print(f"✅ Tabelle 'sys_tabellen_dictionary' existiert")
    
    # Lade Dictionary
    cursor.execute("SELECT uid, name FROM sys_tabellen_dictionary WHERE uid='66666666-6666-6666-6666-666666666666'")
    row = cursor.fetchone()
    
    if row:
        print(f"✅ Dictionary gefunden: {row[1]} ({row[0]})")
    else:
        print(f"❌ Dictionary 66666... NICHT gefunden")
else:
    print(f"❌ Tabelle 'sys_tabellen_dictionary' existiert NICHT")

conn.close()
