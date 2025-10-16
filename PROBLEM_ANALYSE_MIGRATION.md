# PROBLEM-ANALYSE UND MIGRATIONS-PLAN

## 🔍 Identifizierte Probleme

### 1. **Abdatum wird nicht ausgegeben in Matrix-Trace**
**Problem**: Suffix-Mismatch
- **ALT (funktioniert)**: `_abdatum` und `_formatiertes_abdatum`
- **NEU (falsch)**: `__abdatum` und `__formatiert`

**Lösung**: Zurück zu Original-Suffixen

### 2. **Pipeline wird nach Projektion nochmal durchlaufen**
**Problem**: Doppelter Aufruf in Code
**Analyse nötig**: Wo wird Pipeline mehrfach aufgerufen?

### 3. **Tooltip zeigt "Abdatum (nicht vorhanden)"**
**Root Cause**: Falscher Key
- **Alter Code sucht**: `{col_name}_formatiertes_abdatum`
- **Neuer Code liefert**: `{col_name}__formatiert`

**Lösung**: Suffix zurückändern auf `_formatiertes_abdatum`

### 4. **Stichtag-Wechsel aktualisiert View nicht**
**Problem**: Widget hat keine Verbindung zu rebuild_pipeline_with_stichtag()
**Analyse nötig**: Wie war das im alten System verbunden?

### 5. **Migration statt Neuentwicklung**
**Hauptproblem**: Ich habe neu gebaut statt funktionierende Teile zu migrieren

## 📋 MIGRATIONS-PLAN (Richtig)

### Phase 1: Suffix zurück auf Original (KRITISCH)
```python
# FALSCH (neu):
row_data[f"{col_name}__abdatum"] = abdatum
row_data[f"{col_name}__formatiert"] = formatiert

# RICHTIG (alt, funktioniert):
row_data[f"{col_name}_abdatum"] = abdatum
row_data[f"{col_name}_formatiertes_abdatum"] = formatiert
```

### Phase 2: Funktionierende Tooltip-Logik übernehmen
```python
# ALT (funktioniert) - aus pdvm_view_dialog.py Zeile 3020:
abdatum_value = row_data.get(f"{col_name}_formatiertes_abdatum")
if abdatum_value:
    tooltip_parts.append(f"Abdatum: {abdatum_value}")
else:
    tooltip_parts.append("Abdatum: (nicht verfügbar)")
```

### Phase 3: Stichtag-Refresh aus altem System analysieren
**Suchen**: Wie wird Refresh-Button im alten System behandelt?

### Phase 4: Matrix-Logging korrigieren
- Suffix ändern
- Test nochmal laufen lassen

## 🎯 SOFORT-FIXES

1. **Alle `__abdatum` → `_abdatum`**
2. **Alle `__formatiert` → `_formatiertes_abdatum`**
3. **Matrix-Pipeline log_sample() anpassen**
4. **Widget-Tooltip-Code aus altem System übernehmen**

## 📝 Dateien zu ändern

1. `pdvm_view_daten_manager.py`:
   - `_fill_original_columns()` - Suffix ändern
   - `_fill_show_columns()` - Suffix ändern
   - `_debug_print_matrix_row()` - Suffix ändern

2. `pdvm_matrix_pipeline.py`:
   - `log_sample()` - Suffix ändern

3. `pdvm_view_widget_with_tooltips.py`:
   - Tooltip-Logik aus altem System übernehmen
   - Suffix ändern

4. `.github/copilot-instructions.md`:
   - Dokumentation korrigieren
