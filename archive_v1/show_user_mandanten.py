"""Zeigt User-Mandanten-Liste"""
import sqlite3
import json

conn = sqlite3.connect('Daten/auth.db')
cursor = conn.cursor()

cursor.execute('SELECT benutzer, daten FROM sys_benutzer WHERE benutzer = ?', ('admin@super.de',))
row = cursor.fetchone()

daten = json.loads(row[1])
print('\n📋 User-Mandanten:')
print(json.dumps(daten['MANDANTEN'], indent=2, ensure_ascii=False))

conn.close()
