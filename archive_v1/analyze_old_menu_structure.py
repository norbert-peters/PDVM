#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Analysiert alte Menüstruktur aus sys_menues
"""

import sqlite3
import json

def analyze_old_menus():
    """Analysiert alle Menüs in der alten Struktur"""
    
    conn = sqlite3.connect('Daten/mandant_001/datenbank.db')
    cursor = conn.cursor()
    
    # Hole alle Menüs aus daten_backup (alte Struktur)
    cursor.execute('SELECT uid, daten_backup FROM sys_menudaten WHERE daten_backup IS NOT NULL')
    menus = cursor.fetchall()
    
    print("=" * 80)
    print("ALTE MENÜSTRUKTUR ANALYSE")
    print("=" * 80)
    print(f"\n📊 Gefundene Menüs: {len(menus)}\n")
    
    for guid, data_json in menus:
        data = json.loads(data_json)
        
        print(f"\n{'=' * 80}")
        print(f"🎯 Menü: {guid}")
        print(f"{'=' * 80}")
        
        # Zeige Struktur
        if 'PD_vertikal' in data:
            print("\n📂 VERTIKAL:")
            print(json.dumps(data['PD_vertikal'], indent=2, ensure_ascii=False)[:500])
        
        if 'PD_grund' in data:
            print("\n📂 GRUND:")
            grund = data['PD_grund']
            
            # Prüfe auf Template-Einbettung
            if '!guid!' in grund:
                template_guid = grund['!guid!']
                print(f"\n✨ TEMPLATE-EINBETTUNG: {template_guid}")
                
                # Hole Template-Menü
                cursor.execute('SELECT daten_backup FROM sys_menudaten WHERE uid = ?', (template_guid,))
                template_row = cursor.fetchone()
                if template_row:
                    template_data = json.loads(template_row[0])
                    print("\n📋 Template-Inhalt:")
                    if 'PD_grund' in template_data:
                        print(json.dumps(template_data['PD_grund'], indent=2, ensure_ascii=False)[:800])
            else:
                print(json.dumps(grund, indent=2, ensure_ascii=False)[:800])
        
        if 'PD_kommando' in data:
            print("\n📂 KOMMANDOS:")
            kommandos = data['PD_kommando']
            print(f"   Anzahl: {len(kommandos)}")
            # Zeige ALLE Kommandos
            for i, (path, cmd) in enumerate(kommandos.items()):
                print(f"\n   [{i+1}] Pfad: {path}")
                if isinstance(cmd, dict):
                    print(f"       Typ: {cmd.get('Type', 'N/A')}")
                    handler = cmd.get('handler', 'N/A')
                    if len(handler) > 100:
                        print(f"       Handler: {handler[:100]}...")
                    else:
                        print(f"       Handler: {handler}")
        
        print("\n" + "=" * 80)
        print()
    
    conn.close()

if __name__ == '__main__':
    analyze_old_menus()
