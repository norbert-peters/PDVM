#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Diagnose-Skript für Spalten-Problem
=====================================

Analysiert die Spalten-Architektur, um zu verstehen warum:
1. Spalten bei Neustart zurückgesetzt werden
2. Drag & Drop nur die ersten zwei Spalten tauscht
3. Der "Spalten testen" Button nicht richtig funktioniert
"""

import sys
import os
import sqlite3
import json
import logging
from pathlib import Path

# Setup für Logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('spalten_diagnose.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def diagnose_database():
    """Analysiert die Datenbank auf Spalten-Konfiguration"""
    logger.info("🔍 SCHRITT 1: Datenbank-Analyse")
    logger.info("=" * 50)
    
    db_files = [
        'PdvmManager.db',
        'meine_datenbank.db'
    ]
    
    for db_file in db_files:
        if os.path.exists(db_file):
            logger.info(f"📁 Analysiere {db_file}")
            
            try:
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                
                # Tabellen finden
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                logger.info(f"   Tabellen: {[t[0] for t in tables]}")
                
                # Nach Spalten-relevanten Tabellen suchen
                for table_name, in tables:
                    if any(keyword in table_name.lower() for keyword in ['column', 'spalte', 'view', 'order']):
                        logger.info(f"   🎯 Interessante Tabelle: {table_name}")
                        
                        # Struktur anzeigen
                        cursor.execute(f"PRAGMA table_info({table_name});")
                        columns = cursor.fetchall()
                        logger.info(f"      Struktur: {[col[1] for col in columns]}")
                        
                        # Beispieldaten
                        cursor.execute(f"SELECT * FROM {table_name} LIMIT 3;")
                        sample_data = cursor.fetchall()
                        if sample_data:
                            logger.info(f"      Beispiel: {sample_data[0]}")
                
                conn.close()
                
            except Exception as e:
                logger.error(f"❌ Fehler bei {db_file}: {e}")
        else:
            logger.warning(f"⚠️ {db_file} nicht gefunden")

def diagnose_code_architecture():
    """Analysiert die Code-Architektur"""
    logger.info("\n🔍 SCHRITT 2: Code-Architektur-Analyse")
    logger.info("=" * 50)
    
    widget_file = 'pdvm_modern_view_widget.py'
    
    if not os.path.exists(widget_file):
        logger.error(f"❌ {widget_file} nicht gefunden!")
        return
    
    with open(widget_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Kritische Funktionen suchen
    critical_functions = [
        '_apply_or_create_level2',
        '_on_column_moved',
        '_update_level2_order_from_drag_drop',
        '_save_user_column_order_v2',
        '_load_user_column_order_v2',
        'test_column_order_functionality'
    ]
    
    for func_name in critical_functions:
        if f"def {func_name}" in content:
            logger.info(f"✅ Funktion gefunden: {func_name}")
        else:
            logger.error(f"❌ Funktion FEHLT: {func_name}")
    
    # Signal-Verbindungen suchen
    signal_patterns = [
        'sectionMoved.connect',
        '_on_column_moved',
        'header.sectionMoved'
    ]
    
    logger.info("\n🔗 Signal-Verbindungen:")
    for pattern in signal_patterns:
        count = content.count(pattern)
        logger.info(f"   {pattern}: {count}x gefunden")

def test_data_persistence():
    """Testet ob Spalten-Daten gespeichert werden"""
    logger.info("\n🔍 SCHRITT 3: Persistenz-Test")
    logger.info("=" * 50)
    
    # Nach Dateien suchen, die Spalten-Konfiguration enthalten könnten
    possible_config_files = [
        '*.json',
        '*.cfg',
        '*.ini',
        'config/*',
        'settings/*'
    ]
    
    # Aktuelle Directory scannen
    current_dir = Path('.')
    config_files = []
    
    for pattern in possible_config_files:
        if '*' in pattern:
            if '/' in pattern:
                # Subdirectory pattern
                subdir, file_pattern = pattern.split('/')
                if os.path.exists(subdir):
                    subdir_path = Path(subdir)
                    config_files.extend(list(subdir_path.glob(file_pattern)))
            else:
                # Current directory pattern
                config_files.extend(list(current_dir.glob(pattern)))
        else:
            # Exact file
            if os.path.exists(pattern):
                config_files.append(Path(pattern))
    
    logger.info(f"📂 Gefundene Config-Dateien: {len(config_files)}")
    
    for config_file in config_files[:10]:  # Limit für Übersichtlichkeit
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Nach Spalten-relevanten Inhalten suchen
            if any(keyword in content.lower() for keyword in ['column', 'spalte', 'order', 'visible']):
                logger.info(f"🎯 {config_file.name}: Enthält spalten-relevante Daten")
                
                # Wenn JSON, versuche zu parsen
                if config_file.suffix == '.json':
                    try:
                        data = json.loads(content)
                        if isinstance(data, dict):
                            keys = list(data.keys())
                            logger.info(f"   JSON-Keys: {keys[:5]}{'...' if len(keys) > 5 else ''}")
                    except:
                        pass
                        
        except Exception as e:
            logger.debug(f"   Fehler beim Lesen von {config_file}: {e}")

def test_import_functionality():
    """Testet ob die Module korrekt importiert werden können"""
    logger.info("\n🔍 SCHRITT 4: Import-Test")
    logger.info("=" * 50)
    
    try:
        # Versuche pdvm_modern_view_widget zu importieren
        sys.path.insert(0, '.')
        
        import pdvm_modern_view_widget
        logger.info("✅ pdvm_modern_view_widget erfolgreich importiert")
        
        # Prüfe kritische Klassen/Funktionen
        if hasattr(pdvm_modern_view_widget, 'PdvmModernViewWidget'):
            widget_class = pdvm_modern_view_widget.PdvmModernViewWidget
            logger.info("✅ PdvmModernViewWidget Klasse gefunden")
            
            # Prüfe kritische Methoden
            critical_methods = [
                '_apply_or_create_level2',
                '_on_column_moved',
                'test_column_order_functionality'
            ]
            
            for method_name in critical_methods:
                if hasattr(widget_class, method_name):
                    logger.info(f"✅ Methode {method_name} vorhanden")
                else:
                    logger.error(f"❌ Methode {method_name} FEHLT")
        
    except ImportError as e:
        logger.error(f"❌ Import-Fehler: {e}")
    except Exception as e:
        logger.error(f"❌ Unerwarteter Fehler: {e}")

def main():
    """Hauptdiagnose-Funktion"""
    logger.info("🏥 SPALTEN-DIAGNOSE GESTARTET")
    logger.info("="*70)
    
    # Alle Diagnose-Schritte ausführen
    diagnose_database()
    diagnose_code_architecture()
    test_data_persistence()
    test_import_functionality()
    
    logger.info("\n🏥 SPALTEN-DIAGNOSE ABGESCHLOSSEN")
    logger.info("="*70)
    logger.info("📋 Prüfe die Logdatei 'spalten_diagnose.log' für Details")

if __name__ == "__main__":
    main()
