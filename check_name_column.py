# -*- coding: utf-8 -*-
"""Prüft ob 'name' Spalte in Tabellen existiert"""
import sqlite3

db_path = "Daten/datenbank.db"

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Alle Tabellen auflisten
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
all_tables = cursor.fetchall()
print("📚 Alle Tabellen in datenbank.db:")
for t in all_tables:
    print(f"  - {t[0]}")

# Erste paar Tabellen im Detail prüfen
tables = [t[0] for t in all_tables[:5]]

for table in tables:
    try:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        print(f"\n📋 Tabelle '{table}':")
        if columns:
            for col in columns:
                print(f"   - {col[1]} ({col[2]})")
        else:
            print("   (keine Spalten gefunden)")
    except Exception as e:
        print(f"   ❌ Fehler: {e}")

conn.close()
