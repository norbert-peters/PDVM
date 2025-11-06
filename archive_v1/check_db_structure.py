#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prüft Datenbank-Struktur
"""

import sqlite3

conn = sqlite3.connect('Daten/mandant_001/datenbank.db')
cursor = conn.cursor()

# Zeige alle Tabellen
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]

print("=" * 80)
print("TABELLEN IN MANDANT_001")
print("=" * 80)
for table in tables:
    print(f"\n📋 Tabelle: {table}")
    
    # Zeige Spalten
    cursor.execute(f"PRAGMA table_info({table})")
    columns = cursor.fetchall()
    print("   Spalten:")
    for col in columns:
        print(f"      - {col[1]} ({col[2]})")

conn.close()
