#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prüft Frame-Editor Konfiguration"""

import sqlite3
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def check_frame_editor():
    """Prüft welche View der Frame-Editor verwendet"""
    conn = sqlite3.connect('Daten/pdvm_system.db')
    cursor = conn.cursor()
    
    # Frame-Daten holen
    frame_guid = '44d2e239-d429-41ab-b080-e7fcd4b6e8a8'
    cursor.execute('SELECT uid, daten FROM sys_framedaten WHERE uid = ?', (frame_guid,))
    row = cursor.fetchone()
    
    if not row:
        logger.error(f"❌ Frame {frame_guid} nicht gefunden!")
        return
    
    frame_data = json.loads(row[1])
    root = frame_data.get('ROOT', {})
    
    view_guid = root.get('VIEW_GUID')
    dialog_guid = root.get('DIALOG_GUID')
    table = root.get('TABLE')
    
    logger.info("📋 FRAME-EDITOR KONFIGURATION:")
    logger.info(f"   Frame-GUID: {frame_guid}")
    logger.info(f"   TABLE: {table}")
    logger.info(f"   VIEW_GUID: {view_guid}")
    logger.info(f"   DIALOG_GUID: {dialog_guid}")
    
    # View-Daten holen
    if view_guid:
        cursor.execute('SELECT uid, name, daten FROM sys_viewdaten WHERE uid = ?', (view_guid,))
        view_row = cursor.fetchone()
        
        if view_row:
            view_data = json.loads(view_row[2])
            view_root = view_data.get('ROOT', {})
            
            logger.info(f"\n📊 VIEW KONFIGURATION:")
            logger.info(f"   View-Name: {view_row[1]}")
            logger.info(f"   View-TABLE: {view_root.get('TABLE')}")
            logger.info(f"   NO_DATA: {view_root.get('NO_DATA')}")
            
            # Controls prüfen
            gruppen = [k for k in view_data.keys() if k != 'ROOT']
            logger.info(f"   Control-Gruppen: {gruppen}")
            
            if gruppen:
                for gruppe in gruppen:
                    controls = view_data.get(gruppe, {})
                    logger.info(f"\n   📂 Gruppe '{gruppe}': {len(controls)} Controls")
            
            # Ist NO_DATA gesetzt?
            if view_root.get('NO_DATA'):
                logger.warning("\n⚠️ PROBLEM GEFUNDEN:")
                logger.warning("   NO_DATA=True bedeutet: Keine Daten aus JSON werden projiziert!")
                logger.warning("   Nur DB-Spalten (uid, name, dummy) werden angezeigt")
                logger.warning("\n💡 LÖSUNG:")
                logger.warning("   Setze NO_DATA=False in dieser View, damit Controls verwendet werden")
    
    conn.close()

if __name__ == '__main__':
    check_frame_editor()
