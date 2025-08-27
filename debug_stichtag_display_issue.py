# debug_stichtag_display_issue.py
"""
Debug: Warum wird die Tabelle nicht mit refreshten Daten aktualisiert?
================================================================

Untersucht, ob das Problem im PdvmSpaltenManager oder der Widget-Anzeige liegt.
"""

import sys, os, logging
sys.path.append(os.path.dirname(__file__))

# Logger setup
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def debug_stichtag_display_issue():
    """Debuggt das Stichtag-Display-Problem"""
    
    logger.info("🐛 DEBUG: Stichtag-Display-Problem")
    
    try:
        # ViewManager mit initialen Daten
        call_daten = {
            "view_guid": "0d10a0d0-b1a5-4544-b284-e8a09ca979b5",
            "user_guid": "demo_user", 
            "stichtag": 1001.0,
            "view_header": "Debug Test",
            "mode": "admin"
        }
        
        from pdvm_view_daten_manager import PdvmViewDatenManager
        view_manager = PdvmViewDatenManager(call_daten=call_daten, widget=None)
        
        # Daten laden
        loaded = view_manager.load_records_data(limit=2)
        logger.info(f"📊 {loaded} Datensätze initial geladen")
        
        # Erste Anzeige
        from pdvm_spalten_manager import PdvmSpaltenManager
        spalten_manager1 = PdvmSpaltenManager(view_manager.column_control)
        rows1, headers1 = spalten_manager1.get_widget_ready_table()
        
        logger.info("🔍 INITIAL-ZUSTAND:")
        logger.info(f"   Stichtag ViewManager: {view_manager.stichtag}")
        if rows1:
            sample_data = rows1[0]
            logger.info(f"   Erste Zeile Geburtsdatum: '{sample_data.get('Geburtsdatum', 'N/A')}'")
            
            # Direkte ColumnControl-Daten prüfen
            first_guid = view_manager.column_control.row_guids[0]
            direct_row_data = view_manager.column_control.get_row_data(first_guid)
            logger.info(f"   Direkt aus ColumnControl - geburtsdatum_show: '{direct_row_data.get('geburtsdatum_show', 'N/A')}'")
        
        # REFRESH MIT NEUEM STICHTAG
        new_stichtag = 1995365.0
        logger.info(f"\n🔄 REFRESH mit neuem Stichtag: {new_stichtag}")
        
        refreshed = view_manager.refresh_with_stichtag(new_stichtag)
        logger.info(f"📊 {refreshed} Datensätze refresht")
        
        # Nach Refresh - SELBEN SpaltenManager verwenden
        logger.info("\n🔍 NACH REFRESH - SELBER SpaltenManager:")
        rows2, headers2 = spalten_manager1.get_widget_ready_table()  # SELBER Manager!
        
        logger.info(f"   Stichtag ViewManager: {view_manager.stichtag}")
        if rows2:
            sample_data_after = rows2[0]
            logger.info(f"   Erste Zeile Geburtsdatum: '{sample_data_after.get('Geburtsdatum', 'N/A')}'")
            
            # Direkte ColumnControl-Daten nach Refresh prüfen
            direct_row_data_after = view_manager.column_control.get_row_data(first_guid)
            logger.info(f"   Direkt aus ColumnControl - geburtsdatum_show: '{direct_row_data_after.get('geburtsdatum_show', 'N/A')}'")
        
        # Nach Refresh - NEUEN SpaltenManager erstellen
        logger.info("\n🔍 NACH REFRESH - NEUER SpaltenManager:")
        spalten_manager2 = PdvmSpaltenManager(view_manager.column_control)  # NEUER Manager!
        rows3, headers3 = spalten_manager2.get_widget_ready_table()
        
        if rows3:
            sample_data_new_manager = rows3[0]
            logger.info(f"   Erste Zeile Geburtsdatum: '{sample_data_new_manager.get('Geburtsdatum', 'N/A')}'")
        
        # VERGLEICHE
        if rows1 and rows2 and rows3:
            initial = rows1[0].get('Geburtsdatum', '')
            same_manager = rows2[0].get('Geburtsdatum', '')
            new_manager = rows3[0].get('Geburtsdatum', '')
            
            logger.info(f"\n📊 VERGLEICH:")
            logger.info(f"   Initial: '{initial}'")
            logger.info(f"   Nach Refresh (selber Manager): '{same_manager}'")
            logger.info(f"   Nach Refresh (neuer Manager): '{new_manager}'")
            
            if initial == same_manager == new_manager:
                logger.info("✅ Alle Werte gleich - könnte bei gleichem Datensatz normal sein")
            else:
                logger.info("❌ Unterschiedliche Werte - Problem identifiziert!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Debug fehlgeschlagen: {e}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    success = debug_stichtag_display_issue()
    
    print("\n" + "="*60)
    if success:
        print("🔍 DEBUG ABGESCHLOSSEN")
        print("📋 Prüfe die Logs auf Unterschiede zwischen:")
        print("   - Selber SpaltenManager nach Refresh")
        print("   - Neuer SpaltenManager nach Refresh")
    else:
        print("❌ Debug fehlgeschlagen")
    print("="*60)
