"""
Debug: Komplette Analyse des Feldverdopplungs-Problems

Prüft:
1. Daten in sys_framedaten (DB)
2. Was SystemEditor lädt
3. Was InputControlsManager lädt
4. Wo die Verdopplung entsteht
"""
import sys
import json
import sqlite3
from pathlib import Path

# Pfade
db_path = r"C:\Users\norbe\OneDrive\Dokumente\MyApplication\Daten\pdvm_system.db"
frame_uid = "4078079f-4028-45ed-879c-3c779ecf3d0d"

print("=" * 100)
print("FELDVERDOPPLUNGS-ANALYSE")
print("=" * 100)

# ========================================
# 1. DB-DATEN (Ist-Zustand)
# ========================================
print("\n📂 1. DATEN IN DB (sys_framedaten)")
print("-" * 100)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT daten FROM sys_framedaten WHERE uid = ?", (frame_uid,))
result = cursor.fetchone()

if not result:
    print(f"❌ Frame {frame_uid} nicht gefunden!")
    sys.exit(1)

daten_db = json.loads(result[0])
conn.close()

# PERSONDATEN analysieren
if 'PERSONDATEN' in daten_db:
    persondaten = daten_db['PERSONDATEN']
    print(f"PERSONDATEN: {len(persondaten)} Felder")
    
    # Nach display_order sortieren
    sorted_felder = sorted(
        persondaten.items(),
        key=lambda x: x[1].get('display_order', 999)
    )
    
    print("\nFelder nach display_order:")
    for guid, feld in sorted_felder:
        name = feld.get('name', '???')
        label = feld.get('label', '???')
        order = feld.get('display_order', 999)
        tab = feld.get('tab', -1)
        
        print(f"  [{order:3d}] {name:25s} | {label:20s} | Tab={tab:2d} | GUID={guid[:8]}...")

# ========================================
# 2. NAMEN-PRÜFUNG (Duplikate?)
# ========================================
print("\n" + "=" * 100)
print("📋 2. NAMEN-ANALYSE (Duplikate?)")
print("-" * 100)

if 'PERSONDATEN' in daten_db:
    persondaten = daten_db['PERSONDATEN']
    
    # Namen sammeln
    namen_liste = []
    for guid, feld in persondaten.items():
        name = feld.get('name')
        if name:
            namen_liste.append((name, guid, feld.get('label'), feld.get('display_order', 999)))
    
    # Duplikate finden
    namen_counts = {}
    for name, guid, label, order in namen_liste:
        if name not in namen_counts:
            namen_counts[name] = []
        namen_counts[name].append((guid, label, order))
    
    # Duplikate anzeigen
    duplikate_gefunden = False
    for name, entries in namen_counts.items():
        if len(entries) > 1:
            duplikate_gefunden = True
            print(f"\n⚠️ DUPLIKAT: '{name}' kommt {len(entries)} mal vor:")
            for guid, label, order in entries:
                print(f"     - GUID={guid[:8]}... | Label={label} | Order={order}")
    
    if not duplikate_gefunden:
        print("✅ Keine Duplikate in der DB gefunden!")

# ========================================
# 3. FIELDS-NACH-TAB (Was sollte angezeigt werden?)
# ========================================
print("\n" + "=" * 100)
print("📑 3. FELDER NACH TAB")
print("-" * 100)

if 'PERSONDATEN' in daten_db:
    persondaten = daten_db['PERSONDATEN']
    
    # Nach Tab gruppieren
    tabs = {}
    for guid, feld in persondaten.items():
        tab = feld.get('tab', 1)
        if tab not in tabs:
            tabs[tab] = []
        tabs[tab].append((guid, feld))
    
    # Tabs anzeigen
    for tab_nr in sorted(tabs.keys()):
        if tab_nr < 0:
            print(f"\n⚠️ Tab {tab_nr} (NEGATIVER TAB - sollte nicht angezeigt werden?):")
        else:
            print(f"\nTab {tab_nr}:")
        
        felder = sorted(tabs[tab_nr], key=lambda x: x[1].get('display_order', 999))
        for guid, feld in felder:
            name = feld.get('name', '???')
            label = feld.get('label', '???')
            order = feld.get('display_order', 999)
            print(f"  [{order:3d}] {name:25s} | {label}")

# ========================================
# 4. FINANZDATEN-PRÜFUNG
# ========================================
print("\n" + "=" * 100)
print("💰 4. FINANZDATEN-ANALYSE")
print("-" * 100)

if 'FINANZDATEN' in daten_db:
    finanzdaten = daten_db['FINANZDATEN']
    print(f"FINANZDATEN: {len(finanzdaten)} Felder")
    
    sorted_felder = sorted(
        finanzdaten.items(),
        key=lambda x: x[1].get('display_order', 999)
    )
    
    for guid, feld in sorted_felder:
        name = feld.get('name', '???')
        label = feld.get('label', '???')
        order = feld.get('display_order', 999)
        tab = feld.get('tab', -1)
        
        print(f"  [{order:3d}] {name:25s} | {label:20s} | Tab={tab:2d}")
else:
    print("❌ FINANZDATEN Gruppe nicht gefunden!")

# ========================================
# 5. ZUSAMMENFASSUNG
# ========================================
print("\n" + "=" * 100)
print("📊 ZUSAMMENFASSUNG")
print("=" * 100)

print(f"\nGruppen in DB: {list(daten_db.keys())}")
print(f"PERSONDATEN Felder: {len(daten_db.get('PERSONDATEN', {}))}")
print(f"FINANZDATEN Felder: {len(daten_db.get('FINANZDATEN', {}))}")

# Erwartete Anzeige
print("\n✅ ERWARTETE ANZEIGE (Tab 1 - aus DB):")
if 'PERSONDATEN' in daten_db:
    persondaten = daten_db['PERSONDATEN']
    tab1_felder = [(g, f) for g, f in persondaten.items() if f.get('tab') == 1]
    tab1_sorted = sorted(tab1_felder, key=lambda x: x[1].get('display_order', 999))
    
    for guid, feld in tab1_sorted:
        print(f"  - {feld.get('name', '???')} ({feld.get('label', '???')})")

print("\n✅ ANALYSE ABGESCHLOSSEN")
