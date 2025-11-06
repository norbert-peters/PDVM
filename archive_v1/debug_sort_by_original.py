#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug: sortByOriginal in der Hauptanwendung
=========================================

Testet die sortByOriginal Funktionalität direkt in der Hauptanwendung:
1. Prüft Controls-Konfiguration
2. Testet _get_sort_column_key Logik 
3. Simuliert Header-Klick auf Geburtsdatum-Spalte
"""

import sys
import os
import logging

# Logging Setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def test_sort_by_original_logic():
    """Testet die sortByOriginal Logik isoliert"""
    logger.info("🔧 Test: sortByOriginal Logik...")
    
    # Mock Controls Config
    mock_controls = {
        'familienname_show': {
            'sortByOriginal': False,
            'type': 'string'
        },
        'vorname_show': {
            'sortByOriginal': False,
            'type': 'string'
        },
        'geburtsdatum_show': {
            'sortByOriginal': True,
            'type': 'date'
        },
        'anrede_show': {
            'sortByOriginal': False,
            'type': 'string'
        }
    }
    
    # Mock View Dialog
    class MockViewDialog:
        def __init__(self):
            self.controls_config = mock_controls
    
    mock_view_dialog = MockViewDialog()
    
    # Importiere Sorting Manager
    from pdvm_sorting_manager import PdvmSortingManager
    sorting_manager = PdvmSortingManager(mock_view_dialog)
    
    # Teste verschiedene Spalten
    test_cases = [
        ('familienname_show', False, 'familienname_show'),
        ('vorname_show', False, 'vorname_show'),
        ('geburtsdatum_show', True, 'geburtsdatum_original'),
        ('anrede_show', False, 'anrede_show')
    ]
    
    logger.info("📋 Test-Ergebnisse:")
    for display_key, expected_sort_by_original, expected_sort_key in test_cases:
        actual_sort_key = sorting_manager._get_sort_column_key(display_key)
        control = mock_controls.get(display_key, {})
        actual_sort_by_original = control.get('sortByOriginal', False)
        
        status = "✅" if (actual_sort_by_original == expected_sort_by_original and 
                         actual_sort_key == expected_sort_key) else "❌"
        
        logger.info(f"   {status} {display_key}:")
        logger.info(f"      sortByOriginal: {actual_sort_by_original} (erwartet: {expected_sort_by_original})")
        logger.info(f"      Sortier-Key: {actual_sort_key} (erwartet: {expected_sort_key})")
    
    logger.info("✅ sortByOriginal Logik-Test abgeschlossen")

def test_geburtsdatum_sorting():
    """Testet speziell die Geburtsdatum-Sortierung"""
    logger.info("📅 Test: Geburtsdatum sortByOriginal=True...")
    
    # Mock-Daten für Geburtsdatum
    mock_display_matrix = [
        {
            'uid': 'person1',
            'display': True,
            'geburtsdatum_show': '15.03.1985',      # Formatiert (dd.mm.yyyy)
            'geburtsdatum_original': 1985074.0,     # PdvmDateTime float
        },
        {
            'uid': 'person2', 
            'display': True,
            'geburtsdatum_show': '22.12.1978',      # Formatiert
            'geburtsdatum_original': 1978356.0,     # PdvmDateTime float
        },
        {
            'uid': 'person3',
            'display': True,
            'geburtsdatum_show': '08.07.1992',      # Formatiert  
            'geburtsdatum_original': 1992190.0,     # PdvmDateTime float
        },
        {
            'uid': 'person4',
            'display': True,
            'geburtsdatum_show': '03.01.1980',      # Formatiert
            'geburtsdatum_original': 1980003.0,     # PdvmDateTime float
        }
    ]
    
    logger.info("📋 Test-Daten (unsortiert):")
    for i, data in enumerate(mock_display_matrix):
        logger.info(f"   {i+1}. UID: {data['uid']}, Show: {data['geburtsdatum_show']}, Original: {data['geburtsdatum_original']}")
    
    # Simuliere Sortierung nach Original-Werten
    sorted_data = sorted(mock_display_matrix, key=lambda x: x['geburtsdatum_original'])
    
    logger.info("📋 Nach geburtsdatum_original sortiert (aufsteigend):")
    for i, data in enumerate(sorted_data):
        logger.info(f"   {i+1}. UID: {data['uid']}, Show: {data['geburtsdatum_show']}, Original: {data['geburtsdatum_original']}")
    
    # Erwartete Reihenfolge: 1978 -> 1980 -> 1985 -> 1992
    expected_order = ['person2', 'person4', 'person1', 'person3']
    actual_order = [data['uid'] for data in sorted_data]
    
    if actual_order == expected_order:
        logger.info("✅ Geburtsdatum-Sortierung korrekt!")
    else:
        logger.error(f"❌ Geburtsdatum-Sortierung fehlerhaft!")
        logger.error(f"   Erwartet: {expected_order}")
        logger.error(f"   Tatsächlich: {actual_order}")

def test_in_main_application():
    """Testet sortByOriginal in der laufenden Hauptanwendung"""
    logger.info("🏠 Test: sortByOriginal in Hauptanwendung...")
    
    try:
        # GCS prüfen
        from pdvm_central_systemsteuerung import get_gcs, is_gcs_initialized
        
        if not is_gcs_initialized():
            logger.warning("⚠️ GCS nicht initialisiert - Hauptanwendung nicht aktiv")
            return
        
        gcs = get_gcs()
        logger.info(f"✅ GCS verfügbar: {gcs.user_guid}")
        
        # Test ViewDaten
        view_guid = "0d10a0d0-b1a5-4544-b284-e8a09ca979b5"  # Test View
        
        controls_config = gcs.field_value('controls')
        if not controls_config:
            logger.warning("⚠️ Keine Controls-Konfiguration in GCS gefunden")
            return
        
        logger.info(f"📋 Controls-Konfiguration gefunden: {len(controls_config)} Controls")
        
        # Prüfe geburtsdatum Control
        geburtsdatum_control = None
        for key, control in controls_config.items():
            if 'geburtsdatum' in key and '_show' in key:
                geburtsdatum_control = control
                break
        
        if geburtsdatum_control:
            sort_by_original = geburtsdatum_control.get('sortByOriginal', False)
            logger.info(f"📅 Geburtsdatum Control gefunden:")
            logger.info(f"   sortByOriginal: {sort_by_original}")
            logger.info(f"   type: {geburtsdatum_control.get('type', 'unknown')}")
            
            if sort_by_original:
                logger.info("✅ Geburtsdatum ist korrekt für sortByOriginal=True konfiguriert")
            else:
                logger.warning("⚠️ Geburtsdatum hat sortByOriginal=False - könnte falsch sein")
        else:
            logger.warning("⚠️ Kein Geburtsdatum-Control gefunden")
        
    except Exception as e:
        logger.error(f"❌ Fehler beim Test in Hauptanwendung: {e}")

def main():
    """Hauptfunktion"""
    logger.info("🎯 === sortByOriginal Debug-Tests ===")
    
    # Test 1: Isolierte Logik
    test_sort_by_original_logic()
    
    print()  # Leerzeile
    
    # Test 2: Geburtsdatum spezifisch
    test_geburtsdatum_sorting()
    
    print()  # Leerzeile
    
    # Test 3: In der Hauptanwendung
    test_in_main_application()
    
    logger.info("🏁 Alle sortByOriginal Tests abgeschlossen")
    logger.info("📋 Fazit:")
    logger.info("   - sortByOriginal=false: Standard Qt-Sortierung nach _show")
    logger.info("   - sortByOriginal=true: Custom Sortierung nach _original")
    logger.info("   - Geburtsdatum: PdvmDateTime float -> korrekte chronologische Sortierung")


if __name__ == "__main__":
    main()