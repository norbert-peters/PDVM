# Gruppen-Summen Konzept - Lineare Lösung

## 🎯 Problem

Summen-Zeile am Ende funktioniert, aber:
- ❌ Gruppen-Header zeigen keine Gruppen-Summen
- ❌ Gesamtsummen-Zeile zeigt "0" statt echte Werte

## 💡 Lineare Lösung: `group_sums` in `row_type`

### Architektur-Prinzip

**ANALOG zu `count`** - Summen gehören zu Gruppen-Metadaten:

```python
# VORHER (nur count):
row_type = {
    'type': 'group_header',
    'column': 'anrede_show',
    'value': 'Herr',
    'count': 5,  # ← Aggregation
    'level': 0
}

# NACHHER (count + group_sums):
row_type = {
    'type': 'group_header',
    'column': 'anrede_show',
    'value': 'Herr',
    'count': 5,  # ← Aggregation 1
    'group_sums': {  # ← Aggregation 2 (NEU)
        'geburtsdatum_jahr_show': 9945,
        'alter_show': 215
    },
    'level': 0
}
```

### Vorteile

1. ✅ **Linear**: Summen bei Header-Zeile (keine separate Matrix)
2. ✅ **Konsistent**: Analog zu `count` (bereits etabliertes Pattern)
3. ✅ **Erweiterbar**: Weitere Aggregationen möglich (`group_min`, `group_max`, `group_avg`)
4. ✅ **Clean Matrix**: Keine zusätzlichen Spalten in Daten-Zeilen
5. ✅ **UI-freundlich**: Header kann Summen direkt anzeigen

## 🔧 Implementierung

### 1. Gruppen-Header erweitern (pdvm_view_matrix_manager.py)

**In `_insert_group_headers()`**:

```python
# Summen pro Gruppe tracken
group_sums = {}  # {header_uid: {column: sum}}

for idx, row in enumerate(sorted_data):
    # ... Gruppen-Wechsel Logik ...
    
    # Bei Gruppen-Wechsel: Header erstellen
    if group_changed:
        header = self._create_group_header(...)
        header_uid = header.get('uid_original')
        
        # Summen-Dictionary initialisieren
        group_sums[header_uid] = {}
        for col in sum_columns:
            group_sums[header_uid][col] = 0
    
    # Daten-Zeile: Summen akkumulieren
    result.append(row)
    for header_uid in current_headers.values():
        if header_uid in group_sums:
            for col in sum_columns:
                cell = row.get(col)
                value = cell[0] if isinstance(cell, list) else cell
                if isinstance(value, (int, float)):
                    group_sums[header_uid][col] += value

# PASS 2: Counts + Summen in Header eintragen
for row in result:
    row_type_dict = row.get('row_type', {})
    if isinstance(row_type_dict, dict) and row_type_dict.get('type') == 'group_header':
        header_uid = row.get('uid_original')
        
        # Count aktualisieren (wie bisher)
        row['row_type']['count'] = group_counts.get(header_uid, 0)
        
        # Summen aktualisieren (NEU)
        row['row_type']['group_sums'] = group_sums.get(header_uid, {})
```

### 2. Pipeline erweitern (pdvm_pipeline.py)

**In `_apply_sums()`**:

```python
def _apply_sums(self):
    # ... sum_columns laden ...
    
    # Gesamtsummen + Gruppen-Summen berechnen
    total_sums = {}
    current_group_sums = {}
    current_group_header_idx = None
    
    new_matrix = []
    
    for row in self.matrix_sort:
        row_type = row.get('row_type', {})
        
        # === GRUPPEN-HEADER: Summen aus row_type lesen ===
        if isinstance(row_type, dict) and row_type.get('type') == 'group_header':
            # Vorherige Gruppe: Summen-Zeile einfügen (optional)
            # ... 
            
            # Neue Gruppe: Summen aus row_type holen
            group_sums = row_type.get('group_sums', {})
            logger.info(f"📊 Gruppe '{row_type.get('value')}': {group_sums}")
            
            new_matrix.append(row)
            continue
        
        # === DATEN-ZEILE: In Gesamtsummen addieren ===
        for col in sum_columns:
            cell = row.get(col)
            value = cell[0] if isinstance(cell, list) else cell
            if isinstance(value, (int, float)):
                total_sums[col] = total_sums.get(col, 0) + value
        
        new_matrix.append(row)
    
    # Gesamtsummen-Zeile am Ende
    sum_row = {
        'uid_original': 'TOTAL_SUM_ROW',
        'row_type': {
            'type': 'sum_row',
            'label': 'Gesamtsumme',
            'sums': total_sums  # ← Summen in row_type!
        }
    }
    
    # Summen als Spalten-Werte (für UI-Rendering)
    for col in sum_columns:
        sum_row[col] = [total_sums.get(col, 0), None, None]
    
    new_matrix.append(sum_row)
    self.matrix_sum = new_matrix
```

### 3. UI-Rendering erweitern (pdvm_view_ui.py)

**In `_render_group_header_in_table()`**:

```python
def _render_group_header_in_table(self, row_idx, row_type_dict, column_keys):
    # ... bisheriger Code ...
    
    group_value = row_type_dict.get('value', '')
    group_count = row_type_dict.get('count', 0)
    group_sums = row_type_dict.get('group_sums', {})  # ← NEU
    
    # Text mit Summen
    text = f"{indent}{icon} {display_column}: {group_value}"
    if group_count > 0:
        text += f" ({group_count} Einträge)"
    
    # Summen anhängen (optional, kompakt)
    if group_sums:
        sum_parts = [f"{col}: {val}" for col, val in group_sums.items()]
        text += f" | Σ {', '.join(sum_parts)}"
    
    # Tooltip erweitern
    tooltip = (
        f"Gruppierung: {display_column}\n"
        f"Wert: {group_value}\n"
        f"Einträge: {group_count}\n"
    )
    if group_sums:
        tooltip += "Gruppen-Summen:\n"
        for col, val in group_sums.items():
            tooltip += f"  {col}: {val}\n"
```

