# 🎉 NAME-SPALTE IMPLEMENTIERUNG - ZUSAMMENFASSUNG

**Datum**: 26.10.2025  
**Feature**: `name`-Spalte in Datenbank + View-Integration + Viewtable History

---

## 📋 ÜBERSICHT

Die `name`-Spalte wurde **analog zu `uid`** als **System-Spalte** implementiert:
- Verfügbar in **allen Tabellen**
- Automatische Migration bestehender Tabellen
- 3-Ebenen-Struktur in Views (`name_original`, `name_show`)
- **Viewtable History** zeigt jetzt "GUID + Name" statt nur GUID

---

## ✅ IMPLEMENTIERTE KOMPONENTEN

### 1. **PdvmDatenbank** (`pdvm_datenbank.py`)

**Datenbank-Schema erweitert**:
```sql
CREATE TABLE IF NOT EXISTS {table_name} (
    uid TEXT PRIMARY KEY,
    name TEXT DEFAULT '',        -- ✨ NEU
    daten TEXT NOT NULL,
    last_modified TEXT NOT NULL DEFAULT ''
)
```

**Automatische Migration**:
- Prüft bei Initialisierung ob `name`-Spalte existiert
- Fügt Spalte automatisch hinzu falls fehlend: `ALTER TABLE {table_name} ADD COLUMN name TEXT DEFAULT ''`

**Neue Methoden**:
```python
def get_name(self, guid: str) -> Optional[str]:
    """Liest 'name' Wert für GUID"""
    # Returns: Name-String oder None

def set_name(self, guid: str, name_value: str) -> bool:
    """Setzt 'name' Wert für GUID"""
    # Returns: True bei Erfolg, False wenn GUID nicht existiert
```

---

### 2. **PdvmCentralDatenbank** (`pdvm_central_datenbank.py`)

**Business-Logic-Layer**:
```python
def get_name(self, guid: Optional[str] = None) -> Optional[str]:
    """
    Liest 'name' Wert.
    Fallback auf self.guid wenn kein Parameter übergeben.
    """
    target_guid = guid if guid else self.guid
    return self._database.get_name(target_guid)

def set_name(self, name_value: str, guid: Optional[str] = None) -> bool:
    """
    Setzt 'name' Wert.
    Fallback auf self.guid wenn kein Parameter übergeben.
    """
    target_guid = guid if guid else self.guid
    return self._database.set_name(target_guid, name_value)
```

---

### 3. **View-Pipeline** (`pdvm_view_daten_manager.py`)

**System-Spalte `name_original`** (analog zu `uid_original`):
```python
# In get_all_columns() - Zeile ~710
name_orig_col = {
    'name': 'name_original',
    'type': 'string',
    'gruppe': 'SYSTEM',
    'feld': 'NAME',
    'show': False,  # Standard: unsichtbar
    'expertOrder': order_counter,
    'displayOrder': order_counter,
    'field_config': {'feld': 'NAME', 'name': 'Name', 'type': 'string'},
    'spaltenueberschrift': 'Name (orig.)'
}
```

**Automatische `name_show` Generierung**:
- Wird automatisch aus `name_original` erstellt (wie bei allen `_original` Spalten)
- Standard: `show=True` (sichtbar wenn Control definiert)

**3-Ebenen-Struktur**:
```python
# In create_basis_matrix() - Zeile ~1075
# EBENE 1: Wert
row_record['name_original'] = name_value if name_value else ""

# EBENE 2: AB-Datum (roh) - None für System-Felder
row_record['name_original_abdatum'] = None

# EBENE 3: Formatiertes AB-Datum - None für System-Felder
row_record['name_original_formatiertes_abdatum'] = None
```

**Daten-Befüllung**:
```python
# Hole Name aus DB
name_value = temp_instance.get_name(data_guid)
row_record['name_original'] = name_value if name_value else ""
```

**Integration in Logik**:
- Ausschluss in Filter-Verarbeitung (wie `uid_original`)
- Typ-Erkennung: `col_name.startswith(('uid', 'name'))`
- Spalten-Header: "Name (orig.)" / "Name"
- Leere-Zeilen-Prüfung: `name_original` und `name_show` werden ignoriert

---

### 4. **Viewtable History** (`pdvm_input_control_history_dialog.py`)

**Verbesserte Anzeige**:

**VORHER**:
```
0c16bbb8-bd73-4dd9-9bc2-3f50e0df216a
```

**JETZT**:
```
0c16bbb8... (Sparkasse Köln Hauptkonto)
```

**Implementierung**:
```python
elif self.control_type == 'viewtable':
    # Viewtable: wert ist eine GUID
    # Zeige "GUID + Name" für bessere Lesbarkeit
    if wert:
        guid_str = str(wert)
        # Hole Name aus DB (wenn verfügbar)
        name_str = self._get_name_for_viewtable_guid(wert)
        if name_str:
            formatted_value = f"{guid_str[:8]}... ({name_str})"
        else:
            formatted_value = f"{guid_str[:8]}..."
    else:
        formatted_value = "<Keine Auswahl>"
    original_raw_value = wert
```

**Hilfsmethode**:
```python
def _get_name_for_viewtable_guid(self, guid):
    """
    Holt 'name' Wert für GUID aus referenzierter Tabelle.
    
    - Liest viewtable_config aus field_config
    - Extrahiert table_name
    - Erstellt PdvmCentralDatenbank Instanz
    - Ruft get_name(guid) auf
    - Gibt Name zurück oder None
    """
```

