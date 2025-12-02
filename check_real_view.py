#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prüft echte View mit Daten (nicht NO_DATA)"""

import sqlite3
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def check_real_view():
    """Prüft View mit echten Daten"""
    conn = sqlite3.connect('Daten/pdvm_system.db')
    cursor = conn.cursor()
    
    # Finde Views ohne NO_DATA Flag
    cursor.execute('SELECT uid, name, daten FROM sys_viewdaten')
    rows = cursor.fetchall()
    
    logger.info(f"📊 Alle Views ({len(rows)}):\n")
    
    for row in rows:
        uid = row[0]
        name = row[1]
        data = json.loads(row[2])
        root = data.get('ROOT', {})
        no_data = root.get('NO_DATA', False)
        table = root.get('TABLE', 'N/A')
        
        logger.info(f"📋 {name[:30]:30} | Table: {table:20} | NO_DATA: {no_data}")
        
        # Wenn keine NO_DATA View, zeige Controls
        if not no_data:
            logger.info(f"\n✅ Verwende View: {name} ({uid})")
            logger.info(f"   Tabelle: {table}")
            
            # Zeige Gruppen
            gruppen = [k for k in data.keys() if k != 'ROOT']
            logger.info(f"   Gruppen: {gruppen}")
            
            # Zeige erste Controls aus erster Gruppe
            if gruppen:
                erste_gruppe = gruppen[0]
                controls = data.get(erste_gruppe, {})
                logger.info(f"\n   📂 Gruppe '{erste_gruppe}': {len(controls)} Controls")
                
                for i, (guid, control) in enumerate(list(controls.items())[:3]):
                    if isinstance(control, dict):
                        logger.info(f"\n   Control {i+1}:")
                        logger.info(f"     GUID: {guid}")
                        logger.info(f"     feld: {control.get('feld', 'N/A')}")
                        logger.info(f"     label: {control.get('label', 'N/A')}")
                        logger.info(f"     type: {control.get('type', 'N/A')}")
                        logger.info(f"     gruppe: {control.get('gruppe', 'N/A')}")
            break  # Nur erste View ohne NO_DATA zeigen
    
    conn.close()

if __name__ == '__main__':
    check_real_view()
