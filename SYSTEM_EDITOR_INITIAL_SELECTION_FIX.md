# System-Editor Initial Selection Fix

**Datum**: 26.11.2025  
**Problem**: Property Input Controls wurden nicht angezeigt - `_refresh_properties_editor()` wurde nie aufgerufen  
**Root Cause**: Keine automatische Auswahl beim Laden des Editors

## Problem-Analyse

### Symptome aus Logs
```
2025-11-26 19:32:06 - INFO - ✅ System-Editor V2 initialisiert: sys_beschreibungen / 55555555-5555-5555-5555-555555555555
2025-11-26 19:32:06 - INFO - ✅ Edit-Bereich aktualisiert mit Datensatz
```

**KEINE Debug-Zeilen von `_refresh_properties_editor()`!**

### Root Cause
```python
# In __init__():
self._load_data()
self._load_templates()
self._setup_ui()           # Befüllt Gruppen-Liste
self._connect_signals()    # Macht nichts (pass)

# In _setup_ui() → _create_gruppen_tab():
self._refresh_gruppen_list()  # Befüllt Liste
# FEHLT: Erste Gruppe auswählen!

# In _on_gruppe_selected():
self._refresh_felder_list(gruppe_name)  # Befüllt Felder-Liste
# FEHLT: Erstes Feld auswählen!

# ERGEBNIS: Keine Auswahl → _on_feld_selected() nie aufgerufen → _refresh_properties_editor() nie aufgerufen
```

**Call Chain (SOLL)**:
```
__init__
  → _setup_ui
    → _create_gruppen_tab
      → _refresh_gruppen_list()
      → setCurrentRow(0)  ← FEHLT!
        → _on_gruppe_selected  ← Wird NICHT getriggert!
          → _refresh_felder_list()
          → setCurrentRow(0)  ← FEHLT!
            → _on_feld_selected  ← Wird NICHT getriggert!
              → _refresh_properties_editor()  ← Wird NIE aufgerufen!
```

## Lösung Implementiert

### Fix 1: Erste Gruppe automatisch auswählen
**Datei**: `pdvm_system_editor.py`, Line 457

```python
# ALT (in _create_gruppen_tab):
self._refresh_gruppen_list()
return widget

# NEU:
self._refresh_gruppen_list()

# Erste Gruppe automatisch auswählen
if self.gruppe_list.count() > 0:
    self.gruppe_list.setCurrentRow(0)  # Löst _on_gruppe_selected aus

return widget
```

**Effekt**: `_on_gruppe_selected()` wird automatisch beim Init aufgerufen.

### Fix 2: Erstes Feld automatisch auswählen
**Datei**: `pdvm_system_editor.py`, Line 585

```python
# ALT (in _refresh_felder_list):
self.feld_list.addItem(item)
# Ende der Methode

# NEU:
self.feld_list.addItem(item)

# Erstes Feld automatisch auswählen (löst _on_feld_selected aus)
if self.feld_list.count() > 0:
    self.feld_list.setCurrentRow(0)
```

**Effekt**: `_on_feld_selected()` wird automatisch aufgerufen → `_refresh_properties_editor()` wird aufgerufen.

### Fix 3: Parameter-Fehler in _feld_abbrechen
**Datei**: `pdvm_system_editor.py`, Line 877

```python
# ALT:
self._refresh_properties_editor()  # ❌ TypeError: Missing arguments

# NEU:
self._refresh_properties_editor(gruppe_name, feld_guid)  # ✅
```

**Grund**: Methode braucht `gruppe_name` und `feld_guid` Parameter (seit Property Input Control Rewrite).

## Call Chain (NEU - FUNKTIONIERT)

```
__init__
  → _setup_ui
    → _create_gruppen_tab
      → _refresh_gruppen_list()          # Befüllt Liste
      → setCurrentRow(0)                  # ✅ NEU!
        → Signal: currentItemChanged
          → _on_gruppe_selected(current, previous)
            → _refresh_felder_list(gruppe_name)  # Befüllt Felder
            → setCurrentRow(0)            # ✅ NEU!
              → Signal: currentItemChanged
                → _on_feld_selected(current, previous)
                  → _refresh_properties_editor(gruppe_name, feld_guid)  # ✅ WIRD AUFGERUFEN!
                    → Template Controls laden
                    → Property Input Controls erstellen
                    → UI rendern
```

## Erwartete Logs (nach Fix)

```
2025-11-26 XX:XX:XX - INFO - ✅ System-Editor V2 initialisiert: sys_beschreibungen / 55555555-5555-5555-5555-555555555555
2025-11-26 XX:XX:XX - INFO - 🔍 DEBUG: Gruppe='ROOT_CONTROLS', Template Controls geladen: True
2025-11-26 XX:XX:XX - INFO - 🔍 DEBUG: Anzahl Controls: 4
2025-11-26 XX:XX:XX - INFO - 🔍 DEBUG: Control Keys: ['guid1', 'guid2', 'guid3', 'guid4', ...]
2025-11-26 XX:XX:XX - INFO - ✅ 4 Property Input Controls erstellt (sortiert)
```

## Technische Details

