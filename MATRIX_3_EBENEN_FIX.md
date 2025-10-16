# 3-EBENEN MATRIX FIX - KORREKTUR-ANLEITUNG

## 🚨 PROBLEM

Die Tooltips zeigen kein Abdatum, weil:
1. ❌ Die 3 Ebenen werden **nicht konsistent** gespeichert
2. ❌ Abdatum-Matrix ist **separiert** statt integriert
3. ❌ Keys sind **zusammengesetzt** statt über **einheitlichen control_key**

## ✅ LÖSUNG: Einheitlicher Control-Key

### KORREKTE STRUKTUR

```python
# ✅ KORREKT: Einheitlicher control_key mit Suffix-Zugriff
row_data = {
    'geburtsdatum_original': 1980001.0,                        # EBENE 1
    'geburtsdatum_original__abdatum': 2024310.12500,           # EBENE 2  ← __abdatum Suffix!
    'geburtsdatum_original__formatiert': "05.11.2024 03:00",  # EBENE 3  ← __formatiert Suffix!
}

# Zugriff über control_key:
control_key = 'geburtsdatum_original'
wert = row_data[control_key]                      # EBENE 1
abdatum = row_data[f"{control_key}__abdatum"]     # EBENE 2
formatiert = row_data[f"{control_key}__formatiert"]  # EBENE 3
```

### ❌ FALSCH: Zusammengesetzte Keys

```python
# ❌ FALSCH: Zusammengesetzte Keys ohne Basis
row_data = {
    'geburtsdatum_original': 1980001.0,
    'geburtsdatum_original_abdatum': 2024310.12500,           # ❌ Zusammengesetzt
    'geburtsdatum_original_formatiertes_abdatum': "05.11..."  # ❌ Zu lang
}
```

## 🔧 IMPLEMENTIERUNGS-FIX

### 1. Matrix-Erstellung (pdvm_view_daten_manager.py)

```python
def _fill_original_columns(self, row_record: dict, working_db, dt_formatter):
    """Befüllt _original Spalten mit 3 Ebenen"""
    
    for col in self.basis_columns:
        col_name = col['name']
        if not col_name.endswith('_original'):
            continue
        
        gruppe = col.get('gruppe')
        feld = col.get('feld')
        
        if not (gruppe and feld):
            continue
        
        try:
            # DB-Abruf mit Tuple-Rückgabe
            result = working_db.get_value(gruppe, feld, gcs.st_inst.PdvmDateTime)
            
            # Tuple auspacken
            if isinstance(result, tuple) and len(result) >= 2:
                wert, abdatum = result[0], result[1]
            else:
                wert, abdatum = result, None
            
            # === 3 EBENEN MIT SUFFIX-PATTERN ===
            
            # EBENE 1: Wert
            row_record[col_name] = wert
            
            # EBENE 2: AB-Datum (roh)
            row_record[f"{col_name}__abdatum"] = abdatum
            
            # EBENE 3: Formatiert
            if abdatum:
                formatiert = self._format_abdatum(abdatum, dt_formatter)
                row_record[f"{col_name}__formatiert"] = formatiert
            else:
                row_record[f"{col_name}__formatiert"] = None
                
        except Exception as e:
            logger.error(f"❌ Fehler bei {col_name}: {e}")
            row_record[col_name] = None
            row_record[f"{col_name}__abdatum"] = None
            row_record[f"{col_name}__formatiert"] = None

def _format_abdatum(self, abdatum_value, dt_formatter):
    """Formatiert Abdatum länderspezifisch"""
    if abdatum_value is None:
        return None
    if float(abdatum_value) == 1001.0:
        return "01.01.0001 (Default)"
    
    try:
        dt_formatter.PdvmDateTime = float(abdatum_value)
        return dt_formatter.FormTimeStamp
    except Exception as e:
        logger.error(f"❌ Formatierungs-Fehler: {e}")
        return f"{abdatum_value} (Fehler)"
```

### 2. Show-Spalten Kopie

```python
def _fill_show_columns(self, row_record: dict):
    """Kopiert ALLE 3 Ebenen von _original zu _show"""
    
    for col in self.basis_columns:
        col_name = col['name']
        if not col_name.endswith('_show'):
            continue
        
        # Original-Key finden
        original_key = col_name.replace('_show', '_original')
        
        if original_key not in row_record:
            continue
        
        # === ALLE 3 EBENEN KOPIEREN ===
        row_record[col_name] = row_record[original_key]
        row_record[f"{col_name}__abdatum"] = row_record.get(f"{original_key}__abdatum")
        row_record[f"{col_name}__formatiert"] = row_record.get(f"{original_key}__formatiert")
```

### 3. Abdatum-Matrix für UI Export

