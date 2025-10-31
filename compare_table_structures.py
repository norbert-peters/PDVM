"""Zeigt Spalten-Struktur der Tabellen"""
import sqlite3

# PdvmManager.db (alt)
print("\n🔍 ALTE STRUKTUR (PdvmManager.db):")
print("="*70)
conn = sqlite3.connect('PdvmManager.db')
cursor = conn.cursor()

for table in ['anwendungsdaten', 'beschreibungen', 'menudaten', 'systemsteuerung']:
    cursor.execute(f"PRAGMA table_info({table})")
    columns = cursor.fetchall()
    print(f"\n{table}:")
    for col in columns:
        print(f"   {col[1]} ({col[2]})")

conn.close()

# Mandanten-DB (neu)
print("\n\n🔍 NEUE STRUKTUR (mandant_001/datenbank.db):")
print("="*70)
conn = sqlite3.connect('Daten/mandant_001/datenbank.db')
cursor = conn.cursor()

for table in ['sys_anwendungsdaten', 'sys_beschreibungen', 'sys_menudaten', 'sys_systemsteuerung']:
    cursor.execute(f"PRAGMA table_info({table})")
    columns = cursor.fetchall()
    print(f"\n{table}:")
    for col in columns:
        print(f"   {col[1]} ({col[2]})")

conn.close()
