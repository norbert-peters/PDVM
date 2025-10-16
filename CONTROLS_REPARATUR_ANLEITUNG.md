# Controls-Daten Reparatur Anleitung

## Problem identifiziert

Die Spalten-Reihenfolge wird nicht korrekt projiziert, weil:

1. **Inkonsistente Order-Felder:**
   - `display_order` und `expert_order` waren nicht synchronisiert
   - Column Management Dialog aktualisierte nur eines der beiden Felder
   - Projektions-Tabellen erwarten konsistente `display_order` Werte

2. **Alte/Doppelte Daten:**
   - Möglicherweise alte Controls-Daten in der systemsteuerung DB
   - Duplikate oder fehlende Order-Werte

## Lösung implementiert

### 1. Diagnose-Script erstellt

**`diagnose_controls_data.py`**
- Analysiert Controls-Daten für eine View
- Zeigt alle Spalten mit ihren Properties
- Identifiziert Probleme:
  - Fehlende `display_order` Werte
  - Fehlende `expert_order` Werte
  - Duplikate
  - Lücken in der Sortierung

**Verwendung:**
```bash
# Mit Python Environment
python diagnose_controls_data.py

# Script zeigt automatisch alle Views und analysiert die erste
```

### 2. Reparatur-Script erstellt

**`repair_controls_data.py`**
- Repariert automatisch:
  - Setzt fehlende `display_order` Werte
  - Behebt Duplikate
  - Synchronisiert `expert_order` mit `display_order`
  - Baut Projektions-Tabellen neu auf

**Verwendung:**
```bash
# DRY RUN (Simulation, keine Änderungen)
python repair_controls_data.py

# LIVE (Speichert Änderungen)
python repair_controls_data.py --live
```

**Empfohlener Ablauf:**
1. Erst DRY RUN ausführen und Änderungen prüfen
2. Wenn OK, dann mit `--live` ausführen

### 3. Column Management Dialog korrigiert

**Änderung in `column_management_dialog.py`:**

```python
# VORHER (FALSCH):
order_field = 'expert_order' if gcs.expert_mode else 'display_order'
all_controls[column_key][order_field] = new_order_value  # Nur EINS!

# NACHHER (KORREKT):
all_controls[column_key]['display_order'] = new_order_value  # BEIDE
all_controls[column_key]['expert_order'] = new_order_value   # synchronisiert!
```

**Vorteil:**
- `display_order` und `expert_order` bleiben IMMER synchron
- Keine Inkonsistenzen mehr möglich
- Projektions-Tabellen funktionieren zuverlässig

## Schritt-für-Schritt Reparatur

### Schritt 1: Diagnose ausführen

```bash
cd C:\Users\norbe\OneDrive\Dokumente\MyApplication
.venv\Scripts\python.exe diagnose_controls_data.py
```

**Prüfen Sie die Ausgabe:**
- ❌ Spalten ohne `display_order`?
- ❌ Duplikate bei `display_order`?
- ⚠️  Spalten ohne `expert_order`?

### Schritt 2: Reparatur (Simulation)

```bash
.venv\Scripts\python.exe repair_controls_data.py
```

**Ausgabe prüfen:**
- Anzahl der Änderungen
- Welche Spalten werden geändert
- Sehen die Änderungen sinnvoll aus?

### Schritt 3: Reparatur (Live)

```bash
.venv\Scripts\python.exe repair_controls_data.py --live
```

**Das Script:**
1. Repariert alle Controls
2. Baut Projektions-Tabellen neu auf
3. Speichert alles persistent

### Schritt 4: Anwendung testen

1. Anwendung starten
2. View öffnen
3. Spalten verwalten → Reihenfolge ändern → "Spalten übernehmen"
4. ✅ Prüfen: Tabelle zeigt neue Reihenfolge korrekt

## Alternative: Manuelle Bereinigung

Wenn Sie die Daten komplett neu aufbauen wollen:

### Methode A: Über Python Script

```python
from pdvm_central_systemsteuerung import get_gcs

gcs = get_gcs()
view_guid = "IHRE-VIEW-GUID"

# Controls löschen (VORSICHT!)
gcs.db.data[view_guid].pop('controls', None)
gcs.db.save_all_values()

print(f"✅ Controls für {view_guid} gelöscht")
print("⚠️  Beim nächsten View-Start werden Controls neu generiert")
```

### Methode B: Datenbank direkt bearbeiten

1. Öffnen Sie `datenbank.db` (Backup erstellen!)
2. Suchen Sie die Tabelle `systemsteuerung`
3. Löschen Sie den Eintrag für `gruppe=view_guid, feld='controls'`
4. Beim nächsten Start werden Controls neu generiert

**⚠️  VORSICHT:** 
- Alle benutzerdefinierten Spalten-Einstellungen gehen verloren
- Nur als letztes Mittel verwenden

## Architektur-Fix

Die Projektions-Architektur wurde ebenfalls korrigiert:

```python
# pdvm_central_systemsteuerung.py - _build_projection_tables()

# VORHER (INKONSISTENT):
all_controls_expert = sorted(all_controls, key=lambda x: (x['expert_order'], x['display_order']))
projections = {
    'change_expert': [c['key'] for c in all_controls_expert]  # Sortiert nach expert_order
}

# NACHHER (KONSISTENT):
all_controls_sorted = sorted(all_controls, key=lambda x: x['display_order'])
projections = {
    'change_expert': [c['key'] for c in all_controls_sorted]  # ALLES nach display_order!
}
```

**Begründung:**
- Nur EINE Sortierungs-Quelle: `display_order`
- `expert_order` wird nur für Kompatibilität beibehalten
- Vereinfacht Logik massiv
- Keine Inkonsistenzen mehr möglich

## Zusammenfassung

**Änderungen:**
1. ✅ `diagnose_controls_data.py` - Analyse-Tool
2. ✅ `repair_controls_data.py` - Reparatur-Tool
3. ✅ `column_management_dialog.py` - Synchronisiert beide Order-Felder
4. ✅ `pdvm_central_systemsteuerung.py` - Projektionen nur nach `display_order`

**Testing:**
1. Diagnose ausführen
2. Reparatur (dry run) ausführen
3. Reparatur (live) ausführen
4. Anwendung testen
5. Spalten-Reihenfolge ändern
6. ✅ Neue Reihenfolge wird korrekt angezeigt

**Ergebnis:**
- ✅ Konsistente Order-Felder
- ✅ Keine Duplikate
- ✅ Projektionen funktionieren korrekt
- ✅ Spalten-Reihenfolge wird persistent gespeichert
- ✅ View zeigt korrekte Reihenfolge
