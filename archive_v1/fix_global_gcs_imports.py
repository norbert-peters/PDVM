#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix: Ersetzt lokale GCS-Imports durch globale _get_gcs() Funktion
"""

import re

def fix_gcs_imports(file_path):
    """Ersetzt lokale get_gcs() Imports durch _get_gcs() Aufrufe"""
    
    print(f"🔧 Bearbeite: {file_path}")
    
    # Lese Datei
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern 1: Lokale Imports mit direktem Aufruf
    # from pdvm_central_systemsteuerung import get_gcs
    # gcs = get_gcs()
    pattern1 = r'(\s+)from pdvm_central_systemsteuerung import get_gcs\s*\n\s+gcs = get_gcs\(\)'
    
    # Ersetze durch _get_gcs()
    replacement1 = r'\1gcs = _get_gcs()'
    
    content_new = re.sub(pattern1, replacement1, content)
    
    count1 = len(re.findall(pattern1, content))
    print(f"  ✅ {count1} lokale Import+Aufruf-Kombinationen ersetzt")
    
    # Pattern 2: Nur lokale Imports (ohne sofortigen Aufruf)
    pattern2 = r'(\s+)from pdvm_central_systemsteuerung import get_gcs\s*\n'
    
    # Entferne den Import (da global schon vorhanden)
    replacement2 = r'\1# GCS global verfügbar via _get_gcs()\n'
    
    content_final = re.sub(pattern2, replacement2, content_new)
    
    count2 = len(re.findall(pattern2, content_new))
    print(f"  ✅ {count2} alleinstehende Imports entfernt")
    
    # Ersetze get_gcs() Aufrufe durch _get_gcs()
    pattern3 = r'\bget_gcs\(\)'
    content_final = re.sub(pattern3, r'_get_gcs()', content_final)
    
    count3 = len(re.findall(r'\b_get_gcs\(\)', content_final))
    print(f"  ✅ Gesamt {count3} _get_gcs() Aufrufe im finalen Code")
    
    # Schreibe zurück
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content_final)
    
    print(f"💾 Gespeichert: {file_path}\n")

if __name__ == "__main__":
    print("\n=== 🔧 GCS-IMPORT VEREINFACHUNG ===\n")
    
    files = [
        'c:/Users/norbe/OneDrive/Dokumente/MyApplication/pdvm_view_dialog.py',
        'c:/Users/norbe/OneDrive/Dokumente/MyApplication/pdvm_view_pipeline.py',
    ]
    
    for file_path in files:
        try:
            fix_gcs_imports(file_path)
        except Exception as e:
            print(f"❌ Fehler bei {file_path}: {e}\n")
    
    print("✅ FERTIG!")
