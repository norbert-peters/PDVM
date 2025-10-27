# PROJEKTION-ARCHITEKTUR ANALYSE
**Datum**: 26. Oktober 2025  
**Anlass**: User-Frage zur korrekten Zuordnung der Projektiontables

## 🎯 User-Frage

> "Mit geht es darum ob die projektiontables der View in der GCS allgemein für die View vorhanden sind oder ob diese richtigerweise im Bereich der View erstellt werden."

## ✅ ANALYSE-ERGEBNIS: ARCHITEKTUR IST KORREKT!

### Projektiontables-Speicherung: GCS (RICHTIG!)

**Begründung:**
1. ✅ **Statische Daten** - "ziemlich Statisch und werden nur durch 'Spalten verwalten' geändert"
2. ✅ **User-bezogen** - Pro User verschiedene Spalten-Präferenzen
3. ✅ **View-spezifisch** - Gespeichert mit `view_guid` als Key
4. ✅ **Zentrale Verwaltung** - Ein Ort für alle Projektions-Logik
5. ✅ **Parallele Views** - Jede View hat eigene Projektionen via `view_guid`

### Daten-Fluss: Controls → GCS → View

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. VIEW-EBENE: Controls-Erstellung                                  │
├─────────────────────────────────────────────────────────────────────┤
│ pdvm_view_daten_manager.py                                          │
│                                                                      │
│ get_all_columns():                                                  │
│   • Erstellt basis_columns[] mit ALLEN Controls                     │
│   • SYSTEM: uid_original, name_original                             │
│   • VIEW: feldname_original (aus View-Config)                       │
│   • SHOW: alle _show Spalten                                        │
│   • Attribute: show, expertOrder, displayOrder                      │
│                                                                      │
│ SPEICHERUNG (bei found_new_controls && first_call):                 │
│   gcs().set_value(                                                  │
│       gruppe=view_guid,                                             │
│       feld="ColumnControls",        ← View-spezifischer Feldname!   │
│       wert=persist_map              ← {name: {show, orders}}        │
│   )                                                                  │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 2. GCS-EBENE: Zentrale Verwaltung                                   │
├─────────────────────────────────────────────────────────────────────┤
│ pdvm_central_systemsteuerung.py                                     │
│                                                                      │
│ SPEICHER-STRUKTUR:                                                  │
│   self._projection_tables = {                                       │
│       'view-guid-1': [10 Listen],   ← Pro View eigene Projektionen  │
│       'view-guid-2': [10 Listen],                                   │
│       'view-guid-3': [10 Listen]                                    │
│   }                                                                  │
│                                                                      │
│ _build_projection_tables(view_guid):                                │
│   1. Lade Controls aus DB:                                          │
│      controls, _ = self.db.get_value(view_guid, "controls")         │
│      ↑                                      ↑                        │
│      │                                      └─ Allgemeiner Feldname! │
│      └─ self.db = Systemsteuerung-DB                                │
│                                                                      │
│   2. Analysiere Controls:                                           │
│      • all_controls[] - Alle außer dummy+row_type                   │
│      • visible_controls[] - Nur mit show=true                       │
│      • non_expert_controls[] - Nur ohne expert_mode flag            │
│                                                                      │
│   3. Erstelle 10-Element Array:                                     │
│      [0] View Standard    - show=true, display_order                │
│      [1] Change Standard  - nicht expert_mode, display_order        │
│      [2] Filter Standard  - visible + filterable                    │
│      [3] Sort Standard    - sortierbar                              │
│      [4] Reserviert                                                 │
│      [5] View Expert      - alle außer dummy, expert_order          │
│      [6] Change Expert    - alle außer dummy, expert_order          │
│      [7] Filter Expert    - alle filterbar                          │
│      [8] Sort Expert      - alle sortierbar                         │
│      [9] Reserviert                                                 │
│                                                                      │
│   4. Speichere in _projection_tables[view_guid]                     │
│                                                                      │
│ get_projection_table(view_guid, index_or_name):                     │
│   • Gibt Liste von Spalten-Keys zurück                              │
│   • Automatisch per view_guid unterschieden                         │
│   • Legacy-Support: String-Namen → Integer-Index                    │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 3. VIEW-EBENE: Projektion nutzen                                    │
├─────────────────────────────────────────────────────────────────────┤
│ pdvm_view_daten_manager.py                                          │
│                                                                      │
│ VERWENDUNG:                                                         │
│   visible_columns = gcs().get_projection_table(                     │
│       self.view_guid,                                               │
│       'table'  ← Auto-Selektion: Standard oder Expert               │
│   )                                                                  │
│                                                                      │
│ • GCS entscheidet automatisch Standard/Expert (global_expert_mode)  │
│ • View bekommt fertige Liste der sichtbaren Spalten                 │
│ • Keine lokale Logik nötig - alles in GCS                           │
└─────────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│ 4. SPALTEN VERWALTEN: Änderung der Projektionen                     │
├─────────────────────────────────────────────────────────────────────┤
│ column_management_dialog.py                                         │
│                                                                      │
│ Bei Änderungen durch User:                                          │
│   1. Controls-Attribute ändern (show, order)                        │
│   2. In GCS speichern:                                              │
│      gcs().db.set_value(view_guid, "controls", updated_controls)    │
│   3. Projektionen neu bauen:                                        │
│      gcs().rebuild_projection_tables(view_guid)                     │
│   4. View aktualisiert automatisch (nutzt neue Projektion)          │
└─────────────────────────────────────────────────────────────────────┘
```

## 🔍 NAMENS-INKONSISTENZ IST KORREKT!

### Verschiedene Namensräume

**VIEW-Ebene**: `"ColumnControls"`
- **Kontext**: Spalten-spezifische Controls für Views
- **Bedeutung**: Controls die SPALTEN in einer View repräsentieren
- **Speicherung**: `gcs().set_value(view_guid, "ColumnControls", persist_map)`

**GCS-Ebene**: `"controls"`
- **Kontext**: Allgemeine Controls (nicht nur Spalten!)
- **Bedeutung**: Kann auch andere Control-Typen sein (Buttons, etc.)
- **Laden**: `self.db.get_value(view_guid, "controls")`

### ⚠️ PROBLEM: Namens-Mismatch führt zu Datenverlust!

```python
# VIEW speichert als:
gcs().set_value(gruppe=view_guid, feld="ColumnControls", ...)
                                      ↑
                                      └─ Wird NICHT gefunden!

