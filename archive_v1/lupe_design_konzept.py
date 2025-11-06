#!/usr/bin/env python3
"""
Erweiterte Lupe-Funktionalität für View und Input-Bereiche
Jeder Bereich kann die gesamte verfügbare Fläche einnehmen
"""

LUPE_DESIGN_KONZEPT = """
🔍 LUPE-MODUS: DYNAMISCHE FLÄCHENNUTZUNG
========================================

DREI ANZEIGEMODI:
================

┌─ MODUS 1: NORMAL (Standard) ────────────────────────────────────────┐
│                                                                      │
│  ┌─ VIEW-BEREICH (50%) ──────────────────────────────── [🔍] [📝] ─┐ │
│  │ ┌─ DATEN-TABELLE ─────────────────────────────────────────────┐ │ │
│  │ │ [Filter] [Sort] [Search] ____________________________       │ │ │
│  │ │ │Name      │Geburt    │Ort      │Status    │Aktionen      │ │ │ │
│  │ │ │Schmidt   │1985-03-15│Hamburg  │Aktiv     │[Edit][Del]   │ │ │ │
│  │ │ │Müller    │1990-07-22│Berlin   │Inaktiv   │[Edit][Del]   │ │ │ │
│  │ └─────────────────────────────────────────────────────────────┘ │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│  ╔═ SPLITTER (verschiebbar) ═══════════════════════════════════════╗ │
│  ┌─ INPUT-BEREICH (50%) ──────────────────────────────── [🔍] [📝] ─┐ │
│  │ [Stammdaten] [Details] [Zusatz]                                 │ │
│  │ ┌─ AKTIVER TAB ─────────────────────────────────────────────┐   │ │
│  │ │ Name: [Schmidt________________] Vorname: [Hans_________]   │   │ │
│  │ │ Geburt: [1985-03-15___________] Ort: [Hamburg__________]   │   │ │
│  │ │ Email: [hans.schmidt@mail.com_] Status: [Aktiv_v_____]   │   │ │
│  │ └───────────────────────────────────────────────────────────┘   │ │
│  └──────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘

┌─ MODUS 2: VIEW-LUPE (100% View) ────────────────────────────────────┐
│                                                                      │
│  ┌─ VIEW-BEREICH (100%) ────────────────────────────── [🔍] [📝] ───┐ │
│  │ ┌─ ERWEITERTE DATEN-TABELLE ─────────────────────────────────┐   │ │
│  │ │ [🔍 Filter] [📊 Sort] [🔎 Search] [📤 Export] [⚙️ Config] │   │ │
│  │ │ ____________________________________________________________   │ │
│  │ │ │Name    │Vorname│Geburt    │Ort     │PLZ │Land│Status │   │   │ │
│  │ │ │Schmidt │Hans   │1985-03-15│Hamburg │20095│DE  │Aktiv  │   │   │ │
│  │ │ │Müller  │Anna   │1990-07-22│Berlin  │10115│DE  │Inaktiv│   │   │ │
│  │ │ │Johnson │Mike   │1988-11-05│London  │SW1A │UK  │Aktiv  │   │   │ │
│  │ │ │García  │Maria  │1992-02-18│Madrid  │28001│ES  │Aktiv  │   │   │ │
│  │ │ │Dubois  │Pierre │1987-09-30│Paris   │75001│FR  │Pending│   │   │ │
│  │ │ │          ... weitere 20+ Zeilen sichtbar ...          │   │   │ │
│  │ └─────────────────────────────────────────────────────────────┘   │ │
│  │ [Zeige: 25 von 1247] [Seite: 1/50] [📊 Statistiken]             │ │
│  └──────────────────────────────────────────────────────────────────┘ │
│  INPUT-BEREICH: [Ausgeblendet - Klick 📝 zum Einblenden]              │
└──────────────────────────────────────────────────────────────────────┘

┌─ MODUS 3: INPUT-LUPE (100% Input) ──────────────────────────────────┐
│                                                                      │
│  VIEW-BEREICH: [Ausgeblendet - Klick 🔍 zum Einblenden]              │
│  ┌─ INPUT-BEREICH (100%) ────────────────────────────── [🔍] [📝] ───┐ │
│  │ [Stammdaten] [Details] [Zusatz] [Verlauf] [Dokumente]           │ │
│  │ ┌─ ERWEITERTE EINGABE-TABS ──────────────────────────────────┐   │ │
│  │ │ ╔═ STAMMDATEN ══════════════════════════════════════════╗ │   │ │
│  │ │ ║ Persönliche Daten:                                    ║ │   │ │
│  │ │ ║ Name: [Schmidt____________________] ⚠️ Pflichtfeld     ║ │   │ │
│  │ │ ║ Vorname: [Hans___________________] ⚠️ Pflichtfeld     ║ │   │ │
│  │ │ ║ Geburt: [1985-03-15_____] 📅 Kalender [Alter: 40]   ║ │   │ │
│  │ │ ║                                                       ║ │   │ │
│  │ │ ║ Adresse:                                              ║ │   │ │
│  │ │ ║ Straße: [Musterstraße 123_______________________]     ║ │   │ │
│  │ │ ║ PLZ/Ort: [20095] [Hamburg___________________]         ║ │   │ │
│  │ │ ║ Land: [Deutschland_v_________] 🌍                     ║ │   │ │
│  │ │ ║                                                       ║ │   │ │
│  │ │ ║ Kontakt:                                              ║ │   │ │
│  │ │ ║ Email: [hans.schmidt@mail.com__________________] ✓    ║ │   │ │
│  │ │ ║ Telefon: [+49 40 12345678_____________________]      ║ │   │ │
│  │ │ ║ Mobil: [+49 172 9876543_______________________]      ║ │   │ │
│  │ │ ╚═══════════════════════════════════════════════════════╝ │   │ │
│  │ └─────────────────────────────────────────────────────────────┘   │ │
│  │ [💾 Speichern] [❌ Reset] [📋 Kopieren] [📤 Export]               │ │
│  └──────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────┘

STEUERUNGSELEMENTE:
==================
🔍 View-Lupe:   Maximiert View-Bereich (für komplexe Tabellen/Filter)
📝 Input-Lupe:  Maximiert Input-Bereich (für umfangreiche Formulare)
⚖️ Normal:      50/50 Aufteilung (Standard)
🔄 Toggle:      Schneller Wechsel zwischen den Modi

ANWENDUNGSFÄLLE:
===============
📊 VIEW-LUPE:
  ✅ Große Datenmengen analysieren
  ✅ Komplexe Filter und Sortierungen
  ✅ Multi-Spalten-Vergleiche
  ✅ Export-/Import-Operationen
  ✅ Datenvisualisierung

📝 INPUT-LUPE:
  ✅ Umfangreiche Formulare ausfüllen
  ✅ Multi-Tab-Eingaben
  ✅ Dokumenten-Upload
  ✅ Verlaufs-/Notizen-Eingabe
  ✅ Validierung und Korrekturen

TECHNISCHE UMSETZUNG:
====================
QSplitter.setSizes([100, 0])  # View-Lupe
QSplitter.setSizes([0, 100])  # Input-Lupe  
QSplitter.setSizes([50, 50])  # Normal

Persistierung: frame_guid + user_guid → "display_mode": "view_lupe|input_lupe|normal"
"""