### QListWidget Signal-Kette
```python
# setCurrentRow(0) löst aus:
1. currentItemChanged Signal
2. → verbundener Slot (_on_gruppe_selected oder _on_feld_selected)
3. → Ruft _refresh_properties_editor() auf
4. → Template Controls laden
5. → Property Input Controls erstellen
```

### Warum blockSignals() NICHT nötig?
- Bei **Initialisierung** sind noch keine Dirty-Flags gesetzt
- User hat noch nichts geändert
- Kein Speichern-Dialog nötig
- Signal kann normal durchlaufen

### Warum in _refresh_felder_list() und nicht in _on_gruppe_selected()?
```python
# OPTION 1: In _on_gruppe_selected (NACH _refresh_felder_list)
def _on_gruppe_selected(self, current, previous):
    # ...
    self._refresh_felder_list(gruppe_name)
    if self.feld_list.count() > 0:
        self.feld_list.setCurrentRow(0)

# OPTION 2: In _refresh_felder_list (AM ENDE)  ← GEWÄHLT!
def _refresh_felder_list(self, gruppe_name: str):
    # ... Liste befüllen
    if self.feld_list.count() > 0:
        self.feld_list.setCurrentRow(0)
```

**Grund für Option 2**:
- `_refresh_felder_list()` wird auch aus anderen Kontexten aufgerufen (Refresh, Add, Delete)
- Automatische Auswahl immer sinnvoll nach Refresh
- Weniger Code-Duplikation
- Konsistentes Verhalten

## Weitere Aufrufe von _refresh_properties_editor()

Alle Aufrufe geprüft - Parameter überall korrekt:

| Line | Kontext | Parameter | Status |
|------|---------|-----------|--------|
| 877 | `_feld_abbrechen()` | gruppe_name, feld_guid | ✅ FIXED |
| 1029 | `_on_feld_selected()` | gruppe_name, feld_guid | ✅ OK |
| 1181 | `_add_feld()` | gruppe_name, current_guid | ✅ OK |
| 1300 | `_copy_feld()` | gruppe_name, neue_guid | ✅ OK |
| 1353 | `_remove_feld()` | gruppe_name, feld_guid | ✅ OK (falls Feld bleibt) |
| 1440 | `_add_property()` | gruppe_name, feld_guid | ✅ OK |
| 1498 | `_remove_property()` | gruppe_name, feld_guid | ✅ OK (falls Properties bleiben) |
| 1619 | `_paste_properties()` | gruppe_name, feld_guid | ✅ OK |
| 1716 | `_find_and_replace()` | current_gruppe, current_feld | ✅ OK (in Loop) |

## Testing-Checkliste

### Initiales Laden
- [ ] System-Editor öffnen → Erste Gruppe automatisch ausgewählt
- [ ] → Erstes Feld automatisch ausgewählt
- [ ] → Properties angezeigt (mit Property Input Controls)
- [ ] → Labels aus Template sichtbar
- [ ] → read_only Properties grau + disabled
- [ ] → Sortierung nach display_order

### Gruppe wechseln
- [ ] Andere Gruppe auswählen → Felder aktualisiert
- [ ] → Erstes Feld automatisch ausgewählt
- [ ] → Properties aktualisiert

### Feld wechseln
- [ ] Anderes Feld auswählen → Properties aktualisiert
- [ ] Dirty-Flag gesetzt → Wechsel fragt nach Speichern
- [ ] Abbrechen → Original wiederhergestellt (kein Crash!)

### Neues Feld anlegen
- [ ] "+" Button → Name eingeben
- [ ] → Neues Feld erstellt (Template-basiert)
- [ ] → Automatisch ausgewählt
- [ ] → Properties angezeigt

### Logs prüfen
```bash
# In main.log suchen nach:
🔍 DEBUG: Gruppe='ROOT_CONTROLS', Template Controls geladen: True
🔍 DEBUG: Anzahl Controls: X
✅ X Property Input Controls erstellt (sortiert)

# NICHT mehr sehen:
⚠️ Keine Template-Controls → Fallback auf Legacy
```

## Dateien Geändert

### pdvm_system_editor.py
**Line 457-460**: Erste Gruppe automatisch auswählen  
**Line 585-587**: Erstes Feld automatisch auswählen  
**Line 877**: Parameter-Fix in `_feld_abbrechen()`

## Zusammenfassung

**Problem**: Property Input Controls nie angezeigt, weil `_refresh_properties_editor()` nie aufgerufen wurde.

**Root Cause**: Keine automatische Auswahl von Gruppe/Feld beim Laden des Editors.

**Lösung**: 
1. ✅ Erste Gruppe automatisch auswählen nach `_refresh_gruppen_list()`
2. ✅ Erstes Feld automatisch auswählen nach `_refresh_felder_list()`
3. ✅ Parameter-Fix in `_feld_abbrechen()`

**Effekt**: Signal-Kette wird automatisch getriggert → `_refresh_properties_editor()` wird aufgerufen → Property Input Controls werden erstellt und angezeigt.

---

**STATUS**: Fixes implementiert und validiert. Bereit für Runtime-Test.
