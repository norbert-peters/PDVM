"""Findet Menu-Tabellen in Mandanten-DB"""
import sqlite3

conn = sqlite3.connect('Daten/mandant_001/datenbank.db')
cursor = conn.cursor()

# Alle Tabellen mit "menu" im Namen
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%menu%'")
tables = cursor.fetchall()

print('=== MENU-TABELLEN ===')
for table in tables:
    print(f'  {table[0]}')

# V2 Menu-Tabellen
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'v2_%'")
v2_tables = cursor.fetchall()

print('\n=== V2 TABELLEN ===')
for table in v2_tables:
    print(f'  {table[0]}')

conn.close()
