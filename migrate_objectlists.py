#!/usr/bin/env python3
# migrate_objectlists.py
# -*- coding: utf-8 -*-

import sqlite3
import json
from datetime import datetime

def migrate_table(db_path, table_name):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 1. Bestehende Spalten abfragen
    cursor.execute(f"PRAGMA table_info({table_name});")
    existing_cols = [row[1] for row in cursor.fetchall()]

    # 2. Neue Spalten mit Typ-Definitionen
    new_columns = {
        "name":            "TEXT",
        "daten":           "TEXT NOT NULL DEFAULT '[]'",
        "historisch":      "INTEGER NOT NULL DEFAULT 0",
        "last_modified":   "TEXT NOT NULL DEFAULT ''",
        "source_hash":     "TEXT DEFAULT ''",
        "stichtag":        "TEXT NOT NULL DEFAULT '9999-12-31T23:59:59'"
    }

    # 3. Fehlende Spalten hinzufügen
    for col, dtype in new_columns.items():
        if col not in existing_cols:
            cursor.execute(
                f"ALTER TABLE {table_name} ADD COLUMN {col} {dtype};"
            )
            print(f"[{table_name}] Spalte '{col}' hinzugefügt.")

    # 4. Speziell für 'menudaten': 'bezeichnung' → 'name' kopieren
    if table_name == "menudaten":
        if "bezeichnung" in existing_cols:
            cursor.execute(
                f"UPDATE {table_name} "
                f"SET name = bezeichnung "
                f"WHERE name IS NULL OR name = '';"
            )
            print("[menudaten] 'bezeichnung' → 'name' kopiert.")
        else:
            print("[menudaten] WARNUNG: Spalte 'bezeichnung' nicht gefunden.")

    # 5. 'last_modified' initialisieren (ISO-Format) für alle bisherigen Datensätze
    now_iso = datetime.now().isoformat()
    cursor.execute(
        f"UPDATE {table_name} "
        f"SET last_modified = ? "
        f"WHERE last_modified = '';",
        (now_iso,)
    )
    print(f"[{table_name}] 'last_modified' auf '{now_iso}' gesetzt.")

    # 6. 'stichtag' bleibt auf Default '9999-12-31T23:59:59' (offenes Datum)

    conn.commit()
    conn.close()
    print(f"[{table_name}] Migration abgeschlossen.\n")


def main():
    db_path = input("Pfad zur SQLite-Datenbank: ").strip()
    print("Gib die zu migrierenden Tabellennamen ein (eine pro Zeile). Leer lassen zum Beenden.")
    while True:
        tbl = input("Tabellenname: ").strip()
        if not tbl:
            break
        try:
            migrate_table(db_path, tbl)
        except Exception as e:
            print(f"[{tbl}] Fehler: {e}")

if __name__ == "__main__":
    main()