**Alternative: Summen in eigenen Spalten anzeigen**:

```python
def _render_group_header_in_table(self, row_idx, row_data, row_type_dict, column_keys):
    # ... bisheriger Code ...
    
    group_sums = row_type_dict.get('group_sums', {})
    
    # Für jede Spalte prüfen ob Summe verfügbar
    for col_idx, col_key in enumerate(column_keys):
        if col_idx == 0:
            # Erste Spalte: Gruppen-Text (wie bisher)
            item = QTableWidgetItem(text)
            # Spanning über ALLE Spalten
            self.table_widget.setItem(row_idx, 0, item)
            self.table_widget.setSpan(row_idx, 0, 1, len(column_keys))
            break
        elif col_key in group_sums:
            # Summen-Spalte: Wert anzeigen
            sum_value = group_sums[col_key]
            item = QTableWidgetItem(f"Σ {sum_value}")
            # Styling...
            self.table_widget.setItem(row_idx, col_idx, item)
```

## 📊 Datenfluss

```
Matrix Manager: _insert_group_headers()
  ↓
  Berechnet group_sums pro Header-UID
  ↓
  Speichert in row_type['group_sums']
  ↓
Pipeline: _apply_sums()
  ↓
  Liest group_sums aus row_type (für Gruppen-Summen-Zeilen, optional)
  ↓
  Berechnet total_sums über ALLE Daten-Zeilen
  ↓
  Speichert in sum_row['row_type']['sums']
  ↓
UI: _render_group_header_in_table()
  ↓
  Liest group_sums aus row_type
  ↓
  Zeigt in Header-Zeile oder Tooltip
```

## 🎨 UI-Darstellung (Variante 1: Kompakt)

```
┌─────────────────────────────────────────────────────┐
│ ▼ Anrede: Herr (3 Einträge) | Σ Alter: 127         │ ← Summen im Text
│   Herr | Müller  | 1980 | 44                       │
│   Herr | Schmidt | 1990 | 34                       │
│   Herr | Meyer   | 1975 | 49                       │
│ ▼ Anrede: Frau (2 Einträge) | Σ Alter: 88          │ ← Summen im Text
│   Frau | Weber   | 1985 | 39                       │
│   Frau | Bauer   | 1976 | 49                       │
├─────────────────────────────────────────────────────┤
│ Gesamtsumme (5 Zeilen) |        | Σ 215            │ ← Gesamtsumme
└─────────────────────────────────────────────────────┘
```

## 🎨 UI-Darstellung (Variante 2: Spalten)

```
┌─────────────────────────────────────────────────────┐
│ Anrede          | Name    | Jahr | Alter            │
├─────────────────────────────────────────────────────┤
│ ▼ Herr (3)      |         |      | Σ 127            │ ← Summe in Spalte
│   Herr          | Müller  | 1980 | 44               │
│   Herr          | Schmidt | 1990 | 34               │
│   Herr          | Meyer   | 1975 | 49               │
│ ▼ Frau (2)      |         |      | Σ 88             │ ← Summe in Spalte
│   Frau          | Weber   | 1985 | 39               │
│   Frau          | Bauer   | 1976 | 49               │
├─────────────────────────────────────────────────────┤
│ Gesamtsumme (5) |         |      | 215              │ ← Gesamtsumme
└─────────────────────────────────────────────────────┘
```

## ✅ Vorteile dieser Lösung

1. **Linear**: Summen bei Zeile, keine Lookup-Matrix
2. **Analog zu count**: Etabliertes Pattern wird erweitert
3. **Matrix-Clean**: Keine zusätzlichen Spalten in Daten-Zeilen
4. **Erweiterbar**: Weitere Aggregationen (`min`, `max`, `avg`) möglich:
   ```python
   row_type = {
       'type': 'group_header',
       'count': 5,
       'group_sums': {...},
       'group_min': {...},  # ← Einfach hinzufügen
       'group_max': {...},
       'group_avg': {...}
   }
   ```
5. **UI-flexibel**: Summen im Text oder in Spalten anzeigbar

## 🚀 Implementierungs-Reihenfolge

1. ✅ Matrix Manager: `group_sums` in `_insert_group_headers()` berechnen
2. ✅ Matrix Manager: `group_sums` in `row_type` speichern
3. ✅ Pipeline: `_apply_sums()` liest `group_sums` (für Validierung)
4. ✅ UI: `_render_group_header_in_table()` zeigt `group_sums`
5. ⏳ Optional: Gruppen-Summen-Zeilen nach jeder Gruppe einfügen

## 📝 Alternative (nicht empfohlen)

**Separate Matrix/Dict**: `{group_id: {column: sum}}`
- ❌ Zusätzliche Datenstruktur parallel zu Matrix
- ❌ Synchronisation notwendig
- ❌ Lookup-Overhead beim Rendering
- ❌ Nicht linear

**Zusätzliche Spalte**: `group_sum_alter_show`, `group_sum_jahr_show`
- ❌ Matrix-Verschmutzung (viele zusätzliche Spalten)
- ❌ Alle Daten-Zeilen bekommen `None` in diesen Spalten
- ❌ Schwierig erweiterbar (neue Summen-Spalte = neue Matrix-Spalte)
