# GCS Projektion-Architektur - Antwort auf User-Frage

## User-Frage
"Wenn wir mehrere Views haben wie werden diese Projektiontables unterschieden? Projektiontables gehören logisch gesehen zur View und nicht in die zentrale Systemsteuerung, da es ja mehrere Views parallel geben kann... oder sehe ich da etwas falsch?"

## Antwort: JA, Projektiontables SIND pro View!

### ✅ Architektur ist KORREKT

Die Projektiontables werden **PRO VIEW_GUID** unterschieden:

```python
# pdvm_central_systemsteuerung.py Zeile 656
self._projection_tables = {}  # Dictionary!

# Zeile 658: KEY = view_guid
if view_guid not in self._projection_tables:
    self._build_projection_tables(view_guid)

# Zeile 680: Zugriff mit view_guid
view_tables = self._projection_tables.get(view_guid)
```

### Wie funktioniert die Unterscheidung?

**Dictionary-Struktur:**
```python
self._projection_tables = {
    'view-guid-1': [table0, table1, ..., table9],  # 10-Element Array für View 1
    'view-guid-2': [table0, table1, ..., table9],  # 10-Element Array für View 2
    'view-guid-3': [table0, table1, ..., table9],  # 10-Element Array für View 3
}
```

**Jede View hat:**
- Eigene Controls (geladen aus GCS Database mit view_guid als Schlüssel)
- Eigene Projektiontables (10 verschiedene für Standard/Expert/etc.)
- Eigene Filter-Einstellungen (in app_db mit view_guid)

### Control-Speicherung PRO VIEW

```python
# Zeile 734 in pdvm_central_systemsteuerung.py
controls, _ = self.db.get_value(view_guid, "controls")
```

Die Controls werden **MIT view_guid als Gruppe** gespeichert, daher sind sie pro View getrennt!

### Warum ist GCS trotzdem richtig?

**GCS = Global Control System** bedeutet:
- **Zentrale Verwaltung** der Projektion-Logik (Expert Mode, Sortierung, etc.)
- **Aber**: Daten sind **PRO VIEW** gespeichert (via view_guid als Dictionary-Key)
- **Vorteil**: Eine zentrale Stelle für die Projektion-Logik statt in jeder View dupliciert

### Parallele Views - Kein Problem!

Wenn 3 Views parallel offen sind:
```python
view1 = get_view_pipeline('guid-1', matrix_manager1)
view2 = get_view_pipeline('guid-2', matrix_manager2)  
view3 = get_view_pipeline('guid-3', matrix_manager3)

# Jede bekommt EIGENE Projektion
proj1 = gcs().get_projection_table('guid-1', 'table')  # → ['uid_show', 'name_show', ...]
proj2 = gcs().get_projection_table('guid-2', 'table')  # → ['datum_show', 'betrag_show', ...]
proj3 = gcs().get_projection_table('guid-3', 'table')  # → ['produkt_show', 'preis_show', ...]
```

## Fazit

✅ **DU SIEHST NICHTS FALSCH!**

Die Architektur ist korrekt:
- Projektiontables SIND pro View (via view_guid)
- GCS ist nur der **zentrale Manager** (Single Responsibility)
- Jede View hat eigene Controls, eigene Projektion, eigene Filter

## Problem: Warum sind name_original/name_show nicht sichtbar?

**Ursache**: Controls werden korrekt erstellt (Zeile 763 in pdvm_view_daten_manager.py), ABER:

**Persistierung passiert nur wenn:**
```python
if found_new_controls and self.first_call:
    # Speichern in GCS
    gcs().set_value(gruppe=self.view_guid, feld="ColumnControls", wert=persist_map, ab_zeit=1001.0)
```

**Mögliche Gründe:**
1. `first_call` war bereits `False` beim ersten Start
2. `found_new_controls` war `False` (Controls wurden als "existierend" erkannt)
3. GCS hat die Controls noch nicht in die Projektion übernommen

**Lösung**: App-Neustart mit Logging aktiviert, um zu sehen ob Controls gespeichert werden.
