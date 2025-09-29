#!/usr/bin/env python3
"""
FILTER-PIPELINE ANALYSE
=======================

Analysiert die aktuelle Filter-Architektur um die nicht-linearen Pfade zu identifizieren:

PROBLEM:
- Komplexer Filter -> 3 Zeilen gefiltert
- Einfacher Filter "Lau" -> wird auf die 3 bereits gefilterten Zeilen angewendet -> 2 Treffer
- Filter löschen -> Einfacher Filter "Lau" -> wird auf alle Daten angewendet -> 3 Treffer (korrekt)

URSACHE: Filter-Pipeline ist nicht linear - verschiedene Filter-Types haben verschiedene Ablaufpfade

ZIEL: VOLLSTÄNDIG LINEARE PIPELINE:
1. Gesamtfilter (bleibt bestehen, direkt angewendet)
2. Parametrische Filter (ersetzen Gesamtfilter komplett)
3. Bei neuer Filterung: Kompletter Reset aller vorherigen Filter
4. Nur EIN aktiver Filter zur Zeit
5. Immer komplette Datenbasis als Ausgangspunkt
"""

import logging
import sys
import os

# Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Path setup für Imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def analyze_filter_pipeline_issue():
    """Analysiert die Filter-Pipeline um das nicht-lineare Verhalten zu finden"""
    print("🔍 ANALYSE: Filter-Pipeline Nicht-Linearität")
    print("=" * 60)
    
    # Suche nach Filter-Anwendungsstellen
    files_to_check = [
        "main.py",
        "search_parameter_dialog.py", 
        "extended_filter_engine.py",
        "central_filter_reset.py"
    ]
    
    filter_calls = {}
    
    for filename in files_to_check:
        try:
            print(f"\\n📂 Analysiere: {filename}")
            
            with open(filename, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\\n')
                
                # Suche nach Filter-Anwendungen
                filter_patterns = [
                    'filter.*apply', 'apply.*filter', 'search.*filter',
                    'execute.*filter', 'run.*filter', 'process.*filter',
                    'gesamtfilter', 'einfach.*filter', 'komplex.*filter',
                    'current_filters', 'extended.*filter'
                ]
                
                found_calls = []
                for i, line in enumerate(lines, 1):
                    line_lower = line.lower()
                    for pattern in filter_patterns:
                        import re
                        if re.search(pattern, line_lower) and ('def ' in line or 'filter' in line):
                            found_calls.append(f"Zeile {i}: {line.strip()}")
                
                if found_calls:
                    filter_calls[filename] = found_calls
                    for call in found_calls:
                        print(f"  📌 {call}")
                else:
                    print("  ℹ️ Keine Filter-Aufrufe gefunden")
                    
        except Exception as e:
            print(f"  ❌ Fehler beim Analysieren von {filename}: {e}")
    
    # Zusammenfassung der Probleme
    print("\\n🚨 IDENTIFIZIERTE PROBLEME:")
    print("1. Mehrere parallele Filter-Pfade")
    print("2. Filter werden auf bereits gefilterte Daten angewendet")
    print("3. Gesamtfilter vs. Parametrische Filter Konflikte")
    print("4. Keine zentrale Filter-Execution-Pipeline")
    print("5. Reset erfolgt nicht vor jeder neuen Filterung")
    
    # Lösungsvorschlag
    print("\\n💡 LÖSUNGSANSATZ:")
    print("1. Zentraler FilterExecutionManager")
    print("2. Alle Filter gehen durch EINE Pipeline")
    print("3. Automatischer kompletter Reset vor jeder Filterung")
    print("4. Nur EIN aktiver Filter zur Zeit")
    print("5. Immer komplette Datenbasis als Startpunkt")
    
    return filter_calls

if __name__ == "__main__":
    analyze_filter_pipeline_issue()