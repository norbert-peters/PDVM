"""Zeigt User-Datenstruktur aus auth.db"""
import sqlite3
import json
from pathlib import Path

auth_db = Path(__file__).parent / "Daten" / "auth.db"

conn = sqlite3.connect(auth_db)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("SELECT uid, email, name, daten FROM sys_benutzer WHERE email = 'admin@super.de'")
row = cursor.fetchone()
conn.close()

if row:
    print(f"UID: {row['uid']}")
    print(f"Email: {row['email']}")
    print(f"Name: {row['name']}")
    print("\nDaten (JSON):")
    daten = json.loads(row['daten'])
    print(json.dumps(daten, indent=2, ensure_ascii=False))
