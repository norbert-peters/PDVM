"""Zeigt alle Tabellen in PdvmManager.db"""
import sqlite3

conn = sqlite3.connect('PdvmManager.db')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()

print("\n🔍 TABELLEN IN PdvmManager.db:")
print("="*50)
for table in tables:
    print(f"   {table[0]}")
print("")

conn.close()
