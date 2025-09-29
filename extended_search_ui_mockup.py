"""
ERWEITERTE SUCHFUNKTIONALITÄT - UI MOCKUP
===========================================

HAUPTDIALOG (Erweitert um Details-Buttons):
┌────────────────────────────────────────────────┐
│ 🔍 Suchparameter                               │
├────────────────────────────────────────────────┤
│                                                │
│ Familienname: [M*____________] [Details...]    │
│ Zusammenfassung: "beginnt mit M"              │
│                                                │
│ Vorname:      [*au*__________] [Details...]    │  
│ Zusammenfassung: "enthält au, nicht Laure*"   │
│                                                │
│ Alter:        [____________] [Details...]      │
│ Zusammenfassung: "zwischen 18 und 65"         │
│                                                │
│ [🗑️ Alle Filter zurücksetzen]                 │
│                                                │
│ [OK] [Abbrechen]                               │
└────────────────────────────────────────────────┘

DETAIL-DIALOG für ein Feld:
┌────────────────────────────────────────────────┐
│ 🔍 Erweiterte Suche: Vorname                   │
├────────────────────────────────────────────────┤
│                                                │
│ ┌─ UND ──┐ [au___________] ☐Von links ☑Enthält │
│ ├─ NICHT─┤ [Laure_______] ☑Von links ☐Enthält │
│ ├─ ODER──┤ [___________] ☐Von links ☐Enthält  │
│ └────────┘                                     │
│                                                │
│ [+ Weitere Bedingung hinzufügen]               │
│                                                │
│ ┌─ Vorschau ──────────────────────────────────┐ │
│ │ ✅ "Paul"     (enthält au)                   │ │
│ │ ✅ "Klaus"    (enthält au)                   │ │
│ │ ❌ "Laurence" (beginnt mit Laure)            │ │
│ │ ❌ "Max"      (kein au)                      │ │
│ └──────────────────────────────────────────────┘ │
│                                                │
│ [OK] [Abbrechen] [Zurücksetzen]               │
└────────────────────────────────────────────────┘

SUCHTYPEN (Pro Bedingung wählbar):
┌─────────────────┬────────────────────────────────┐
│ ☑ Von links     │ "M" → "Max", "Maria"          │
│ ☐ Von rechts    │ "er" → "Müller", "Weber"      │
│ ☑ Enthält       │ "au" → "Paul", "Klaus"        │
│ ☐ Exakt         │ "Max" → nur "Max"             │
│ ☐ Wildcard (*)  │ "M*er" → "Müller", "Meier"   │
│ ☐ Regex         │ "^[A-M]" → A bis M            │
└─────────────────┴────────────────────────────────┘
"""

def create_extended_search_ui_concept():
    """
    IMPLEMENTIERUNGS-KONZEPT:
    
    1. HAUPTDIALOG erweitern:
       - Bestehende Filter-Felder behalten
       - [Details...] Button pro Feld hinzufügen
       - Zusammenfassung unter jedem Feld anzeigen
       
    2. DETAIL-DIALOG erstellen:
       - FieldSearchDetailDialog Klasse
       - Dynamische Bedingungszeilen
       - Vorschau-Bereich (optional)
       - UND/ODER/NICHT Operatoren
       
    3. DATENSTRUKTUR erweitern:
       - Rückwärtskompatibel zu aktuellen Filtern
       - Komplexe Bedingungen als Array
       - Einfache Filter → automatisch AND-Bedingung
       
    4. ANWENDUNGSLOGIK:
       - apply_extended_filters() Methode
       - Für jede Zeile alle Feld-Gruppen prüfen
       - Kombinierte Bedingungen auswerten
    
    RÜCKWÄRTSKOMPATIBILITÄT:
    Alte Filter:     {"name": "Max"}
    Neue Filter:     {"name": [{"op": "AND", "value": "Max", "type": "exact"}]}
    
    AUTO-KONVERTIERUNG:
    - Einfache Strings → contains Bedingung
    - Wildcard (*) → startswith/wildcard 
    - NOT: prefix → NOT-Bedingung
    """
    pass