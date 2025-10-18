# Integer vs Float Summen - Intelligente Type-Detection

**Datum**: 17.10.2025  
**Status**: ✅ VOLLSTÄNDIG IMPLEMENTIERT & GETESTET

## 🎯 Problem

**Anforderung**: 
- Ganzzahl-Summen sollen als **Integer** gespeichert werden (ohne `.00`)
- Float-Summen sollen als **Float** mit Nachkommastellen gespeichert werden

**Vorher**:
```python
# Alle Summen waren Float (wegen float() Konvertierung)
alter_show: 127.0   # ❌ Sollte 127 sein
preis_show: 64.49   # ✅ OK
```

**UI-Anzeige vorher**:
```
Σ 127,00  # ❌ Unnötige Nachkommastellen
Σ 64,49   # ✅ OK
```

## ✅ Lösung: Float-Tracking + Intelligente Konvertierung

### Konzept

1. **Float-Detection während Summierung**:
   - Tracke pro Spalte: Waren Float-Werte dabei?
   - String mit `.` oder `,` → Float erkannt
   - Bereits Float-Wert mit Nachkommastellen → Float erkannt

2. **Integer-Konvertierung am Ende**:
   - Wenn KEINE Floats dabei waren → Konvertiere Summe zu Integer
   - Wenn Floats dabei waren → Behalte als Float

### Implementierung

#### 1. Matrix Manager (Gruppen-Summen)

**Float-Tracking initialisieren**:
```python
group_sums = {}  # {header_uid: {column: sum}}
group_has_floats = {}  # 🆕 {header_uid: {column: bool}}

# Bei Header-Erstellung:
group_has_floats[header_uid] = {}
for col in sum_columns:
    group_sums[header_uid][col] = 0
    group_has_floats[header_uid][col] = False  # Initial: keine Floats
```

**Float-Detection beim Summieren**:
```python
# String-zu-Zahl Konvertierung
if isinstance(value, str):
    try:
        # Dezimaltrennzeichen → Float
        if '.' in value or ',' in value:
            value = float(value.replace(',', '.'))
            group_has_floats[header_uid][col] = True
        else:
            # Ganzzahl-String → Int
            try:
                value = int(value)
            except ValueError:
                value = float(value)
                group_has_floats[header_uid][col] = True
    except (ValueError, TypeError):
        continue

# Original Float mit Nachkommastellen
elif isinstance(value, float):
    if value % 1 != 0:  # Hat Nachkommastellen
        group_has_floats[header_uid][col] = True

# Summieren
if isinstance(value, (int, float)):
    group_sums[header_uid][col] += value
```

**Integer-Konvertierung in PASS 2**:
```python
for row in result:
    if row_type == 'group_header':
        header_uid = row.get('uid_original')
        
        # Konvertiere Summen zu Integer, falls keine Floats dabei waren
        final_sums = {}
        for col, sum_value in group_sums[header_uid].items():
            has_floats = group_has_floats.get(header_uid, {}).get(col, False)
            
            if not has_floats and isinstance(sum_value, float):
                # Keine Floats + keine Nachkommastellen → Integer
                if sum_value % 1 == 0:
                    final_sums[col] = int(sum_value)
                else:
                    final_sums[col] = sum_value
            else:
                final_sums[col] = sum_value
        
        row['row_type']['group_sums'] = final_sums
```

#### 2. Pipeline (Gesamtsummen)

**Float-Tracking initialisieren**:
```python
sums = {}
has_floats = {}  # 🆕

for col in sum_columns:
    sums[col] = 0
    has_floats[col] = False
```

**Float-Detection beim Summieren** (analog zu Matrix Manager):
```python
if isinstance(value, str):
    if '.' in value or ',' in value:
        value = float(value.replace(',', '.'))
        has_floats[col] = True
    else:
        try:
            value = int(value)
        except ValueError:
            value = float(value)
            has_floats[col] = True

elif isinstance(value, float):
    if value % 1 != 0:
        has_floats[col] = True

if isinstance(value, (int, float)):
    sums[col] += value
```

**Integer-Konvertierung vor Summen-Zeile**:
```python
# Konvertiere Summen zu Integer, falls keine Floats dabei waren
final_sums = {}
for col in sum_columns:
    sum_value = sums[col]
    
    if not has_floats.get(col, False) and isinstance(sum_value, float):
        if sum_value % 1 == 0:
            final_sums[col] = int(sum_value)
        else:
            final_sums[col] = sum_value
    else:
        final_sums[col] = sum_value

# Summen-Zeile mit final_sums erstellen
for col in sum_columns:
    sum_row[col] = [final_sums[col], None, None]
```

## ✅ Test-Ergebnisse

**Test-Skript**: `test_integer_float_summen.py`

