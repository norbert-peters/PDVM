# Phase 3: Gruppierung - Konzept & Implementation

## 🎯 Ziel

Daten nach Spalten gruppieren mit:
- Gruppen-Header-Zeilen (visuell hervorgehoben)
- Collapse/Expand für Gruppen
- Summen-Zeilen an Gruppen-Grenzen

## 📋 Input vom Dialog

Der Dialog liefert bereits `is_group` Flag:

```python
[
    {'column_key': 'anrede_original', 'direction': 'asc', 'is_group': True},   # Gruppierung!
    {'column_key': 'familienname_show', 'direction': 'asc', 'is_group': False}, # Sortierung
    {'column_key': 'vorname_show', 'direction': 'desc', 'is_group': False}
]
```

**Semantik**:
- `is_group=True`: Diese Spalte ist eine **Gruppierungs-Ebene**
- `is_group=False`: Diese Spalte ist nur eine **Sortierungs-Ebene**

**Beispiel-Hierarchie**:
```
Anrede (Gruppe)
├── Herr
│   ├── Müller, Anton
│   ├── Müller, Berta
│   └── Schmidt, Clara
└── Frau
    ├── Meyer, Doris
    └── Weber, Emil
```

## 🏗️ Architektur

### 1. **Daten-Ebene: Matrix Manager**

**Neue Methode**: `apply_grouping()`

```python
def apply_grouping(self, group_columns: list, sort_columns: list):
    """
    Gruppiert die Matrix nach mehreren Spalten.
    
    Args:
        group_columns: [{'column': 'anrede_original', 'direction': 'asc'}, ...]
        sort_columns: [{'column': 'familienname_show', 'direction': 'asc'}, ...]
    
    Ablauf:
        1. Sortiere nach allen Spalten (Gruppen + Sort)
        2. Erkenne Gruppen-Wechsel
        3. Füge Gruppen-Header-Zeilen ein
        4. Berechne Summen an Gruppen-Grenzen
        5. Füge Gruppen-Footer-Zeilen ein
    """
```

**Gruppen-Zeilen Format**:
```python
# GRUPPEN-HEADER
{
    '__ROW_TYPE__': 'GROUP_HEADER',
    '__GROUP_LEVEL__': 0,  # Verschachtelungs-Ebene (0=äußerste)
    '__GROUP_VALUE__': 'Herr',  # Gruppenwert
    '__GROUP_COLUMN__': 'anrede_original',  # Gruppen-Spalte
    '__GROUP_COUNT__': 15,  # Anzahl Zeilen in Gruppe
    '__COLLAPSED__': False,  # Eingeklappt?
    '__GROUP_ID__': 'anrede_original_Herr',  # Eindeutige ID
    # Alle anderen Spalten: None oder ''
}

# NORMALE DATEN-ZEILE
{
    'anrede_original': 'Herr',
    'familienname_show': 'Müller',
    'vorname_show': 'Anton',
    # ... weitere Spalten
    '__ROW_TYPE__': 'DATA'  # Marker
}

# GRUPPEN-FOOTER (Summen)
{
    '__ROW_TYPE__': 'GROUP_FOOTER',
    '__GROUP_LEVEL__': 0,
    '__GROUP_COLUMN__': 'anrede_original',
    '__GROUP_VALUE__': 'Herr',
    # Summierte Spalten:
    'alter_show': 487,  # Summe aller Alter in Gruppe
    'count': 15,  # Anzahl
    # Andere Spalten: None
}
```

### 2. **View-Ebene: Spezielle Rendering**

**In `pdvm_view_widget_with_tooltips.py` (oder neue Klasse)**:

