#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prüft ob Commands korrekt zu Handlers gemappt wurden
"""

import sqlite3
import json

conn = sqlite3.connect('Daten/mandant_001/datenbank.db')
cursor = conn.cursor()

cursor.execute('SELECT daten FROM sys_menudaten WHERE uid = ?', ('5ca6674e-b9ce-4581-9756-64e742883f80',))
data = json.loads(cursor.fetchone()[0])

print("=" * 80)
print("ADMIN-STARTMENÜ COMMANDS")
print("=" * 80)

for cmd in data['COMMANDS']:
    print(f"\n📌 {cmd['NAME']}")
    print(f"   Handler: {cmd['HANDLER']}")
    print(f"   Params: {cmd['PARAMS']}")

conn.close()
