"""Zeigt komplette User-Daten-Struktur"""
import sqlite3
import json

conn = sqlite3.connect("Daten/auth.db")
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("SELECT * FROM sys_benutzer WHERE benutzer = 'admin@super.de'")
row = cursor.fetchone()

daten = json.loads(row['daten'])

print("=" * 70)
print("📋 KOMPLETTE USER-DATEN STRUKTUR (admin@super.de)")
print("=" * 70)
print(json.dumps(daten, indent=2, ensure_ascii=False))
print("=" * 70)

conn.close()