```python
def _populate_table(self, data: list):
    """Befüllt Tabelle mit Gruppen-Unterstützung"""
    
    for row_idx, row_data in enumerate(data):
        row_type = row_data.get('__ROW_TYPE__', 'DATA')
        
        if row_type == 'GROUP_HEADER':
            self._add_group_header_row(row_idx, row_data)
        
        elif row_type == 'GROUP_FOOTER':
            self._add_group_footer_row(row_idx, row_data)
        
        else:  # DATA
            self._add_data_row(row_idx, row_data)

def _add_group_header_row(self, row_idx: int, row_data: dict):
    """Fügt Gruppen-Header-Zeile ein"""
    
    group_level = row_data.get('__GROUP_LEVEL__', 0)
    group_value = row_data.get('__GROUP_VALUE__')
    group_count = row_data.get('__GROUP_COUNT__', 0)
    collapsed = row_data.get('__COLLAPSED__', False)
    
    # Zeile einfügen
    self.table.insertRow(row_idx)
    
    # SPANNING: Über alle Spalten
    item = QTableWidgetItem()
    
    # Einrückung nach Ebene
    indent = "  " * group_level
    
    # Icon: ▼ (offen) oder ▶ (zu)
    icon = "▼" if not collapsed else "▶"
    
    # Text: "[Icon] Ebene: Wert (Anzahl)"
    text = f"{indent}{icon} {group_value} ({group_count} Einträge)"
    item.setText(text)
    
    # Styling
    item.setBackground(QColor("#e3f2fd"))  # Hellblau
    font = item.font()
    font.setBold(True)
    font.setPointSize(font.pointSize() + 1)
    item.setFont(font)
    
    # Erste Spalte setzen, über alle spannen
    self.table.setItem(row_idx, 0, item)
    self.table.setSpan(row_idx, 0, 1, self.table.columnCount())
    
    # Click-Handler: Toggle Collapse
    item.setData(Qt.UserRole, row_data.get('__GROUP_ID__'))
```

### 3. **Controller-Ebene: Bridge**

```python
def handle_sort_request(self, sort_config):
    """Verarbeitet Sort + Gruppierung"""
    
    # Trenne Gruppierungs-Spalten von Sortier-Spalten
    group_columns = []
    sort_columns = []
    
    for col in sort_config:
        col_config = {
            'column': col.get('column_key'),
            'direction': col.get('direction'),
            'use_original': control.get('sortByOriginal', False)
        }
        
        if col.get('is_group', False):
            group_columns.append(col_config)
        else:
            sort_columns.append(col_config)
    
    # An Matrix Manager übergeben
    if group_columns:
        logger.info(f"📊 Gruppierung: {len(group_columns)} Ebenen")
        self.matrix_manager.apply_grouping(group_columns, sort_columns)
    else:
        logger.info(f"🔄 Normale Sortierung: {len(sort_columns)} Spalten")
        self.matrix_manager.apply_sort_config({'columns': sort_columns})
```

## 🔄 Ablauf

### 1. **Sortierung**
```python
# Sortiere nach ALLEN Spalten (Gruppen zuerst, dann Sort)
all_columns = group_columns + sort_columns
sorted_data = self._sort_by_columns(all_columns)
```

### 2. **Gruppen-Erkennung**
```python
# Multi-Level Gruppierung
groups = {}  # {group_id: {'rows': [], 'value': ...}}

for row in sorted_data:
    # Baue Group-Key aus allen Gruppen-Spalten
    group_key_parts = []
    for group_col in group_columns:
        col_name = group_col['column']
        value = row.get(col_name)
        group_key_parts.append(f"{col_name}_{value}")
    
    group_id = "_".join(group_key_parts)
    
    if group_id not in groups:
        groups[group_id] = {
            'rows': [],
            'values': {},  # {column: value} für jede Gruppen-Spalte
            'level': len(group_columns) - 1
        }
    
    groups[group_id]['rows'].append(row)
```

### 3. **Header/Footer einfügen**
```python
result = []

for group_id, group_data in groups.items():
    # HEADER
    header = {
        '__ROW_TYPE__': 'GROUP_HEADER',
        '__GROUP_ID__': group_id,
        '__GROUP_LEVEL__': group_data['level'],
        '__GROUP_VALUE__': group_data['values'],
        '__GROUP_COUNT__': len(group_data['rows']),
        '__COLLAPSED__': False
    }
    result.append(header)
    
    # DATA ROWS
    result.extend(group_data['rows'])
    
    # FOOTER (Summen)
    footer = self._calculate_group_summary(group_data['rows'])
    footer['__ROW_TYPE__'] = 'GROUP_FOOTER'
    footer['__GROUP_ID__'] = group_id
    result.append(footer)

return result
```

