#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Validiert migrierte Menüs

Prüft:
- VERTIKAL Items vorhanden
- TEMPLATE Items korrekt
- Commands verknüpft
"""

import sqlite3
import json

def validate_menu(db_path: str, menu_guid: str, menu_name: str):
    """Validiert ein migriertes Menü"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('SELECT daten FROM sys_menudaten WHERE uid = ?', (menu_guid,))
    row = cursor.fetchone()
    
    if not row:
        print(f"❌ {menu_name}: Nicht gefunden!")
        return
    
    data = json.loads(row[0])
    
    print(f"\n{'─'*80}")
    print(f"📋 {menu_name}")
    print(f"{'─'*80}")
    print(f"GUID: {data['MENU_GUID']}")
    print(f"NAME: {data['MENU_NAME']}")
    print(f"VERTIKAL: {len(data['VERTIKAL'])} Items")
    print(f"GRUND: {len(data['GRUND'])} Items")
    print(f"ZUSATZ: {len(data['ZUSATZ'])} Items")
    print(f"COMMANDS: {len(data['COMMANDS'])} Items")
    
    # VERTIKAL-Struktur
    if data['VERTIKAL']:
        print(f"\n📊 VERTIKAL-Menü:")
        for item in data['VERTIKAL']:
            print(f"  • {item['LABEL']} (Type: {item['TYPE']}, Command: {item['COMMAND_GUID'] is not None})")
    
    # GRUND-Struktur (nur Top-Level + Templates)
    print(f"\n📊 GRUND-Menü:")
    for item in data['GRUND']:
        if item['PARENT_GUID'] is None:
            if item['TYPE'] == 'TEMPLATE':
                print(f"  🔗 TEMPLATE → {item['TEMPLATE_GUID']}")
            else:
                # Zähle Children
                children_count = sum(1 for i in data['GRUND'] if i['PARENT_GUID'] == item['GUID'])
                print(f"  • {item['LABEL']} ({children_count} Children, Command: {item['COMMAND_GUID'] is not None})")
    
    # Commands
    if data['COMMANDS']:
        print(f"\n📊 COMMANDS:")
        for cmd in data['COMMANDS'][:5]:  # Nur erste 5 anzeigen
            print(f"  • {cmd['LABEL']}: {cmd['COMMAND'][:50]}...")
        if len(data['COMMANDS']) > 5:
            print(f"  ... und {len(data['COMMANDS']) - 5} weitere")
    
    conn.close()

def main():
    """Hauptfunktion"""
    print("=" * 80)
    print("🔍 MENÜ-VALIDIERUNG")
    print("=" * 80)
    
    # Admin-Startmenü (hat VERTIKAL!)
    validate_menu(
        'Daten/mandant_001/datenbank.db',
        '5ca6674e-b9ce-4581-9756-64e742883f80',
        'Admin-Startmenü'
    )
    
    # Admin-Benutzermenü (hat TEMPLATE!)
    validate_menu(
        'Daten/mandant_001/datenbank.db',
        'e1e77039-d1b5-46ff-b12b-cced0ae0da7c',
        'Admin-Benutzermenü'
    )
    
    # Basis-Menü (ist selbst TEMPLATE)
    validate_menu(
        'Daten/mandant_001/datenbank.db',
        '1a653694-3132-48d9-bc3e-a512962ae8e6',
        'Basis-Menü'
    )

if __name__ == '__main__':
    main()
