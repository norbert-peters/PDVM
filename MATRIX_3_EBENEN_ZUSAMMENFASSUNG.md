# 3-EBENEN MATRIX-STRUKTUR - ZUSAMMENFASSUNG

## 📋 Übersicht

Die **3-Ebenen Matrix-Struktur** ist eine zentrale Architektur-Komponente des PDVM-Systems, die für jeden Datenwert **drei separate Ebenen** bereitstellt:

1. **EBENE 1**: Rohdatum-Wert aus der Datenbank
2. **EBENE 2**: AB-Datum (Änderungs-Zeitstempel, roh)
3. **EBENE 3**: Formatiertes AB-Datum (länderspezifisch)

## 🎯 Zweck

Diese Struktur ermöglicht:
- ✅ Maximale Performance (keine Neu-Berechnungen)
- ✅ Länderspezifische Formatierung (DEU/ENG/USA)
- ✅ Tooltips mit Änderungs-Zeitstempeln
- ✅ Konsistente Datenstruktur durch alle Pipeline-Ebenen

## 📊 Beispiel

```python
row_data = {
    # Geburtsdatum mit 3 Ebenen
    'geburtsdatum_original': 1980001.0,                        # EBENE 1: DB-Wert
    'geburtsdatum_original_abdatum': 2024310.12500,            # EBENE 2: AB-Datum (roh)
    'geburtsdatum_original_formatiertes_abdatum': "05.11.2024 03:00:00",  # EBENE 3: Formatiert
}
```

## 🔧 Implementierung

### Kern-Code-Pattern

```python
# 1. Daten aus DB holen
result = instance.get_value(gruppe, feld, gcs.st_inst.PdvmDateTime)
wert, abdatum = result[0], result[1] if isinstance(result, tuple) else (result, None)

# 2. Alle 3 Ebenen befüllen (ATOMIC!)
row_data[control_key] = wert
row_data[f"{control_key}_abdatum"] = abdatum
row_data[f"{control_key}_formatiertes_abdatum"] = self._format_abdatum(abdatum)
```

### Formatierungs-Funktion

```python
def _format_abdatum(self, abdatum_value):
    if abdatum_value is None:
        return None
    if float(abdatum_value) == 1001.0:
        return "01.01.0001 (Default)"
    
    dt = self.gcs.temp_dt_inst
    dt.PdvmDateTime = float(abdatum_value)
    return dt.FormTimeStamp  # Länderspezifisch!
```

## 📁 Wichtige Dateien

### Dokumentation
- `MATRIX_3_EBENEN_STRUKTUR.md` - Vollständige technische Dokumentation
- `MATRIX_3_EBENEN_VISUAL.txt` - ASCII-Art Visualisierung
- `matrix_3_ebenen_example.py` - Praktische Code-Beispiele
- `.github/copilot-instructions.md` - Integration in AI-Assistenten

### Implementierung
- `pdvm_view_matrix_manager.py` - Matrix-Pipeline-Manager mit 3-Ebenen-Logik
- `pdvm_view_dialog.py` - Original BasisMatrix-Erstellung
- `pdvm_view_daten_manager.py` - Daten-Layer mit Matrix-Export

### Formatierung & UI
- `pd_datetime.py` - `Pdvm_DateTime` Klasse mit `FormTimeStamp` Property
- `pdvm_view_widget.py` - TableWidget mit Tooltip-Integration (EBENE 3)
- `pdvm_view_ui.py` - UI-Layout mit Matrix-Binding

## ⚠️ KRITISCHE REGELN

### ✅ KORREKT

```python
# Alle 3 Ebenen zusammen befüllen
row_data[key] = wert
row_data[f"{key}_abdatum"] = abdatum
row_data[f"{key}_formatiertes_abdatum"] = self._format_abdatum(abdatum)

# Show-Spalten kopieren ALLE 3 Ebenen
row_data[show_key] = row_data[original_key]
row_data[f"{show_key}_abdatum"] = row_data[f"{original_key}_abdatum"]
row_data[f"{show_key}_formatiertes_abdatum"] = row_data[f"{original_key}_formatiertes_abdatum"]
```

### ❌ FALSCH

```python
# NUR EBENE 1 setzen
row_data[key] = wert  # ❌ Unvollständig!

# Nachträgliche Formatierung
row_data[key] = wert
# ... später ...
row_data[f"{key}_formatiertes_abdatum"] = format(...)  # ❌ Nicht atomic!

# Show-Spalten kopieren nur Wert
row_data[show_key] = row_data[original_key]  # ❌ Ebene 2+3 fehlen!
```

## 🌍 Länderspezifische Formatierung

Die **EBENE 3** wird automatisch länderspezifisch formatiert:

| Land | Raw AB-Datum    | EBENE 3 (Formatiert)     |
|------|-----------------|--------------------------|
| DEU  | 2024310.12500   | "05.11.2024 03:00:00"   |
| ENG  | 2024310.12500   | "05/11/2024 03:00:00"   |
| USA  | 2024310.12500   | "11/05/2024 03:00:00"   |

Basierend auf: `gcs.field_value('country')`

## 💡 Verwendungszwecke

### 1. UI-Tooltips
```python
# Tooltip mit EBENE 3 (formatiert)
formatted_abdatum = row_data.get(f"{col_key}_formatiertes_abdatum")
item.setToolTip(f"abdatum: {formatted_abdatum}")
```

### 2. Export/Reporting
```python
# Export verwendet EBENE 1 (Rohdaten) für technische Verarbeitung
# Export verwendet EBENE 3 (formatiert) für Benutzer-Ansicht
```

### 3. Filter/Suche
```python
# Filter arbeitet mit EBENE 1 (Rohdaten)
# - Performante numerische Vergleiche
# - Keine Format-Varianten-Probleme
```

## 📊 Pipeline-Integration

Die 3-Ebenen-Struktur wird durch die gesamte Matrix-Pipeline beibehalten:

```
BasisMatrix (3 Ebenen)
    ↓
FilterMatrix (3 Ebenen kopiert)
    ↓
SortMatrix (3 Ebenen kopiert)
    ↓
Projektion (EBENE 3 für Tooltips extrahiert)
    ↓
UI (Tooltips mit EBENE 3)
```

## 🔍 Memory-Footprint

**Pro Feld**: 3 Dictionary-Keys
- EBENE 1: ~8 Bytes (float) oder ~20 Bytes (string)
- EBENE 2: ~8 Bytes (float)
- EBENE 3: ~20 Bytes (string)
- **Gesamt**: ~36-48 Bytes pro Feld

**Bei 1000 Datensätzen mit 100 Feldern**:
- Gesamt: ~4.6 MB
- **Vorteil**: Keine Neu-Berechnungen → maximale Performance

## 🚀 Schnellstart

### Neues Matrix-Feld hinzufügen

```python
# In pdvm_view_matrix_manager.py oder pdvm_view_dialog.py

# 1. DB-Abruf
result = instance.get_value('BASIS', 'neues_feld', gcs.st_inst.PdvmDateTime)
wert, abdatum = result[0], result[1] if isinstance(result, tuple) else (result, None)

# 2. 3 Ebenen befüllen
row_data['neues_feld_original'] = wert
row_data['neues_feld_original_abdatum'] = abdatum
row_data['neues_feld_original_formatiertes_abdatum'] = self._format_abdatum(abdatum)

# 3. Show-Spalte erstellen (falls benötigt)
row_data['neues_feld_show'] = row_data['neues_feld_original']
row_data['neues_feld_show_abdatum'] = row_data['neues_feld_original_abdatum']
row_data['neues_feld_show_formatiertes_abdatum'] = row_data['neues_feld_original_formatiertes_abdatum']
```

## 🐛 Debugging

### Matrix-Struktur prüfen

```python
# In matrix_3_ebenen_example.py
matrix_manager = Matrix3EbenenExample(gcs)
matrix_manager._debug_print_matrix_structure(row_data)
```

### Log-Output
```
🔍 === MATRIX-STRUKTUR (Sample Row) ===

  📋 geburtsdatum_original:
    ├─ 🗄️ EBENE 1 (Wert):     1980001.0
    ├─ 📅 EBENE 2 (AB-Datum):  2024310.12500
    └─ 🎨 EBENE 3 (Format):    05.11.2024 03:00:00
```

## 📚 Weiterführende Links

- Haupt-Dokumentation: `MATRIX_3_EBENEN_STRUKTUR.md`
- Code-Beispiele: `matrix_3_ebenen_example.py`
- Visualisierung: `MATRIX_3_EBENEN_VISUAL.txt`
- Filter-System: `linear_filter_execution_manager.py`
- GCS-System: `pdvm_central_systemsteuerung.py`

## ✅ Checkliste für Entwickler

Beim Arbeiten mit der Matrix:

- [ ] Alle 3 Ebenen zusammen befüllen
- [ ] `_format_abdatum()` für EBENE 3 verwenden
- [ ] Show-Spalten kopieren ALLE 3 Ebenen
- [ ] GCS für `temp_dt_inst` verfügbar
- [ ] Keine nachträgliche Formatierung
- [ ] EBENE 3 in Tooltips verwenden
- [ ] EBENE 1 für Filter/Suche verwenden

---

**PDVM-System v0.9 | 3-Ebenen Matrix-Architektur**  
**Stand**: Oktober 2025  
**Status**: ✅ Produktionsreif und dokumentiert
