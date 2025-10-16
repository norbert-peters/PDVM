# KORREKTE BASISMATRIX-ERSTELLUNG - MIGRATION GUIDE

## 🎯 Problem

Die aktuelle Implementierung in `pdvm_view_daten_manager.py` **initialisiert PdvmCentralDatenbank mehrfach** und verwendet **nicht die bewährte Original-Logik**.

## ✅ Korrekte Logik (aus pdvm_view_dialog.py)

### Schritt 1: Alle Datensätze EINMAL lesen

```python
# Einmaliges Lesen ALLER Datensätze (außer 0000...-GUID)
data_db = PdvmCentralDatenbank(
    db_name="PdvmManager.db",
    table_name=self.view_table,
    guid=None  # Keine GUID = Lese-Modus
)

all_records = data_db.lesen_alle_ohne_system(limit=limit)
# all_records = [{'uid': '<guid>', 'daten_dict': {...}}, ...]
```

### Schritt 2: EINE temp_instance für ALLE Datensätze

```python
# NUR EINMAL initialisieren - NICHT pro Datensatz!
temp_instance = PdvmCentralDatenbank(
    db_name="PdvmManager.db",
    table_name=self.view_table,
    guid=None  # Ohne GUID = für set_data nutzbar
)

# Einmal DateTime-Formatter initialisieren
temp_dt = Pdvm_DateTime("DEU")  # Oder aus GCS
```

### Schritt 3: Pro Datensatz - set_data + get_value

```python
for record in all_records:
    guid = record['uid']
    daten_dict = record['daten_dict']
    
    # === KRITISCH: set_data befüllt temp_instance ===
    temp_instance.set_data(daten_dict, guid)
    
    # Jetzt können wir stichtagsgenau Daten holen!
    # get_value gibt Tupel zurück: (wert, abdatum)
    result = temp_instance.get_value(gruppe, feld, gcs.st_inst.PdvmDateTime)
    
    # Tupel auspacken
    if isinstance(result, tuple) and len(result) >= 2:
        wert, abdatum = result[0], result[1]
    else:
        wert, abdatum = result, None
    
    # === 3-EBENEN BEFÜLLEN ===
    row_data[control_key] = wert  # EBENE 1
    row_data[f"{control_key}_abdatum"] = abdatum  # EBENE 2
    row_data[f"{control_key}_formatiertes_abdatum"] = format_abdatum(abdatum, temp_dt)  # EBENE 3
```

### Schritt 4: _original Felder (alle Controls)

```python
# Sortiere Controls: Basis-Felder vor Zusatzfeldern
def sort_key(control_key):
    control_config = controls_config.get(control_key, {})
    control_type = control_config.get('type', '')
    if control_type in ['date_alter', 'date_jahr', 'date_monat', 'date_tag']:
        return 1  # Zusatzfelder später
    else:
        return 0  # Basis-Felder zuerst

original_controls = [(k, v) for k, v in controls_config.items() 
                   if v.get('control_type') == 'original' and k != 'uid_original']
sorted_controls = sorted(original_controls, key=lambda x: sort_key(x[0]))

# Durchlaufe sortierte Controls
for control_key, control_config in sorted_controls:
    feld = control_config.get('feld')
    gruppe = control_config.get('gruppe', 'SYSTEM')
    control_type = control_config.get('type', '')
    
    # SPEZIALFALL: Date-Zusatzfelder (alter, jahr, etc.)
    if control_type in ['date_alter', 'date_jahr', 'date_monat', 'date_tag']:
        # Basis-Feld finden
        base_field = control_key.replace('_original', '').replace(f'_{control_type.replace("date_", "")}', '')
        base_original = f"{base_field}_original"
        base_wert = row_data.get(base_original)
        
        if base_wert and base_wert != 1001.0:
            temp_dt.PdvmDateTime = float(base_wert)
            
            if control_type == 'date_alter':
                calculated_value = str(temp_dt.calc_alter(gcs.stichtag))
            elif control_type == 'date_jahr':
                calculated_value = str(temp_dt.Year)
            elif control_type == 'date_monat':
                calculated_value = str(temp_dt.Month)
            elif control_type == 'date_tag':
                calculated_value = str(temp_dt.Day)
            
            row_data[control_key] = calculated_value
        else:
            row_data[control_key] = ""
        
        # Date-Zusatzfelder haben kein eigenes Abdatum
        row_data[f"{control_key}_abdatum"] = None
        row_data[f"{control_key}_formatiertes_abdatum"] = None
        continue
    
    # NORMALFALL: Basis-Feld aus DB
    if feld:
        result = temp_instance.get_value(gruppe, feld, gcs.st_inst.PdvmDateTime)
        
        if isinstance(result, tuple) and len(result) >= 2:
            wert, abdatum = result[0], result[1]
        else:
            wert, abdatum = result, None
        
        # === 3-EBENEN BEFÜLLEN ===
        row_data[control_key] = wert
        row_data[f"{control_key}_abdatum"] = abdatum
        
        if abdatum:
            temp_dt.PdvmDateTime = float(abdatum)
            formatiert = temp_dt.FormTimeStamp
            row_data[f"{control_key}_formatiertes_abdatum"] = formatiert
        else:
            row_data[f"{control_key}_formatiertes_abdatum"] = None
```