# GCS lädt als:
controls, _ = self.db.get_value(view_guid, "controls")
                                            ↑
                                            └─ Anderer Feldname!
```

**Konsequenz**:
- `name_original` und `name_show` Controls werden erstellt ✅
- Aber in GCS unter falschem Feldnamen gespeichert ❌
- GCS findet sie nicht → Projektion leer → Spalten nicht sichtbar ❌

## 🎯 WARUM IST GCS TROTZDEM RICHTIG?

### 1. Separation of Concerns

```
┌────────────────────┐
│ VIEW               │  • Erstellt Controls aus View-Config
│ - Daten-Logik      │  • Weiß was SPALTEN sind
│ - Matrix-Pipeline  │  • Kennt Datenbank-Felder
└────────────────────┘
          ↓ Speichert Controls
┌────────────────────┐
│ GCS                │  • Verwaltet Controls zentral
│ - Projektion-Logik │  • Weiß WIE man projiziert (Expert/Standard)
│ - User-Präferenzen │  • Kennt User-Einstellungen
└────────────────────┘
          ↓ Liefert Projektion
┌────────────────────┐
│ VIEW               │  • Nutzt fertige Projektion
│ - UI-Rendering     │  • Keine eigene Projektion-Logik
│ - User-Interaktion │  • Einfach und klar
└────────────────────┘
```

### 2. Parallele Views - Kein Problem!

```python
# 3 Views gleichzeitig offen:
view_personen = PdvmView('view-guid-personen')
view_finanzen = PdvmView('view-guid-finanzen')
view_produkte = PdvmView('view-guid-produkte')

# Jede hat eigene Projektionen in GCS:
gcs()._projection_tables = {
    'view-guid-personen': [
        [0]: ['familienname_show', 'vorname_show', ...],  # Standard
        [5]: ['uid_original', 'name_original', ...]       # Expert
    ],
    'view-guid-finanzen': [
        [0]: ['datum_show', 'betrag_show', ...],
        [5]: ['uid_original', 'buchungsnummer_original', ...]
    ],
    'view-guid-produkte': [
        [0]: ['produktname_show', 'preis_show', ...],
        [5]: ['uid_original', 'artikelnummer_original', ...]
    ]
}