### 4. **Collapse/Expand**
```python
def toggle_group(self, group_id: str):
    """Klappt Gruppe ein/aus"""
    
    # Finde alle Zeilen mit diesem group_id
    for row in self.grouped_data:
        if row.get('__GROUP_ID__') == group_id:
            if row.get('__ROW_TYPE__') == 'GROUP_HEADER':
                # Toggle State
                row['__COLLAPSED__'] = not row.get('__COLLAPSED__', False)
        
        elif row.get('__PARENT_GROUP__') == group_id:
            # Verberge/Zeige Daten-Zeilen
            row['__HIDDEN__'] = row['__COLLAPSED__']
    
    # View neu befüllen (nur sichtbare Zeilen)
    self._refresh_view()
```

## 📊 Beispiel-Output

### Input:
```python
[
    {'column_key': 'anrede_original', 'direction': 'asc', 'is_group': True},
    {'column_key': 'familienname_show', 'direction': 'asc', 'is_group': False}
]
```

### Output-Matrix:
```
[GROUP_HEADER] ▼ Herr (3 Einträge)
  [DATA] Herr, Müller, Anton
  [DATA] Herr, Müller, Berta
  [DATA] Herr, Schmidt, Clara
[GROUP_FOOTER] Summe: 3 | Alter: 187

[GROUP_HEADER] ▼ Frau (2 Einträge)
  [DATA] Frau, Meyer, Doris
  [DATA] Frau, Weber, Emil
[GROUP_FOOTER] Summe: 2 | Alter: 145
```

## 🎨 Styling

### Gruppen-Header:
- **Hintergrund**: Hellblau `#e3f2fd`
- **Font**: Bold, +1pt
- **Spanning**: Über alle Spalten
- **Icon**: ▼ (offen) oder ▶ (zu)
- **Click**: Toggle Collapse

### Gruppen-Footer:
- **Hintergrund**: Hellgrau `#f5f5f5`
- **Font**: Italic
- **Border-Top**: 1px solid `#bdbdbd`

### Einrückung:
- Level 0: Keine Einrückung
- Level 1: 2 Spaces
- Level 2: 4 Spaces
- etc.

## 🚀 Implementation Plan

### Phase 3.1: Basis-Gruppierung ✅
- [x] `is_group` aus Dialog verarbeiten
- [ ] Gruppen-Spalten von Sort-Spalten trennen
- [ ] `apply_grouping()` in Matrix Manager
- [ ] Gruppen-Wechsel erkennen
- [ ] Gruppen-Header-Zeilen einfügen

### Phase 3.2: View-Rendering
- [ ] Spezielle Rendering für `__ROW_TYPE__`
- [ ] Spanning über alle Spalten
- [ ] Styling (Farben, Font, Icons)

### Phase 3.3: Collapse/Expand
- [ ] Click-Handler auf Gruppen-Header
- [ ] Toggle State verwalten
- [ ] Zeilen ein-/ausblenden
- [ ] State persistent speichern

### Phase 3.4: Summen
- [ ] Numerische Spalten summieren
- [ ] Text-Spalten zählen
- [ ] Gruppen-Footer-Zeilen
- [ ] Total-Summe am Ende

## 🔧 Technische Details

### Persistierung:
```python
# In App-DB speichern
gcs._app_db.set_value(view_guid, 'group_collapse_state', {
    'anrede_original_Herr': False,  # offen
    'anrede_original_Frau': True    # zugeklappt
})
```

### Performance:
- Gruppierung nur bei Bedarf (wenn `is_group=True`)
- Collapse-State ohne komplettes Re-Grouping
- Summen lazy berechnen (erst beim Rendern)

### Multi-Level:
```python
# 2 Gruppen-Ebenen
[
    {'column_key': 'land', 'is_group': True},      # Level 0
    {'column_key': 'stadt', 'is_group': True},     # Level 1
    {'column_key': 'name', 'is_group': False}      # Sort
]

# Ergebnis:
▼ Deutschland (10 Einträge)
  ▼ Berlin (3)
    - Müller
    - Schmidt
  ▼ München (7)
    - Bauer
▼ Österreich (5 Einträge)
  ▼ Wien (5)
    - Huber
```

## ✅ Status

- ✅ Konzept definiert
- ✅ Dialog liefert `is_group`
- 🔄 Implementation Phase 3.1 läuft
- ⏳ View-Rendering ausstehend
- ⏳ Collapse/Expand ausstehend
- ⏳ Summen ausstehend