**Eingabe**:
```python
test_matrix = [
    {'alter_show': ['44', ...], 'preis_show': ['19.99', ...]},   # Int + Float
    {'alter_show': ['34', ...], 'preis_show': ['29.50', ...]},   # Int + Float
    {'alter_show': ['49', ...], 'preis_show': ['15.00', ...]},   # Int + Float
]
```

**Verarbeitung**:
```
alter_show:
  '44' → Int: 44 (kein Float-Flag)
  '34' → Int: 34 (kein Float-Flag)
  '49' → Int: 49 (kein Float-Flag)
  → Summe: 127 (Int) ✅

preis_show:
  '19.99' → Float: 19.99 (Float-Flag gesetzt)
  '29.50' → Float: 29.5 (Float-Flag gesetzt)
  '15.00' → Float: 15.0 (Float-Flag gesetzt)
  → Summe: 64.49 (Float) ✅
```

**Ausgabe**:
```
alter_show: 127 (type=int)
  UI-Display: 'Σ 127'        ✅ Keine Nachkommastellen!

preis_show: 64.49 (type=float)
  UI-Display: 'Σ 64,49'      ✅ Mit Nachkommastellen!
```

## 🎨 UI-Formatierung

**Im UI-Rendering** (`pdvm_view_ui.py`):
```python
# Formatierung basierend auf Type
if isinstance(sum_value, float):
    display_value = f"Σ {sum_value:,.2f}".replace(',', ' ').replace('.', ',')
    # Beispiel: 64.49 → "Σ 64,49"
elif isinstance(sum_value, int):
    display_value = f"Σ {sum_value:,}".replace(',', ' ')
    # Beispiel: 127 → "Σ 127"
```

**Ergebnis**:
- Integer-Summen: `Σ 127` (ohne `.00`)
- Float-Summen: `Σ 64,49` (mit 2 Nachkommastellen)
- Tausender-Trennzeichen: `Σ 1 234` statt `Σ 1234`

## 📊 Entscheidungslogik

```
Wert: '44'
  ↓
String-Check: Kein '.' oder ',' → Versuche int()
  ↓
int('44') = 44 ✅
  ↓
has_floats[col] bleibt False
  ↓
Summe: 127 (int + int + int = int)
  ↓
Final: isinstance(127, int) → Keine Konvertierung nötig
  ↓
UI: 'Σ 127' (ohne Nachkommastellen)
```

```
Wert: '19.99'
  ↓
String-Check: Enthält '.' → float()
  ↓
float('19.99') = 19.99 ✅
  ↓
has_floats[col] = True (Float erkannt!)
  ↓
Summe: 64.49 (float + float + float = float)
  ↓
Final: has_floats[col] = True → Behalte als Float
  ↓
UI: 'Σ 64,49' (mit 2 Nachkommastellen)
```

## 🔧 Geänderte Dateien

1. **pdvm_view_matrix_manager.py** (Zeile 1180-1330):
   - `group_has_floats` Dictionary hinzugefügt
   - Float-Detection beim Summieren
   - Integer-Konvertierung in PASS 2

2. **pdvm_pipeline.py** (Zeile 430-520):
   - `has_floats` Dictionary hinzugefügt
   - Float-Detection beim Summieren
   - Integer-Konvertierung vor Summen-Zeile

## 📝 Wichtige Details

1. **String-Analyse**:
   ```python
   # Dezimaltrennzeichen → Float
   if '.' in value or ',' in value:
       value = float(value.replace(',', '.'))
       has_floats[col] = True
   ```

2. **Float-Nachkommastellen-Check**:
   ```python
   # Float mit echten Nachkommastellen
   if value % 1 != 0:
       has_floats[col] = True
   ```

3. **Integer-Konvertierung nur wenn sinnvoll**:
   ```python
   # NUR konvertieren wenn:
   # 1. Keine Float-Werte dabei waren UND
   # 2. Summe keine Nachkommastellen hat
   if not has_floats[col] and sum_value % 1 == 0:
       final_sum = int(sum_value)
   ```

## 🎉 Zusammenfassung

✅ **Float-Tracking** während Summierung implementiert  
✅ **Intelligente Type-Detection**: String-Analyse + Float-Nachkommastellen-Check  
✅ **Integer-Konvertierung** am Ende (nur wenn sinnvoll)  
✅ **UI-Formatierung** abhängig von Type (int vs float)  
✅ **2 Stellen geändert**: Matrix Manager + Pipeline  
✅ **Test erfolgreich**: 127 (int) vs 64.49 (float)  

**Ergebnis**:
- Ganzzahl-Summen ohne unnötige `.00`
- Float-Summen mit korrekten Nachkommastellen
- Saubere, typsichere Implementierung
- Export-freundlich (korrekte Types in Daten)