def create_lupe_controls():
    """Erzeugt die Steuerungselemente für den Lupe-Modus"""
    return """
    LUPE-STEUERUNG (Top-Right Corner jedes Bereichs):
    ================================================
    
    ┌─ VIEW-BEREICH ─────────────────────────────── [🔍] [📝] [⚖️] ─┐
    │ 🔍 = View maximieren (dieser Bereich 100%)                   │
    │ 📝 = Input maximieren (anderer Bereich 100%)                 │  
    │ ⚖️ = Normal-Modus (50/50 Aufteilung)                         │
    └───────────────────────────────────────────────────────────────┘
    
    ┌─ INPUT-BEREICH ────────────────────────────── [🔍] [📝] [⚖️] ─┐
    │ 🔍 = View maximieren (anderer Bereich 100%)                  │
    │ 📝 = Input maximieren (dieser Bereich 100%)                  │
    │ ⚖️ = Normal-Modus (50/50 Aufteilung)                         │
    └───────────────────────────────────────────────────────────────┘
    
    KEYBOARD SHORTCUTS:
    ==================
    F1  = View-Lupe
    F2  = Input-Lupe  
    F3  = Normal-Modus
    F11 = Toggle zwischen aktuell und vorherigem Modus
    """

if __name__ == "__main__":
    print(LUPE_DESIGN_KONZEPT)
    print(create_lupe_controls())
