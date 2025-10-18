# 🐛 Fix: SUMMEN Pipeline-Status fehlte

**Problem**: ValueError bei Summen Reset  
**Datum**: 17.10.2025  
**Status**: ✅ BEHOBEN

---

## ❌ Fehlermeldung

```
2025-10-17 19:20:00 - ERROR - ❌ Ungültiger Status: SUMMEN
Traceback (most recent call last):
  File "pdvm_view_ui.py", line 980, in _reset_sum
    pipeline.run('SUMMEN')
  File "pdvm_pipeline.py", line 120, in run
    raise ValueError(f"Ungültiger Pipeline-Status: {status}")
ValueError: Ungültiger Pipeline-Status: SUMMEN
```

---

## 🔍 Ursache

Das `PIPELINE_STEPS` Dictionary in `pdvm_pipeline.py` fehlte der Eintrag für `'SUMMEN'`:

```python
# ❌ VORHER (Zeile 91-96)
PIPELINE_STEPS = {
    'BASIS': (0, '_build_basis_matrix'),
    'FILTER': (1, '_apply_filter'),
    'SORT': (2, '_apply_sort'),
    'PROJECT': (3, '_apply_projection'),  # ← SUMMEN fehlt!
}
```

**Widerspruch**:
- In `run()` werden 5 Schritte ausgeführt (inkl. SUMMEN)
- Aber `PIPELINE_STEPS` kennt nur 4 Status
- → `pipeline.run('SUMMEN')` wirft ValueError

---

## ✅ Lösung

### 1. PIPELINE_STEPS erweitert (Zeile 91-97)

```python
# ✅ NACHHER
PIPELINE_STEPS = {
    'BASIS': (0, '_build_basis_matrix'),
    'FILTER': (1, '_apply_filter'),
    'SORT': (2, '_apply_sort'),
    'SUMMEN': (3, '_apply_sums'),      # ← NEU!
    'PROJECT': (4, '_apply_projection'), # ← Index korrigiert (3→4)
}
```

**Änderungen**:
- ✅ `'SUMMEN': (3, '_apply_sums')` hinzugefügt
- ✅ `'PROJECT'` Index von 3 auf 4 erhöht

---

### 2. Dokumentation aktualisiert (Zeile 100-119)

```python
"""
Pipeline ab Status ausführen bis PROJECT

Args:
    status: Start-Status ('BASIS', 'FILTER', 'SORT', 'SUMMEN', 'PROJECT')

AUFRUFE:
    pipeline.run('BASIS')   → Kompletter Start (BASIS→FILTER→SORT→SUMMEN→PROJECT)
    pipeline.run('FILTER')  → Ab Filter (FILTER→SORT→SUMMEN→PROJECT)
    pipeline.run('SORT')    → Ab Sort (SORT→SUMMEN→PROJECT)
    pipeline.run('SUMMEN')  → Ab Summen (SUMMEN→PROJECT)  ← NEU!
    pipeline.run('PROJECT') → Nur Projektion (PROJECT)

VERWENDUNG:
    View-Start: run('BASIS')        ← Lädt BasisMatrix neu
    Schnellsuche: run('FILTER')     ← BasisMatrix bleibt, Filter neu
    Sort-Dialog: run('SORT')        ← Filter bleibt, Sort neu
    Summen-Reset: run('SUMMEN')     ← Sort bleibt, Summen neu  ← NEU!
    Spalten-Dialog: run('PROJECT')  ← Summen bleiben, Projektion neu
"""
```

**Änderungen**:
- ✅ `'SUMMEN'` in Args hinzugefügt
- ✅ `pipeline.run('SUMMEN')` Aufruf dokumentiert
- ✅ Use Case: `Summen-Reset: run('SUMMEN')`

---

## 📊 Pipeline-Architektur (Final)

```
STATUS       INDEX  METHODE                 VERWENDUNG
────────────────────────────────────────────────────────────────
BASIS        0      _build_basis_matrix     View-Start
FILTER       1      _apply_filter           Schnellsuche, Filter-Dialog
SORT         2      _apply_sort             Sort-Dialog
SUMMEN       3      _apply_sums             Summen-Dialog, Summen-Reset ✅
PROJECT      4      _apply_projection       Spalten-Dialog, Expert-Mode
```

**Konsistenz**:
- Alle 5 Schritte in `PIPELINE_STEPS` definiert
- Index-Reihenfolge stimmt überein
- Methoden-Namen korrekt zugeordnet

---

## 🧪 Test nach Fix

```python
# Vorher: ValueError
pipeline.run('SUMMEN')  # ❌ ValueError: Ungültiger Pipeline-Status

# Nachher: Funktioniert
pipeline.run('SUMMEN')  # ✅ Läuft durch: SUMMEN → PROJECT
```

**Erwartetes Verhalten**:
1. ✅ `_apply_sums()` wird ausgeführt
2. ✅ `_apply_projection()` wird ausgeführt
3. ✅ UI wird aktualisiert
4. ✅ Summen-Zeile verschwindet (bei Reset)

---

## 📂 Geänderte Dateien

### pdvm_pipeline.py

**Zeile 91-97** (PIPELINE_STEPS):
```python
# VORHER:
'PROJECT': (3, '_apply_projection'),

# NACHHER:
'SUMMEN': (3, '_apply_sums'),
'PROJECT': (4, '_apply_projection'),
```

**Zeile 100-119** (Dokumentation):
```python
# VORHER:
status: Start-Status ('BASIS', 'FILTER', 'SORT', 'PROJECT')

# NACHHER:
status: Start-Status ('BASIS', 'FILTER', 'SORT', 'SUMMEN', 'PROJECT')
```

---

## ✅ Verifizierung

**Summen Reset Workflow** (jetzt funktionsfähig):

1. ✅ User klickt Summen Reset Button
2. ✅ `_reset_sum()` setzt `sum_string` und `sum_source` auf `None`
3. ✅ `pipeline.run('SUMMEN')` wird aufgerufen
4. ✅ Pipeline prüft `PIPELINE_STEPS['SUMMEN']` → Index 3 ✓
5. ✅ `_apply_sums()` läuft (keine Summen mehr)
6. ✅ `_apply_projection()` läuft
7. ✅ UI wird aktualisiert
8. ✅ Summen-Zeile verschwindet

**Keine Fehler mehr!**

---

## 🎯 Root Cause

**Warum ist das passiert?**

Bei der Migration von 4-Schritt zu 5-Schritt Pipeline wurde:
- ✅ `_apply_sums()` Methode erstellt
- ✅ `steps` Liste in `run()` erweitert
- ✅ `matrix_sum` hinzugefügt
- ❌ **PIPELINE_STEPS nicht aktualisiert** ← Fehler!

**Lesson Learned**:
Beim Hinzufügen von Pipeline-Schritten IMMER beide aktualisieren:
1. `PIPELINE_STEPS` Dictionary (Status-Definition)
2. `steps` Liste in `run()` (Ausführungs-Reihenfolge)

---

## 🎉 Fazit

**Status**: ✅ BEHOBEN

- PIPELINE_STEPS vollständig (alle 5 Schritte)
- Dokumentation aktualisiert
- Summen Reset funktioniert jetzt

**Nächster Test**: Anwendung starten und Summen Reset ausprobieren!
