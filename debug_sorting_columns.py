#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Debug-Script für Sortier-Projektions-Tabellen
Analysiert warum keine Spalten zum Verschieben angezeigt werden
"""

import logging
import sys

# Logging Setup
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def debug_sorting_projections():
    """Analysiert die Sortier-Projektions-Tabellen"""
    print("🔍 DEBUG: Sortier-Projektions-Tabellen")
    print("=" * 50)
    
    try:
        # GCS initialisieren (Simple Version für Test)
        from create_simple_gcs import initialize_simple_gcs, get_simple_gcs
        try:
            initialize_simple_gcs("test-user-guid")
            logger.info("✅ Simple GCS initialisiert")
        except RuntimeError as e:
            if "bereits initialisiert" in str(e):
                logger.info("♻️ Simple GCS bereits initialisiert")
            else:
                raise
        
        # Oder zentrale GCS verwenden falls verfügbar
        try:
            from pdvm_central_systemsteuerung import get_gcs
            gcs = get_gcs()
            if gcs:
                logger.info("✅ Zentrale GCS gefunden")
            else:
                logger.info("⚠️ Keine zentrale GCS - verwende Simple GCS")
                gcs = get_simple_gcs()
        except Exception as e:
            logger.info(f"⚠️ Zentrale GCS Fehler: {e} - verwende Simple GCS")
            gcs = get_simple_gcs()
        
        if not gcs:
            print("❌ Keine GCS verfügbar!")
            return
        
        print(f"📋 GCS Status: {type(gcs).__name__}")
        print(f"👤 User GUID: {getattr(gcs, 'user_guid', 'N/A')}")
        print(f"⚙️ Expert Mode: {getattr(gcs, 'expert_mode', 'N/A')}")
        
        # Prüfe Projektions-Tabellen
        if hasattr(gcs, '_projection_tables'):
            print(f"📊 Projektions-Tabellen verfügbar: {len(gcs._projection_tables)} Views")
            
            for view_guid, projections in gcs._projection_tables.items():
                print(f"\n🎯 View: {view_guid}")
                for proj_type, columns in projections.items():
                    print(f"  - {proj_type}: {len(columns)} Spalten")
                    if proj_type.startswith('sort_'):
                        print(f"    └── {columns[:5]}..." if len(columns) > 5 else f"    └── {columns}")
        else:
            print("❌ Keine _projection_tables in GCS!")
        
        # Teste get_projection Methode
        if hasattr(gcs, 'get_projection'):
            print("\n🧪 Teste get_projection Methoden:")
            
            test_projections = ['sort_standard', 'sort_expert', 'view_standard', 'view_expert']
            for proj_key in test_projections:
                try:
                    result = gcs.get_projection(proj_key)
                    print(f"  - {proj_key}: {len(result) if result else 0} Spalten")
                    if result and len(result) > 0:
                        print(f"    └── Erste 3: {result[:3]}")
                except Exception as e:
                    print(f"  - {proj_key}: FEHLER - {e}")
        else:
            print("❌ Keine get_projection Methode in GCS!")
        
        # Mock Controls-Config testen
        print("\n🎮 Mock Controls-Config Test:")
        mock_controls = {
            'familienname': {'name': 'Familienname', 'original': 'Familienname'},
            'vorname': {'name': 'Vorname', 'original': 'Vorname'},
            'geburtsdatum': {'name': 'Geburtsdatum', 'original': 'Geburtsdatum'},
            'email': {'name': 'E-Mail', 'original': 'E-Mail'},
            'telefon': {'name': 'Telefon', 'original': 'Telefon'}
        }
        
        print(f"📋 Mock Controls: {len(mock_controls)} Spalten")
        for key, config in mock_controls.items():
            print(f"  - {key}: {config['original']}")
        
    except Exception as e:
        logger.error(f"❌ Debug Fehler: {e}")
        import traceback
        traceback.print_exc()

def debug_fallback_columns():
    """Testet die Fallback-Spalten aus dem Dialog"""
    print("\n🆘 DEBUG: Emergency Fallback Spalten")
    print("=" * 50)
    
    fallback_columns = [
        ('familienname', 'Familienname'),
        ('vorname', 'Vorname'),
        ('geburtsdatum', 'Geburtsdatum'),
        ('email', 'E-Mail'),
        ('telefon', 'Telefon'),
        ('plz', 'PLZ'),
        ('ort', 'Ort'),
        ('strasse', 'Straße'),
        ('land', 'Land'),
        ('notizen', 'Notizen')
    ]
    
    print(f"📋 Fallback Spalten: {len(fallback_columns)} verfügbar")
    for column_key, display_name in fallback_columns:
        print(f"  - {column_key}: {display_name}")

def main():
    """Hauptfunktion"""
    debug_sorting_projections()
    debug_fallback_columns()
    
    print("\n" + "=" * 50)
    print("💡 LÖSUNGSANSÄTZE:")
    print("1. Prüfe ob GCS _projection_tables initialisiert sind")
    print("2. Teste get_projection Methode für sort_standard/expert")
    print("3. Emergency Fallback sollte Standard-Spalten anzeigen")
    print("4. Falls immer noch leer: controls_config von view_dialog prüfen")

if __name__ == "__main__":
    main()