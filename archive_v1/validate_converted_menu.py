#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validiert konvertiertes Menü

AUTOR: Norbert Peters  
DATUM: 02.11.2025
"""

import sqlite3
import json

def show_menu_details(db_path: str, menu_guid: str):
    """Zeigt Details eines konvertierten Menüs"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('SELECT daten FROM sys_menudaten WHERE uid = ?', (menu_guid,))
    row = cursor.fetchone()
    
    if not row:
        print(f"❌ Menü nicht gefunden: {menu_guid}")
        return
    
    data = json.loads(row[0])
    
    print("=" * 80)
    print(f"MENÜ: {data['NAME']}")
    print("=" * 80)
    print(f"GUID: {data['MENU_GUID']}")
    print(f"GRUND Items: {len(data['GRUND'])}")
    print(f"VERTIKAL Items: {len(data['VERTIKAL'])}")
    print(f"ZUSATZ Items: {len(data['ZUSATZ'])}")
    print(f"COMMANDS: {len(data['COMMANDS'])}")
    
    print("\n" + "─" * 80)
    print("GRUND-STRUKTUR:")
    print("─" * 80)
    for item in data['GRUND']:
        indent = "  " if item['PARENT_GUID'] is None else "    "
        type_marker = "├─" if item['TYPE'] == 'ITEM' else "│ "
        print(f"{indent}{type_marker} {item['LABEL']} (Type: {item['TYPE']}, Command: {item['COMMAND_GUID'] is not None})")
    
    print("\n" + "─" * 80)
    print("COMMANDS:")
    print("─" * 80)
    for cmd in data['COMMANDS']:
        params = json.loads(cmd['PARAMS'])
        print(f"  • {cmd['LABEL']}")
        print(f"    Handler: {cmd['HANDLER']}")
        print(f"    Params: {params}")
    
    conn.close()

def main():
    """Hauptfunktion"""
    print("\n🔍 MENÜ-VALIDIERUNG\n")
    
    # Admin-Startmenü prüfen
    show_menu_details(
        'Daten/mandant_001/datenbank.db',
        '5ca6674e-b9ce-4581-9756-64e742883f80'  # Admin-Startmenü
    )
    
    print("\n\n")
    
    # Admin-Testmenü prüfen (größtes Menü)
    show_menu_details(
        'Daten/mandant_001/datenbank.db',
        '113c6a2c-af9a-4022-929b-6544799e8954'  # Admin-Testmenü
    )

if __name__ == '__main__':
    main()
