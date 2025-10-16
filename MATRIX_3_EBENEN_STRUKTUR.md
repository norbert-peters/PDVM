# 3-EBENEN MATRIX-STRUKTUR für PDVM-System

## 🎯 Konzept-Übersicht

Die Matrix-Datenstruktur verwendet **3 separate Ebenen** für jeden Datenwert, um maximale Flexibilität bei der Anzeige und Formatierung zu ermöglichen:

```
┌─────────────────────────────────────────────────────────────┐
│  MATRIX ROW (Dictionary pro Datensatz)                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Für jedes Control-Feld existieren 3 Keys:                 │
│                                                              │
│  1️⃣ EBENE 1: {control_key}                                 │
│     └─ Rohdatum-Wert (direkt aus DB)                       │
│     └─ Beispiel: 2024365.45833  (YYYYDDD.TIME)             │
│                                                              │
│  2️⃣ EBENE 2: {control_key}_abdatum                         │
│     └─ AB-Datum (Änderungs-Zeitstempel aus DB)            │
│     └─ Beispiel: 2024310.12500  (Datum der letzten Änd.)  │
│                                                              │
│  3️⃣ EBENE 3: {control_key}_formatiertes_abdatum            │
│     └─ Formatiertes AB-Datum (länderspezifisch)           │
│     └─ Formatierung via pdvm_DateTime                      │
│     └─ Beispiel: "05.11.2024 03:00:00"  (DEU-Format)      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 📋 Datenfluss-Pipeline

```
┌─────────────────┐
│  DATENBANK      │  get_value(gruppe, feld, stichtag)
│  PdvmCentral... │  → (wert, abdatum)
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  EBENE 1        │  row_data[control_key] = wert
│  Rohdatum       │  Beispiel: 2024365.45833
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  EBENE 2        │  row_data[f"{control_key}_abdatum"] = abdatum
│  AB-Datum (roh) │  Beispiel: 2024310.12500
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│  EBENE 3        │  formatiertes_abdatum = _format_abdatum(abdatum)
│  Formatiert     │  row_data[f"{control_key}_formatiertes_abdatum"]
│  (länderspez.)  │  Beispiel: "05.11.2024 03:00:00"
└─────────────────┘
         │
         ↓
┌─────────────────┐
│  UI (Tooltip)   │  Anzeige des formatierten Wertes
│  TableWidget    │  item.setToolTip(f"abdatum: {formatiertes_abdatum}")
└─────────────────┘
```

## 🔧 Implementierungs-Details

### Matrix-Struktur (Python Dict)

```python
# Beispiel für einen Matrix-Row:
row_data = {
    # GUID des Datensatzes
    'uid_original': '54073c2c-0efa-4979-8900-2bd1c53d5014',
    
    # BEISPIEL: geburtsdatum_original (3 Ebenen)
    'geburtsdatum_original': 1980001.0,              # EBENE 1: Rohdatum aus DB
    'geburtsdatum_original_abdatum': 2024310.12500,  # EBENE 2: AB-Datum (roh)
    'geburtsdatum_original_formatiertes_abdatum': "05.11.2024 03:00:00",  # EBENE 3: Formatiert
    
    # BEISPIEL: familienname_original (3 Ebenen)
    'familienname_original': 'Müller',               # EBENE 1: Wert aus DB
    'familienname_original_abdatum': 2024305.08000,  # EBENE 2: AB-Datum (roh)
    'familienname_original_formatiertes_abdatum': "01.11.2024 01:55:12",  # EBENE 3: Formatiert
    
    # BEISPIEL: vorname_show (Kopie von _original)
    'vorname_show': 'Hans',                          # EBENE 1: Von _original kopiert
    'vorname_show_abdatum': 2024305.08000,           # EBENE 2: Von _original kopiert
    'vorname_show_formatiertes_abdatum': "01.11.2024 01:55:12",  # EBENE 3: Von _original kopiert
}
```

### Code-Pattern für Matrix-Erstellung

```python
# 1. Wert und AB-Datum aus Datenbank holen
result = instance.get_value(gruppe, feld, gcs.st_inst.PdvmDateTime)

# 2. Tupel auspacken
if isinstance(result, tuple) and len(result) >= 2:
    wert, abdatum = result[0], result[1]
else:
    wert, abdatum = result, None

# 3. EBENE 1: Rohdatum speichern
row_data[control_key] = wert

# 4. EBENE 2: AB-Datum (roh) speichern
row_data[f"{control_key}_abdatum"] = abdatum

