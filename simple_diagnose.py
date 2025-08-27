#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Einfache Spalten-Diagnose
=========================
"""

import os

print("🏥 EINFACHE SPALTEN-DIAGNOSE")
print("=" * 50)

# 1. Prüfe wichtige Dateien
important_files = [
    'pdvm_modern_view_widget.py',
    'PdvmManager.db',
    'meine_datenbank.db'
]

print("\n📁 Datei-Check:")
for file in important_files:
    if os.path.exists(file):
        size = os.path.getsize(file)
        print(f"✅ {file}: {size:,} Bytes")
    else:
        print(f"❌ {file}: NICHT GEFUNDEN")

# 2. Prüfe Code-Struktur
widget_file = 'pdvm_modern_view_widget.py'
if os.path.exists(widget_file):
    print(f"\n🔍 Code-Analyse von {widget_file}:")
    
    with open(widget_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Zähle kritische Funktionen
    critical_functions = [
        'def _apply_or_create_level2',
        'def _on_column_moved',
        'def _update_level2_order_from_drag_drop', 
        'def test_column_order_functionality',
        'sectionMoved.connect'
    ]
    
    for func in critical_functions:
        count = content.count(func)
        status = "✅" if count > 0 else "❌"
        print(f"   {status} {func}: {count}x")

# 3. Import-Test
print("\n🔄 Import-Test:")
try:
    import pdvm_modern_view_widget
    print("✅ pdvm_modern_view_widget importiert")
    
    # Prüfe Klasse
    if hasattr(pdvm_modern_view_widget, 'PdvmModernViewWidget'):
        print("✅ PdvmModernViewWidget Klasse gefunden")
    else:
        print("❌ PdvmModernViewWidget Klasse FEHLT")
        
except Exception as e:
    print(f"❌ Import-Fehler: {e}")

print("\n🏥 DIAGNOSE ABGESCHLOSSEN")