```python
def get_abdatum_matrix_for_ui(self, projection: List[str]) -> List[List[Optional[str]]]:
    """
    Erstellt Abdatum-Matrix für UI-Tooltips
    
    Args:
        projection: Liste der sichtbaren Spalten (control_keys)
    
    Returns:
        2D-Matrix mit formatierten Abdatum-Werten (EBENE 3)
    """
    abdatum_matrix = []
    
    # Über alle GUIDs iterieren
    for guid in self.column_control.row_guids:
        row_data = self.column_control.get_row_data(guid)
        
        abdatum_row = []
        for control_key in projection:
            # EBENE 3: Formatiertes Abdatum holen
            formatiert = row_data.get(f"{control_key}__formatiert")
            abdatum_row.append(formatiert)
        
        abdatum_matrix.append(abdatum_row)
    
    return abdatum_matrix
```

### 4. UI-Integration (pdvm_view_widget.py)

```python
def _load_table_data(self):
    """Lädt Daten mit Abdatum-Tooltips"""
    
    # Daten vom Manager holen
    result = self.view_manager.get_table_data_for_display()
    data = result.get('rows', [])
    headers = result.get('headers', [])
    abdatum_matrix = result.get('abdatum_matrix', None)
    
    # Tabelle füllen
    for row_idx, row_data in enumerate(data):
        for col_idx, cell_value in enumerate(row_data):
            item = QTableWidgetItem(str(cell_value))
            
            # TOOLTIP: EBENE 3 verwenden
            if abdatum_matrix and row_idx < len(abdatum_matrix):
                abdatum_row = abdatum_matrix[row_idx]
                if col_idx < len(abdatum_row):
                    formatiert = abdatum_row[col_idx]
                    if formatiert:
                        item.setToolTip(f"Geändert: {formatiert}")
            
            self.table.setItem(row_idx, col_idx, item)
```

## 📊 SUFFIX-PATTERN

### Suffix-Konvention

```python
# Basis-Key (control_key)
control_key = 'geburtsdatum_original'

# EBENE 1: Kein Suffix
key_ebene1 = control_key
# → 'geburtsdatum_original'

# EBENE 2: __abdatum Suffix (2 Underscores!)
key_ebene2 = f"{control_key}__abdatum"
# → 'geburtsdatum_original__abdatum'

# EBENE 3: __formatiert Suffix (2 Underscores!)
key_ebene3 = f"{control_key}__formatiert"
# → 'geburtsdatum_original__formatiert'
```

### Warum Double-Underscore `__`?

- ✅ **Klar abgegrenzt** von control_key
- ✅ **Keine Verwechslung** mit field_name
- ✅ **Python-Konvention** für interne Attribute
- ✅ **Einfach zu parsen**: `key.split('__')`

## 🔍 DEBUGGING

### Matrix-Struktur prüfen

```python
# Row-Data inspizieren
row_data = column_control.get_row_data(guid)

for key in sorted(row_data.keys()):
    if '__' in key:
        # Suffix-Key gefunden
        base_key, suffix = key.rsplit('__', 1)
        print(f"  {base_key}")
        print(f"    EBENE 1: {row_data.get(base_key)}")
        print(f"    EBENE 2: {row_data.get(f'{base_key}__abdatum')}")
        print(f"    EBENE 3: {row_data.get(f'{base_key}__formatiert')}")
```

### Abdatum-Matrix prüfen

```python
abdatum_matrix = daten_manager.get_abdatum_matrix_for_ui(projection)

print(f"Abdatum-Matrix: {len(abdatum_matrix)} Zeilen")
for row_idx, row in enumerate(abdatum_matrix[:3]):  # Erste 3 Zeilen
    print(f"  Row {row_idx}: {row}")
```

## ✅ CHECKLISTE

Beim Implementieren der 3-Ebenen-Struktur:

- [ ] Einheitlicher `control_key` als Basis
- [ ] `__abdatum` Suffix für EBENE 2
- [ ] `__formatiert` Suffix für EBENE 3
- [ ] Alle 3 Ebenen **zusammen** befüllen
- [ ] Show-Spalten kopieren **alle 3 Ebenen**
- [ ] `_format_abdatum()` für EBENE 3
- [ ] `get_abdatum_matrix_for_ui()` verwendet EBENE 3
- [ ] UI-Tooltips verwenden `abdatum_matrix`

## 🚀 NÄCHSTE SCHRITTE

1. **pdvm_view_daten_manager.py** aktualisieren:
   - `_fill_original_columns()` mit Suffix-Pattern
   - `_fill_show_columns()` mit 3-Ebenen-Kopie
   - `get_abdatum_matrix_for_ui()` hinzufügen

2. **get_table_data_for_display()** anpassen:
   - `get_abdatum_matrix_for_ui()` aufrufen
   - In `result['abdatum_matrix']` zurückgeben

3. **Testen**:
   - Anwendung starten
   - View öffnen
   - Maus über Zelle bewegen
   - Tooltip mit Abdatum prüfen

---

**Status**: 🔧 Implementierungs-Anleitung  
**Priorität**: 🔴 HOCH - Tooltips funktionieren nicht
