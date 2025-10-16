#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DIREKTE DATENBANK BEREINIGUNG - OHNE LOGIN

Entfernt Controls-Daten direkt aus der Datenbank ohne GCS-Initialisierung.
Beim nächsten View-Start werden die Controls neu generiert.
"""

import sqlite3
import json
import os
from pathlib import Path

# Datenbank-Pfad
DB_PATH = Path(__file__).parent / "datenbank.db"

def list_views_with_controls():
    """Liste alle Views mit Controls-Daten"""
    if not DB_PATH.exists():
        print(f"❌ Datenbank nicht gefunden: {DB_PATH}")
        return []
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        # Suche in systemsteuerung Tabelle nach controls
        cursor.execute("""
            SELECT DISTINCT gruppe 
            FROM systemsteuerung 
            WHERE feld = 'controls'
            ORDER BY gruppe
        """)
        
        views = [row[0] for row in cursor.fetchall()]
        return views
        
    finally:
        conn.close()


def analyze_controls(view_guid):
    """Analysiere Controls für eine View"""
    if not DB_PATH.exists():
        print(f"❌ Datenbank nicht gefunden: {DB_PATH}")
        return
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            SELECT wert 
            FROM systemsteuerung 
            WHERE gruppe = ? AND feld = 'controls'
        """, (view_guid,))
        
        row = cursor.fetchone()
        if not row:
            print(f"❌ Keine Controls für View '{view_guid}' gefunden")
            return
        
        # Wert ist JSON
        controls = json.loads(row[0])
        
        print(f"\n{'='*80}")
        print(f"📊 Controls für View: {view_guid}")
        print(f"{'='*80}\n")
        print(f"Anzahl Controls: {len(controls)}")
        
        # Zähle Probleme
        missing_display = 0
        duplicates = {}
        show_true = 0
        
        for key, control in controls.items():
            display_order = control.get('display_order')
            if display_order is None:
                missing_display += 1
            else:
                if display_order not in duplicates:
                    duplicates[display_order] = []
                duplicates[display_order].append(key)
            
            if control.get('show', False):
                show_true += 1
        
        # Duplikate filtern
        dup_count = sum(1 for keys in duplicates.values() if len(keys) > 1)
        
        print(f"\nStatistik:")
        print(f"  - Controls mit show=true: {show_true}")
        print(f"  - Controls ohne display_order: {missing_display}")
        print(f"  - Duplikate bei display_order: {dup_count}")
        
        if missing_display > 0 or dup_count > 0:
            print(f"\n⚠️  PROBLEME GEFUNDEN!")
            print(f"   Empfehlung: Controls löschen und neu generieren lassen")
        else:
            print(f"\n✅ Keine offensichtlichen Probleme")
        
    finally:
        conn.close()


def delete_controls(view_guid, confirm=True):
    """Lösche Controls für eine View"""
    if not DB_PATH.exists():
        print(f"❌ Datenbank nicht gefunden: {DB_PATH}")
        return False
    
    if confirm:
        print(f"\n⚠️  WARNUNG: Controls für View '{view_guid}' werden gelöscht!")
        print(f"   Alle benutzerdefinierten Spalten-Einstellungen gehen verloren.")
        print(f"   Beim nächsten View-Start werden Controls neu generiert.\n")
        
        response = input("Fortfahren? (ja/nein): ").strip().lower()
        if response not in ['ja', 'j', 'yes', 'y']:
            print("❌ Abgebrochen")
            return False
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        # Prüfe ob Controls existieren
        cursor.execute("""
            SELECT COUNT(*) 
            FROM systemsteuerung 
            WHERE gruppe = ? AND feld = 'controls'
        """, (view_guid,))
        
        count = cursor.fetchone()[0]
        if count == 0:
            print(f"ℹ️  Keine Controls für View '{view_guid}' vorhanden")
            return False
        
        # Lösche Controls
        cursor.execute("""
            DELETE FROM systemsteuerung 
            WHERE gruppe = ? AND feld = 'controls'
        """, (view_guid,))
        
        conn.commit()
        
        print(f"✅ Controls für View '{view_guid}' erfolgreich gelöscht")
        print(f"   Gelöschte Einträge: {cursor.rowcount}")
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"❌ Fehler beim Löschen: {e}")
        return False
        
    finally:
        conn.close()


def delete_all_controls(confirm=True):
    """Lösche Controls für ALLE Views"""
    views = list_views_with_controls()
    
    if not views:
        print("ℹ️  Keine Views mit Controls gefunden")
        return
    
    print(f"\n{'='*80}")
    print(f"📊 Gefundene Views mit Controls: {len(views)}")
    print(f"{'='*80}\n")
    
    for i, view_guid in enumerate(views, 1):
        print(f"{i}. {view_guid}")
    
    if confirm:
        print(f"\n⚠️  WARNUNG: Controls für ALLE {len(views)} Views werden gelöscht!")
        print(f"   Alle benutzerdefinierten Spalten-Einstellungen gehen verloren.")
        print(f"   Beim nächsten View-Start werden Controls neu generiert.\n")
        
        response = input("Fortfahren? (ja/nein): ").strip().lower()
        if response not in ['ja', 'j', 'yes', 'y']:
            print("❌ Abgebrochen")
            return
    
    # Lösche alle
    success_count = 0
    for view_guid in views:
        if delete_controls(view_guid, confirm=False):
            success_count += 1
    
    print(f"\n{'='*80}")
    print(f"✅ Erfolgreich gelöscht: {success_count}/{len(views)} Views")
    print(f"{'='*80}\n")


def main():
    """Hauptprogramm"""
    print("\n" + "="*80)
    print("🗑️  PDVM CONTROLS BEREINIGUNG (Direkter DB-Zugriff)")
    print("="*80 + "\n")
    
    # Liste Views
    views = list_views_with_controls()
    
    if not views:
        print("ℹ️  Keine Views mit Controls gefunden")
        return
    
    print(f"Gefundene Views: {len(views)}\n")
    
    for i, view_guid in enumerate(views, 1):
        print(f"{i}. {view_guid}")
    
    print("\nOptionen:")
    print("  [1-N] - Analysiere spezifische View")
    print("  [d]   - Lösche Controls für spezifische View")
    print("  [all] - Lösche Controls für ALLE Views")
    print("  [q]   - Beenden")
    
    while True:
        print()
        choice = input("Wählen Sie eine Option: ").strip().lower()
        
        if choice == 'q':
            print("👋 Auf Wiedersehen")
            break
        
        elif choice == 'all':
            delete_all_controls(confirm=True)
            break
        
        elif choice == 'd':
            print("\nWelche View? (Nummer eingeben)")
            for i, view_guid in enumerate(views, 1):
                print(f"{i}. {view_guid}")
            
            try:
                idx = int(input("\nView-Nummer: ").strip()) - 1
                if 0 <= idx < len(views):
                    delete_controls(views[idx], confirm=True)
                else:
                    print("❌ Ungültige Nummer")
            except ValueError:
                print("❌ Ungültige Eingabe")
        
        elif choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(views):
                analyze_controls(views[idx])
            else:
                print("❌ Ungültige Nummer")
        
        else:
            print("❌ Ungültige Option")


if __name__ == "__main__":
    main()
