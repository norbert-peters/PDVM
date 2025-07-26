#!/usr/bin/env python3
"""Analysiere die View-Konfiguration und Datenstruktur"""

from pdvm_central_datenbank import PdvmCentralDatenbank

def analyze_view_config():
    """Analysiere die View-Konfiguration im Detail"""
    
    print("🔍 ANALYSE: View-Konfiguration und Datenstruktur")
    print("=" * 60)
    
    # 1. View-Konfiguration aus viewdaten laden
    print("\n1️⃣ VIEW-KONFIGURATION LADEN:")
    view_db = PdvmCentralDatenbank(
        db_name='PdvmManager.db',
        table_name='viewdaten',
        guid='0d10a0d0-b1a5-4544-b284-e8a09ca979b5'
    )
    
    view_config = view_db.lesen()
    if view_config:
        print(f"✅ View-Konfiguration geladen")
        
        # ROOT-Bereich
        root = view_config.get('ROOT', {})
        print(f"📊 ROOT: {root}")
        
        # Metadata-Bereich
        metadata = view_config.get('metadata', {})
        print(f"📊 Metadata keys: {list(metadata.keys())}")
        
        if 'persondaten' in metadata:
            felder = metadata['persondaten'].get('felder', [])
            print(f"📊 Anzahl Felder: {len(felder)}")
            
            for i, feld in enumerate(felder):
                print(f"\n📌 Feld {i+1}:")
                print(f"   feld: {feld.get('feld', 'N/A')}")
                print(f"   name: {feld.get('name', 'N/A')}")
                print(f"   gruppe: {feld.get('gruppe', 'N/A')}")
                print(f"   type: {feld.get('type', 'N/A')}")
        else:
            print("❌ Keine 'persondaten' in metadata gefunden")
            print(f"   Verfügbare Keys: {list(metadata.keys())}")
    else:
        print("❌ Keine View-Konfiguration gefunden")
    
    # 2. Beispiel-Datensatz analysieren
    print("\n2️⃣ BEISPIEL-DATENSATZ ANALYSIEREN:")
    person_db = PdvmCentralDatenbank('PdvmManager.db', 'persondaten', '58c0acaa-fd40-4444-b516-c162f17a39b8')
    person_data = person_db.lesen()
    
    if person_data:
        print(f"✅ Person-Daten geladen")
        print(f"📊 Gruppen: {list(person_data.keys())}")
        
        # PERSDATEN-Gruppe im Detail
        if 'PERSDATEN' in person_data:
            persdaten = person_data['PERSDATEN']
            print(f"\n📁 PERSDATEN-Gruppe:")
            for field, value in persdaten.items():
                print(f"   {field}: {value}")
        else:
            print("❌ Keine PERSDATEN-Gruppe gefunden")
    else:
        print("❌ Keine Person-Daten gefunden")
    
    # 3. Test get_value_view mit korrekter Konfiguration
    print("\n3️⃣ GET_VALUE_VIEW TEST:")
    test_db = PdvmCentralDatenbank('PdvmManager.db')
    
    # Korrekte View-Config mit Namen
    corrected_view_config = {
        'ROOT': {
            'view_table': 'persondaten'
        },
        'metadata': {
            'persondaten': {
                'felder': [
                    {
                        'feld': 'FAMILIENNAME',
                        'name': 'Familienname',  # DISPLAY NAME!
                        'gruppe': 'PERSDATEN',
                        'type': 'string'
                    },
                    {
                        'feld': 'VORNAME', 
                        'name': 'Vorname',  # DISPLAY NAME!
                        'gruppe': 'PERSDATEN',
                        'type': 'string'
                    },
                    {
                        'feld': 'GEBURTSDATUM',
                        'name': 'Geburtsdatum',  # DISPLAY NAME!
                        'gruppe': 'PERSDATEN',
                        'type': 'date'
                    },
                    {
                        'feld': 'ANREDE',
                        'name': 'Anrede',  # DISPLAY NAME!
                        'gruppe': 'PERSDATEN',
                        'type': 'string'
                    }
                ]
            }
        }
    }
    
    result = test_db.get_value_view(corrected_view_config)
    
    print(f"📊 Anzahl Datensätze: {len(result)}")
    if result:
        first_record = result[0]
        print(f"\n📋 Erster Datensatz:")
        for key, value in first_record.items():
            print(f"   {key}: {value}")
            
    return view_config, corrected_view_config

if __name__ == "__main__":
    analyze_view_config()
