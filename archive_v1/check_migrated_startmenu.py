#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prüft Admin-Startmenü nach Migration

AUTOR: Norbert Peters
DATUM: 02.11.2025
"""

import sqlite3
import json

def check_menu(db_path: str, menu_name: str):
    """Prüft Menü-Struktur"""
    
    print(f"\n{'='*80}")
    print(f"📂 {db_path}")
    print(f"📋 {menu_name}")
    print(f"{'='*80}\n")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Hole Menü
    cursor.execute('SELECT uid, daten FROM sys_menudaten WHERE name = ?', (menu_name,))
    row = cursor.fetchone()
    
    if not row:
        print(f"❌ Menü nicht gefunden!")
        conn.close()
        return
    
    menu_guid, daten_str = row
    data = json.loads(daten_str)
    
    print(f"🔹 MENU_GUID: {menu_guid}")
    print(f"🔹 MENU_NAME: {data.get('MENU_NAME')}")
    print()
    
    # COMMANDS
    commands = data.get('COMMANDS', [])
    print(f"📦 COMMANDS ({len(commands)}):")
    print(f"{'─'*80}")
    for cmd in commands:
        print(f"  GUID: {cmd.get('GUID')}")
        print(f"  NAME: {cmd.get('NAME')}")
        print(f"  HANDLER: {cmd.get('HANDLER')}")
        print(f"  PARAMS: {json.dumps(cmd.get('PARAMS'), ensure_ascii=False)}")
        print()
    
    # VERTIKAL
    vertikal = data.get('VERTIKAL', [])
    print(f"\n🔹 VERTIKAL ({len(vertikal)}):")
    print(f"{'─'*80}")
    for item in vertikal:
        print(f"  {item.get('LABEL')} ({item.get('TYPE')})")
        print(f"    GUID: {item.get('GUID')}")
        print(f"    COMMAND_GUID: {item.get('COMMAND_GUID')}")
        
        # Finde Command
        if item.get('COMMAND_GUID'):
            cmd = next((c for c in commands if c.get('GUID') == item.get('COMMAND_GUID')), None)
            if cmd:
                print(f"    → {cmd.get('HANDLER')}({json.dumps(cmd.get('PARAMS'), ensure_ascii=False)})")
            else:
                print(f"    ❌ Command nicht gefunden!")
        print()
    
    # GRUND
    grund = data.get('GRUND', [])
    print(f"\n🔹 GRUND ({len(grund)}):")
    print(f"{'─'*80}")
    for item in grund:
        indent = "    " if item.get('PARENT_GUID') else "  "
        print(f"{indent}{item.get('LABEL')} ({item.get('TYPE')})")
        
        if item.get('COMMAND_GUID'):
            cmd = next((c for c in commands if c.get('GUID') == item.get('COMMAND_GUID')), None)
            if cmd:
                print(f"{indent}  → {cmd.get('HANDLER')}({json.dumps(cmd.get('PARAMS'), ensure_ascii=False)})")
            else:
                print(f"{indent}  ❌ Command nicht gefunden!")
    
    conn.close()

if __name__ == '__main__':
    check_menu('Daten/mandant_001/datenbank.db', 'Admin-Startmenü')