**Fehlerbehandlung**:
- Falls `viewtable_config` fehlt → zeigt nur gekürzte GUID
- Falls `table_name` fehlt → zeigt nur gekürzte GUID
- Falls `get_name()` None zurückgibt → zeigt nur gekürzte GUID
- Exceptions werden geloggt, aber Dialog bleibt funktional

---

## 🧪 TESTS

### Test 1: PdvmDatenbank
```
✅ Datensatz erstellt
✅ set_name(): True
✅ get_name(): 'Max Mustermann'
✅ get_name() nach Update: 'Erika Musterfrau'
✅ Testdaten gelöscht
```

### Test 2: PdvmCentralDatenbank
```
✅ Datensatz erstellt
✅ set_name(): True
✅ get_name(): 'Dr. Schmidt'
✅ get_name() mit self.guid: 'Prof. Müller'
✅ Testdaten gelöscht
```

### Test 3: View-Code-Struktur
```
✅ name_original Spalten-Def vorhanden
✅ name_show Spalten-Logik vorhanden
✅ name_show in Code vorhanden
✅ 3-Ebenen name_original vorhanden
✅ get_name Aufruf vorhanden

Statistik:
  - 'name_original' Vorkommen: 27
  - 'name_show' Vorkommen: 10
```

### Test 4: Viewtable History Name-Anzeige
```
✅ Referenz-Datensatz erstellt
✅ Name gesetzt: 'Sparkasse Köln Hauptkonto'
✅ get_name(): 'Sparkasse Köln Hauptkonto'
✅ Formatierter Wert: '0c16bbb8... (Sparkasse Köln Hauptkonto)'
✅ Testdaten gelöscht
```

**ALLE TESTS BESTANDEN** ✅

---

## 📖 NUTZUNG

### In Datenbank-Layer

```python
# PdvmDatenbank
db = PdvmDatenbank("personenstamm")
db.set_name(guid, "Max Mustermann")
name = db.get_name(guid)

# PdvmCentralDatenbank
central = PdvmCentralDatenbank("finanzstamm", guid)
central.set_name("Sparkasse Köln")  # Nutzt self.guid
name = central.get_name()            # Nutzt self.guid
```

### In Views/Controls

**viewdaten.json / framedaten.json**:
```json
{
  "feld": "NAME",
  "name": "Name",
  "type": "string",
  "gruppe": "SYSTEM"
}
```

Sobald Control definiert:
- `name_original` bleibt versteckt
- `name_show` wird automatisch sichtbar
- In Projektion verfügbar
- Sortierbar/Filterbar

### In Viewtable History

Automatisch aktiv wenn:
1. `viewtable_config` in field_config definiert ist
2. `table_name` in viewtable_config vorhanden
3. Referenzierter Datensatz hat `name`-Wert gesetzt

**Fallback**: Falls Name nicht verfügbar → zeigt nur gekürzte GUID

---

## 🔧 MIGRATION

**Automatisch beim App-Start**:
- Jede Tabellen-Initialisierung prüft `name`-Spalte
- Falls fehlend: `ALTER TABLE` wird ausgeführt
- Bestehende Datensätze: `name` = "" (leerer String)
- **Keine manuelle Migration nötig!**

**Bestehende Daten befüllen**:
```python
# Beispiel: Personenstamm mit Familienname als Name
db = PdvmCentralDatenbank("personenstamm")
for record in db.get_all_records():
    guid = record['uid']
    daten = record['daten']
    familienname = daten.get('PERSDATEN', {}).get('familienname', '')
    if familienname:
        db.set_name(familienname, guid)
        db.save_all_values()
```

---

## 📁 GEÄNDERTE DATEIEN

1. **pdvm_datenbank.py**
   - Schema: `name TEXT DEFAULT ''`
   - Migration: ALTER TABLE wenn Spalte fehlt
   - Methoden: `get_name()`, `set_name()`

2. **pdvm_central_datenbank.py**
   - Wrapper: `get_name()`, `set_name()` mit self.guid Fallback

3. **pdvm_view_daten_manager.py**
   - System-Spalte: `name_original` Definition
   - 3-Ebenen: Befüllung in `create_basis_matrix()`
   - Show-Spalte: `name_show` in `_fill_show_columns()`
   - Integration: Filter-Ausschluss, Typ-Erkennung, Header

4. **pdvm_input_control_history_dialog.py**
   - Formatierung: "GUID + Name" statt nur GUID
   - Hilfsmethode: `_get_name_for_viewtable_guid()`
   - Fehlerbehandlung: Graceful Fallback

---

## 🎯 VORTEILE

✅ **Benutzerfreundlichkeit**: Name statt kryptische GUID  
✅ **Konsistenz**: Analog zu uid-Architektur  
✅ **Automatisch**: Kein manuelles Eingreifen nötig  
✅ **Rückwärtskompatibel**: Bestehende Daten funktionieren weiter  
✅ **Flexibel**: Name kann in Views ein-/ausgeblendet werden  
✅ **Performant**: Nur ein zusätzlicher DB-Abruf bei History-Anzeige

---

**IMPLEMENTIERUNG ABGESCHLOSSEN** ✅  
**AUTOR**: GitHub Copilot + Norbert Peters  
**DATUM**: 26.10.2025
