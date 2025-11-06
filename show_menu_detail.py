"""Zeigt detaillierte Struktur eines Menüs"""
import sqlite3
import json

conn = sqlite3.connect('Daten/mandant_001/datenbank.db')
cursor = conn.cursor()
cursor.execute('SELECT daten FROM sys_menudaten WHERE uid = ?', ('113c6a2c-af9a-4022-929b-6544799e8954',))
row = cursor.fetchone()

if row and row[0]:
    daten = json.loads(row[0])
    print(json.dumps(daten, indent=2, ensure_ascii=False))
    
conn.close()
