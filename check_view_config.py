from pdvm_central_datenbank import PdvmCentralDatenbank

# Viewdaten für die Test-View laden
view_db = PdvmCentralDatenbank(
    db_name='PdvmManager.db',
    table_name='viewdaten',
    guid='0d10a0d0-b1a5-4544-b284-e8a09ca979b5'  # Test-View für persondaten
)

view_data = view_db.lesen()
print('📊 View-Konfiguration:')

if view_data and 'metadata' in view_data:
    table_name = view_data['ROOT']['view_table']
    fields = view_data['metadata'][table_name]['felder']
    
    print(f'🗃️ Tabelle: {table_name}')
    print(f'📋 Anzahl Felder: {len(fields)}')
    
    for i, field in enumerate(fields):
        print(f'📌 Feld {i+1}: {field}')
        if field.get('feld') == 'ANREDE':
            print('🎯 *** ANREDE-Feld gefunden ***')
            if 'lookup' in field:
                print(f'    Lookup-Config: {field["lookup"]}')
            else:
                print('    ❌ KEIN LOOKUP KONFIGURIERT!')
else:
    print('❌ Keine View-Konfiguration gefunden')