### Schritt 5: _show Felder (separate Schleife)

```python
# NACH _original Feldern: Befülle _show Felder
for control_key, control_config in controls_config.items():
    if control_config.get('control_type') != 'show':
        continue
    
    original_key = control_key.replace('_show', '_original')
    
    # SPEZIALFALL: uid_show (erste 8 Zeichen)
    if control_key == 'uid_show':
        original_guid = row_data.get('uid_original')
        if original_guid and len(original_guid) >= 8:
            row_data[control_key] = f"{original_guid[:8]}..."
        else:
            row_data[control_key] = ""
        row_data[f"{control_key}_abdatum"] = None
        row_data[f"{control_key}_formatiertes_abdatum"] = None
        continue
    
    # SPEZIALFALL: Date-Zusatzfelder - direkt kopieren
    control_type = control_config.get('type', '')
    if control_type in ['date_alter', 'date_jahr', 'date_monat', 'date_tag']:
        row_data[control_key] = row_data.get(original_key, "")
        row_data[f"{control_key}_abdatum"] = None
        row_data[f"{control_key}_formatiertes_abdatum"] = None
        continue
    
    # SPEZIALFALL: Date-Felder - formatieren
    if control_type == 'date':
        original_wert = row_data.get(original_key)
        if original_wert and original_wert != 1001.0:
            temp_dt.PdvmDateTime = float(original_wert)
            row_data[control_key] = temp_dt.Date
        else:
            row_data[control_key] = ""
        
        # Abdatum von original kopieren
        row_data[f"{control_key}_abdatum"] = row_data.get(f"{original_key}_abdatum")
        row_data[f"{control_key}_formatiertes_abdatum"] = row_data.get(f"{original_key}_formatiertes_abdatum")
        continue
    
    # SPEZIALFALL: Dropdown - übersetzen
    if control_type == 'dropdown':
        original_wert = row_data.get(original_key)
        if original_wert:
            dropdown_config = control_config.get('dropdown', {})
            dropdown_guid = dropdown_config.get('key', '')
            dropdown_gruppe = dropdown_config.get('value', '')
            
            if dropdown_guid:
                translated = gcs.translate_dropdown_value(dropdown_guid, str(original_wert), dropdown_gruppe)
                row_data[control_key] = translated
            else:
                row_data[control_key] = str(original_wert)
        else:
            row_data[control_key] = ""
        
        # Abdatum von original kopieren
        row_data[f"{control_key}_abdatum"] = row_data.get(f"{original_key}_abdatum")
        row_data[f"{control_key}_formatiertes_abdatum"] = row_data.get(f"{original_key}_formatiertes_abdatum")
        continue
    
    # NORMALFALL: Wert + alle 3 Ebenen kopieren
    row_data[control_key] = row_data.get(original_key, "")
    row_data[f"{control_key}_abdatum"] = row_data.get(f"{original_key}_abdatum")
    row_data[f"{control_key}_formatiertes_abdatum"] = row_data.get(f"{original_key}_formatiertes_abdatum")
```

## 📊 Vorteile dieser Logik

1. **Einmaliges DB-Lesen**: Alle Daten in einem Rutsch
2. **Eine temp_instance**: Nur einmal initialisiert, für alle Datensätze wiederverwendet
3. **Stichtags-Wechsel**: Kein DB-Zugriff nötig - nur `set_data()` auf gespeicherten Daten
4. **Performance**: Bei 1000 Datensätzen massiver Unterschied!
5. **3-Ebenen garantiert**: Durch Suffix-Pattern (`__abdatum`, `__formatiert`)

## 🚫 Fehler in aktueller Implementierung

```python
# ❌ FALSCH - Pro Datensatz neue Instanz!
for record in all_records:
    working_db = PdvmCentralDatenbank(...)  # FEHLER!
    working_db.set_data(...)
```

```python
# ✅ KORREKT - Eine Instanz für alle!
temp_instance = PdvmCentralDatenbank(...)
for record in all_records:
    temp_instance.set_data(...)  # Überschreibt interne Daten
```

## 🔄 Stichtags-Wechsel

```python
# Bei Stichtags-Wechsel: Nur set_data neu aufrufen!
for record in all_records:
    guid = record['uid']
    daten_dict = record['daten_dict']
    
    # set_data mit GLEICHEN Daten, aber neuem Stichtag in GCS
    temp_instance.set_data(daten_dict, guid)
    
    # get_value berücksichtigt automatisch neuen Stichtag
    result = temp_instance.get_value(gruppe, feld, gcs.st_inst.PdvmDateTime)
```

**Kein erneutes Lesen aus Datenbank nötig!**

## 🎯 Optimierungspotential

Die Logik ist bereits optimal! Die einzigen möglichen Verbesserungen:

### 1. Caching der all_records
```python
# Speichere all_records für Stichtags-Wechsel
self._cached_all_records = all_records
```

### 2. Parallel-Processing (optional, für sehr große Tables)
```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(process_record, record) for record in all_records]
    results = [f.result() for f in futures]
```

Aber für normale Größen (< 10.000 Datensätze) ist die aktuelle Logik perfekt!

---

**STATUS**: Diese Logik muss in `pdvm_view_daten_manager.py._load_records_data()` implementiert werden!
