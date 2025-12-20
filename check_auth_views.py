#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prüfe Views für auth.db Tabellen
"""
import sqlite3
import json

conn = sqlite3.connect('Daten/pdvm_system.db')
cursor = conn.cursor()

cursor.execute('SELECT uid, daten FROM sys_viewdaten')
rows = cursor.fetchall()

print("=== Views für auth.db Tabellen ===\n")

for row in rows:
    uid = row[0]
    data = json.loads(row[1])
    table = data.get('ROOT', {}).get('TABLE')
    
    if table in ['sys_benutzer', 'sys_mandanten']:
        print(f"View-GUID: {uid}")
        print(f"TABLE: {table}")
        print(f"ROOT-Daten: {data.get('ROOT', {})}")
        print("---\n")

conn.close()
