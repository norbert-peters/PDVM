#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prüft Struktur von sys_viewdaten nach Migration"""

import sqlite3
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def check_view_structure():
    """Prüft sys_viewdaten Struktur"""
    conn = sqlite3.connect('Daten/pdvm_system.db')
    cursor = conn.cursor()
    
    # View laden
    view_guid = '641da120-6d2d-41c9-8f88-ccfc32431a55'
    cursor.execute('SELECT uid, daten FROM sys_viewdaten WHERE uid = ?', (view_guid,))
    row = cursor.fetchone()
    
    if not row:
        logger.error(f"❌ View {view_guid} nicht gefunden!")
        return
    
    data = json.loads(row[1])
    
    logger.info(f"📋 View-GUID: {view_guid}")
    logger.info(f"📂 Gruppen: {list(data.keys())}")
    logger.info(f"\n🔍 ROOT-Gruppe:")
    root = data.get('ROOT', {})
    for key, value in root.items():
        logger.info(f"  {key}: {value}")
    
    # Prüfe ob METADATEN oder direkte Gruppen
    if 'METADATEN' in data:
        logger.warning("⚠️ ALTE STRUKTUR: Hat noch METADATEN-Gruppe!")
    else:
        logger.info("✅ NEUE STRUKTUR: Keine METADATEN (lineare Gruppen)")
    
    # Zeige weitere Gruppen
    for gruppe_name in data.keys():
        if gruppe_name != 'ROOT':
            felder = data[gruppe_name]
            logger.info(f"\n📂 Gruppe '{gruppe_name}': {len(felder)} Felder")
            for feld_guid, feld_data in list(felder.items())[:3]:
                if isinstance(feld_data, dict):
                    feld_label = feld_data.get('label', 'N/A')
                    feld_feld = feld_data.get('feld', 'N/A')
                    feld_type = feld_data.get('type', 'N/A')
                    logger.info(f"  - GUID: {feld_guid[:8]}...")
                    logger.info(f"    Label: {feld_label}")
                    logger.info(f"    Feld: {feld_feld}")
                    logger.info(f"    Type: {feld_type}")
                else:
                    logger.info(f"  - {feld_guid[:8]}... {feld_data}")
    
    conn.close()

if __name__ == '__main__':
    check_view_structure()
