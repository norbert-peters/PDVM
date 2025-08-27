# find_persons_with_time_changes.py
"""
Finde Personen mit echten Stichtag-abhängigen Änderungen
========================================================

Durchsucht die Datenbank nach Personen, die zu verschiedenen Stichtagen
unterschiedliche Daten haben (nicht nur leere Werte).
"""

import sys, os, logging
sys.path.append(os.path.dirname(__file__))

# Logger setup  
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def find_persons_with_changes():
    """Findet Personen mit echten Stichtag-abhängigen Änderungen"""
    
    logger.info("🔍 SUCHE PERSONEN MIT STICHTAG-ÄNDERUNGEN")
    
    try:
        # SETUP: ViewManager mit modernem Stichtag
        call_daten = {
            "view_guid": "0d10a0d0-b1a5-4544-b284-e8a09ca979b5",
            "user_guid": "demo_user", 
            "stichtag": 2020001.0,  # Moderner Stichtag
            "view_header": "Person Change Detection",
            "mode": "admin"
        }
        
        logger.info(f"📅 Lade zunächst mit modernem Stichtag {call_daten['stichtag']}")
        
        from pdvm_view_daten_manager import PdvmViewDatenManager
        view_manager = PdvmViewDatenManager(call_daten=call_daten, widget=None)
        
        # Mehr Datensätze laden für bessere Chance
        loaded = view_manager.load_records_data(limit=10)
        logger.info(f"📊 {loaded} Datensätze geladen")
        
        if loaded > 0:
            from pdvm_spalten_manager import PdvmSpaltenManager
            spalten_manager = PdvmSpaltenManager(view_manager.column_control)
            
            # SAMMLE ALLE PERSONEN MIT GEFÜLLTEN DATEN
            rows_modern, headers = spalten_manager.get_widget_ready_table()
            
            persons_with_data = []
            logger.info("📋 MODERNE DATEN (2020):")
            
            for i, row in enumerate(rows_modern):
                familienname = row.get('Familienname', '')
                vorname = row.get('Vorname', '')
                id_guid = row.get('ID', '')
                
                if familienname or vorname:  # Hat Daten
                    persons_with_data.append({
                        'index': i,
                        'id': id_guid,
                        'familienname_modern': familienname,
                        'vorname_modern': vorname,
                        'name_modern': f"{familienname} {vorname}".strip()
                    })
                    logger.info(f"   ✅ Person {i+1}: '{familienname} {vorname}' (ID: {str(id_guid)[:8]})")
            
            logger.info(f"\n🎯 {len(persons_with_data)} Personen mit Namen gefunden")
            
            if len(persons_with_data) > 0:
                # TESTE VERSCHIEDENE STICHTAGE
                test_stichtage = [1950001.0, 1980001.0, 1990001.0, 2000001.0, 2010001.0]
                
                for stichtag in test_stichtage:
                    logger.info(f"\n🧪 TESTE STICHTAG: {stichtag}")
                    
                    # Refresh mit Test-Stichtag
                    refreshed = view_manager.refresh_with_stichtag(stichtag)
                    logger.info(f"📊 {refreshed} Datensätze refresht")
                    
                    # Neue Daten abrufen
                    rows_test, _ = spalten_manager.get_widget_ready_table()
                    
                    # Vergleiche mit ursprünglichen Personen
                    changes_found = False
                    for person_info in persons_with_data:
                        test_row = rows_test[person_info['index']]
                        test_familienname = test_row.get('Familienname', '')
                        test_vorname = test_row.get('Vorname', '')
                        test_name = f"{test_familienname} {test_vorname}".strip()
                        
                        if test_name != person_info['name_modern']:
                            logger.info(f"   🎯 ÄNDERUNG bei {str(person_info['id'])[:8]}:")
                            logger.info(f"      Modern (2020): '{person_info['name_modern']}'")
                            logger.info(f"      Stichtag ({stichtag}): '{test_name or 'LEER'}'")
                            changes_found = True
                    
                    if not changes_found:
                        logger.info(f"   ↔️ Keine Änderungen bei Stichtag {stichtag}")
                
                # DETAILLIERTE ANALYSE FÜR ERSTE PERSON
                if len(persons_with_data) > 0:
                    first_person = persons_with_data[0]
                    logger.info(f"\n🔬 DETAILLIERTE ANALYSE für {str(first_person['id'])[:8]}:")
                    
                    # ColumnControl direkt abfragen
                    row_data = view_manager.column_control.get_row_data(first_person['id'])
                    
                    logger.info("📊 ColumnControl Rohdaten:")
                    for key, value in row_data.items():
                        if 'familienname' in key or 'vorname' in key:
                            logger.info(f"   {key}: '{value}'")
                
                return True
            else:
                logger.warning("⚠️ Keine Personen mit Namen im Datenbestand")
                return False
        else:
            logger.warning("⚠️ Keine Daten geladen")
            return False
            
    except Exception as e:
        logger.error(f"❌ Suche fehlgeschlagen: {e}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = find_persons_with_changes()
    
    print("\n" + "="*60)
    if success:
        print("🔍 PERSON-ÄNDERUNGS-SUCHE ABGESCHLOSSEN")
        print("📋 Zeigt Personen mit echten Stichtag-Unterschieden")
    else:
        print("❌ Keine Änderungen gefunden oder Fehler")
    print("="*60)
