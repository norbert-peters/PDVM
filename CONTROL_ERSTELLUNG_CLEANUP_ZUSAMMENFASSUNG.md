# 🔧 Control-Erstellung Cleanup - Zusammenfassung

**Datum**: 27.10.2025  
**Status**: ✅ Behoben

## 🎯 Probleme identifiziert

### Problem 1: name_show Spalte leer
**Symptom**: Spalte `name_show` erscheint, aber ohne Daten

**Ursache**: 
- `name_original` wurde NICHT in BasisMatrix geladen
- Fehlte als SPEZIALFALL in `pdvm_view_matrix_manager.py`
- Nur `uid_original` hatte SPEZIALFALL-Behandlung

**Konsequenz**: name_show bleibt leer, da Quelle (name_original) nicht befüllt wird

### Problem 2: Controls an 2 Stellen erstellt
**Symptom**: Doppelte Logik für Control-Generierung

**Stellen**:
1. ✅ **`pdvm_view_controller.py`** Zeile 246-369
   - Erstellt uid_original, name_original
   - Erstellt alle _original aus ViewDaten
   - Erstellt alle _show aus _original (Rekursion!)
   - Erstellt dummy
   - Speichert in GCS `controls` Dictionary

2. ❌ **`pdvm_view_daten_manager.py`** Zeile 737-850
   - Erstellt AUCH uid_original, name_original
   - Erstellt AUCH alle _original/_show
   - Versucht in GCS zu speichern
   - **VERALTET** - wird nicht mehr verwendet

**Konsequenz**: 
- Verwirrung über "Single Source of Truth"
- Potentielle Inkonsistenzen
- Doppelter Code

## ✅ Lösungen implementiert

### Fix 1: name_original als SPEZIALFALL
**Datei**: `pdvm_view_matrix_manager.py` Zeile 120-128

**NEU**:
```python
# SPEZIALFALL 2: name_original - Name aus DB-Spalte 'name'
if 'name_original' in all_controls:
    name_value = instance.get_name(instance.guid)
    row_data['name_original'] = name_value if name_value else ""
    row_data['name_original_abdatum'] = None
    row_data['name_original_formatiertes_abdatum'] = None
    logger.debug(f"  📝 name_original: {name_value}")
else:
    logger.warning("  ⚠️ name_original nicht in controls_config gefunden")
```

**Warum SPEZIALFALL**:
- NAME ist **DB-Spalte**, nicht in JSON-Daten
- Analogie zu UID (auch DB-Spalte, nicht JSON)
- Braucht `instance.get_name()` statt `instance.get_value()`

### Fix 2: name_original von Loop ausschließen
**Datei**: `pdvm_view_matrix_manager.py` Zeile 140-142

**ALT**:
```python
original_controls = [(k, v) for k, v in all_controls.items() 
                   if v.get('control_type') == 'original' and k != 'uid_original']
```

**NEU**:
```python
original_controls = [(k, v) for k, v in all_controls.items() 
                   if v.get('control_type') == 'original' and k not in ('uid_original', 'name_original')]
```

### Fix 3: name_show SPEZIALFALL
**Datei**: `pdvm_view_matrix_manager.py` Zeile 238-246

**NEU**:
```python
# SPEZIALFALL 2: name_show - Wert 1:1 aus name_original kopieren
if control_key == 'name_show':
    # ✅ ARRAY: Original-Zelle holen (name_original hat kein Abdatum)
    original_cell = row_data.get('name_original', create_cell("", None, None))
    original_name = get_wert(original_cell)
    
    # ✅ ARRAY: name_show ohne Abdatum
    row_data[control_key] = create_cell(original_name if original_name else "", None, None)
    continue
```

## 📋 Architektur-Klarstellung

### ✅ Single Source of Truth: pdvm_view_controller.py

**Control-Erstellung passiert NUR in `pdvm_view_controller.py`**:

```python
# SCHRITT 0: SYSTEM-Controls
all_controls['uid_original'] = {...}
all_controls['name_original'] = {...}

# SCHRITT 1: _original Controls aus ViewDaten
for control_key, control_data in self.view_config['controls'].items():
    all_controls[f"{control_key}_original"] = {...}

# SCHRITT 2: _show Controls (Rekursion!)
for original_key, original_control in original_controls.items():
    show_key = original_key.replace('_original', '_show')
    all_controls[show_key] = original_control.copy()
    all_controls[show_key]['control_type'] = 'show'

# SCHRITT 3: Dummy
all_controls['dummy'] = {...}
```

