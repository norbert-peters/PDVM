#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pdvm_central_datenbank import PdvmCentralDatenbank
import json

def analyze_view_config():
    # View-Konfiguration laden
    db = PdvmCentralDatenbank(
        db_name='PdvmManager.db',
        table_name='viewdaten',
        guid='0d10a0d0-b1a5-4544-b284-e8a09ca979b5'
    )

    view_data = db.lesen()
    if view_data:
        print('📊 VIEW-KONFIGURATION:')
        print(json.dumps(view_data, indent=2, ensure_ascii=False))
        
        # Lookup-Felder identifizieren
        if 'metadata' in view_data:
            table_name = view_data['ROOT']['view_table']
            fields = view_data['metadata'][table_name]['felder']
            
            print('\n🔍 LOOKUP-FELDER:')
            lookup_found = False
            for field in fields:
                if field['type'] == 'lookup':
                    lookup_found = True
                    lookup_config = field.get('lookup', 'KEINE LOOKUP-CONFIG')
                    print(f'  - {field["feld"]} ({field["name"]}): {lookup_config}')
            
            if not lookup_found:
                print('  - Keine Lookup-Felder gefunden')
                
            print('\n🗂️ ALLE FELDER MIT TYPEN:')
            for i, field in enumerate(fields):
                field_type = field['type']
                field_name = field['feld']
                display_name = field['name']
                print(f'  {i+1}. {field_name} → "{display_name}" (Type: {field_type})')
    else:
        print('❌ Keine View-Daten gefunden')

if __name__ == "__main__":
    analyze_view_config()
