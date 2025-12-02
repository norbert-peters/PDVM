#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Inspiziert Frame-Struktur in pdvm_system.db
"""

import sqlite3
import json
from pathlib import Path

db_path = Path(__file__).parent / 'Daten' / 'pdvm_system.db'
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Erstes Frame laden (nicht Template)
cursor.execute('''
    SELECT uid, name, daten 
    FROM sys_framedaten 
    WHERE uid != '55555555-5555-5555-5555-555555555555'
    LIMIT 1
''')

frame = cursor.fetchone()
if frame:
    guid, name, daten_json = frame
    print(f"📋 Frame: {name}")
    print(f"🆔 GUID: {guid}")
    print()
    
    data = json.loads(daten_json)
    metadaten = data.get('METADATEN', {})
    
    print(f"📊 METADATEN Keys (erste 10):")
    for i, key in enumerate(list(metadaten.keys())[:10]):
        print(f"  [{i+1}] {key}")
    
    # Ersten Key detailliert anzeigen
    if metadaten:
        first_key = list(metadaten.keys())[0]
        first_value = metadaten[first_key]
        print()
        print(f"📌 Beispiel-Key: {first_key}")
        print(f"   Typ: {type(first_value)}")
        if isinstance(first_value, dict):
            print(f"   Sub-Keys: {list(first_value.keys())}")

conn.close()
