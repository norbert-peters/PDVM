#!/usr/bin/env python3
"""
🔧 Debug-Script für PdvmViewDialog
Testet die Matrix-Erstellung und Table-Display isoliert
"""

import sys
import os
import logging
from pathlib import Path

# QApplication importieren
from PyQt5.QtWidgets import QApplication

# Logging konfigurieren
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('debug_view_dialog.log', mode='w', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

# Arbeitsverzeichnis setzen
os.chdir(Path(__file__).parent)

# QApplication erstellen
app = QApplication(sys.argv)

try:
    from pdvm_view_dialog import PdvmViewDialog
    from pdvm_central_systemsteuerung import initialize_gcs, get_gcs
    
    logger.info("🔧 DEBUG: Teste PdvmViewDialog isoliert...")
    
    # 1. GCS initialisieren
    try:
        logger.info("🔧 Initialisiere GCS...")
        # Dummy User-Daten für Debug
        user_guid = "debug-user-12345"
        user_data = {"name": "Debug User", "role": "admin"}
        initialize_gcs(user_guid, user_data)
        gcs = get_gcs()
        logger.info(f"✅ GCS verfügbar: {type(gcs).__name__}")
        logger.info(f"📅 Current Stichtag: {gcs.st_inst.PdvmDateTime}")
        
        # 🚀 AKTUELLEN STICHTAG SETZEN direkt über st_inst!
        from pdvm_datetime import Pdvm_DateTime
        current_dt = Pdvm_DateTime("DEU")
        gcs.st_inst.PdvmDateTime = current_dt.PdvmDateTime
        logger.info(f"📅 Neuer aktueller Stichtag über st_inst: {gcs.st_inst.PdvmDateTime}")
        
    except Exception as e:
        logger.error(f"❌ GCS Problem: {e}")
        sys.exit(1)
    
    # 2. View Dialog erstellen mit korrekten call_daten
    try:
        logger.info("🔧 Erstelle PdvmViewDialog...")
        call_daten = {
            'view_guid': 'test-view-guid',
            'title': 'Debug Test View',
            'first_call': True  # Auch first_call für Debug setzen
        }
        view_dialog = PdvmViewDialog(parent=None, call_daten=call_daten)
        logger.info("✅ PdvmViewDialog erstellt")
        
        # 3. Matrix prüfen
        logger.info(f"📊 Display Matrix: {len(view_dialog.display_matrix) if hasattr(view_dialog, 'display_matrix') else 'NICHT VERFÜGBAR'}")
        if hasattr(view_dialog, 'display_matrix') and view_dialog.display_matrix:
            logger.info(f"🔍 Erste Zeile: {view_dialog.display_matrix[0]}")
            logger.info(f"🔍 Matrix Schlüssel: {list(view_dialog.display_matrix[0].keys()) if view_dialog.display_matrix else 'LEER'}")
            
            # Sichtbare Spalten prüfen
            columns = list(view_dialog.display_matrix[0].keys()) if view_dialog.display_matrix else []
            visible_columns = [col for col in columns if col.endswith('_show') or col == 'uid_show']
            logger.info(f"🔍 Sichtbare Spalten: {visible_columns}")
        
        # 4. View Config prüfen
        if hasattr(view_dialog, 'view_config'):
            logger.info(f"🔧 View Config Keys: {list(view_dialog.view_config.keys())}")
            if 'spalten' in view_dialog.view_config:
                logger.info(f"🔧 Anzahl Spalten-Configs: {len(view_dialog.view_config['spalten'])}")
        
        # 5. Optimized Instances prüfen
        if hasattr(view_dialog, 'optimized_instances'):
            logger.info(f"🚀 Optimized Instances: {len(view_dialog.optimized_instances)}")
        
        # 6. Raw Records prüfen
        if hasattr(view_dialog, 'raw_records'):
            logger.info(f"📋 Raw Records: {len(view_dialog.raw_records)}")
            
        # 7. Display Widget prüfen
        try:
            display_widget = view_dialog.get_display_widget()
            logger.info(f"🖼️ Display Widget erstellt: {type(display_widget).__name__}")
        except Exception as e:
            logger.error(f"❌ Display Widget Fehler: {e}")
            
    except Exception as e:
        logger.error(f"❌ View Dialog Fehler: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    logger.info("🏁 Debug abgeschlossen - siehe debug_view_dialog.log für Details")
    
except Exception as e:
    logger.error(f"❌ Import/Setup Fehler: {e}")
    import traceback
    logger.error(traceback.format_exc())
