# debug_complex_filter.py
# DEBUG-Script für komplexe Filter - prüft genau wo die Daten verloren gehen

import logging

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

def debug_extended_filter_engine():
    """Debug: Prüft den Status der Extended Filter Engine"""
    logger.info("🔍 === DEBUG: Extended Filter Engine Status ===")
    
    try:
        from extended_filter_engine import ExtendedFilterEngine
        
        # Test mit einer bekannten view_guid
        test_view_guid = "test_view_guid_12345"
        
        # Erstelle Extended Filter Engine
        engine = ExtendedFilterEngine()
        
        # Prüfe initial State
        logger.info(f"🔧 Initial Engine State: {bool(engine.extended_conditions)}")
        logger.info(f"📋 Initial Conditions: {engine.extended_conditions}")
        
        # Teste get_active_conditions
        active_conditions = engine.get_active_conditions()
        logger.info(f"🎯 Active Conditions: {active_conditions}")
        
        # Teste reload von persistenten Daten
        logger.info("🔄 Teste reload_extended_conditions...")
        from pdvm_central_systemsteuerung import get_gcs
        gcs = get_gcs()
        
        if gcs:
            logger.info(f"✅ GCS verfügbar: {gcs.user_guid}")
            
            # Prüfe was in APP-DB gespeichert ist
            app_db = gcs._app_db
            stored_data, success = app_db.get_value(test_view_guid, "extended_filter_conditions")
            logger.info(f"📂 Gespeicherte Daten in APP-DB: {stored_data}")
            logger.info(f"📈 Erfolg beim Laden: {success}")
            
            # Teste reload
            loaded_conditions = engine.reload_extended_conditions(test_view_guid)
            logger.info(f"🔧 Nach reload: {loaded_conditions}")
            logger.info(f"📋 Engine Conditions nach reload: {engine.extended_conditions}")
            
        else:
            logger.error("❌ GCS nicht verfügbar - kann persistente Daten nicht prüfen")
            
    except Exception as e:
        logger.error(f"❌ Debug-Fehler: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

def debug_linear_filter_manager():
    """Debug: Prüft LinearFilterExecutionManager"""
    logger.info("🔍 === DEBUG: LinearFilterExecutionManager ===")
    
    try:
        from linear_filter_execution_manager import get_linear_filter_manager
        
        test_view_guid = "test_view_guid_12345"
        manager = get_linear_filter_manager(test_view_guid)
        
        if manager:
            logger.info(f"✅ LinearFilterExecutionManager verfügbar für: {test_view_guid}")
            
            # Teste execute_parameter_dialog_filter mit force_complex
            test_simple_filters = {"familienname_show": "test"}
            test_extended_conditions = {
                "familienname_show": [
                    {
                        'value': 'ma',
                        'operator_type': 'beginnt mit',
                        'logic_operator': 'FIRST',
                        'negation': 'IS'
                    }
                ]
            }
            
            logger.info("🔧 Teste execute_parameter_dialog_filter mit force_complex=True")
            logger.info(f"📋 Simple Filters: {test_simple_filters}")
            logger.info(f"🔍 Extended Conditions: {test_extended_conditions}")
            
            # Das ist der kritische Aufruf - schauen wir ob die Daten durchkommen
            result = manager.execute_parameter_dialog_filter(
                test_simple_filters,
                test_extended_conditions,
                force_complex=True
            )
            
            logger.info(f"📊 Ergebnis: {result}")
            
        else:
            logger.error("❌ LinearFilterExecutionManager nicht verfügbar")
            
    except Exception as e:
        logger.error(f"❌ Debug-Fehler: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

def main():
    """Haupt-Debug-Funktion"""
    logger.info("🚀 === KOMPLEX-FILTER DEBUG SESSION ===")
    
    # Initialisiere zuerst das System
    try:
        from pdvm_central_systemsteuerung import get_gcs
        gcs = get_gcs()
        
        if not gcs:
            logger.error("❌ GCS nicht initialisiert - starte Mini-Setup")
            # Hier könnte man ein Mini-Setup machen, aber das ist für Debug nicht nötig
            return
        
        logger.info(f"✅ System initialisiert: User={gcs.user_guid}")
        
        # Debug Extended Filter Engine
        debug_extended_filter_engine()
        
        # Debug LinearFilterExecutionManager  
        debug_linear_filter_manager()
        
    except Exception as e:
        logger.error(f"❌ Hauptfehler: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    main()