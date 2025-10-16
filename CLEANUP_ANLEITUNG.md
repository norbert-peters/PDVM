# Controls Bereinigung - Kurzanleitung

## Problem
Die Spalten-Reihenfolge wird nicht korrekt angezeigt, weil alte/inkonsistente Controls-Daten in der Datenbank vorhanden sind.

## Lösung
Alte Controls-Daten löschen → werden beim nächsten View-Start automatisch neu generiert.

## Tool: cleanup_controls_db.py

**Vorteil:** Kein Login erforderlich! Arbeitet direkt auf der Datenbank.

### Verwendung

```bash
cd C:\Users\norbe\OneDrive\Dokumente\MyApplication
.venv\Scripts\python.exe cleanup_controls_db.py
```

### Funktionen

1. **Views auflisten:**
   - Zeigt alle Views mit Controls-Daten
   - Nummerierte Liste

2. **View analysieren:**
   - Eingabe: View-Nummer (z.B. `1`)
   - Zeigt Statistiken und Probleme

3. **Controls für eine View löschen:**
   - Eingabe: `d`
   - Dann View-Nummer auswählen
   - Bestätigung erforderlich

4. **Controls für ALLE Views löschen:**
   - Eingabe: `all`
   - Bestätigung erforderlich
   - Löscht alle Controls-Daten

5. **Beenden:**
   - Eingabe: `q`

### Beispiel-Ablauf

```
🗑️  PDVM CONTROLS BEREINIGUNG (Direkter DB-Zugriff)
================================================================================

Gefundene Views: 1

1. 54073c2c-0efa-4979-8900-2bd1c53d5014

Optionen:
  [1-N] - Analysiere spezifische View
  [d]   - Lösche Controls für spezifische View
  [all] - Lösche Controls für ALLE Views
  [q]   - Beenden

Wählen Sie eine Option: 1

================================================================================
📊 Controls für View: 54073c2c-0efa-4979-8900-2bd1c53d5014
================================================================================

Anzahl Controls: 62

Statistik:
  - Controls mit show=true: 7
  - Controls ohne display_order: 15
  - Duplikate bei display_order: 8

⚠️  PROBLEME GEFUNDEN!
   Empfehlung: Controls löschen und neu generieren lassen

Wählen Sie eine Option: d

Welche View? (Nummer eingeben)
1. 54073c2c-0efa-4979-8900-2bd1c53d5014

View-Nummer: 1

⚠️  WARNUNG: Controls für View '54073c2c-0efa-4979-8900-2bd1c53d5014' werden gelöscht!
   Alle benutzerdefinierten Spalten-Einstellungen gehen verloren.
   Beim nächsten View-Start werden Controls neu generiert.

Fortfahren? (ja/nein): ja

✅ Controls für View '54073c2c-0efa-4979-8900-2bd1c53d5014' erfolgreich gelöscht
   Gelöschte Einträge: 1
```

### Nach der Bereinigung

1. **Anwendung starten**
   ```bash
   .venv\Scripts\python.exe main.py
   ```

2. **View öffnen**
   - Controls werden automatisch neu generiert
   - Mit Default-Werten initialisiert

3. **Spalten verwalten**
   - Reihenfolge anpassen
   - Show/Hide einstellen
   - "Spalten übernehmen" klicken

4. **Prüfen**
   - ✅ Neue Reihenfolge wird korrekt angezeigt
   - ✅ Änderungen werden gespeichert

## Alternative: Manuelle Bereinigung

Falls Sie die Datenbank manuell bearbeiten wollen:

### SQLite Browser verwenden

1. **Tool installieren:** https://sqlitebrowser.org/
2. **Datenbank öffnen:** `datenbank.db`
3. **Tabelle öffnen:** `systemsteuerung`
4. **Filter setzen:** `feld = 'controls'`
5. **Zeilen löschen** (für gewünschte Views)
6. **Speichern**

### SQL-Befehl (direkt)

```sql
-- Alle Controls löschen
DELETE FROM systemsteuerung WHERE feld = 'controls';

-- Controls für spezifische View löschen
DELETE FROM systemsteuerung 
WHERE gruppe = '54073c2c-0efa-4979-8900-2bd1c53d5014' 
  AND feld = 'controls';
```

## Wichtig

**Was passiert beim Löschen:**
- ✅ Controls werden beim nächsten View-Start neu generiert
- ❌ Benutzerdefinierte Spalten-Einstellungen gehen verloren (Reihenfolge, Show/Hide)
- ✅ Alle Inkonsistenzen werden behoben
- ✅ System startet mit "sauberen" Controls

**Was bleibt erhalten:**
- ✅ Filter-Einstellungen (in `anwendungsdaten`)
- ✅ Sort-Einstellungen
- ✅ Alle anderen View-Einstellungen
- ✅ Alle Datensätze

## Nach dem Fix

Die korrigierte Spalten-Verwaltung:
- ✅ Aktualisiert BEIDE Order-Felder (`display_order` UND `expert_order`)
- ✅ Keine Inkonsistenzen mehr möglich
- ✅ Projektionen funktionieren zuverlässig
- ✅ Spalten-Reihenfolge wird korrekt gespeichert und angezeigt

## Zusammenfassung

1. **Tool ausführen:** `python cleanup_controls_db.py`
2. **Controls löschen** (für betroffene Views)
3. **Anwendung starten** (Controls werden neu generiert)
4. **Spalten anpassen** (neue Reihenfolge wird korrekt gespeichert)
5. **Fertig!** System arbeitet jetzt konsistent