# 5. EBENE 3: Formatiertes AB-Datum speichern
if abdatum:
    formatiertes_abdatum = self._format_abdatum(abdatum)
    row_data[f"{control_key}_formatiertes_abdatum"] = formatiertes_abdatum
else:
    row_data[f"{control_key}_formatiertes_abdatum"] = None
```

### Formatierungs-Funktion (_format_abdatum)

```python
def _format_abdatum(self, abdatum_value):
    """
    Formatiert einen Abdatum-Wert länderspezifisch via pdvm_DateTime
    
    Args:
        abdatum_value: Rohdatum aus DB (z.B. 2024310.12500)
        
    Returns:
        str: Formatiertes Datum (z.B. "05.11.2024 03:00:00" für DEU)
    """
    if abdatum_value is None:
        return None
    
    # SPEZIALFALL: Default-Wert 1001.0 (01.01.0001)
    if float(abdatum_value) == 1001.0:
        return "01.01.0001 (Default)"
    
    try:
        # GCS temporäre DateTime-Instanz verwenden
        dt = self.gcs.temp_dt_inst
        if dt is None:
            return f"{abdatum_value} (nicht formatiert)"
        
        # Setze PdvmDateTime und hole formatierte Ausgabe
        dt.PdvmDateTime = float(abdatum_value)
        formatted = dt.FormTimeStamp  # Länderspezifisches Format
        
        return formatted
    except Exception as e:
        logger.debug(f"Fehler bei Abdatum-Formatierung {abdatum_value}: {e}")
        return f"{abdatum_value} (Fehler)"
```

## 🌍 Länderspezifische Formatierung

Die Formatierung erfolgt durch `pdvm_DateTime` basierend auf der GCS-Konfiguration:

```python
# GCS-Konfiguration bestimmt das Format
country = gcs.field_value('country')  # z.B. 'DEU', 'ENG', 'USA'

# pdvm_DateTime verwendet diese Einstellung:
dt = Pdvm_DateTime(country)  # Instanz mit Ländercode

# Automatische Formatierung:
# - DEU: "05.11.2024 03:00:00"  (TT.MM.JJJJ HH:MM:SS)
# - ENG: "05/11/2024 03:00:00"  (DD/MM/YYYY HH:MM:SS)
# - USA: "11/05/2024 03:00:00"  (MM/DD/YYYY HH:MM:SS)
```

## 📊 Verwendung in der UI

### Tooltip-Anzeige (pdvm_view_widget.py)

```python
# Matrix-Daten aus ViewManager holen
result = self.view_manager.get_table_data_for_display()
data = result.get('rows', [])
abdatum_matrix = result.get('abdatum_matrix', None)

# Tabelle füllen mit Tooltip-Integration
for row_idx, row_data in enumerate(data):
    for col_idx, cell_value in enumerate(row_data):
        item = QTableWidgetItem(str(cell_value))
        
        # EBENE 3: Formatiertes Abdatum als Tooltip
        if abdatum_matrix is not None:
            try:
                ab_value = abdatum_matrix[row_idx][col_idx]
                if ab_value is not None:
                    item.setToolTip(f"abdatum: {ab_value}")
            except Exception:
                pass
        
        self.table.setItem(row_idx, col_idx, item)
```

### Matrix-Export für UI (pdvm_view_daten_manager.py)

```python
def get_abdatum_matrix(self, show_only=True):
    """
    Gibt die Abdatum-Matrix für die aktuelle Projektion zurück
    
    Returns:
        List[List[str]]: 2D-Matrix mit formatierten AB-Daten (EBENE 3)
    """
    abdatum_matrix = []
    
    # Projektion anwenden (nur sichtbare Spalten)
    for row in self._internal_matrix:
        abdatum_row = []
        
        for col_name in self.current_projection:
            # EBENE 3: Formatiertes Abdatum holen
            formatted_abdatum = row.get(f"{col_name}_formatiertes_abdatum")
            abdatum_row.append(formatted_abdatum)
        
        abdatum_matrix.append(abdatum_row)
    
    return abdatum_matrix
