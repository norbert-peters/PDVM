# 🎯 Lineare DB-Architektur Wiederhergestellt

**Datum**: 04.12.2024  
**Status**: ✅ KOMPLETT UMGESETZT

## Ziel
Rückkehr zur strikten linearen Programmierung - SQLs nur intern in `PdvmDatenbank`, keine direkten SQL-Queries von außen.

## Änderungen

### ✅ 1. execute_query() entfernt
**Datei**: `pdvm_datenbank.py`

```python
# ❌ VORHER: Direkter SQL-Zugriff von außen möglich
db.execute_query("SELECT uid, name FROM sys_framedaten")

# ✅ JETZT: Nur definierte Methoden
db.alle_lesen()  # Liefert uid + name + daten + modified_at
```

**Begründung**: 
- SQLs sollen **nur intern** in PdvmDatenbank existieren
- Keine SQL-Queries außerhalb dieser Klasse
- Einfache, gleichartige Datenhaltung

### ✅ 2. alle_lesen() erweitert
**Datei**: `pdvm_datenbank.py`

```python
def alle_lesen(self):
    """
    Returns:
        list[dict]: [
            {
                'uid': '...',
                'name': '',           # ✅ NEU: Aus daten.ROOT.name extrahiert
                'daten': {...},
                'modified_at': 123.456
            }
        ]
    """
```

**Vorteile**:
- Kein JSON-Extrakt in SQL nötig
- Name wird aus `daten.ROOT.name` gelesen
- Konsistente Datenstruktur

### ✅ 3. created_at/modified_at automatisch
**Datei**: `pdvm_datenbank.py` → `speichern()`

```python
# ✅ AUTOMATISCH bei jedem Speichern:
if exists:
    # UPDATE: Nur modified_at
    UPDATE ... SET modified_at = ? ...
else:
    # INSERT: created_at + modified_at
    INSERT ... (created_at, modified_at) VALUES (?, ?) ...
```

**Regel**:
- `created_at`: Nur bei **INSERT** (neuer Datensatz)
- `modified_at`: Immer bei **jedem** Speichern
- Kein manuelles Setzen nötig

### ✅ 4. handler_test_dialog.py umgestellt
**Vorher**:
```python
query = "SELECT uid, name FROM sys_framedaten"
frames = db.execute_query(query)
for uid, name in frames:
    ...
```

**Nachher**:
```python
frames = db.alle_lesen()  # ✅ Einfach!
frames.sort(key=lambda f: f.get('name', ''))
for frame_dict in frames:
    uid = frame_dict['uid']
    name = frame_dict.get('name', '')
    ...
```

### ✅ 5. pdvm_config_editor_widget umgestellt
**Vorher**:
```python
query = """
    SELECT uid, json_extract(daten, '$.ROOT.BESCHREIBUNG_NAME') as name
    FROM {table_name}
    ...
"""
records = db.execute_query(query)
for uid, name in records:
    ...
```

**Nachher**:
```python
db = PdvmDatenbank(table_name)  # ✅ Table direkt angeben
records = db.alle_lesen()
records.sort(key=lambda r: r.get('name', ''))
for record in records:
    uid = record['uid']
    name = record.get('name', '')
    ...
```

## Architektur-Regeln (STRIKT)

### 1️⃣ SQLs nur intern in PdvmDatenbank
```python
# ✅ RICHTIG
db = PdvmDatenbank('sys_framedaten')
frames = db.alle_lesen()

# ❌ FALSCH
db.execute_query("SELECT * FROM ...")
```

### 2️⃣ Daten immer über definierte Methoden
```python
# Verfügbare Methoden:
db.speichern(guid, data)          # Einzelner Datensatz
db.lesen(guid)                     # Einzelner Datensatz
db.loeschen(guid)                  # Einzelner Datensatz
db.alle_lesen()                    # Alle Datensätze mit uid + name
db.get_name(guid)                  # Nur Name-Wert
db.set_name(guid, name)            # Name setzen
```

### 3️⃣ Verarbeitung über PdvmCentralDatenbank
```python
# View-Verarbeitung (pro Zeile):
for row in view_matrix:
    uid = row['uid']
    temp_db = PdvmCentralDatenbank(table_name, uid)  # Temporär
    wert, abdatum = temp_db.get_value(gruppe, feld, stichtag)
    # Verarbeitung...

# Einzelner Dialog:
dialog_db = PdvmCentralDatenbank(table_name, selected_uid)
dialog_db.set_value(gruppe, feld, new_value)
dialog_db.save_all_values()  # Speichert mit modified_at
```

### 4️⃣ created_at/modified_at automatisch
```python
# ✅ AUTOMATISCH - kein manuelles Setzen!
db.speichern(guid, data)  
# → created_at bei INSERT
# → modified_at bei UPDATE
```

## Vorteile der linearen Architektur

✅ **Einfachheit**: Keine SQL-Queries außerhalb PdvmDatenbank  
✅ **Konsistenz**: Alle Datenzugriffe über gleiche Methoden  
✅ **Wartbarkeit**: Änderungen nur an einer Stelle (PdvmDatenbank)  
✅ **Typsicherheit**: Klare Return-Typen (dict statt tuple)  
✅ **Automatismus**: Zeitstempel ohne manuellen Code

## Migration Complete! 🎉

Alle `execute_query()` Aufrufe entfernt und durch:
- `alle_lesen()` für Listen
- `lesen()` für einzelne Datensätze
- `PdvmCentralDatenbank` für Verarbeitung

**Keine SQL-Queries mehr außerhalb von PdvmDatenbank!**