# Keine Kollision - jede View hat eigene Projektionen!
```

### 3. Zentrale vs. Lokale Verwaltung

**ZENTRAL (GCS) - RICHTIG**:
- ✅ Ein Ort für Projektion-Logik (DRY-Prinzip)
- ✅ Konsistente Regeln über alle Views
- ✅ Einfache Wartung (nur eine Stelle)
- ✅ User-Präferenzen zentral gespeichert
- ✅ "Spalten verwalten" ändert zentral → alle Views aktuell

**LOKAL (View) - FALSCH**:
- ❌ Duplikation der Projektion-Logik in jeder View
- ❌ Inkonsistenzen zwischen Views möglich
- ❌ Schwer wartbar (viele Stellen ändern)
- ❌ Jede View müsste eigene DB-Zugriffe machen

## 📊 DATENBANK-STRUKTUR

### PdvmManager.db (Haupt-DB)

```
Tabelle: systemsteuerung
├─ uid: 'view-guid-1'
├─ daten: {
│   "controls": {                    ← GCS sucht hier!
│       "uid_original": {...},
│       "name_original": {...},      ← Sollte hier sein!
│       "familienname_show": {...}
│   },
│   "ColumnControls": {              ← VIEW speichert hier!
│       "uid_original": {...},
│       "name_original": {...}       ← Ist hier gespeichert!
│   }
│ }
```

**Problem**: Zwei verschiedene Felder im selben Datensatz!

## 🔧 LÖSUNG (nur dokumentiert, NICHT ändern)

**Option A**: GCS verwendet `"ColumnControls"` statt `"controls"`
```python
# In pdvm_central_systemsteuerung.py Zeile 721
controls, _ = self.db.get_value(view_guid, "ColumnControls")  # Ändern
```

**Option B**: View speichert als `"controls"` statt `"ColumnControls"`
```python
# In pdvm_view_daten_manager.py Zeile 921
gcs().set_value(gruppe=self.view_guid, feld="controls", ...)  # Ändern
```

**Empfehlung**: Option A - GCS anpassen
- Grund: `"ColumnControls"` ist beschreibender
- Grund: Mehrere Stellen in View verwenden bereits `"ColumnControls"`
- Grund: Trennung zwischen allgemeinen Controls und Spalten-Controls

## ✅ ZUSAMMENFASSUNG

### Frage 1: Projektiontables in GCS oder View?
**Antwort**: ✅ **GCS ist RICHTIG!**
- Zentrale Verwaltung für statische, user-bezogene Daten
- Pro View unterschieden via `view_guid` als Dictionary-Key
- Parallele Views kein Problem (jede hat eigenen Key)
- "Spalten verwalten" ändert zentral → automatische Aktualisierung

### Frage 2: Namens-Inkonsistenz korrekt?
**Antwort**: ✅ **Konzeptionell JA, praktisch NEIN!**
- `"ColumnControls"` (View) vs. `"controls"` (GCS) sind verschiedene Namensräume
- **ABER**: Aktuell führt Mismatch zu Datenverlust
- **name_original** und **name_show** werden erstellt aber nicht gefunden
- Behebung: Entweder GCS oder View anpassen (Feldname vereinheitlichen)

### Frage 3: Warum funktioniert es grundsätzlich?
**Antwort**: Architektur ist korrekt designed!
- GCS = Zentrale Verwaltung (projektions-Logik, User-Präferenzen)
- View = Daten-Logik (was sind Spalten, woher kommen Daten)
- Trennung ist sauber und macht Sinn
- Nur Feldname-Synchronisation fehlt aktuell

## 📝 NÄCHSTE SCHRITTE

1. **User-Entscheidung**: Welcher Feldname soll verwendet werden?
   - `"ColumnControls"` (spezifisch für Spalten)
   - `"controls"` (allgemein für alle Controls)

2. **Einmalige Änderung**: Nur eine Stelle anpassen
   - Entweder GCS (1 Zeile)
   - Oder View-Manager (6 Zeilen)

3. **App-Neustart**: Controls werden gespeichert
   - `first_call=True` triggert Persistierung
   - GCS baut Projektionen mit allen Controls
   - **name_original** und **name_show** erscheinen automatisch!

4. **Keine weitere Änderung**: System läuft dann automatisch
   - Neue Spalten werden immer erkannt und hinzugefügt
   - Projektionen aktualisieren sich automatisch
   - "Es ist doch so einfach" - genau wie gewünscht! ✅
