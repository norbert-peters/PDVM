#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Spalten-Problem Analyse ohne Unicode
====================================
"""

import sys
import os
import sqlite3

def analyze_database():
    """Analysiert Datenbank nach Spalten-Konfiguration"""
    print("\nDATENBANK-ANALYSE")
    print("=" * 40)
    
    db_files = ['PdvmManager.db', 'meine_datenbank.db']
    
    for db_file in db_files:
        if not os.path.exists(db_file):
            continue
            
        print(f"\nAnalysiere {db_file}")
        
        try:
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            # Alle Tabellen
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [t[0] for t in cursor.fetchall()]
            print(f"  Tabellen gefunden: {len(tables)}")
            
            # Suche spalten-relevante Tabellen
            relevant_tables = []
            for table in tables:
                if any(keyword in table.lower() for keyword in ['column', 'view', 'config', 'order']):
                    relevant_tables.append(table)
            
            if relevant_tables:
                print(f"  Spalten-relevante Tabellen: {relevant_tables}")
                
                for table in relevant_tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table};")
                    count = cursor.fetchone()[0]
                    print(f"    {table}: {count} Eintraege")
                    
                    if count > 0:
                        # Zeige Beispiel-Daten
                        cursor.execute(f"SELECT * FROM {table} LIMIT 1;")
                        sample = cursor.fetchone()
                        if sample:
                            print(f"      Beispiel: {str(sample)[:100]}...")
            
            # Suche nach JSON-Konfiguration
            print(f"  Pruefe {len(tables)} Tabellen auf JSON-Spalten...")
            json_found = False
            
            for table in tables:
                try:
                    cursor.execute(f"PRAGMA table_info({table});")
                    columns = cursor.fetchall()
                    
                    # Suche JSON/Config Spalten
                    for col_info in columns:
                        col_name = col_info[1].lower()
                        if 'json' in col_name or 'config' in col_name or 'data' in col_name:
                            print(f"    JSON-Spalte gefunden: {table}.{col_info[1]}")
                            
                            # Pruefe Content
                            cursor.execute(f"SELECT {col_info[1]} FROM {table} WHERE {col_info[1]} IS NOT NULL LIMIT 1;")
                            result = cursor.fetchone()
                            if result and result[0]:
                                content = str(result[0])
                                if any(keyword in content.lower() for keyword in ['column', 'order', 'visible']):
                                    print(f"      SPALTEN-KONFIGURATION GEFUNDEN!")
                                    print(f"      Content: {content[:150]}...")
                                    json_found = True
                except:
                    pass
            
            if not json_found:
                print("  Keine Spalten-Konfiguration in JSON gefunden")
            
            conn.close()
            
        except Exception as e:
            print(f"  FEHLER: {e}")

def test_pyqt_signals():
    """Testet PyQt Signal-Verhalten"""
    print("\nPYQT SIGNAL-TEST")
    print("=" * 40)
    
    try:
        from PyQt5.QtWidgets import QApplication, QTableWidget
        from PyQt5.QtCore import Qt
        
        app = QApplication.instance() or QApplication(sys.argv)
        
        # Test-Tabelle
        table = QTableWidget(2, 3)
        table.setHorizontalHeaderLabels(['Col1', 'Col2', 'Col3'])
        
        header = table.horizontalHeader()
        header.setSectionsMovable(True)
        
        print(f"Tabelle erstellt: {table.columnCount()} Spalten")
        print(f"Header movable: {header.sectionsMovable()}")
        
        # Signal-Test
        signal_received = []
        
        def on_section_moved(logical, old_visual, new_visual):
            signal_received.append((logical, old_visual, new_visual))
            print(f"Signal: logical={logical}, old={old_visual}, new={new_visual}")
        
        header.sectionMoved.connect(on_section_moved)
        print("Signal verbunden")
        
        # Simuliere Bewegung
        print("Simuliere Spalten-Verschiebung...")
        original_order = [header.logicalIndex(i) for i in range(header.count())]
        print(f"Original Order: {original_order}")
        
        # Verschiebe Spalte 0 zu Position 1
        header.moveSection(0, 1)
        app.processEvents()
        
        new_order = [header.logicalIndex(i) for i in range(header.count())]
        print(f"Neue Order: {new_order}")
        
        if signal_received:
            print(f"SUCCESS: {len(signal_received)} Signale empfangen")
            for sig in signal_received:
                print(f"  Signal: {sig}")
        else:
            print("PROBLEM: Keine Signale empfangen!")
        
        return len(signal_received) > 0
        
    except ImportError:
        print("PyQt5 nicht verfügbar")
        return False
    except Exception as e:
        print(f"FEHLER: {e}")
        return False

def main():
    print("SPALTEN-PROBLEM RUNTIME-ANALYSE")
    print("=" * 50)
    
    # 1. Datenbank analysieren
    analyze_database()
    
    # 2. PyQt Signale testen
    signals_working = test_pyqt_signals()
    
    # 3. Zusammenfassung
    print("\nZUSAMMENFASSUNG")
    print("=" * 40)
    print(f"PyQt Signale funktionieren: {'JA' if signals_working else 'NEIN'}")
    
    # 4. Mögliche Probleme identifizieren
    print("\nMOEGLICHE PROBLEME:")
    print("- Spalten-Konfiguration wird nicht persistiert")
    print("- Signal-Handler wird nicht korrekt aufgerufen")  
    print("- Tabellen-Update nach Drag&Drop fehlt")
    print("- Level2-Architektur wird bei Neustart nicht geladen")

if __name__ == "__main__":
    main()