```

## 🎨 Visualisierung der Ebenen

```
┌──────────────────────────────────────────────────────────────┐
│  DATENSATZ: 54073c2c-0efa-4979-8900-2bd1c53d5014            │
├──────────────────────────────────────────────────────────────┤
│                                                               │
│  geburtsdatum_original:                                      │
│  ├─ 🗄️ EBENE 1 (DB-Wert):       1980001.0                   │
│  ├─ 📅 EBENE 2 (AB-Datum roh):  2024310.12500               │
│  └─ 🎨 EBENE 3 (Formatiert):    "05.11.2024 03:00:00"      │
│                                                               │
│  familienname_original:                                      │
│  ├─ 🗄️ EBENE 1 (DB-Wert):       "Müller"                    │
│  ├─ 📅 EBENE 2 (AB-Datum roh):  2024305.08000               │
│  └─ 🎨 EBENE 3 (Formatiert):    "01.11.2024 01:55:12"      │
│                                                               │
│  vorname_show: (kopiert von vorname_original)               │
│  ├─ 🗄️ EBENE 1 (DB-Wert):       "Hans"                      │
│  ├─ 📅 EBENE 2 (AB-Datum roh):  2024305.08000               │
│  └─ 🎨 EBENE 3 (Formatiert):    "01.11.2024 01:55:12"      │
│                                                               │
└──────────────────────────────────────────────────────────────┘
```

## 🔍 Wichtige Implementierungs-Dateien

### Matrix-Erstellung (3 Ebenen befüllen)
- `pdvm_view_matrix_manager.py` → `initialize_basis_matrix()`
- `pdvm_view_dialog.py` → BasisMatrix-Erstellung (Original-Logik)
- `pdvm_view_daten_manager.py` → `_fill_original_columns()`

### Formatierung (EBENE 3)
- `pdvm_view_matrix_manager.py` → `_format_abdatum()`
- `pd_datetime.py` → `Pdvm_DateTime.FormTimeStamp` Property
- `pd_datetime.py` → Länderspezifische Formatierungs-Parameter

### UI-Integration
- `pdvm_view_widget.py` → Tooltip-Anzeige
- `pdvm_view_ui.py` → Matrix-Tooltip-Integration
- `pdvm_view_daten_manager.py` → `get_abdatum_matrix()`

## 🚀 Anwendungsfälle

### 1. Tooltip mit formatiertem Abdatum
```python
# Benutzer bewegt Maus über Zelle
# → Tooltip zeigt: "abdatum: 05.11.2024 03:00:00"
# → Verwendet EBENE 3 (formatiertes_abdatum)
```

### 2. Länder-Anpassung
```python
# Admin ändert GCS-Konfiguration: country = 'USA'
# → System lädt Daten neu
# → _format_abdatum() verwendet neues Format
# → Tooltip zeigt: "abdatum: 11/05/2024 03:00:00"
```

### 3. Export/Reporting
```python
# Export-Funktion benötigt sowohl:
# - EBENE 1: Rohdaten für technische Verarbeitung
# - EBENE 3: Formatierte Daten für Benutzer-Ansicht
```

### 4. Filter/Suche
```python
# Filter arbeitet mit EBENE 1 (Rohdaten)
# - Performante numerische Vergleiche
# - Keine Parsing-Fehler durch Format-Varianten
```

## ⚠️ Wichtige Hinweise

### 1. **Speicher-Overhead**
- Jedes Feld benötigt 3 Dictionary-Keys
- Bei 100 Spalten → 300 Keys pro Row
- Für 1000 Datensätze → 300.000 Dictionary-Entries
- **Vorteil**: Maximale Performance, keine Neu-Berechnung

### 2. **Konsistenz-Garantie**
- EBENE 2 und EBENE 3 werden IMMER zusammen befüllt
- Keine asynchrone Formatierung
- Einmalige Formatierung bei Matrix-Erstellung

### 3. **Show-Spalten Kopie**
- `_show` Spalten kopieren ALLE 3 Ebenen von `_original`
- Konsistente Abdatum-Daten in beiden Spalten-Typen

### 4. **Default-Werte**
- Abdatum `1001.0` = "01.01.0001 (Default)"
- Kennzeichnet noch nicht bearbeitete Felder
- Spezielle Behandlung in `_format_abdatum()`

## 📚 Referenzen

- **Template-System**: `!guid!` Referenzen in GCS
- **Stichtag-System**: `gcs.st_inst.FormTimeStamp`
- **Duale Datenbank**: `datenbank.db` + `app_data.db`
- **Filter-System**: `LinearFilterExecutionManager`

---

**KRITISCH**: Verwende IMMER alle 3 Ebenen konsistent!
**NIEMALS** nur einzelne Ebenen befüllen oder formatieren.

✅ **KORREKT**: Alle 3 Ebenen in einem Durchgang
❌ **FALSCH**: Nachträgliche Formatierung oder selektive Ebenen