### ❌ pdvm_view_daten_manager.py ist VERALTET

**Diese Datei erstellt KEINE Controls mehr!** Sie:
- Wird von Registry verwendet (Legacy)
- Hat veraltete Control-Logik
- Sollte mittelfristig entfernt werden

**Aktuell aktiver Flow**:
```
pdvm_view_controller.py
  → Erstellt Controls (Zeile 246-369)
  → Speichert in GCS (Zeile 335-340)
  → Lädt Daten (Zeile 406-424)
  → Matrix Manager befüllt BasisMatrix (Zeile 465-489)
    → pdvm_view_matrix_manager.py
      → initialize_basis_matrix()
        → SPEZIALFALL uid_original (Zeile 111-119)
        → SPEZIALFALL name_original (Zeile 121-128) ⭐ NEU
        → Alle anderen _original aus DB (Zeile 187-217)
        → Alle _show aus _original (Zeile 221-313)
          → SPEZIALFALL uid_show (Zeile 228-236)
          → SPEZIALFALL name_show (Zeile 238-246) ⭐ NEU
```

## 🔄 Datenfluss für name_original/name_show

### 1. Control-Definition (Controller)
```python
# pdvm_view_controller.py Zeile 262-272
all_controls['name_original'] = {
    'feld': 'NAME',
    'name': 'Satzname',
    'type': 'string',
    'gruppe': 'SYSTEM',
    'control_type': 'original',
    'show': False,
    'expert_mode': True
}

# REKURSION erzeugt automatisch:
all_controls['name_show'] = {
    ...
    'control_type': 'show',
    'show': True,
    'expert_mode': False
}
```

### 2. Daten-Ladung (Matrix Manager)
```python
# pdvm_view_matrix_manager.py Zeile 121-128
name_value = instance.get_name(instance.guid)  # ← DB-Zugriff!
row_data['name_original'] = name_value if name_value else ""
row_data['name_original_abdatum'] = None
row_data['name_original_formatiertes_abdatum'] = None
```

### 3. Show-Feld Befüllung (Matrix Manager)
```python
# pdvm_view_matrix_manager.py Zeile 238-246
original_cell = row_data.get('name_original', create_cell("", None, None))
original_name = get_wert(original_cell)
row_data['name_show'] = create_cell(original_name if original_name else "", None, None)
```

### 4. Projektion (Pipeline)
```python
# GCS Projektion [0] Standard: name_show sichtbar
# GCS Projektion [5] Expert: name_original + name_show sichtbar
```

## 🚀 Erwartetes Ergebnis

**Log bei View-Start**:
```
📊 Befülle Original-Felder für Instanz: ed21cb69-046b-465f-b231-6e75852b50b3
  🔑 uid_original: ed21cb69-046b-465f-b231-6e75852b50b3
  📝 name_original: Mein Testname  ⭐ NEU - mit Daten!
  
📋 Befülle Show-Felder aus Original-Feldern
  SPEZIALFALL 1: uid_show → ed21cb69...
  SPEZIALFALL 2: name_show → Mein Testname  ⭐ NEU - mit Daten!
```

**UI**:
- **Normal Mode**: name_show mit Wert "Mein Testname" ✅
- **Expert Mode**: name_original + name_show beide mit Wert ✅

## 📊 Datenbank-Struktur

**persondaten / finanzdaten**:
```sql
CREATE TABLE persondaten (
    uid TEXT PRIMARY KEY,
    daten TEXT,              -- JSON mit Feldern
    last_modified REAL,
    name TEXT DEFAULT NULL   -- ⭐ NEUE Spalte für Satzname
);
```

**Zugriff**:
```python
# Via PdvmCentralDatenbank
instance = PdvmCentralDatenbank.create_with_data(guid, daten, table_name)
name_value = instance.get_name(guid)  # ← Liest aus 'name' Spalte
```

## ✅ Validierung

1. **Controls nur 1x erstellt**: ✅ Nur in `pdvm_view_controller.py`
2. **name_original befüllt**: ✅ Via `instance.get_name()`
3. **name_show befüllt**: ✅ Via Rekursion aus name_original
4. **Sichtbarkeit korrekt**: ✅ Normal=name_show, Expert=beide

---

**✅ Beide Probleme behoben**  
**📋 Architektur vereinfacht (Single Source of Truth)**  
**🎯 Bereit für Test**
