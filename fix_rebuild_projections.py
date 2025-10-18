#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix-Skript: Erzwingt Neuaufbau der Projektions-Tabellen

Löscht gecachte Projektions-Tabellen und erzwingt Neuberechnung
nach den korrigierten Regeln.
"""

import sys
import logging
from PyQt5.QtWidgets import QApplication

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def rebuild_projections():
    """Erzwingt Neuaufbau der Projektions-Tabellen"""
    app = QApplication(sys.argv)
    
    print("\n" + "="*80)
    print("🔧 FIX: PROJEKTIONS-TABELLEN NEU AUFBAUEN")
    print("="*80)
    
    try:
        from pdvm_central_systemsteuerung import get_gcs
        
        gcs = get_gcs()
        if not gcs:
            print("❌ GCS nicht initialisiert - bitte erst einloggen!")
            return False
        
        print(f"✅ GCS verfügbar für User: {gcs.user_guid}")
        
        # Alle Views aus der Datenbank holen
        print("\n📋 Suche Views in Datenbank...")
        
        # Alle Keys aus der Systemsteuerungs-DB
        all_keys = list(gcs.db.data.get(gcs.user_guid, {}).keys())
        
        # Views sind Keys, die als GUID aussehen und "controls" haben
        view_guids = []
        for key in all_keys:
            # Prüfe ob es eine GUID ist (Format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
            if len(key) == 36 and key.count('-') == 4:
                # Prüfe ob "controls" existiert
                controls, _ = gcs.db.get_value(key, "controls")
                if controls:
                    view_guids.append(key)
        
        print(f"   Gefunden: {len(view_guids)} Views mit Controls")
        
        if not view_guids:
            print("⚠️  Keine Views gefunden!")
            return False
        
        # Zeige Views
        print("\n📊 Vorhandene Views:")
        for i, guid in enumerate(view_guids, 1):
            # Versuche Namen zu holen
            view_name, _ = gcs.db.get_value(guid, "name")
            if not view_name:
                view_name = "Unbenannt"
            print(f"   {i}. {view_name} ({guid})")
        
        # Lösche gecachte Projektions-Tabellen
        print(f"\n🗑️  Lösche gecachte Projektions-Tabellen...")
        cleared_count = len(gcs._projection_tables)
        gcs._projection_tables.clear()
        print(f"   ✅ {cleared_count} gecachte Tabellen gelöscht")
        
        # Baue für jede View neu auf
        print(f"\n🏗️  Baue Projektions-Tabellen neu auf...")
        for i, view_guid in enumerate(view_guids, 1):
            view_name, _ = gcs.db.get_value(view_guid, "name")
            print(f"\n   [{i}/{len(view_guids)}] {view_name or 'Unbenannt'}")
            print(f"   GUID: {view_guid}")
            
            try:
                # Erzwinge Neuaufbau durch Aufruf
                gcs._build_projection_tables(view_guid)
                
                # Zeige Ergebnis
                tables = gcs._projection_tables.get(view_guid, [])
                if tables and len(tables) >= 10:
                    print(f"   ✅ Erfolgreich aufgebaut:")
                    print(f"      [0] View Standard:  {len(tables[0])} Spalten")
                    print(f"      [5] View Expert:    {len(tables[5])} Spalten")
                    
                    # Prüfe Exclusion
                    has_dummy = any('dummy' in col.lower() for col in tables[5])
                    has_row_type = 'row_type' in tables[5]
                    
                    if has_dummy or has_row_type:
                        print(f"      ⚠️  WARNING: dummy oder row_type in Expert!")
                    else:
                        print(f"      ✅ Exclusion korrekt (dummy+row_type ausgeschlossen)")
                else:
                    print(f"   ❌ Aufbau fehlgeschlagen!")
                    
            except Exception as e:
                print(f"   ❌ Fehler: {e}")
        
        print("\n" + "="*80)
        print("✅ NEUAUFBAU ABGESCHLOSSEN")
        print("="*80)
        print("\n💡 Tipp: Starte die Anwendung neu, um die neuen Projektionen zu verwenden.\n")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Fix-Fehler: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("\n🔧 PDVM - Projektions-Tabellen Neuaufbau")
    print("Löscht gecachte Tabellen und erzwingt Neuberechnung.\n")
    
    success = rebuild_projections()
    
    sys.exit(0 if success else 1)
