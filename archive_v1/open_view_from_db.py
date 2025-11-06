#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SAUBERE VIEW-ÖFFNUNG direkt aus Datenbank

Holt View-Konfiguration aus DB und startet View-Manager in neuem Fenster
"""

import logging
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from pdvm_central_systemsteuerung import get_gcs
from pdvm_central_datenbank import PdvmCentralDatenbank
from pdvm_view_daten_manager import PdvmViewDatenManager

logger = logging.getLogger(__name__)


def create_call_daten_from_db(view_guid: str) -> dict:
    """
    Erstellt call_daten Dictionary direkt aus Datenbank
    
    Args:
        view_guid: GUID der View (z.B. "0d10a0d0-b1a5-4544-b284-e8a09ca979b5")
        
    Returns:
        dict: Vollständiges call_daten Dictionary
    """
    gcs = get_gcs()
    if not gcs:
        logger.error("❌ GCS nicht verfügbar!")
        return None
        
    try:
        # 1. View-Datenbank öffnen
        view_db = PdvmCentralDatenbank(table_name='viewdaten')
        view_db.set_guid(view_guid)
        
        # 2. ROOT-Daten holen
        stichtag = gcs.stichtag  # Aktueller Stichtag aus GCS
        view_table, _ = view_db.get_value('ROOT', 'VIEW_TABLE', stichtag)
        
        if not view_table:
            logger.error(f"❌ VIEW_TABLE nicht gefunden für view_guid={view_guid}")
            return None
            
        logger.info(f"✅ VIEW_TABLE geladen: {view_table}")
        
        # 3. METADATEN holen (enthält controls-Struktur)
        metadaten_gruppe = f"METADATEN"
        table_upper = view_table.upper()  # PERSONDATEN oder FINANZDATEN
        
        metadaten, _ = view_db.get_value(metadaten_gruppe, table_upper, stichtag)
        
        if not metadaten:
            logger.error(f"❌ METADATEN nicht gefunden für {table_upper}")
            return None
            
        # 4. Controls extrahieren - FLEXIBEL für beide Strukturen!
        controls = None
        if 'controls' in metadaten:
            # Neue Struktur: Dictionary mit Control-Configs
            controls = metadaten['controls']
            logger.info(f"✅ {len(controls)} Controls geladen (controls-Dict): {list(controls.keys())}")
        elif 'felder' in metadaten:
            # Alte Struktur: Array von Feld-Configs
            # In Dict umwandeln für Kompatibilität
            felder_list = metadaten['felder']
            controls = {}
            for feld in felder_list:
                feld_name = feld.get('name', feld.get('feld', 'unknown'))
                controls[feld_name] = feld
            logger.info(f"✅ {len(controls)} Controls geladen (felder-Array konvertiert)")
        else:
            logger.error(f"❌ Weder 'controls' noch 'felder' in METADATEN gefunden")
            return None
        
        # 5. Call-Daten Dictionary zusammenbauen
        call_daten = {
            'view_guid': view_guid,
            'user_guid': gcs.user_guid,
            'stichtag': stichtag,
            'view_table': view_table,
            'controls': controls,
            'first_call': True
        }
        
        logger.info(f"✅ call_daten erstellt: view_table={view_table}, {len(controls)} controls")
        return call_daten
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Erstellen von call_daten: {e}")
        import traceback
        traceback.print_exc()
        return None


def open_view_in_window(view_guid: str, window_title: str = "PDVM View"):
    """
    Öffnet View in neuem Fenster
    
    Args:
        view_guid: GUID der View
        window_title: Fenstertitel
    """
    try:
        # 1. call_daten aus DB erstellen
        call_daten = create_call_daten_from_db(view_guid)
        if not call_daten:
            logger.error("❌ Konnte call_daten nicht erstellen!")
            return None
            
        # 2. Neues Fenster erstellen
        window = QMainWindow()
        window.setWindowTitle(window_title)
        window.resize(1200, 800)
        
        # 3. Container Widget
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 4. View-Manager mit call_daten erstellen
        view_manager = PdvmViewDatenManager(
            call_daten=call_daten,
            widget=None,  # Widget wird im Manager erstellt
            parent_app=None
        )
        
        # 5. Kontrolliertes Widget erstellen und in Container einfügen
        view_widget = view_manager.create_controlled_widget(
            parent=container,
            reload_callback=None
        )
        
        if not view_widget:
            logger.error("❌ Konnte View-Widget nicht erstellen!")
            return None
            
        layout.addWidget(view_widget)
        
        # 6. Fenster anzeigen
        window.setCentralWidget(container)
        window.show()
        
        logger.info(f"✅ View-Fenster geöffnet: {window_title}")
        return window
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Öffnen der View: {e}")
        import traceback
        traceback.print_exc()
        return None


# ============================================================================
# BEISPIEL-VERWENDUNG
# ============================================================================

def test_persondaten_view():
    """Öffnet Persondaten-View"""
    PERSONDATEN_VIEW_GUID = "0d10a0d0-b1a5-4544-b284-e8a09ca979b5"
    return open_view_in_window(PERSONDATEN_VIEW_GUID, "Persondaten - Test")


def test_finanzdaten_view():
    """Öffnet Finanzdaten-View"""
    # TODO: Richtige GUID für Finanzdaten eintragen
    FINANZDATEN_VIEW_GUID = "54073c2c-0efa-4979-8900-2bd1c53d5014"
    return open_view_in_window(FINANZDATEN_VIEW_GUID, "Finanzdaten - Test")


if __name__ == '__main__':
    # Logging Setup
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Qt Application
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    # GCS prüfen
    gcs = get_gcs()
    if not gcs:
        print("❌ FEHLER: GCS nicht initialisiert!")
        print("   Bitte erst main.py starten für Login und GCS-Initialisierung")
        sys.exit(1)
    
    # Persondaten-View öffnen
    window = test_persondaten_view()
    
    if window:
        sys.exit(app.exec_())
    else:
        print("❌ Konnte View nicht öffnen!")
        sys.exit(1)
